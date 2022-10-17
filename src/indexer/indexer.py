from dataclasses import asdict
from datetime import datetime
import logging
from typing import Any, Callable, Coroutine
from apibara.model import EventFilter, NewEvents, Event, BlockHeader, StarkNetEvent
from apibara.indexer.runner import IndexerRunner, Info
from apibara.indexer import IndexerRunnerConfiguration
from starknet_py.contract import identifier_manager_from_abi
from starknet_py.utils.data_transformer.data_transformer import DataTransformer
from starknet_py.net.gateway_client import GatewayClient


from .deserializer import ProposalAdded
from . import config


async def handle_proposal_added_event(
    info: Info, block: BlockHeader, event: StarkNetEvent
):
    proposal_added = await ProposalAdded.from_event(info=info, block=block, event=event)

    logger.debug("Inserting %s", proposal_added)
    await info.storage.insert_one("proposals", asdict(proposal_added))


async def handle_xxxx_event(info: Info, block: BlockHeader, event: StarkNetEvent):
    pass


EventHandler = Callable[[Info, BlockHeader, StarkNetEvent], Coroutine[Any, Any, None]]

DEFAULT_EVENT_HANDLERS: dict[str, EventHandler] = {
    "ProposalAdded": handle_proposal_added_event,
    "xxxx": handle_xxxx_event,
}

logger = logging.getLogger(__name__)


async def default_new_events_handler(
    info: Info,
    block_events: NewEvents,
    event_handlers: dict[str, EventHandler] = None,
):
    if event_handlers is None:
        event_handlers = DEFAULT_EVENT_HANDLERS

    for event in block_events.events:
        if event_handler := event_handlers.get(event.name):
            logger.debug("Handling block=%s, event=%s", block_events.block, event)
            await event_handler(info, block_events.block, event)
        else:
            logger.error("Cannot find event_handler for %s", event)


DEFAULT_FILTERS = [
    EventFilter.from_event_name(
        name="Transfer",
        address="0x0266b1276d23ffb53d99da3f01be7e29fa024dd33cd7f7b1eb7a46c67891c9d0",
    ),
]


async def run_indexer(
    server_url,
    mongo_url,
    starknet_network_url,
    ssl=True,
    restart: bool = False,
    indexer_id: str = config.INDEXER_ID,
    new_events_handler=default_new_events_handler,
    filters: list[EventFilter] = None,
):
    if filters is None:
        filters = DEFAULT_FILTERS

    logger.info(
        "Starting the indexer with server_url=%s, mongo_url=%s, indexer_id=%s restart=%s",
        server_url,
        mongo_url,
        indexer_id,
        restart,
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
