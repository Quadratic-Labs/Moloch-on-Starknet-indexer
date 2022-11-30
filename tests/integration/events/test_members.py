from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer


from .. import constants, utils


async def test_updateMembers(
    contract: Contract,
    contract_events: dict,
    client: AccountClient,

    invoke_result = await contract.functions["submitSignaling"].invoke(
        title=title, link=link, max_fee=10**16
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["ProposalAdded"]

    # ProposalAdded.emit(id=info.id, title=info.title, link=info.link, type=info.type, submittedBy=info.submittedBy, submittedAt=info.submittedAt);

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.id == 0
    assert utils.felt_to_str(python_data.title) == title
    assert utils.felt_to_str(python_data.link) == link
    assert python_data.submittedAt == transaction_receipt.block_number
    assert python_data.submittedBy == client.address

    return transaction_receipt