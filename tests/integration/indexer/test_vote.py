import pymongo
import pytest
from apibara import EventFilter
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient

from indexer.indexer import default_new_events_handler
from indexer.models import ProposalRawStatus
from indexer.utils import get_block_datetime_utc

from ...conftest import IndexerProcessRunner
from .. import utils
from ..events import test_vote


@pytest.mark.parametrize("vote", [0, 1])
async def test_vote_submitted(
    vote,
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer signaling event"
    link = "Indexer signaling link"

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="VoteSubmitted",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    proposal_transaction_receipt, transaction_receipt = await test_vote.test_vote(
        vote=vote,
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
    )
    proposal_block = await client.get_block(proposal_transaction_receipt.block_hash)
    proposal_block_datetime = get_block_datetime_utc(proposal_block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    # assert int(event["address"].hex(), 16) == contract.address
    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["link"] == link
    assert proposal["type"] == "Signaling"
    assert proposal["submittedBy"] == utils.int_to_bytes(client.address)
    assert proposal["rawStatus"] == ProposalRawStatus.SUBMITTED.value
    if vote:
        assert proposal["yesVoters"] == [utils.int_to_bytes(client.address)]
    else:
        assert proposal["noVoters"] == [utils.int_to_bytes(client.address)]

    assert proposal["submittedAt"] == proposal_block_datetime
    assert proposal["rawStatusHistory"] == [
        [ProposalRawStatus.SUBMITTED.value, proposal_block_datetime]
    ]
