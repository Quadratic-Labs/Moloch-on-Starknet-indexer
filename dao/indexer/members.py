from dataclasses import asdict, dataclass

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent

from dao.indexer import storage
from dao.indexer.base_event import BaseEvent
from dao.indexer.deserializer import BlockNumber


@dataclass
class VoteSubmitted(BaseEvent):
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

        await storage.update_proposal(
            proposal_id=self.proposalId,
            update=update_proposal_vote,
            info=info,
        )

        if self.vote:
            update_member_vote = {"$push": {"yesVotes": self.proposalId}}
        else:
            update_member_vote = {"$push": {"noVotes": self.proposalId}}

        await storage.update_member(
            member_address=self.onBehalfAddress,
            update=update_member_vote,
            info=info,
        )


@dataclass
class MemberAdded(BaseEvent):
    memberAddress: bytes
    shares: int
    loot: int
    onboardedAt: BlockNumber

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await info.storage.insert_one("members", asdict(self))


@dataclass
class MemberUpdated(BaseEvent):
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
        return await storage.update_member(
            member_address=self.memberAddress,
            update={"$set": asdict(self)},
            info=info,
        )


@dataclass
class RoleGranted(BaseEvent):
    # TODO: rename account to memberAddress and sender to senderAddress or granteeAddress
    account: bytes
    role: str
    sender: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        # TODO: add roles history
        return await storage.update_member(
            member_address=self.account,
            update={"$push": {"roles": self.role}},
            info=info,
        )


@dataclass
class RoleRevoked(BaseEvent):
    # TODO: rename account to memberAddress and sender to senderAddress or granteeAddress
    account: bytes
    role: str
    sender: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        # TODO: add roles history
        return await storage.update_member(
            member_address=self.account,
            update={"$pull": {"roles": self.role}},
            info=info,
        )
