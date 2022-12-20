from typing import Any, Callable, Coroutine

from apibara import IndexerRunner, Info
from apibara.indexer import IndexerRunnerConfiguration
from apibara.model import BlockHeader, EventFilter, StarkNetEvent
from starknet_py.net.gateway_client import GatewayClient

from dao import config
from dao.indexer import logger
from dao.indexer.handler import default_new_events_handler

EventHandler = Callable[[Info, BlockHeader, StarkNetEvent], Coroutine[Any, Any, None]]


# pylint: disable=too-many-arguments
async def run_indexer(
    server_url,
    mongo_url,
    starknet_network_url,
    filters: list[EventFilter],
    ssl=True,
    restart: bool = False,
    indexer_id: str = config.indexer_id,
    new_events_handler=default_new_events_handler,
):
    logger.info(
        "Starting the indexer with server_url=%s, mongo_url=%s,"
        " starknet_network_url=%s, indexer_id=%s, restart=%s, ssl=%s, filters=%s",
        server_url,
        mongo_url,
        starknet_network_url,
        indexer_id,
        restart,
        ssl,
        filters,
    )

    runner = IndexerRunner(
        config=IndexerRunnerConfiguration(
            apibara_url=server_url,
            apibara_ssl=ssl,
            storage_url=mongo_url,
        ),
        reset_state=restart,
        indexer_id=indexer_id,
        new_events_handler=new_events_handler,
    )

    runner.set_context(
        {
            "starknet_network_url": starknet_network_url,
            "starknet_client": GatewayClient(starknet_network_url),
        }
    )

    # Create the indexer if it doesn't exist on the server,
    # otherwise it will resume indexing from where it left off.
    #
    # For now, this also helps the SDK map between human-readable
    # event names and StarkNet events.
    runner.create_if_not_exists(filters=filters)

    logger.info("Initialization completed. Entering main loop.")

    await runner.run()
