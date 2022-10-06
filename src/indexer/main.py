"""Apibara indexer entrypoint."""

import asyncio
from functools import wraps

import click

from indexer.graphql import run_graphql_api
from indexer.indexer import run_indexer

DEFAULT_MONGO_URL = "mongodb://apibara:apibara@localhost:27018"
DEFAULT_APIBARA_SERVER_URL = "goerli.starknet.stream.apibara.com"
DEFAULT_APIBARA_SERVER_URL = "localhost:7171"


def async_command(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--server-url",
    default=DEFAULT_APIBARA_SERVER_URL,
    show_default=True,
    help="Apibara stream url.",
)
@click.option(
    "--mongo-url", default=DEFAULT_MONGO_URL, show_default=True, help="MongoDB url."
)
@click.option("--restart", is_flag=True, help="Restart indexing from the beginning.")
@async_command
async def start(server_url, mongo_url, restart):
    """Start the Apibara indexer."""
    await run_indexer(
        restart=restart,
        server_url=server_url,
        mongo_url=mongo_url,
    )


@cli.command()
@click.option(
    "--mongo-url", default=DEFAULT_MONGO_URL, show_default=True, help="MongoDB url."
)
@async_command
async def graphql(mongo_url):
    """Start the GraphQL server."""
    await run_graphql_api(
        mongo_url=mongo_url,
    )
