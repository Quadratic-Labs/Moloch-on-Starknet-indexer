import json
import pymongo
from multiprocessing import Process
from pathlib import Path
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer
from pymongo.database import Database

from .conftest import Account
from . import config


async def test_contract(contract: Contract):
    with open(Path(__file__).parent / "assets/test_contract_abi.json") as file:
        contract_abi = json.loads(file.read())

    assert contract.data.abi == contract_abi


async def test_invoke(contract: Contract, client: AccountClient, account: Account):
    amount = 10

    invoke_result = await contract.functions["increase_balance"].invoke(
        amount, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    call_result = await contract.functions["get_balance"].call(account.address)
    assert call_result.res == amount


async def test_event(contract: Contract, client: AccountClient):
    invoke_result = await contract.functions["increase_balance"].invoke(
        10, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = {
        "data": [
            {"name": "current_balance", "type": "felt"},
            {"name": "amount", "type": "felt"},
        ],
        "keys": [],
        "name": "increase_balance_called",
        "type": "event",
    }

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    # Transforms python data to cairo (needs types of the values and python data)
    event_data = cairo_serializer.from_python(emitted_event_abi["data"], *python_data)
    expected_event_data = ([0, 10], {"current_balance": [0], "amount": [10]})

    assert event_data == expected_event_data


async def test_indexer(
    indexer: Process,
    contract: Contract,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    await test_event(contract=contract, client=client)

    mongo_db = mongo_client[indexer.indexer_id]

    import asyncio

    # Wait for apibara to send the events and for the indexer to handle them
    # TODO: find a better way to do that ?
    await asyncio.sleep(5)

    events = list(mongo_db["events"].find())
    assert len(events) == 1

    event = events[0]

    assert event["name"] == "increase_balance_called"
    assert int(event["address"].hex(), 16) == contract.address
