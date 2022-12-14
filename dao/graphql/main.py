import asyncio

from aiohttp import web
from pymongo import MongoClient
from strawberry.aiohttp.views import GraphQLView

from . import logger
from .schema import schema


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
