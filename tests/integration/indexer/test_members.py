import pymongo
from apibara import EventFilter
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient


from ...conftest import IndexerProcessRunner
from .. import utils
from indexer.indexer import default_new_events_handler
from indexer.utils import get_block_datetime_utc


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
    utils.wait_for_indexer(mongo_db, block.block_number)

    block_datetime = get_block_datetime_utc(block)

    members = list(mongo_db["members"].find({"_chain.valid_to": None}))
    assert len(members) == 1

    member = members[0]

    assert member["memberAddress"] == utils.int_to_bytes(client.address)
    assert member["onboardedAt"] == block_datetime
    assert member["shares"] == 1
    assert member["loot"] == 50
