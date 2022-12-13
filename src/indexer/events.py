# pylint: disable=redefined-builtin
"""Inherit from `Event` to get a free `from_starknet_event` method that creates
in instance from a `StarkNetEvent`, the from_starknet_event method uses the type hints
given in the dataclass to know how to deserialize the values
"""

import logging
from dataclasses import asdict, dataclass
from typing import Optional, Type

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent

from indexer.utils import get_block_datetime_utc

from . import config, utils
from .deserializer import BlockNumber
from .models import ProposalRawStatus

logger = logging.getLogger(__name__)


@dataclass
class Event:
    async def _write_to_events_collection(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        logger.debug("Inserting to 'events': %s", self)

        event_dict = {
            "name": starknet_event.name,
            "emittedAt": get_block_datetime_utc(block),
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


async def update_proposal(
    proposal_id: int,
    update: dict,
    info: Info,
):
    logger.debug("Updating proposal %s with %s", proposal_id, update)
    existing = await info.storage.find_one_and_update(
        collection="proposals",
        filter={"id": proposal_id},
        update=update,
    )
    logger.debug("Existing proposal %s", existing)


async def update_member(
    member_address: bytes,
    update: dict,
    info: Info,
    filter: Optional[dict] = None,
):
    if filter is None:
        filter = {}

    logger.debug("Updating member %s with %s", member_address, update)
    existing = await info.storage.find_one_and_update(
        filter={"memberAddress": member_address, **filter},
        collection="members",
        update=update,
    )
    logger.debug("Existing member %s", existing)


async def get_member(
    member_address: bytes,
    info: Info,
    filter: Optional[dict] = None,
):
    if filter is None:
        filter = {}

    return await info.storage.find_one(
        collection="members",
        filter={"memberAddress": member_address, **filter},
    )


async def update_bank(
    update: dict,
    info: Info,
    filter: Optional[dict] = None,
):
    if filter is None:
        filter = {}

    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)

    # C
    if not await info.storage.find_one("bank", {"bankAddress": bank_address}):
        logger.debug(
            "Bank not found, creating it with %s", {"bankAddress": bank_address}
        )
        await info.storage.insert_one("bank", {"bankAddress": bank_address})

    logger.debug("Updating bank with %s", update)

    existing = await info.storage.find_one_and_update(
        collection="bank",
        filter={"bankAddress": bank_address, **filter},
        update=update,
    )
    logger.debug("Existing bank %s", existing)


async def get_bank(info: Info, filter: Optional[dict] = None):
    if filter is None:
        filter = {}

    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)
    bank = await info.storage.find_one("bank", {"bankAddress": bank_address, **filter})
    return bank


async def add_token_if_not_exists(
    member_address: bytes, token_address: bytes, token_name: str, info: Info
):
    token_address_filter = {"balances.tokenAddress": token_address}

    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)
    if member_address == bank_address:
        bank = await get_bank(info=info, filter=token_address_filter)
        # The member doesn't have the token in his balances list
        # TODO: make it clearer and easier. Ex: use another functions get_balances
        # to avoid checking if the member is None to know if the query returned
        # or not
        if not bank:
            await update_bank(
                info=info,
                update={
                    "$push": {
                        "balances": {
                            "tokenAddress": token_address,
                            "tokenName": token_name,
                        }
                    }
                },
            )

    else:
        member = await get_member(
            member_address=member_address, info=info, filter=token_address_filter
        )
        # The member doesn't have the token in his balances list
        # TODO: make it clearer and easier. Ex: use another functions get_balances
        # to avoid checking if the member is None to know if the query returned
        # or not
        if not member:
            await update_member(
                info=info,
                member_address=member_address,
                update={
                    "$push": {
                        "balances": {
                            "tokenAddress": token_address,
                            "tokenName": token_name,
                        }
                    }
                },
            )


async def get_token_name(info: Info, token_address: bytes) -> Optional[str]:
    bank = await get_bank(info) or {}
    for whitelisted_token in bank.get("whitelistedTokens", []):
        if whitelisted_token["tokenAddress"] == token_address:
            return whitelisted_token["tokenName"]


async def update_balance(
    info: Info,
    block: BlockHeader,
    member_address: bytes,
    token_address: bytes,
    amount: int,
):
    bank_address = utils.int_to_bytes(config.BANK_ADDRESS)
    token_name = await get_token_name(token_address=token_address, info=info)

    await add_token_if_not_exists(
        info=info,
        member_address=member_address,
        token_name=token_name,
        token_address=token_address,
    )

    add_amount_filter = {"balances.tokenAddress": token_address}
    add_amount = {
        "$inc": {"balances.$.amount": amount},
        "$push": {
            "transactions": {
                "tokenAddress": token_address,
                "timestamp": get_block_datetime_utc(block),
                "amount": amount,
            },
        },
    }

    if member_address == bank_address:
        await update_bank(info=info, update=add_amount, filter=add_amount_filter)
    else:
        await update_member(
            info=info,
            member_address=member_address,
            update=add_amount,
            filter=add_amount_filter,
        )


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

        proposal_dict = {
            **asdict(self),
            **proposal_params,
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
            update={"$set": asdict(self)},
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
            update={
                "$set": {"rawStatus": self.status},
                "$push": {
                    "rawStatusHistory": (
                        ProposalRawStatus(self.status).value,
                        get_block_datetime_utc(block),
                    )
                },
            },
            info=info,
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
            update={"$set": asdict(self)},
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
            update={"$set": asdict(self)},
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
            update={"$set": asdict(self)},
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
            update={"$set": asdict(self)},
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

        await update_proposal(
            proposal_id=self.proposalId,
            update=update_proposal_vote,
            info=info,
        )

        if self.vote:
            update_member_vote = {"$push": {"yesVotes": self.proposalId}}
        else:
            update_member_vote = {"$push": {"noVotes": self.proposalId}}

        await update_member(
            member_address=self.onBehalfAddress,
            update=update_member_vote,
            info=info,
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
            member_address=self.memberAddress,
            update={"$set": asdict(self)},
            info=info,
        )


@dataclass
class TokenWhitelisted(Event):
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        token_dict = {
            **asdict(self),
            "whitelistedAt": get_block_datetime_utc(block),
        }
        await update_bank(
            update={"$push": {"whitelistedTokens": token_dict}}, info=info
        )


@dataclass
class TokenUnWhitelisted(Event):
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        token_dict = {
            **asdict(self),
            "unWhitelistedAt": get_block_datetime_utc(block),
        }
        await update_bank(
            update={"$push": {"unWhitelistedTokens": token_dict}}, info=info
        )


@dataclass
class UserTokenBalanceIncreased(Event):
    memberAddress: bytes
    tokenAddress: bytes
    # TODO: why is this ?
    # File "/home/mohammedi/workspace/dao/indexer/src/indexer/utils.py", line 47, in uint256_to_int
    #     return uint[0] + (uint[1] << 128)
    # TypeError: 'int' object is not subscriptable
    # amount: Uint256
    amount: int

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_balance(
            info=info,
            block=block,
            member_address=self.memberAddress,
            token_address=self.tokenAddress,
            amount=self.amount,
        )


@dataclass
class UserTokenBalanceDecreased(Event):
    memberAddress: bytes
    tokenAddress: bytes
    amount: int

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await update_balance(
            info=info,
            block=block,
            member_address=self.memberAddress,
            token_address=self.tokenAddress,
            amount=-self.amount,
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
    "TokenWhitelisted": TokenWhitelisted,
    "TokenUnWhitelisted": TokenUnWhitelisted,
    "UserTokenBalanceIncreased": UserTokenBalanceIncreased,
    "UserTokenBalanceDecreased": UserTokenBalanceDecreased,
}
