import json
from pathlib import Path
from starknet_py.contract import Contract


async def test_contract(contract: Contract):
    with open(Path(__file__).parent / "assets/test_contract_abi.json") as file:
        contract_abi = json.loads(file.read())

    assert contract.data.abi == contract_abi
