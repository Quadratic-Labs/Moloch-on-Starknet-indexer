import asyncio
from datetime import datetime, timedelta
import logging
from typing import List, NewType

import strawberry
from aiohttp import web
from pymongo import MongoClient
from strawberry.aiohttp.views import GraphQLView

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
    description: str
    submittedAt: datetime
    # When it was bytes, we had this error:
    # TypeError: Proposal fields cannot be resolved. Unexpected type '<class 'bytes'>'
    submittedBy: HexValue

    majority: int
    quorum: int
    votingDuration: int
    graceDuration: int

    @strawberry.field
    def votingDurationEndingAt(self) -> datetime:
        return self.submittedAt + timedelta(minutes=self.votingDuration)

    @strawberry.field
    def gracePeriodEndingAt(self) -> datetime:
        return self.submittedAt + timedelta(minutes=self.graceDuration)

    @strawberry.field
    def active(self) -> bool:
        return True

    @classmethod
    def from_mongo(cls, data):
        logger.debug("Creating from mongo: %s", data)
        kwargs = {
            name: value for name, value in data.items() if name in cls.__annotations__
        }
        logger.debug("Annotaions: %s", cls.__annotations__)
        logger.debug("Creating with kwargs: %s", kwargs)
        return cls(**kwargs)


@strawberry.type
class Onboard(Proposal):
    id: int
    title: str
    type: str
    description: str
    submittedAt: datetime
    # When it was bytes, we had this error:
    # TypeError: Proposal fields cannot be resolved. Unexpected type '<class 'bytes'>'
    submittedBy: HexValue

    applicantAddress: HexValue
    shares: int
    loot: int
    tributeOffered: int
    tributeAddress: HexValue

    majority: int
    quorum: int
    votingDuration: int
    graceDuration: int


def get_proposals(info, limit: int = 10, skip: int = 0) -> List[Proposal]:
    db = info.context["db"]

    filter = {"_chain.valid_to": None}

    query = db["proposals"].find(filter).skip(skip).limit(limit).sort("submittedAt", -1)

    return [Onboard.from_mongo(t) for t in query]


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

    schema = strawberry.Schema(query=Query, types=[Onboard])
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
