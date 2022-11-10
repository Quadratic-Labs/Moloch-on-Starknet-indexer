import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, List, NewType, Type

import strawberry
from aiohttp import web
from pymongo import MongoClient
from pymongo.database import Database
from strawberry.aiohttp.views import GraphQLView

from .models import ProposalStatus
from .utils import all_annotations

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

    yesVotes: list[HexValue] = strawberry.field(default_factory=list)
    noVotes: list[HexValue] = strawberry.field(default_factory=list)

    @strawberry.field
    def votingDurationEndingAt(self) -> datetime:
        return self.submittedAt + timedelta(minutes=self.votingDuration)

    @strawberry.field
    def gracePeriodEndingAt(self) -> datetime:
        return self.votingDurationEndingAt() + timedelta(minutes=self.graceDuration)

    @strawberry.field
    def active(self) -> bool:
        return True

    @strawberry.field
    def yesVotesTotal(self) -> int:
        return sum([member["shares"] for member in self.yesVotesMembers])

    @strawberry.field
    def noVotesTotal(self) -> int:
        return sum([member["shares"] for member in self.noVotesMembers])

    @strawberry.field
    def totalVotableShares(self, info) -> int:
        db: Database = info.context["db"]
        # TODO: Filter only users who could have voted for this particular proposal
        # TODO: Use dataloaders or any other mechanism for caching
        members = db["members"].find({"_chain.valid_to": None})
        return sum([member["shares"] for member in members])

    @strawberry.field
    def currentMajority(self) -> float:
        # TODO: is this a fraction like 0.5 or an int from 0 to 100 ?
        return self.yesVotesTotal() / (self.yesVotesTotal() + self.noVotesTotal())

    @strawberry.field
    def currentQuorum(self, info) -> float:
        return (self.yesVotesTotal() + self.noVotesTotal()) / self.totalVotableShares(
            info
        )

    @strawberry.field
    def status(self) -> str:
        now = datetime.utcnow()

        if now < self.votingDurationEndingAt():
            return ProposalStatus.VOTING_PERIOD.value

        if (
            self.currentMajority() >= self.majority
            and self.currentQuorum() >= self.quorum
        ):
            if now < self.gracePeriodEndingAt():
                return ProposalStatus.GRACE_PERIOD.value
            else:
                return ProposalStatus.APPROVED_READY.value
        else:
            return ProposalStatus.REJECTED_READY.value

    @classmethod
    def from_mongo(cls, data: dict):
        logger.debug("Creating from mongo: %s", data)

        fields = all_annotations(cls)

        kwargs = {name: value for name, value in data.items() if name in fields}
        non_kwargs = {name: value for name, value in data.items() if name not in fields}

        logger.debug("Fields: %s", fields)
        logger.debug("Creating with kwargs: %s, non_kwargs: %s", kwargs, non_kwargs)

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

    pipeline: list[dict[str, Any]] = [
        {"$match": current_block_filter},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "members",
                "pipeline": [{"$match": current_block_filter}],
                "localField": "yesVotes",
                "foreignField": "memberAddress",
                "as": "yesVotesMembers",
            }
        },
        {
            "$lookup": {
                "from": "members",
                "pipeline": [{"$match": current_block_filter}],
                "localField": "noVotes",
                "foreignField": "memberAddress",
                "as": "noVotesMembers",
            }
        },
        {"$sort": {"submittedAt": -1}},
    ]

    query = db["proposals"].aggregate(pipeline)

    return [PROPOSAL_TYPE_TO_CLASS[doc["type"]].from_mongo(doc) for doc in query]


@strawberry.type
class Query:
    proposals: List[Proposal] = strawberry.field(resolver=get_proposals)


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
