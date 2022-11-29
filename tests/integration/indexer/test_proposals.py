import pytest
import pymongo
from apibara import EventFilter
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient

from ..events import test_proposals


from ...conftest import Account, IndexerProcessRunner
from .. import constants, utils
from indexer.indexer import default_new_events_handler
from indexer.models import ProposalRawStatus
from indexer.utils import get_block_datetime_utc


async def test_proposal_added(
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
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_proposals.test_signaling(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
    )
    block = await client.get_block(transaction_receipt.block_hash)
    block_datetime = get_block_datetime_utc(block)

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
    assert proposal["submittedAt"] == block_datetime
    assert proposal["rawStatus"] == ProposalRawStatus.SUBMITTED.value
    assert proposal["rawStatusHistory"] == [
        [ProposalRawStatus.SUBMITTED.value, block_datetime]
    ]


async def test_onboard_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
    predeployed_accounts: list[Account],
):
    title = "Indexer onboard event"
    link = "Indexer onboard link"
    address = predeployed_accounts[1].address
    shares = 1
    loot = 1
    tribute_address = constants.FEE_TOKEN_ADDRESS
    tribute_offered = 0

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="OnboardProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_proposals.test_onboard(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
        address=address,
        shares=shares,
        loot=loot,
        tribute_address=tribute_address,
        tribute_offered=tribute_offered,
    )
    block = await client.get_block(transaction_receipt.block_hash)
    block_datetime = get_block_datetime_utc(block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["link"] == link
    assert proposal["type"] == "Onboard"
    assert proposal["applicantAddress"] == utils.int_to_bytes(address)
    assert proposal["loot"] == loot
    assert proposal["shares"] == shares
    assert proposal["tributeAddress"] == utils.int_to_bytes(tribute_address)
    assert proposal["tributeOffered"] == tribute_offered
    assert proposal["rawStatus"] == ProposalRawStatus.SUBMITTED.value
    assert proposal["rawStatusHistory"] == [
        [ProposalRawStatus.SUBMITTED.value, block_datetime],
    ]


async def test_swap_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer swap event"
    link = "Indexer swap link"
    paymentAddress = constants.FEE_TOKEN_ADDRESS
    paymentRequested = 0
    tributeAddress = constants.FEE_TOKEN_ADDRESS
    tributeOffered = 0

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="SwapProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_proposals.test_swap(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
        paymentAddress=paymentAddress,
        paymentRequested=paymentRequested,
        tributeAddress=tributeAddress,
        tributeOffered=tributeOffered,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["link"] == link
    assert proposal["type"] == "Swap"
    assert proposal["paymentAddress"] == utils.int_to_bytes(paymentAddress)
    assert proposal["tributeAddress"] == utils.int_to_bytes(tributeAddress)
    assert proposal["paymentRequested"] == paymentRequested
    assert proposal["tributeOffered"] == tributeOffered


async def test_guild_kick_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer guild kick event"
    link = "Indexer guild kick link"
    memberAddress = client.address

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="GuildKickProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_proposals.test_guild_kick(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
        memberAddress=memberAddress,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["link"] == link
    assert proposal["type"] == "GuildKick"
    assert proposal["memberAddress"] == utils.int_to_bytes(memberAddress)


async def test_whitelist_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer whitelist event"
    link = "Indexer whitelist link"
    tokenName = "Test Token"
    tokenAddress = client.address

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="WhitelistProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_proposals.test_whitelist(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
        tokenName=tokenName,
        tokenAddress=tokenAddress,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["link"] == link
    assert proposal["type"] == "Whitelist"
    assert proposal["tokenName"] == tokenName
    assert proposal["tokenAddress"] == utils.int_to_bytes(tokenAddress)


async def test_unwhitelist_added(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    title = "Indexer un-whitelist event"
    link = "Indexer un-whitelist link"
    tokenName = "Test Token"
    tokenAddress = constants.FEE_TOKEN_ADDRESS

    filters = [
        EventFilter.from_event_name(
            name="ProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="UnWhitelistProposalAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalStatusUpdated",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="ProposalParamsUpdated",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_proposals.test_unwhitelist(
        contract=contract,
        contract_events=contract_events,
        client=client,
        title=title,
        link=link,
        tokenName=tokenName,
        tokenAddress=tokenAddress,
    )

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    # Apibara's chain-aware storage adds _chain.valid_to and _chain.valid_from
    # to every document, current documents have _chain.valid_to: null
    proposals = list(mongo_db["proposals"].find({"_chain.valid_to": None}))
    assert len(proposals) == 1

    proposal = proposals[0]

    assert proposal["id"] == 0
    assert proposal["title"] == title
    assert proposal["link"] == link
    assert proposal["type"] == "UnWhitelist"
    assert proposal["tokenName"] == tokenName
    assert proposal["tokenAddress"] == utils.int_to_bytes(tokenAddress)
