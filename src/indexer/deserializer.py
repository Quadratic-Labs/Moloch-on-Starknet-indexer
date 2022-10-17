from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import NamedTuple

from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent
from starknet_py.contract import Contract
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer


# TODO: check https://docs.openzeppelin.com/contracts-cairo/0.3.1/utilities
def int_to_bytes(n: int) -> bytes:
    return n.to_bytes(32, "big")


def str_to_felt(text):
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")


def felt_to_str(felt: int) -> str:
    length = (felt.bit_length() + 7) // 8
    return felt.to_bytes(length, byteorder="big").decode("utf-8")


@lru_cache(maxsize=100)
async def get_contract(address, client) -> Contract:
    return await Contract.from_address(address, client=client)


@lru_cache(maxsize=100)
def get_contract_events(contract: Contract) -> dict:
    return {
        element["name"]: element
        for element in contract.data.abi
        if element["type"] == "event"
    }


async def deserialize_event(
    info: Info, block: BlockHeader, event: StarkNetEvent
) -> NamedTuple:
    contract = await get_contract(event.address.hex(), info.context["starknet_client"])

    contract_events = get_contract_events(contract)

    # Takes an abi of the event which data we want to serialize
    emitted_event_abi = contract_events[event.name]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(contract.data.identifier_manager)

    # Transforms cairo data to python (needs types of the values and values)
    event_data = [int.from_bytes(b, "big") for b in event.data]
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"],
        values=event_data,
    )

    return python_data


@dataclass
class ProposalAdded:
    id: int
    title: str
    type: str
    description: str
    submitted_at: datetime
    submitted_by: bytes

    @classmethod
    async def from_event(cls, info: Info, block: BlockHeader, event: StarkNetEvent):
        python_data = await deserialize_event(info=info, block=block, event=event)
        return cls(
            id=python_data.id,
            title=felt_to_str(python_data.title),
            type=felt_to_str(python_data.type),
            description=felt_to_str(python_data.description),
            # python_data.submittedAt is the block number
            submitted_at=block.timestamp,
            submitted_by=int_to_bytes(python_data.submittedBy),
        )
