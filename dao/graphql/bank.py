from datetime import datetime

import strawberry
from strawberry.types import Info

from . import storage
from .common import FromMongoMixin, HexValue


@strawberry.type
class Balance:
    tokenName: str
    tokenAddress: HexValue
    amount: int


@strawberry.type
class Transaction:
    tokenAddress: HexValue
    memberAddress: HexValue
    timestamp: datetime
    amount: int


@strawberry.type
class Bank(FromMongoMixin):
    bankAddress: HexValue
    balances: list[Balance]
    transactions: list[Transaction]


def get_bank(info: Info) -> Bank:
    bank = storage.get_bank(info=info)
    return Bank(
        bankAddress=bank["bankAddress"],
        balances=[Balance(**balance) for balance in bank["balances"]],
        transactions=[
            Transaction(**transaction) for transaction in bank["transactions"]
        ],
    )
