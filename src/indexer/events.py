"""Inherit from `Event` to get a free `from_starknet_event` method that creates
in instance from a `StarkNetEvent`, the from_starknet_event method uses the type hints
given in the dataclass to know how to deserialize the values
"""

import logging
from typing import Type

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent
from dataclasses import dataclass, asdict
from .deserializer import BlockNumber, deserialize_starknet_event

logger = logging.getLogger(__name__)


@dataclass
class Event:
    async def _write_to_events_collection(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.debug("Inserting to 'events': %s", self)
        await info.storage.insert_one("events", asdict(self))

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.warning(f"No custom _handle implemented for {self.__class__.__name__}")

    async def handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await self._write_to_events_collection(info, block, starknet_event)
        await self._handle(info, block, starknet_event)


class UpdateProposalMixin:
    async def _update_proposal(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.debug("Updating proposal %s", self)
        existing = await info.storage.find_one_and_update(
            "proposals",
            {"id": self.id},
            {"$set": asdict(self)},
        )
        logger.debug("Existing proposal %s", existing)


@dataclass
class ProposalAdded(Event):
    id: int
    title: str
    type: str
    description: str
    submittedAt: BlockNumber
    submittedBy: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.debug("Inserting %s", self)
        await info.storage.insert_one("proposals", asdict(self))

        proposal_params = await info.storage.find_one(
            "proposal_params", {"type": self.type}
        )

        if proposal_params is None:
            # TODO: find a better exception for that
            raise Exception(
                f"Cannot find proposal params(majority, quorum ...) for type"
                f" '{self.type}' in 'proposal_params' collection, check if the"
                f" indexer is handling ProposalParamsUpdated events"
            )

        del proposal_params["_id"]

        logger.debug("Updating proposal %s", self)
        existing = await info.storage.find_one_and_update(
            "proposals",
            {"id": self.id},
            {"$set": proposal_params},
        )
        logger.debug("Existing proposal %s", existing)


@dataclass
class ProposalParamsUpdated(Event):
    type: str
    majority: int
    quorum: int
    votingDuration: int
    graceDuration: int

    async def handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.debug("Inserting %s", self)
        await info.storage.insert_one("proposal_params", asdict(self))


@dataclass
class OnboardProposalAdded(Event, UpdateProposalMixin):
    id: int
    applicantAddress: bytes
    shares: int
    loot: int
    tributeOffered: int
    tributeAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):

        return await self._update_proposal(info, block, starknet_event)


@dataclass
class ProposalStatusUpdated(Event, UpdateProposalMixin):
    id: int
    status: int

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):

        return await self._update_proposal(info, block, starknet_event)


@dataclass
class GuildKickProposalAdded(Event, UpdateProposalMixin):
    id: int
    memberAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await self._update_proposal(info, block, starknet_event)


@dataclass
class WhitelisteProposalAdded(Event, UpdateProposalMixin):
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await self._update_proposal(info, block, starknet_event)


@dataclass
class UnWhitelisteProposalAdded(Event, UpdateProposalMixin):
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await self._update_proposal(info, block, starknet_event)


@dataclass
class SwapProposalAdded(Event, UpdateProposalMixin):
    id: int
    tributeAddress: bytes
    tributeOffered: int
    paymentAddress: bytes
    paymentRequested: int

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await self._update_proposal(info, block, starknet_event)


ALL_EVENTS: dict[str, Type[Event]] = {
    "ProposalAdded": ProposalAdded,
    "OnboardProposalAdded": OnboardProposalAdded,
    "ProposalStatusUpdated": ProposalStatusUpdated,
    "ProposalParamsUpdated": ProposalParamsUpdated,
    "SwapProposalAdded": SwapProposalAdded,
}
