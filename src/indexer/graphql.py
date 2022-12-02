import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, NewType, Optional, Type

import strawberry
from aiohttp import web
from pymongo import MongoClient
from strawberry.aiohttp.views import GraphQLView
from strawberry.types import Info

from . import storage, utils
from .models import ProposalRawStatus, ProposalStatus

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def parse_hex(value: str) -> bytes:
    if not value.startswith("0x"):
        raise ValueError("invalid Hex value")
    return bytes.fromhex(value.replace("0x", ""))


def serialize_hex(token_id: bytes) -> str:
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
    rawStatus: strawberry.Private[str]
    rawStatusHistory: strawberry.Private[list[tuple[str, datetime]]]

    @strawberry.field
    def votingPeriodEndingAt(self) -> datetime:
        return self.submittedAt + timedelta(minutes=self.votingDuration)

    @strawberry.field
    def gracePeriodEndingAt(self) -> datetime:
        return self.votingPeriodEndingAt() + timedelta(minutes=self.graceDuration)

    @strawberry.field
    def approvedToProcessAt(self, info: Info) -> Optional[datetime]:
        if self.status(info) is ProposalStatus.APPROVED_READY:
            return self.gracePeriodEndingAt()

    @strawberry.field
    def rejectedToProcessAt(self, info: Info) -> Optional[datetime]:
        if self.status(info) is ProposalStatus.REJECTED_READY:
            return self.votingPeriodEndingAt()

    @strawberry.field
    def approvedAt(self, info: Info) -> Optional[datetime]:
        if self.status(info) is ProposalStatus.APPROVED:
            return self.get_raw_status_time(ProposalRawStatus.APPROVED)

    @strawberry.field
    def rejectedAt(self, info: Info) -> Optional[datetime]:
        if self.status(info) is ProposalStatus.REJECTED:
            return self.get_raw_status_time(ProposalRawStatus.REJECTED)

    @strawberry.field
    def processedAt(self, info: Info) -> Optional[datetime]:
        return self.approvedAt(info) or self.rejectedAt(info) or None

    def get_raw_status_time(self, status: ProposalRawStatus) -> Optional[datetime]:
        for status_, time_ in self.rawStatusHistory:
            if ProposalRawStatus(status_) is status:
                return time_

    @strawberry.field
    def active(self, info: Info) -> bool:
        return self.status(info).is_active

    @strawberry.field
    def yesVotesTotal(self) -> int:
        return sum(member["shares"] for member in self.yesVotersMembers)

    @strawberry.field
    def noVotesTotal(self) -> int:
        return sum(member["shares"] for member in self.noVotersMembers)

    @strawberry.field
    def totalVotableShares(self, info: Info) -> int:
        members = storage.list_votable_members(
            info=info,
            voting_period_ending_at=self.votingPeriodEndingAt(),
            submitted_at=self.submittedAt,
        )
        return sum(member["shares"] for member in members)

    @strawberry.field
    def currentMajority(self) -> float:
        total_votes = self.yesVotesTotal() + self.noVotesTotal()

        if total_votes == 0:
            return 0

        majority_fraction = self.yesVotesTotal() / total_votes

        return round(majority_fraction * 100, 2)

    @strawberry.field
    def currentQuorum(self, info: Info) -> float:
        total_votable_shares = self.totalVotableShares(info)

        if total_votable_shares == 0:
            return 0

        quroum_fraction = (
            self.yesVotesTotal() + self.noVotesTotal()
        ) / total_votable_shares

        return round(quroum_fraction * 100, 2)

    @strawberry.field
    def timeRemaining(self, info: Info) -> Optional[int]:
        now = utils.utcnow()

        if self.status(info) == ProposalStatus.VOTING_PERIOD:
            return int((now - self.votingPeriodEndingAt()).total_seconds())

        if self.status(info) == ProposalStatus.GRACE_PERIOD:
            return int((now - self.gracePeriodEndingAt()).total_seconds())

    def _handle_submitted_status(self, info: Info) -> ProposalStatus:
        now = utils.utcnow()

        if now < self.votingPeriodEndingAt():
            return ProposalStatus.VOTING_PERIOD

        if (
            self.currentMajority() >= self.majority
            and self.currentQuorum(info) >= self.quorum
        ):
            if now < self.gracePeriodEndingAt():
                return ProposalStatus.GRACE_PERIOD

            return ProposalStatus.APPROVED_READY

        return ProposalStatus.REJECTED_READY

    @strawberry.field
    def status(self, info: Info) -> ProposalStatus:
        raw_status = ProposalRawStatus(self.rawStatus)

        if raw_status is ProposalRawStatus.APPROVED:
            return ProposalStatus.APPROVED

        if raw_status is ProposalRawStatus.REJECTED:
            return ProposalStatus.REJECTED

        if raw_status is ProposalRawStatus.SUBMITTED:
            return self._handle_submitted_status(info)

        return ProposalStatus.UNKNOWN

    @strawberry.field
    def memberDidVote(self, memberAddress: HexValue) -> bool:
        return memberAddress in self.yesVoters + self.noVoters

    # pylint: disable=unused-argument
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
        logger.debug(
            "Creating %s with kwargs: %s, non_kwargs: %s",
            cls.__name__,
            kwargs,
            non_kwargs,
        )

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


@strawberry.type
class GuildKick(Proposal):
    memberAddress: HexValue


@strawberry.type
class Whitelist(Proposal):
    tokenName: str
    tokenAddress: HexValue


@strawberry.type
class UnWhitelist(Proposal):
    tokenName: str
    tokenAddress: HexValue


@strawberry.type
class Swap(Proposal):
    tributeAddress: HexValue
    tributeOffered: int
    paymentAddress: HexValue
    paymentRequested: int


PROPOSAL_TYPE_TO_CLASS: dict[str, Type[Proposal]] = {
    "Signaling": Signaling,
    "Onboard": Onboard,
    "GuildKick": GuildKick,
    "Whitelist": Whitelist,
    "UnWhitelist": UnWhitelist,
    "Swap": Swap,
}


# pylint: disable=too-few-public-methods
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


def get_proposals(info: Info, limit: int = 10, skip: int = 0) -> List[Proposal]:
    proposals = storage.list_proposals(info=info, skip=skip, limit=limit)
    return [PROPOSAL_TYPE_TO_CLASS[doc["type"]].from_mongo(doc) for doc in proposals]


# pylint: disable=unused-argument
def get_members(info: Info, limit: int = 10, skip: int = 0) -> List[Member]:
    members = storage.list_members(info=info)
    return [Member.from_mongo(doc) for doc in members]


@strawberry.type
class Query:
    proposals: List[Proposal] = strawberry.field(resolver=get_proposals)
    members: List[Member] = strawberry.field(resolver=get_members)


schema = strawberry.Schema(query=Query, types=list(PROPOSAL_TYPE_TO_CLASS.values()))


class IndexerGraphQLView(GraphQLView):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self._db = db

    async def get_context(self, _request, _response):
        return {"db": self._db}


async def run_graphql(
    mongo_url: str, db_name: str, host: str = "localhost", port: int = 8080
):
    mongo = MongoClient(mongo_url, tz_aware=True)
    db = mongo[db_name]

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
