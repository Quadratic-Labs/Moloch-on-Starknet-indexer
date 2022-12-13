from dataclasses import asdict, dataclass

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent

from dao import utils
from dao.indexer import logger


@dataclass
class BaseEvent:
    async def _write_to_events_collection(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.debug("Inserting to 'events': %s", self)

        event_dict = {
            "name": starknet_event.name,
            "emittedAt": utils.get_block_datetime_utc(block),
            **asdict(self),
        }
        await info.storage.insert_one("events", event_dict)

    # pylint: disable=unused-argument
    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.warning("No custom _handle implemented for %s", self.__class__.__name__)

    async def handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await self._write_to_events_collection(
            info=info, block=block, starknet_event=starknet_event
        )
        await self._handle(info, block, starknet_event)
