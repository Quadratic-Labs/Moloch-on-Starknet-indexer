from pymongo.database import Database


def list_members(info):
    db: Database = info.context["db"]
    # TODO: Filter only users who could have voted for this particular proposal
    # TODO: Use dataloaders or any other mechanism for caching
    members = db["members"].find({"_chain.valid_to": None})
    return members
