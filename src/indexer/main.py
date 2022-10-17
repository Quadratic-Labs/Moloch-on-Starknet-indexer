"""Apibara indexer entrypoint."""

import asyncio
from functools import wraps

import click
from starknet_py.net.client import Client

from indexer.graphql import run_graphql_api
from indexer.indexer import run_indexer
from indexer import config


def async_command(coro):
    @wraps(coro)
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))

    return wrapper


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--server-url",
    default=config.APIBARA_SERVER_URL,
    show_default=True,
    help="Apibara stream url.",
)
@click.option(
    "--mongo-url", default=config.MONGO_URL, show_default=True, help="MongoDB url."
)
@click.option(
    "--starknet-network-url",
    default=config.STARKNET_NETWORK_URL,
    show_default=True,
    help="Starknet Network url.",
)
@click.option(
    "--restart",
    is_flag=True,
    show_default=True,
    help="Restart indexing from the beginning.",
)
@click.option(
    "--ssl",
    is_flag=True,
    show_default=True,
    help="Wether to use ssl when interacting with Apibara.",
)
@async_command
async def start(server_url, mongo_url, starknet_network_url, restart, ssl):
    """Start the Apibara indexer."""
    await run_indexer(
        server_url=server_url,
        mongo_url=mongo_url,
        starknet_network_url=starknet_network_url,
        restart=restart,
        ssl=ssl,
    )


@cli.command()
@click.option(
    "--mongo-url", default=config.MONGO_URL, show_default=True, help="MongoDB url."
)
@async_command
async def graphql(mongo_url):
    """Start the GraphQL server."""
    await run_graphql_api(
        mongo_url=mongo_url,
    )
