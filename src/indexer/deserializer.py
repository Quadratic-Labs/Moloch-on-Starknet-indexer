import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Type, Union

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
    get_block_datetime_utc,
)


class BlockNumber(int):
    pass


async def deserialize_block_number(
    block_number: BlockNumber,
    info: Info,
    block: BlockHeader,
    starknet_event: StarkNetEvent,
) -> datetime:
    if block.number != block_number:
        block = await get_block(
            block_number=block_number, client=info.context["starknet_client"]
        )

    return get_block_datetime_utc(block)


# serializers could take info, block and event parameter just like from_starknet_event
# see the block_number_serializer above for an example
Serializer = Union[
    Callable[[Any], Any], Callable[[Any, Info, BlockHeader, StarkNetEvent], Any]
]


deserializers: dict[Type, Serializer] = {
    int: lambda x: x,
    bool: lambda x: x,
    BlockNumber: deserialize_block_number,
    bytes: int_to_bytes,
    str: felt_to_str,
}


async def deserialize_starknet_event(
    fields: dict[str, Type],
    info: Info,
    block: BlockHeader,
    starknet_event: StarkNetEvent,
) -> dict:
    contract = await get_contract(
        starknet_event.address.hex(), info.context["starknet_client"]
    )

    contract_events = get_contract_events(contract)

    # Takes an abi of the event which data we want to serialize
    emitted_event_abi = contract_events[starknet_event.name]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(contract.data.identifier_manager)

    # Transforms cairo data to python (needs types of the values and values)
    event_data = [int.from_bytes(b, "big") for b in starknet_event.data]
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"],
        values=event_data,
    )

    # TODO: validate the matching between the fields and their types in python_data and __annotations__
    kwargs = {}
    for name, field_type in fields.items():
        if deserializer := deserializers.get(field_type):
            value = getattr(python_data, name)

            # Pass info, block and event arguments if the serializer accepts them
            if function_accepts(deserializer, ("info", "block", "starknet_event")):
                deserialized_value = deserializer(
                    value, info=info, block=block, starknet_event=starknet_event
                )
            else:
                deserialized_value = deserializer(value)

            if asyncio.iscoroutine(deserialized_value):
                deserialized_value = await deserialized_value

            kwargs[name] = deserialized_value
        else:
            raise ValueError(f"No deserializer found for type {field_type}")

    return kwargs
