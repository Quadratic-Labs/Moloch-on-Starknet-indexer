from datetime import timedelta
from unittest.mock import Mock

import pytest
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, WriteError

from dao import utils
from dao.graphql import storage

from . import data


def test_unique_member_address(mongomock_client: MongoClient):
    storage.init_db(mongomock_client.db)
    member = {"memberAddress": "0x1"}
    mongomock_client.db.members.insert_one(member)
    with pytest.raises(DuplicateKeyError):
        mongomock_client.db.members.insert_one(member)


def test_unique_proposal_id(mongomock_client: MongoClient):
    storage.init_db(mongomock_client.db)
    proposal = {"id": 1}
    mongomock_client.db.proposals.insert_one(proposal)
    with pytest.raises(DuplicateKeyError):
        mongomock_client.db.proposals.insert_one(proposal)


def test_unique_proposal_type(mongomock_client: MongoClient):
    storage.init_db(mongomock_client.db)
    proposal_param = {"type": 1}
    mongomock_client.db.proposal_params.insert_one(proposal_param)
    with pytest.raises(DuplicateKeyError):
        mongomock_client.db.proposal_params.insert_one(proposal_param)


def test_unique_bank_address(mongomock_client: MongoClient):
    storage.init_db(mongomock_client.db)
    bank = {"bankAddress": "0x1"}
    mongomock_client.db.bank.insert_one(bank)
    with pytest.raises(DuplicateKeyError):
        mongomock_client.db.bank.insert_one(bank)


def test_proposals_validation_pass(mongo_db: Database):
    storage.init_db(mongo_db)
    mongo_db.proposals.insert_one(data.mongo_validation.PROPOSAL)
    assert len(list(mongo_db.proposals.find())) == 1


@pytest.mark.parametrize("proposal", data.mongo_validation.PROPOSAL_TYPE_MISMATCH)
def test_proposals_validation_type(proposal, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*type did not match.*"):
        mongo_db.proposals.insert_one(proposal)


@pytest.mark.parametrize("proposal", data.mongo_validation.PROPOSAL_WRONG_VALUES)
def test_proposals_validation_wrong(proposal, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*minimum|maximum.*"):
        mongo_db.proposals.insert_one(proposal)


@pytest.mark.parametrize("proposal", data.mongo_validation.PROPOSAL_MISSING_REQUIRED)
def test_proposals_validation_required(proposal, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*required.*"):
        mongo_db.proposals.insert_one(proposal)


def test_list_members(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    members = storage.list_members(info)

    assert not list(members)

    new_members = [
        {"memberAddress": "0x1"},
        {"memberAddress": "0x2"},
        {"memberAddress": "0x3"},
    ]
    mongomock_client.db.members.insert_many(new_members)

    members = storage.list_members(info)

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

    members = storage.list_members(info, filter=query)

    assert list(members) == onboarded_before_members


def test_list_votable_members(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    submitted_at = utils.utcnow()
    voting_period_ending_at = submitted_at + timedelta(days=7)

    members = storage.list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert not list(members)

    new_members = [
        {"memberAddress": "0x1", "onboardedAt": submitted_at},
        {"memberAddress": "0x2", "onboardedAt": submitted_at},
        {"memberAddress": "0x3", "onboardedAt": submitted_at},
    ]
    mongomock_client.db.members.insert_many(new_members)

    members = storage.list_votable_members(
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

    members = storage.list_votable_members(
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
        {
            "memberAddress": "0x8",
            "onboardedAt": submitted_at + timedelta(days=3),
            "jailedAt": None,
        },
        {
            "memberAddress": "0x9",
            "onboardedAt": submitted_at + timedelta(days=3),
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

    members = storage.list_votable_members(
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
        {
            "memberAddress": "0x8",
            "onboardedAt": submitted_at + timedelta(days=3),
            "exitedAt": None,
        },
        {
            "memberAddress": "0x9",
            "onboardedAt": submitted_at + timedelta(days=3),
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

    members = storage.list_votable_members(
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
        {
            "memberAddress": "0x8",
            "onboardedAt": submitted_at + timedelta(days=3),
            "jailedAt": None,
            "exitedAt": voting_period_ending_at + timedelta(days=1),
        },
        {
            "memberAddress": "0x9",
            "onboardedAt": submitted_at + timedelta(days=3),
            "jailedAt": voting_period_ending_at,
            "exitedAt": None,
        },
        {
            "memberAddress": "0x10",
            "onboardedAt": submitted_at + timedelta(days=3),
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

    members = storage.list_votable_members(
        info=info,
        voting_period_ending_at=voting_period_ending_at,
        submitted_at=submitted_at,
    )

    assert list(members) == votable_members


def test_list_proposals(mongomock_client: MongoClient):
    info = Mock(context={"db": mongomock_client.db})

    mongomock_client.db.proposals.insert_many(data.PROPOSALS)
    mongomock_client.db.members.insert_many(data.MEMBERS)

    proposals = storage.list_proposals(info)
    proposals = list(proposals)

    # Remove MongoDB auto generated _id from the result to be able to compare it
    # to the expected one
    for proposal in proposals:
        del proposal["_id"]
        for member in proposal["yesVotersMembers"] + proposal["noVotersMembers"]:
            del member["_id"]

    assert proposals == data.mongo_expected.LIST_PROPOSALS
