from datetime import datetime
import os
from typing import Any, Optional
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


def get_list_proposals_query(
    skip: Optional[int] = None,
    limit: Optional[int] = None,
):
    current_block_filter = {"_chain.valid_to": None}

    # TODO: use $set with MongoDB Expressions[1] to add fields we need for sorting
    # like timeRemaining and processedAt
    # [1]: https://www.mongodb.com/docs/manual/meta/aggregation-quick-reference/#std-label-aggregation-expressions
    pipeline: list[dict[str, Any]] = [
        {"$match": current_block_filter},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "members",
                "pipeline": [{"$match": current_block_filter}],
                "localField": "yesVoters",
                "foreignField": "memberAddress",
                "as": "yesVotersMembers",
            }
        },
        {
            "$lookup": {
                "from": "members",
                "pipeline": [{"$match": current_block_filter}],
                "localField": "noVoters",
                "foreignField": "memberAddress",
                "as": "noVotersMembers",
            }
        },
        {"$sort": {"submittedAt": -1}},
    ]

    # Disable pipeline operator when using mongomock
    # because it doesn't support it
    if os.getenv("USING_MONGOMOCK", "").lower() == "true":
        for step in pipeline:
            if lookup := step.get("$lookup"):
                if "pipeline" in lookup:
                    del lookup["pipeline"]

    return pipeline


def list_proposals(
    info: Info,
    skip: Optional[int] = None,
    limit: Optional[int] = None,
):
    db: Database = info.context["db"]

    pipeline = get_list_proposals_query(skip=skip, limit=limit)

    proposals = db["proposals"].aggregate(pipeline)

    return proposals
