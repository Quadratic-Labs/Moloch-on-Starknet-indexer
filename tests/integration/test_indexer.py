import pymongo
from apibara import EventFilter
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient

from ..conftest import IndexerProcessRunner
from . import constants, test_events, utils
from indexer.indexer import default_new_events_handler
from indexer.models import ProposalStatus


async def test_proposal_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer signaling event"
    description = "Indexer signaling description"

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_events.test_signaling(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        description=description,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    # assert int(event["address"].hex(), 16) == contract.address
    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["description"] == description
    assert proposal["type"] == "Signaling"


async def test_onboard_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer onboard event"
    description = "Indexer onboard description"
    address = constants.ACCOUNT_ADDRESS
    shares = 1
    loot = 1
    tribute_address = constants.FEE_TOKEN_ADDRESS
    tribute_offered = 0

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="OnboardProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_events.test_onboard(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        description=description,
        address=address,
        shares=shares,
        loot=loot,
        tribute_address=tribute_address,
        tribute_offered=tribute_offered,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["description"] == description
    assert proposal["type"] == "Onboard"
    assert proposal["applicantAddress"] == utils.int_to_bytes(address)
    assert proposal["loot"] == loot
    assert proposal["shares"] == shares
    assert proposal["tributeAddress"] == utils.int_to_bytes(tribute_address)
    assert proposal["tributeOffered"] == tribute_offered
    assert proposal["status"] == ProposalStatus.FORCED.value


async def test_swap_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer swap event"
    description = "Indexer swap description"
    paymentAddress = constants.FEE_TOKEN_ADDRESS
    paymentRequested = 0
    tributeAddress = constants.FEE_TOKEN_ADDRESS
    tributeOffered = 0

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="SwapProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_events.test_swap(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        description=description,
        paymentAddress=paymentAddress,
        paymentRequested=paymentRequested,
        tributeAddress=tributeAddress,
        tributeOffered=tributeOffered,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["description"] == description
    assert proposal["type"] == "Swap"
    assert proposal["paymentAddress"] == utils.int_to_bytes(paymentAddress)
    assert proposal["tributeAddress"] == utils.int_to_bytes(tributeAddress)
    assert proposal["paymentRequested"] == paymentRequested
    assert proposal["tributeOffered"] == tributeOffered
