from datetime import datetime
from typing import NewType

import strawberry

from dao import utils

from . import logger


def parse_hex(value: str) -> bytes:
    if not value.startswith("0x"):
        raise ValueError("invalid Hex value")
    return bytes.fromhex(value.replace("0x", ""))


def serialize_hex(token_id: bytes) -> str:
    return "0x" + token_id.hex()


HexValue = strawberry.scalar(
    NewType("HexValue", bytes), parse_value=parse_hex, serialize=serialize_hex
)


class FromMongoMixin:
    @classmethod
    def from_mongo(cls, data: dict):
        logger.debug("Creating %s from mongo data: %s", cls.__name__, data)

        fields = utils.all_annotations(cls)

        kwargs = {name: value for name, value in data.items() if name in fields}
        non_kwargs = {name: value for name, value in data.items() if name not in fields}

        logger.debug("Fields: %s", fields)
        logger.debug(
            "Creating %s with kwargs: %s, non_kwargs: %s",
            cls.__name__,
            kwargs,
            non_kwargs,
        )

        instance = cls(**kwargs)

        instance.__dict__.update(non_kwargs)

        return instance


@strawberry.type
class Balance:
    tokenName: str
    tokenAddress: HexValue
    amount: int


@strawberry.type
class Transaction:
    tokenAddress: HexValue
    timestamp: datetime
    amount: int
