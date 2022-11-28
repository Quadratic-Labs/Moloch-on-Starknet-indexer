from datetime import timedelta
from unittest.mock import Mock
from pymongo import MongoClient

from indexer.storage import list_members, list_votable_members, list_proposals
from indexer import utils

from . import list_proposals_data


def test_list_members(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    members = list_members(info)

    assert list(members) == []

    new_members = [
        {"memberAddress": "0x1"},
        {"memberAddress": "0x2"},
        {"memberAddress": "0x3"},
    ]
    mongomock_client.db.members.insert_many(new_members)

    members = list_members(info)

    assert list(members) == new_members


def test_list_members_query(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    now = utils.utcnow()

    onboarded_before_members = [
        {"memberAddress": "0x1", "onboardedAt": now},
        {"memberAddress": "0x2", "onboardedAt": now - timedelta(days=1)},
    ]
    onboarded_after_members = [
        {"memberAddress": "0x3", "onboardedAt": now + timedelta(days=1)},
    ]

    all_members = onboarded_before_members + onboarded_after_members

    mongomock_client.db.members.insert_many(all_members)

    query = {"onboardedAt": {"$lte": now}}

    members = list_members(info, query=query)

    assert list(members) == onboarded_before_members


def test_list_votable_members(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    submitted_at = utils.utcnow()
    voting_period_ending_at = submitted_at + timedelta(days=7)

    members = list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == []

    new_members = [
        {"memberAddress": "0x1", "onboardedAt": submitted_at},
        {"memberAddress": "0x2", "onboardedAt": submitted_at},
        {"memberAddress": "0x3", "onboardedAt": submitted_at},
    ]
    mongomock_client.db.members.insert_many(new_members)

    members = list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == new_members


def test_list_votable_members_onboarded_at(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    submitted_at = utils.utcnow()
    voting_period_ending_at = submitted_at + timedelta(days=7)

    votable_members = [
        {"memberAddress": "0x1", "onboardedAt": submitted_at - timedelta(days=1)},
        {"memberAddress": "0x2", "onboardedAt": submitted_at},
        {"memberAddress": "0x3", "onboardedAt": submitted_at + timedelta(days=3)},
    ]

    non_votable_members = [
        {"memberAddress": "0x4", "onboardedAt": voting_period_ending_at},
        {
            "memberAddress": "0x5",
            "onboardedAt": voting_period_ending_at + timedelta(days=1),
        },
    ]

    all_members = votable_members + non_votable_members
    mongomock_client.db.members.insert_many(all_members)

    members = list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == votable_members


def test_list_votable_members_jailed_at(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    submitted_at = utils.utcnow()
    voting_period_ending_at = submitted_at + timedelta(days=7)

    votable_members = [
        {
            "memberAddress": "0x1",
            "onboardedAt": submitted_at - timedelta(days=1),
            "jailedAt": submitted_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x2",
            "onboardedAt": submitted_at,
            "jailedAt": voting_period_ending_at,
        },
        {
            "memberAddress": "0x3",
            "onboardedAt": submitted_at + timedelta(days=3),
            "jailedAt": voting_period_ending_at + timedelta(days=1),
        },
    ]

    non_votable_members = [
        {"memberAddress": "0x4", "onboardedAt": voting_period_ending_at},
        {
            "memberAddress": "0x5",
            "onboardedAt": voting_period_ending_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x6",
            "onboardedAt": submitted_at,
            "jailedAt": submitted_at,
        },
        {
            "memberAddress": "0x7",
            "onboardedAt": submitted_at - timedelta(days=3),
            "jailedAt": submitted_at - timedelta(days=1),
        },
    ]

    all_members = votable_members + non_votable_members
    mongomock_client.db.members.insert_many(all_members)

    members = list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == votable_members


def test_list_votable_members_exited_at(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    submitted_at = utils.utcnow()
    voting_period_ending_at = submitted_at + timedelta(days=7)

    votable_members = [
        {
            "memberAddress": "0x1",
            "onboardedAt": submitted_at - timedelta(days=1),
            "exitedAt": submitted_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x2",
            "onboardedAt": submitted_at,
            "exitedAt": voting_period_ending_at,
        },
        {
            "memberAddress": "0x3",
            "onboardedAt": submitted_at + timedelta(days=3),
            "exitedAt": voting_period_ending_at + timedelta(days=1),
        },
    ]

    non_votable_members = [
        {"memberAddress": "0x4", "onboardedAt": voting_period_ending_at},
        {
            "memberAddress": "0x5",
            "onboardedAt": voting_period_ending_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x6",
            "onboardedAt": submitted_at,
            "exitedAt": submitted_at,
        },
        {
            "memberAddress": "0x7",
            "onboardedAt": submitted_at - timedelta(days=3),
            "exitedAt": submitted_at - timedelta(days=1),
        },
    ]

    all_members = votable_members + non_votable_members
    mongomock_client.db.members.insert_many(all_members)

    members = list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == votable_members


def test_list_votable_members_jailed_at_and_exited_at(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    submitted_at = utils.utcnow()
    voting_period_ending_at = submitted_at + timedelta(days=7)

    votable_members = [
        {
            "memberAddress": "0x1",
            "onboardedAt": submitted_at - timedelta(days=1),
            "jailedAt": submitted_at + timedelta(days=1),
            "exitedAt": submitted_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x2",
            "onboardedAt": submitted_at,
            "jailedAt": voting_period_ending_at - timedelta(days=1),
            "exitedAt": voting_period_ending_at,
        },
        {
            "memberAddress": "0x3",
            "onboardedAt": submitted_at + timedelta(days=3),
            "jailedAt": voting_period_ending_at,
            "exitedAt": voting_period_ending_at + timedelta(days=1),
        },
    ]

    non_votable_members = [
        {"memberAddress": "0x4", "onboardedAt": voting_period_ending_at},
        {
            "memberAddress": "0x5",
            "onboardedAt": voting_period_ending_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x6",
            "onboardedAt": submitted_at - timedelta(days=2),
            "jailedAt": submitted_at - timedelta(days=1),
            "exitedAt": submitted_at,
        },
        {
            "memberAddress": "0x7",
            "onboardedAt": submitted_at - timedelta(days=3),
            "jailedAt": submitted_at - timedelta(days=1),
            "exitedAt": submitted_at - timedelta(days=2),
        },
    ]

    all_members = votable_members + non_votable_members
    mongomock_client.db.members.insert_many(all_members)

    members = list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == votable_members


def test_list_proposals(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    mongomock_client.db.proposals.insert_many(list_proposals_data.proposals)
    mongomock_client.db.members.insert_many(list_proposals_data.members)

    proposals = list_proposals(info, disable_pipeline_operator=True)
    proposals = list(proposals)

    # Remove MongoDB auto generated _id from the result to be able to compare it
    # to the expected one
    for proposal in proposals:
        del proposal["_id"]
        for member in proposal["yesVotersMembers"] + proposal["noVotersMembers"]:
            del member["_id"]

    assert proposals == list_proposals_data.list_proposals_query_expected_result