"""Inherit from `Event` to get a free `from_starknet_event` method that creates
in instance from a `StarkNetEvent`, the from_starknet_event method uses the type hints
given in the dataclass to know how to deserialize the values
"""

import logging
from dataclasses import asdict, dataclass
from typing import Type

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent

from indexer.utils import get_block_datetime_utc

from .deserializer import BlockNumber
from .models import ProposalRawStatus

logger = logging.getLogger(__name__)


@dataclass
class Event:
    async def _write_to_events_collection(self, info: Info):
        logger.debug("Inserting to 'events': %s", self)
        await info.storage.insert_one("events", asdict(self))

    # pylint: disable=unused-argument
    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.warning("No custom _handle implemented for %s", self.__class__.__name__)

    async def handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await self._write_to_events_collection(info)
        await self._handle(info, block, starknet_event)


async def update_proposal(
    proposal_id: int,
    document: dict,
    info: Info,
):
    logger.debug("Updating proposal %s with %s", proposal_id, document)
    existing = await info.storage.find_one_and_update(
        collection="proposals",
        filter={"id": proposal_id},
        update={"$set": document},
    )
    logger.debug("Existing proposal %s", existing)


@dataclass
class ProposalAdded(Event):
    id: int
    title: str
    type: str
    link: str
    submittedAt: BlockNumber
    submittedBy: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        proposal_dict = {
            **asdict(self),
            "rawStatus": ProposalRawStatus.SUBMITTED.value,
            "rawStatusHistory": [
                (
                    ProposalRawStatus.SUBMITTED.value,
                    get_block_datetime_utc(block),
                )
            ],
        }
        logger.debug("Inserting ProposalAdded(%s)", proposal_dict)
        await info.storage.insert_one("proposals", proposal_dict)

        proposal_params = await info.storage.find_one(
            "proposal_params", {"type": self.type}
        )

        if proposal_params is None:
            # TODO: find a better / more specific exception class
            raise Exception(
                "Cannot find proposal params(majority, quorum ...) for type"
                f" '{self.type}' in 'proposal_params' collection, check if the"
                " indexer is handling ProposalParamsUpdated events"
            )

        del proposal_params["_id"]

        logger.debug("Updating proposal %s", self)
        existing = await info.storage.find_one_and_update(
            collection="proposals",
            filter={"id": self.id},
            update={"$set": proposal_params},
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
        logger.debug("Inserting proposal_params %s", self)
        await info.storage.insert_one("proposal_params", asdict(self))


@dataclass
class OnboardProposalAdded(Event):
    id: int
    applicantAddress: bytes
    shares: int
    loot: int
    tributeOffered: int
    tributeAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_proposal(
            proposal_id=self.id,
            document=asdict(self),
            info=info,
        )


@dataclass
class ProposalStatusUpdated(Event):
    id: int
    status: str

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await update_proposal(
            proposal_id=self.id,
            document={"rawStatus": self.status},
            info=info,
        )

        await info.storage.find_one_and_update(
            collection="proposals",
            filter={"id": self.id},
            update={
                "$push": {
                    "rawStatusHistory": (
                        ProposalRawStatus(self.status).value,
                        get_block_datetime_utc(block),
                    )
                }
            },
        )


@dataclass
class GuildKickProposalAdded(Event):
    id: int
    memberAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_proposal(
            proposal_id=self.id,
            document=asdict(self),
            info=info,
        )


@dataclass
class WhitelistProposalAdded(Event):
    id: int
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_proposal(
            proposal_id=self.id,
            document=asdict(self),
            info=info,
        )


@dataclass
class UnWhitelistProposalAdded(Event):
    id: int
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_proposal(
            proposal_id=self.id,
            document=asdict(self),
            info=info,
        )


@dataclass
class SwapProposalAdded(Event):
    id: int
    tributeAddress: bytes
    tributeOffered: int
    paymentAddress: bytes
    paymentRequested: int

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_proposal(
            proposal_id=self.id,
            document=asdict(self),
            info=info,
        )


# func VoteSubmitted(callerAddress: felt, proposalId: felt, vote: felt, onBehalfAddress: felt) {
@dataclass
class VoteSubmitted(Event):
    callerAddress: bytes
    proposalId: int
    vote: bool
    onBehalfAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        # TODO: store both calledAddress and onBehalfAddress, we'll need to know
        # who voted at some point
        if self.vote:
            update_proposal_vote = {"$push": {"yesVoters": self.onBehalfAddress}}
        else:
            update_proposal_vote = {"$push": {"noVoters": self.onBehalfAddress}}

        await info.storage.find_one_and_update(
            collection="proposals",
            filter={"id": self.proposalId},
            update=update_proposal_vote,
        )

        if self.vote:
            update_member_vote = {"$push": {"yesVotes": self.proposalId}}
        else:
            update_member_vote = {"$push": {"noVotes": self.proposalId}}

        await info.storage.find_one_and_update(
            collection="members",
            filter={"memberAddress": self.onBehalfAddress},
            update=update_member_vote,
        )


@dataclass
class MemberAdded(Event):
    memberAddress: bytes
    shares: int
    loot: int
    onboardedAt: BlockNumber

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await info.storage.insert_one("members", asdict(self))


async def update_member(
    memberAddress: bytes,
    document: dict,
    info: Info,
):
    logger.debug("Updating member %s with %s", memberAddress, document)
    existing = await info.storage.find_one_and_update(
        filter={"memberAddress": memberAddress},
        collection="members",
        update={"$set": document},
    )
    logger.debug("Existing member %s", existing)


@dataclass
class MemberUpdated(Event):
    memberAddress: bytes
    delegateAddress: bytes
    shares: int
    loot: int
    jailed: bool
    lastProposalYesVote: int
    onboardedAt: BlockNumber

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_member(
            memberAddress=self.memberAddress,
            document=asdict(self),
            info=info,
        )


ALL_EVENTS: dict[str, Type[Event]] = {
    "ProposalStatusUpdated": ProposalStatusUpdated,
    "ProposalParamsUpdated": ProposalParamsUpdated,
    "ProposalAdded": ProposalAdded,
    "OnboardProposalAdded": OnboardProposalAdded,
    "GuildKickProposalAdded": GuildKickProposalAdded,
    "WhitelistProposalAdded": WhitelistProposalAdded,
    "UnWhitelistProposalAdded": UnWhitelistProposalAdded,
    "SwapProposalAdded": SwapProposalAdded,
    "VoteSubmitted": VoteSubmitted,
    "MemberAdded": MemberAdded,
    "MemberUpdated": MemberUpdated,
}
