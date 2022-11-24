from pymongo.database import Database
from strawberry.types import Info


def list_members(info: Info, query=None):
    if query is None:
        query = {}

    db: Database = info.context["db"]
    # TODO: Filter only users who could have voted for this particular proposal
    # TODO: Use dataloaders or any other mechanism for caching
    members = db["members"].find({"_chain.valid_to": None, **query})
    return members
