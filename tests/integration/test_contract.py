import pymongo
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer
from apibara import EventFilter

from ..conftest import Account, IndexerProcessRunner
from .utils import (
    wait_for_indexer,
    default_new_events_handler_test,
    felt_to_str,
    int_to_uint256_dict,
    str_to_felt,
    int_to_bytes,
)
from indexer.indexer import default_new_events_handler
from . import constants


async def test_submit_signaling_event(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Signaling event",
    description="Signaling event description",
):
    # TODO: test description with more than 31 chars

    invoke_result = await contract.functions["submitSignaling"].invoke(
        title=title, description=description, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["ProposalAdded"]

    # ProposalAdded.emit(id=info.id, title=info.title, description=info.description, type=info.type, submittedBy=info.submittedBy, submittedAt=info.submittedAt);

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert felt_to_str(python_data.title) == title
    assert felt_to_str(python_data.description) == description

    return transaction_receipt


async def test_submit_onboard_event(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Onboard event",
    description="Onboard event description",
    address=constants.FEE_TOKEN_ADDRESS,
    shares=1,
    loot=1,
    tribute_address=constants.FEE_TOKEN_ADDRESS,
    tribute_offered=0,
):
    # address: felt, shares: felt, loot: felt,tributeOffered: Uint256, tributeAddress: felt,title: felt, description: felt
    invoke_result = await contract.functions["submitOnboard"].invoke(
        title=str_to_felt(title),
        description=str_to_felt(description),
        address=address,
        shares=shares,
        loot=loot,
        tributeAddress=tribute_address,
        tributeOffered=int_to_uint256_dict(tribute_offered),
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events emitted by our contract from transaction receipt
    events = [
        event
        for event in transaction_receipt.events
        if event.from_address == contract.address
    ]

    # Both ProposalAdded and OnboardProposalAdded events should be emitted
    # assert len(events) == 2

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    event_abi = contract_events["OnboardProposalAdded"]

    # The first event is ProposalAdded, the second is OnBoardProposalAdded
    event_data = events[1].data

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=event_abi["data"], values=event_data
    )

    assert python_data.id == 0
    assert python_data.address == address
    assert python_data.loot == loot
    assert python_data.shares == shares
    assert python_data.tributeAddress == tribute_address
    assert python_data.tributeOffered == tribute_offered

    return transaction_receipt


async def test_indexer_proposal_added(
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
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_submit_signaling_event(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        description=description,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    wait_for_indexer(mongo_db, transaction_receipt.block_number)

    proposals = list(mongo_db["proposals"].find())
    assert len(proposals) == 1

    proposal = proposals[0]

    # assert int(event["address"].hex(), 16) == contract.address
    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["description"] == description
    assert proposal["type"] == "Signaling"


async def test_indexer_onboard_added(
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
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_submit_onboard_event(
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
    wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["description"] == description
    assert proposal["type"] == "Onboard"
    assert proposal["address"] == int_to_bytes(address)
    assert proposal["loot"] == loot
    assert proposal["shares"] == shares
    assert proposal["tributeAddress"] == int_to_bytes(tribute_address)
    assert proposal["tributeOffered"] == tribute_offered
