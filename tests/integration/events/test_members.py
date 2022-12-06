# pylint: disable=too-many-arguments,too-many-locals
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer

from .. import constants


# pylint: disable=duplicate-code
async def test_member_added(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    address=constants.ACCOUNT_ADDRESS2,
    delegateAddress=constants.ACCOUNT_ADDRESS2,
    shares=69,
    loot=66,
    jailed=0,
    lastProposalYesVote=0,
    onboardedAt=8638726,
):
    info = {
        "address": address,
        "delegateAddress": delegateAddress,
        "shares": shares,
        "loot": loot,
        "jailed": jailed,
        "lastProposalYesVote": lastProposalYesVote,
        "onboardedAt": onboardedAt,
    }

    invoke_result = await contract.functions["Member_add_member_proxy"].invoke(
        info=info,
        max_fee=10**16,
    )

    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["MemberAdded"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.memberAddress == address
    assert python_data.loot == loot
    assert python_data.shares == shares
    assert python_data.onboardedAt == onboardedAt

    return transaction_receipt


async def test_member_updated(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    address=constants.ACCOUNT_ADDRESS,
    delegateAddress=35555,
    shares=42,
    loot=42,
    jailed=0,
    lastProposalYesVote=3,
    onboardedAt=86348726,
):
    info = {
        "address": address,
        "delegateAddress": delegateAddress,
        "shares": shares,
        "loot": loot,
        "jailed": jailed,
        "lastProposalYesVote": lastProposalYesVote,
        "onboardedAt": onboardedAt,
    }

    invoke_result = await contract.functions["Member_update_member_proxy"].invoke(
        info=info,
        max_fee=10**16,
    )

    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["MemberUpdated"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.memberAddress == address
    assert python_data.delegateAddress == delegateAddress
    assert python_data.loot == loot
    assert python_data.shares == shares
    assert python_data.jailed == jailed
    assert python_data.lastProposalYesVote == lastProposalYesVote
    assert python_data.onboardedAt == onboardedAt

    return transaction_receipt
