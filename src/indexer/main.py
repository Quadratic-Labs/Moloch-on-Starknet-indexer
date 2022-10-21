"""Apibara indexer entrypoint."""

import asyncio
from functools import wraps

import click
from starknet_py.net.gateway_client import GatewayClient
from apibara.model import EventFilter

from indexer.graphql import run_graphql_api
from indexer.indexer import run_indexer
from indexer.utils import get_contract, get_contract_events
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
@click.option(
    "--contract-address",
    required=True,
    help="The contract address of the events.",
)
@click.option(
    "--events",
    help="The list of the events to listen for, defaults to all events coming from the contract address.",
)
@async_command
async def start(
    server_url,
    mongo_url,
    starknet_network_url,
    restart,
    ssl,
    contract_address,
    events=None,
):
    """Start the Apibara indexer."""
    starknet_client = GatewayClient(starknet_network_url)

    contract = await get_contract(contract_address, starknet_client)
    contract_events = get_contract_events(contract)

    if events is None:
        events = contract_events.keys()

    filters = [EventFilter.from_event_name(name, contract_address) for name in events]

    await run_indexer(
        server_url=server_url,
        mongo_url=mongo_url,
        starknet_network_url=starknet_network_url,
        restart=restart,
        ssl=ssl,
        filters=filters,
    )


@cli.command()
@click.option(
    "--mongo-url", default=config.MONGO_URL, show_default=True, help="MongoDB URL."
)
@click.option(
    "--db-name",
    default=config.INDEXER_ID.replace("-", "_"),
    show_default=True,
    help="MongoDB database name.",
)
@async_command
async def graphql(mongo_url, db_name):
    """Start the GraphQL server."""
    await run_graphql_api(
        mongo_url=mongo_url,
        db_name=db_name,
    )
