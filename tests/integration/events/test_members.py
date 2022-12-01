from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer


from .. import constants, utils


async def test_member_added(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    address=0x363B71D0029390D64F3458939B470E3E6293904D36510B,
    delegateAddress=0x363B71D0029390D64F3458939B470E3E6293904D36510B,
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

    # ProposalAdded.emit(id=info.id, title=info.title, link=info.link, type=info.type, submittedBy=info.submittedBy, submittedAt=info.submittedAt);

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
    address=0x363B71D002935E7822EC0B1BAF02EE90D64F3458939B470E3E629390436510B,
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

    # ProposalAdded.emit(id=info.id, title=info.title, link=info.link, type=info.type, submittedBy=info.submittedBy, submittedAt=info.submittedAt);

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
