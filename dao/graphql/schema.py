import strawberry

from .bank import Bank, get_bank
from .members import Member, get_members
from .proposals import PROPOSAL_TYPE_TO_CLASS, Proposal, get_proposals


@strawberry.type
class Query:
    proposals: list[Proposal] = strawberry.field(resolver=get_proposals)
    members: list[Member] = strawberry.field(resolver=get_members)
    bank: Bank = strawberry.field(resolver=get_bank)


schema = strawberry.Schema(query=Query, types=list(PROPOSAL_TYPE_TO_CLASS.values()))
