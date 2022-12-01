# pylint: disable=too-many-arguments,too-many-locals
import pytest
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.utils.data_transformer.data_transformer import CairoSerializer

from . import test_proposals


@pytest.mark.parametrize("vote", [0, 1])
async def test_vote(
    vote,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    title="Vote event",
    link="Vote event link",
):
    proposal_transaction_receipt = await test_proposals.test_signaling(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
    )

    # TODO: get proposalId from the previous call ?
    proposal_id = 0

    invoke_result = await contract.functions["submitVote"].invoke(
        proposalId=proposal_id,
        vote=vote,
        # TODO: test with an address different than the caller here
        onBehalf=client.address,
        max_fee=10**16,
    )
    await invoke_result.wait_for_acceptance()

    transaction_hash = invoke_result.hash
    transaction_receipt = await client.get_transaction_receipt(transaction_hash)

    # Takes events from transaction receipt
    events = transaction_receipt.events

    # Takes an abi of the event which data we want to serialize
    # We can get it from the contract abi
    emitted_event_abi = contract_events["VoteSubmitted"]

    # Creates CairoSerializer with contract's identifier manager
    cairo_serializer = CairoSerializer(
        identifier_manager=contract.data.identifier_manager
    )

    # Transforms cairo data to python (needs types of the values and values)
    python_data = cairo_serializer.to_python(
        value_types=emitted_event_abi["data"], values=events[0].data
    )

    assert python_data.proposalId == proposal_id
    assert python_data.vote == vote
    assert python_data.callerAddress == client.address
    assert python_data.onBehalfAddress == client.address

    return proposal_transaction_receipt, transaction_receipt
