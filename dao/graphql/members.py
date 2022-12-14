from datetime import datetime
from typing import List

import strawberry
from strawberry.types import Info

from . import storage
from .common import FromMongoMixin, HexValue


@strawberry.type
class Member(FromMongoMixin):
    memberAddress: HexValue
    shares: int
    loot: int
    onboardedAt: datetime
    yesVotes: list[HexValue] = strawberry.field(default_factory=list)
    noVotes: list[HexValue] = strawberry.field(default_factory=list)


# pylint: disable=unused-argument
def get_members(info: Info, limit: int = 10, skip: int = 0) -> List[Member]:
    members = storage.list_members(info=info)
    return [Member.from_mongo(doc) for doc in members]
