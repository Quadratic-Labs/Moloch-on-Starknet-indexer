from dataclasses import asdict, dataclass

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent

from dao import utils
from dao.indexer import logger, storage
from dao.indexer.base_event import BaseEvent
from dao.indexer.deserializer import BlockNumber
from dao.models import ProposalRawStatus


@dataclass
class ProposalAdded(BaseEvent):
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
                    utils.get_block_datetime_utc(block),
                )
            ],
        }
        logger.debug("Inserting ProposalAdded(%s)", proposal_dict)
        await info.storage.insert_one("proposals", proposal_dict)


@dataclass
class ProposalParamsUpdated(BaseEvent):
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
class OnboardProposalAdded(BaseEvent):
    id: int
    applicantAddress: bytes
    shares: int
    loot: int
    tributeOffered: int
    tributeAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await storage.update_proposal(
            proposal_id=self.id,
            update={"$set": asdict(self)},
            info=info,
        )


@dataclass
class ProposalStatusUpdated(BaseEvent):
    id: int
    status: str

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        await storage.update_proposal(
            proposal_id=self.id,
            update={
                "$set": {"rawStatus": self.status},
                "$push": {
                    "rawStatusHistory": (
                        ProposalRawStatus(self.status).value,
                        utils.get_block_datetime_utc(block),
                    )
                },
            },
            info=info,
        )


@dataclass
class GuildKickProposalAdded(BaseEvent):
    id: int
    memberAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await storage.update_proposal(
            proposal_id=self.id,
            update={"$set": asdict(self)},
            info=info,
        )


@dataclass
class WhitelistProposalAdded(BaseEvent):
    id: int
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await storage.update_proposal(
            proposal_id=self.id,
            update={"$set": asdict(self)},
            info=info,
        )


@dataclass
class UnWhitelistProposalAdded(BaseEvent):
    id: int
    tokenName: str
    tokenAddress: bytes

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await storage.update_proposal(
            proposal_id=self.id,
            update={"$set": asdict(self)},
            info=info,
        )


@dataclass
class SwapProposalAdded(BaseEvent):
    id: int
    tributeAddress: bytes
    tributeOffered: int
    paymentAddress: bytes
    paymentRequested: int

    async def _handle(
        self, info: Info, block: BlockHeader, starknet_event: StarkNetEvent
    ):
        return await storage.update_proposal(
            proposal_id=self.id,
            update={"$set": asdict(self)},
            info=info,
        )
