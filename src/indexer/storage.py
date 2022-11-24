from datetime import datetime
from pymongo.database import Database
from strawberry.types import Info


def list_members(info: Info, query=None):
    if query is None:
        query = {}

    db: Database = info.context["db"]
    # TODO: Use dataloaders or any other mechanism for caching
    members = db["members"].find({"_chain.valid_to": None, **query})
    return members


def get_votable_members_query(
    voting_period_ending_at: datetime, submitted_at: datetime
):

    # if (
    #     onboardedAt <= votingPeriodEndingAt
    #     and (jailedAt is None or jailedAt > submittedAt)
    #     and (exitedAt is None or exitedAt > submittedAt)
    # )
    return {
        "$and": [
            {"onboardedAt": {"$lt": voting_period_ending_at}},
            {
                "$or": [
                    {"jailedAt": {"$exists": False}},
                    {"jailedAt": {"$gt": submitted_at}},
                ]
            },
            {
                "$or": [
                    {"exitedAt": {"$exists": False}},
                    {"exitedAt": {"$gt": submitted_at}},
                ]
            },
        ]
    }


def list_votable_members(
    info: Info, voting_period_ending_at: datetime, submitted_at: datetime
):
    db: Database = info.context["db"]

    query = get_votable_members_query(
        voting_period_ending_at=voting_period_ending_at, submitted_at=submitted_at
    )

    # TODO: Use dataloaders or any other mechanism for caching
    members = db["members"].find({"_chain.valid_to": None, **query})
    return members
