import pymongo
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer
from apibara import EventFilter

from ..conftest import Account, IndexerProcessRunner
from .utils import felt_to_str, str_to_felt


async def test_submit_signaling_event(
    contract: Contract, contract_events: dict, client: AccountClient
):
    title = "Test signaling event"
    # TODO: test description with more than 31 chars
    description = "Test signaling event"

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


async def test_indexer(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler_test)

    transaction_receipt = await test_submit_signaling_event(
        contract=contract, contract_events=contract_events, client=client
    )

    mongo_db = mongo_client[indexer.id]

    wait_for_indexer(mongo_db, transaction_receipt.block_number)

    events = list(mongo_db["events"].find())
    assert len(events) == 1

    event = events[0]

    assert event["name"] == "ProposalAdded"
    assert int(event["address"].hex(), 16) == contract.address
