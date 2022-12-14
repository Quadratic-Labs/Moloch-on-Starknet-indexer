# pylint: disable=too-many-arguments,too-many-locals
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer

from dao import utils

from .. import constants


async def test_token_whitelisted(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    token_name="Some Token",
    token_address=constants.TOKEN_ADDRESS,
):
    invoke_result = await contract.functions["Bank_add_token_proxy"].invoke(
        tokenName=token_name, tokenAddress=token_address, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["TokenWhitelisted"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.tokenName == utils.str_to_felt(token_name)
    assert python_data.tokenAddress == token_address

    return transaction_receipt


async def test_token_unwhitelisted(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    token_name="Some Token",
    token_address=constants.FEE_TOKEN_ADDRESS,
):
    invoke_result = await contract.functions["Bank_remove_token_proxy"].invoke(
        tokenName=token_name, tokenAddress=token_address, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["TokenUnWhitelisted"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.tokenName == utils.str_to_felt(token_name)
    assert python_data.tokenAddress == token_address

    return transaction_receipt


async def test_balance_increased(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    member_address=constants.ACCOUNT_ADDRESS,
    token_address=constants.FEE_TOKEN_ADDRESS,
    amount=10,
):
    invoke_result = await contract.functions[
        "Bank_increase_userTokenBalances_proxy"
    ].invoke(
        userAddress=member_address,
        tokenAddress=token_address,
        amount=utils.int_to_uint256_dict(amount),
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["UserTokenBalanceIncreased"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.tokenAddress == token_address
    assert python_data.memberAddress == member_address
    assert python_data.amount == amount

    return transaction_receipt


async def test_balance_decreased(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    member_address=constants.ACCOUNT_ADDRESS,
    token_address=constants.FEE_TOKEN_ADDRESS,
    # Set to zero to avoid Error message: SafeUint256: subtraction overflow since
    # cairo doesn't accept negative values
    amount=0,
):
    invoke_result = await contract.functions[
        "Bank_decrease_userTokenBalances_proxy"
    ].invoke(
        userAddress=member_address,
        tokenAddress=token_address,
        amount=utils.int_to_uint256_dict(amount),
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["UserTokenBalanceDecreased"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.tokenAddress == token_address
    assert python_data.memberAddress == member_address
    assert python_data.amount == amount

    return transaction_receipt
