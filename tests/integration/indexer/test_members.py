# pylint: disable=too-many-arguments,too-many-locals
import pymongo
from apibara import EventFilter
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient

from indexer import utils
from indexer.indexer import default_new_events_handler

from ...conftest import IndexerProcessRunner
from .. import test_utils
from ..events import test_members


# We're adding the first predeployed account in devnet manually in main.cairo
# That's why this test works without invoking any contract function
async def test_member_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    filters = [
        EventFilter.from_event_name(
            name="MemberAdded",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    mongo_db = mongo_client[indexer.id]

    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    block = await client.get_block("latest")
    test_utils.wait_for_indexer(mongo_db, block.block_number)

    block_datetime = utils.get_block_datetime_utc(block)

    members = list(mongo_db["members"].find({"_chain.valid_to": None}))
    assert len(members) == 1

    member = members[0]

    assert member["memberAddress"] == utils.int_to_bytes(client.address)
    assert member["onboardedAt"] == block_datetime
    assert member["shares"] == 1
    assert member["loot"] == 50


async def test_member_updated(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
    address=0x363B71D002935E7822EC0B1BAF02EE90D64F3458939B470E3E629390436510B,
    delegateAddress=0x363B71D002935E7822EC0B1BAF02EE90D64F3458939B470E3E629390436510B,
    shares=42,
    loot=42,
    jailed=0,
    lastProposalYesVote=3,
    onboardedAt=2,
):
    filters = [
        EventFilter.from_event_name(
            name="MemberAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="MemberUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_members.test_member_updated(
        contract=contract,
        contract_events=contract_events,
        client=client,
        address=address,
        delegateAddress=delegateAddress,
        shares=shares,
        loot=loot,
        jailed=jailed,
        lastProposalYesVote=lastProposalYesVote,
        onboardedAt=onboardedAt,
    )

    onboarded_at_block = await client.get_block(block_number=onboardedAt)
    onboarded_at_block_timestamp = utils.get_block_datetime_utc(onboarded_at_block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    test_utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    members = list(mongo_db["members"].find({"_chain.valid_to": None}))
    assert len(members) == 1

    member = members[0]

    assert member["memberAddress"] == utils.int_to_bytes(address)
    assert member["delegateAddress"] == utils.int_to_bytes(delegateAddress)
    assert member["shares"] == shares
    assert member["jailed"] == jailed
    assert member["loot"] == loot
    assert member["onboardedAt"] == onboarded_at_block_timestamp
