from dataclasses import asdict
from datetime import datetime
import logging
from typing import Any, Callable, Coroutine, Type
from apibara.model import EventFilter, NewEvents, BlockHeader, StarkNetEvent
from apibara.indexer.runner import IndexerRunner, Info
from apibara.indexer import IndexerRunnerConfiguration
from starknet_py.contract import identifier_manager_from_abi
from starknet_py.utils.data_transformer.data_transformer import DataTransformer
from starknet_py.net.gateway_client import GatewayClient


from . import config, events
from .deserializer import deserialize_starknet_event


EventHandler = Callable[[Info, BlockHeader, StarkNetEvent], Coroutine[Any, Any, None]]

logger = logging.getLogger(__name__)


async def default_new_events_handler(
    info: Info,
    block_events: NewEvents,
    event_classes: dict[str, Type[events.Event]] = None,
):
    if event_classes is None:
        event_classes = events.ALL_EVENTS

    for starknet_event in block_events.events:
        if event_class := event_classes.get(starknet_event.name):
            logger.debug(
                "Handling block=%s, event=%s", block_events.block, starknet_event.name
            )
            kwargs = await deserialize_starknet_event(
                fields=event_class.__annotations__,
                info=info,
                block=block_events.block,
                starknet_event=starknet_event,
            )
            event = event_class(**kwargs)

            await event.handle(
                info=info, block=block_events.block, starknet_event=starknet_event
            )
        else:
            logger.error("Cannot find event handler for %s", starknet_event)


async def run_indexer(
    server_url,
    mongo_url,
    starknet_network_url,
    filters: list[EventFilter],
    ssl=True,
    restart: bool = False,
    indexer_id: str = config.INDEXER_ID,
    new_events_handler=default_new_events_handler,
):

    logger.info(
        "Starting the indexer with server_url=%s, mongo_url=%s, starknet_network_url=%s, indexer_id=%s, restart=%s, ssl=%s, filters=%s",
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
