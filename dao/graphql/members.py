from datetime import datetime

import strawberry
from strawberry.types import Info

from . import storage
from .common import Balance, FromMongoMixin, HexValue, Transaction


@strawberry.type
class Member(FromMongoMixin):
    memberAddress: HexValue
    shares: int
    loot: int
    onboardedAt: datetime
    yesVotes: list[HexValue] = strawberry.field(default_factory=list)
    noVotes: list[HexValue] = strawberry.field(default_factory=list)
    balances: list[Balance] = strawberry.field(default_factory=list)
    transactions: list[Transaction] = strawberry.field(default_factory=list)
    roles: list[str] = strawberry.field(default_factory=list)

    @strawberry.field
    def percentageOfTreasury(self, info) -> float:
        bank = storage.get_bank(info)
        total = bank.get("totalShares", 0) + bank.get("totalLoot", 0)
        return (self.shares + self.loot) / total

    @strawberry.field
    def votingWeight(self, info) -> float:
        bank = storage.get_bank(info)
        totalShares = bank.get("totalShares", 0)
        return self.shares / totalShares

    @classmethod
    def from_mongo(cls, data: dict):
        data["balances"] = [Balance(**balance) for balance in data.get("balances", [])]
        data["transactions"] = [
            Transaction(**transaction) for transaction in data.get("transactions", [])
        ]
        return super().from_mongo(data)


# pylint: disable=unused-argument
def get_members(info: Info, limit: int = 10, skip: int = 0) -> list[Member]:
    members = storage.list_members(info=info)
    return [Member.from_mongo(doc) for doc in members]
