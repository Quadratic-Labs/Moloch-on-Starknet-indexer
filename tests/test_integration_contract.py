import json
from pathlib import Path
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient

from .conftest import Account


async def test_contract(contract: Contract):
    with open(Path(__file__).parent / "assets/test_contract_abi.json") as file:
        contract_abi = json.loads(file.read())

    assert contract.data.abi == contract_abi


async def test_increase_balance(
    contract: Contract, client: AccountClient, account: Account
):
    amount = 10

    invoke_result = await contract.functions["increase_balance"].invoke(
        amount, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    call_result = await contract.functions["get_balance"].call(account.address)
    assert call_result.res == amount
