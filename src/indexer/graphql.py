import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, List, NewType, Optional, Type

import strawberry
from aiohttp import web
from pymongo import MongoClient
from pymongo.database import Database
from strawberry.aiohttp.views import GraphQLView

from .models import ProposalRawStatus, ProposalStatus
from . import utils, storage

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def parse_hex(value):
    if not value.startswith("0x"):
        raise ValueError("invalid Hex value")
    return bytes.fromhex(value.replace("0x", ""))


def serialize_hex(token_id):
    return "0x" + token_id.hex()


HexValue = strawberry.scalar(
    NewType("HexValue", bytes), parse_value=parse_hex, serialize=serialize_hex
)


@strawberry.interface
class Proposal:
    id: int
    title: str
    type: str
    link: str
    submittedAt: datetime
    # When it was bytes, we had this error:
    # TypeError: Proposal fields cannot be resolved. Unexpected type '<class 'bytes'>'
    submittedBy: HexValue

    majority: int
    quorum: int
    votingDuration: int
    graceDuration: int

    yesVoters: list[HexValue] = strawberry.field(default_factory=list)
    noVoters: list[HexValue] = strawberry.field(default_factory=list)

    # private fields are not exposed to the GraphQL API
    yesVotersMembers: strawberry.Private[list[dict]]
    noVotersMembers: strawberry.Private[list[dict]]
    rawStatus: strawberry.Private[int]
    rawStatusHistory: strawberry.Private[list[tuple[int, datetime]]]

    @strawberry.field
    def votingPeriodEndingAt(self) -> datetime:
        return self.submittedAt + timedelta(minutes=self.votingDuration)

    @strawberry.field
    def gracePeriodEndingAt(self) -> datetime:
        return self.votingPeriodEndingAt() + timedelta(minutes=self.graceDuration)

    @strawberry.field
    def approvedToProcessAt(self) -> Optional[datetime]:
        if self.status() is ProposalStatus.APPROVED_READY:
            return self.gracePeriodEndingAt()

    @strawberry.field
    def rejectedToProcessAt(self) -> Optional[datetime]:
        if self.status() is ProposalStatus.REJECTED_READY:
            return self.votingPeriodEndingAt()

    @strawberry.field
    def approvedAt(self) -> Optional[datetime]:
        if self.status() is ProposalStatus.APPROVED:
            return self._get_raw_status_time(ProposalRawStatus.ACCEPTED)

    @strawberry.field
    def rejectedAt(self) -> Optional[datetime]:
        if self.status() is ProposalStatus.REJECTED:
            return self._get_raw_status_time(ProposalRawStatus.REJECTED)

    @strawberry.field
    def processedAt(self) -> Optional[datetime]:
        return self.approvedAt() or self.rejectedAt() or None

    def _get_raw_status_time(self, status: ProposalRawStatus) -> Optional[datetime]:
        for status_, time_ in self.rawStatusHistory:
            if ProposalRawStatus(status_) is status:
                return time_

    @strawberry.field
    def active(self) -> bool:
        return self.status().is_active

    @strawberry.field
    def yesVotesTotal(self) -> int:
        return sum([member["shares"] for member in self.yesVotersMembers])

    @strawberry.field
    def noVotesTotal(self) -> int:
        return sum([member["shares"] for member in self.noVotersMembers])

    @strawberry.field
    def totalVotableShares(self, info) -> int:
        members = storage.list_members(info)
        return sum([member["shares"] for member in members])

    @strawberry.field
    def currentMajority(self) -> float:
        total_votes = self.yesVotesTotal() + self.noVotesTotal()

        if total_votes == 0:
            return 0

        majority_fraction = self.yesVotesTotal() / total_votes

        return round(majority_fraction * 100, 2)

    @strawberry.field
    def currentQuorum(self, info) -> float:
        total_votable_shares = self.totalVotableShares(info)

        if total_votable_shares == 0:
            return 0

        quroum_fraction = (
            self.yesVotesTotal() + self.noVotesTotal()
        ) / total_votable_shares

        return round(quroum_fraction * 100, 2)

    @strawberry.field
    def timeRemaining(self) -> Optional[int]:
        now = utils.utcnow()

        if self.status() == ProposalStatus.VOTING_PERIOD:
            return int((now - self.votingPeriodEndingAt()).total_seconds())

        if self.status() == ProposalStatus.GRACE_PERIOD:
            return int((now - self.gracePeriodEndingAt()).total_seconds())

    def _handle_submitted_status(self) -> ProposalStatus:
        now = utils.utcnow()

        if now < self.votingPeriodEndingAt():
            return ProposalStatus.VOTING_PERIOD

        if (
            self.currentMajority() >= self.majority
            and self.currentQuorum() >= self.quorum
        ):
            if now < self.gracePeriodEndingAt():
                return ProposalStatus.GRACE_PERIOD
            else:
                return ProposalStatus.APPROVED_READY
        else:
            return ProposalStatus.REJECTED_READY

    @strawberry.field
    def status(self) -> ProposalStatus:
        raw_status = ProposalRawStatus(self.rawStatus)

        if raw_status is ProposalRawStatus.ACCEPTED:
            return ProposalStatus.APPROVED

        if raw_status is ProposalRawStatus.REJECTED:
            return ProposalStatus.REJECTED

        if raw_status is ProposalRawStatus.SUBMITTED:
            return self._handle_submitted_status()

        return ProposalStatus.UNKNOWN

    @strawberry.field
    def memberDidVote(self, memberAddress: HexValue) -> bool:
        return memberAddress in self.yesVoters + self.noVoters

    @strawberry.field
    def memberCanVote(self, memberAddress: HexValue) -> bool:
        return True

    @classmethod
    def from_mongo(cls, data: dict):
        logger.debug("Creating proposal from mongo: %s", data)

        fields = utils.all_annotations(cls)

        kwargs = {name: value for name, value in data.items() if name in fields}
        non_kwargs = {name: value for name, value in data.items() if name not in fields}

        logger.debug("Fields: %s", fields)
        logger.debug("Creating %s with kwargs: %s, non_kwargs: %s", cls.__name__, kwargs, non_kwargs)

        proposal = cls(**kwargs)

        proposal.__dict__.update(non_kwargs)

        return proposal


@strawberry.type
class Signaling(Proposal):
    pass


@strawberry.type
class Onboard(Proposal):
    applicantAddress: HexValue
    shares: int
    loot: int
    tributeOffered: int
    tributeAddress: HexValue


PROPOSAL_TYPE_TO_CLASS: dict[str, Type[Proposal]] = {
    "Signaling": Signaling,
    "Onboard": Onboard,
}


def get_proposals(info, limit: int = 10, skip: int = 0) -> List[Proposal]:
    db: Database = info.context["db"]

    current_block_filter = {"_chain.valid_to": None}

    # TODO: use $set with MongoDB Expressions[1] to add fields we need for sorting
    # like timeRemaining and processedAt
    # [1]: https://www.mongodb.com/docs/manual/meta/aggregation-quick-reference/#std-label-aggregation-expressions
    pipeline: list[dict[str, Any]] = [
        {"$match": current_block_filter},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "members",
                "pipeline": [{"$match": current_block_filter}],
                "localField": "yesVoters",
                "foreignField": "memberAddress",
                "as": "yesVotersMembers",
            }
        },
        {
            "$lookup": {
                "from": "members",
                "pipeline": [{"$match": current_block_filter}],
                "localField": "noVoters",
                "foreignField": "memberAddress",
                "as": "noVotersMembers",
            }
        },
        {"$sort": {"submittedAt": -1}},
    ]

    query = db["proposals"].aggregate(pipeline)

    return [PROPOSAL_TYPE_TO_CLASS[doc["type"]].from_mongo(doc) for doc in query]


@strawberry.type
class Member:
    memberAddress: HexValue
    shares: int
    loot: int
    onboardedAt: datetime
    yesVotes: list[HexValue] = strawberry.field(default_factory=list)
    noVotes: list[HexValue] = strawberry.field(default_factory=list)

    @classmethod
    def from_mongo(cls, data: dict):
        logger.debug("Creating member from mongo: %s", data)

        fields = utils.all_annotations(cls)

        kwargs = {name: value for name, value in data.items() if name in fields}
        non_kwargs = {name: value for name, value in data.items() if name not in fields}

        logger.debug("Fields: %s", fields)
        logger.debug("Creating with kwargs: %s, non_kwargs: %s", kwargs, non_kwargs)

        member = cls(**kwargs)

        member.__dict__.update(non_kwargs)

        return member


def get_members(info, limit: int = 10, skip: int = 0) -> List[Member]:
    db: Database = info.context["db"]

    current_block_filter = {"_chain.valid_to": None}

    members = db["members"].find(current_block_filter)

    return [Member.from_mongo(doc) for doc in members]


@strawberry.type
class Query:
    proposals: List[Proposal] = strawberry.field(resolver=get_proposals)
    members: List[Member] = strawberry.field(resolver=get_members)


class IndexerGraphQLView(GraphQLView):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self._db = db

    async def get_context(self, _request, _response):
        return {"db": self._db}


async def run_graphql(
    mongo_url: str, db_name: str, host: str = "localhost", port: int = 8080
):
    mongo = MongoClient(mongo_url)
    db = mongo[db_name]

    schema = strawberry.Schema(query=Query, types=[Signaling, Onboard])
    view = IndexerGraphQLView(db, schema=schema)

    logger.info(schema.as_str())

    app = web.Application()
    app.router.add_route("*", "/graphql", view)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()

    print(f"GraphQL server started at http://{host}:{port}/graphql")

    while True:
        await asyncio.sleep(5_000)
