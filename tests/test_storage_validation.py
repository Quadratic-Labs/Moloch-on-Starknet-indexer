import pytest
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError, WriteError

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
    mongo_db.proposals.insert_one(data.PROPOSALS[0])
    assert len(list(mongo_db.proposals.find())) == 1


@pytest.mark.parametrize("proposal", data.mongo_validation.PROPOSAL_TYPE_MISMATCH)
def test_proposals_validation_type(proposal, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*type did not match.*"):
        mongo_db.proposals.insert_one(proposal)


@pytest.mark.parametrize("proposal", data.mongo_validation.PROPOSAL_WRONG_VALUES)
def test_proposals_validation_wrong(proposal, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*minimum|maximum|duplicate.*"):
        mongo_db.proposals.insert_one(proposal)


def test_proposal_params_validation_pass(mongo_db: Database):
    storage.init_db(mongo_db)
    mongo_db.proposal_params.insert_one(data.PROPOSAL_PARAMS)
    assert len(list(mongo_db.proposal_params.find())) == 1


@pytest.mark.parametrize(
    "proposal_params", data.mongo_validation.PROPOSAL_PARAMS_TYPE_MISMATCH
)
def test_proposal_params_validation_type(proposal_params, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*type did not match.*"):
        mongo_db.proposal_params.insert_one(proposal_params)


@pytest.mark.parametrize(
    "proposal_params", data.mongo_validation.PROPOSAL_PARAMS_WRONG_VALUES
)
def test_proposal_params_validation_wrong(proposal_params, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*minimum|maximum|duplicate.*"):
        mongo_db.proposal_params.insert_one(proposal_params)


def test_members_validation_pass(mongo_db: Database):
    storage.init_db(mongo_db)
    mongo_db.members.insert_one(data.MEMBERS[0])
    assert len(list(mongo_db.members.find())) == 1


@pytest.mark.parametrize("member", data.mongo_validation.MEMBER_TYPE_MISMATCH)
def test_members_validation_type(member, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*type did not match.*"):
        mongo_db.members.insert_one(member)


@pytest.mark.parametrize("member", data.mongo_validation.MEMBER_WRONG_VALUES)
def test_members_validation_wrong(member, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*minimum|maximum|duplicate.*"):
        mongo_db.members.insert_one(member)


@pytest.mark.parametrize("member", data.mongo_validation.MEMBER_MISSING_REQUIRED)
def test_members_validation_required(member, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*required.*"):
        mongo_db.members.insert_one(member)


def test_bank_validation_pass(mongo_db: Database):
    storage.init_db(mongo_db)
    mongo_db.bank.insert_one(data.BANK)
    assert len(list(mongo_db.bank.find())) == 1


@pytest.mark.parametrize("bank", data.mongo_validation.BANK_TYPE_MISMATCH)
def test_bank_validation_type(bank, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*type did not match.*"):
        mongo_db.bank.insert_one(bank)


@pytest.mark.parametrize("bank", data.mongo_validation.BANK_WRONG_VALUES)
def test_bank_validation_wrong(bank, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*minimum|maximum|duplicate.*"):
        mongo_db.bank.insert_one(bank)


@pytest.mark.parametrize("bank", data.mongo_validation.BANK_MISSING_REQUIRED)
def test_bank_validation_required(bank, mongo_db: Database):
    storage.init_db(mongo_db)
    with pytest.raises(WriteError, match=".*required.*"):
        mongo_db.bank.insert_one(bank)
