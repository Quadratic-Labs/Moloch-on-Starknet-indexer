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
