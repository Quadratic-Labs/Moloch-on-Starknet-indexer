from datetime import datetime

import strawberry
from strawberry.types import Info

from . import storage
from .common import Balance, FromMongoMixin, HexValue, Transaction


@strawberry.type
class WhitelistedToken:
    tokenName: str
    tokenAddress: HexValue
    whitelistedAt: datetime


@strawberry.type
class UnWhitelistedToken:
    tokenName: str
    tokenAddress: HexValue
    unWhitelistedAt: datetime


@strawberry.type
class Bank(FromMongoMixin):
    bankAddress: HexValue
    whitelistedTokens: list[WhitelistedToken]
    unWhitelistedTokens: list[UnWhitelistedToken]
    balances: list[Balance]
    transactions: list[Transaction]
    totalShares: int = 0
    totalLoot: int = 0

    @classmethod
    def from_mongo(cls, data: dict):
        data["balances"] = [Balance(**balance) for balance in data.get("balances", [])]
        data["transactions"] = [
            Transaction(**transaction) for transaction in data.get("transactions", [])
        ]

        unwhitelisted_addresses = [
            token["tokenAddress"] for token in data["unWhitelistedTokens"]
        ]
        data["whitelistedTokens"] = [
            WhitelistedToken(**token)
            for token in data["whitelistedTokens"]
            if token["tokenAddress"] not in unwhitelisted_addresses
        ]

        data["unWhitelistedTokens"] = [
            UnWhitelistedToken(**token) for token in data["unWhitelistedTokens"]
        ]

        return super().from_mongo(data)


def get_bank(info: Info) -> Bank:
    bank = storage.get_bank(info=info)
    return Bank.from_mongo(bank)
