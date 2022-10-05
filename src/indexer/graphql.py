import asyncio
from datetime import datetime
from typing import List, NewType, Optional

import strawberry
from aiohttp import web
from pymongo import MongoClient
from strawberry.aiohttp.views import GraphQLView
from indexer.indexer import indexer_id


def parse_hex(value):
    if not value.startswith("0x"):
        raise ValueError("invalid Hex value")
    return bytes.fromhex(value.replace("0x", ""))


def serialize_hex(token_id):
    return "0x" + token_id.hex()


HexValue = strawberry.scalar(
    NewType("HexValue", bytes), parse_value=parse_hex, serialize=serialize_hex
)


@strawberry.type
class Transfer:
    from_address: HexValue
    to_address: HexValue
    timestamp: datetime

    @classmethod
    def from_mongo(cls, data):
        return cls(
            from_address=data["from_address"],
            to_address=data["to_address"],
            timestamp=data["timestamp"],
        )


@strawberry.type
class Token:
    token_id: HexValue
    owner: HexValue
    updated_at: datetime

    @strawberry.field
    def transfers(self, info, limit: int = 10, skip: int = 0) -> List[Transfer]:
        db = info.context["db"]
        query = (
            db["transfers"]
            .find({"token_id": self.token_id})
            .limit(limit)
            .skip(skip)
            .sort("timestamp", -1)
        )

        return [Transfer.from_mongo(t) for t in query]

    @classmethod
    def from_mongo(cls, data):
        return cls(
            token_id=data["token_id"],
            owner=data["owner"],
            updated_at=data["updated_at"],
        )


def get_token_by_id(info, id: HexValue) -> Optional[Token]:
    db = info.context["db"]
    token = db["tokens"].find_one({"token_id": id, "_chain.valid_to": None})

    if token is not None:
        return Token.from_mongo(token)
    return None


def get_tokens(
    info, owner: Optional[HexValue] = None, limit: int = 10, skip: int = 0
) -> List[Token]:
    db = info.context["db"]

    filter = {"_chain.valid_to": None}
    if owner is not None:
        filter["owner"] = owner

    query = db["tokens"].find(filter).skip(skip).limit(limit).sort("updated_at", -1)

    return [Token.from_mongo(t) for t in query]


@strawberry.type
class Query:
    tokens: List[Token] = strawberry.field(resolver=get_tokens)
    token: Optional[Token] = strawberry.field(resolver=get_token_by_id)


class IndexerGraphQLView(GraphQLView):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self._db = db

    async def get_context(self, _request, _response):
        return {"db": self._db}


async def run_graphql_api(mongo_url=None):
    if mongo_url is None:
        mongo_url = "mongodb://apibara:apibara@localhost:27017"

    mongo = MongoClient(mongo_url)
    db_name = indexer_id.replace("-", "_")
    db = mongo[db_name]

    schema = strawberry.Schema(query=Query)
    view = IndexerGraphQLView(db, schema=schema)

    app = web.Application()
    app.router.add_route("*", "/graphql", view)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", "8080")
    await site.start()

    print(f"GraphQL server started on port 8080")

    while True:
        await asyncio.sleep(5_000)
