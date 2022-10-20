import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, NamedTuple, Type, Union

import stringcase
from apibara import Info
from apibara.model import BlockHeader, StarkNetEvent
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer

from .utils import (
    function_accepts,
    int_to_bytes,
    felt_to_str,
    get_contract,
    get_contract_events,
    get_block,
)


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


class BlockNumber(int):
    pass


async def deserialize_block_number(
    block_number: BlockNumber, info: Info, block: BlockHeader, event: StarkNetEvent
) -> datetime:
    if block.number == block_number:
        return block.timestamp

    block_ = await get_block(
        block_number=block_number, client=info.context["starknet_client"]
    )

    # TODO: make sure block_.timestamp is a real timestamp that could be passed to
    # datetime.fromtimestamp
    return datetime.fromtimestamp(block_.timestamp)


# serializers could take info, block and event parameter just like from_event
# see the block_number_serializer above for an example
Serializer = Union[
    Callable[[Any], Any], Callable[[Any, Info, BlockHeader, StarkNetEvent], Any]
]


class FromEventMixin:
    deserializers: dict[Type, Serializer] = {
        int: lambda x: x,
        BlockNumber: deserialize_block_number,
        bytes: int_to_bytes,
        str: felt_to_str,
    }

    @classmethod
    async def from_event(cls, info: Info, block: BlockHeader, event: StarkNetEvent):
        python_data = await deserialize_event(info=info, block=block, event=event)

        # TODO: validate the matching between the fields and their types in python_data and __annotations__
        kwargs = {}
        for name, field_type in cls.__annotations__.items():
            if deserializer := cls.deserializers.get(field_type):
                # attributes in cairo-contracts use camel case instead of snake case
                # we have to convert the dataclass attribute name
                value = getattr(python_data, stringcase.camelcase(name))

                # Pass info, block and event arguments if the serializer accepts them
                if function_accepts(deserializer, ("info", "block", "event")):
                    deserialized_value = deserializer(
                        value, info=info, block=block, event=event
                    )
                else:
                    deserialized_value = deserializer(value)

                if asyncio.iscoroutine(deserialized_value):
                    deserialized_value = await deserialized_value

                kwargs[name] = deserialized_value
            else:
                raise ValueError(f"No deserializer found for type {field_type}")

        return cls(**kwargs)
