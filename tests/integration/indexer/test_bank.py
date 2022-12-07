# pylint: disable=too-many-arguments,too-many-locals
import pymongo
import pytest
from apibara import EventFilter
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient

from indexer import config, utils
from indexer.indexer import default_new_events_handler

from ...conftest import IndexerProcessRunner
from .. import constants, test_utils
from ..events import test_bank


async def test_token_whitelisted(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    filters = [
        EventFilter.from_event_name(
            name="TokenWhitelisted",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    token_name = "Fee Token"
    token_address = constants.FEE_TOKEN_ADDRESS

    # the fee token is already being whitelisted in main.cairo
    # No need to trigger the event again

    # token_address = constants.TOKEN_ADDRESS
    # transaction_receipt = await test_bank.test_token_whitelisted(
    #     contract=contract,
    #     contract_events=contract_events,
    #     client=client,
    #     token_address=token_address,
    # )

    block = await client.get_block("latest")
    block_datetime = utils.get_block_datetime_utc(block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    test_utils.wait_for_indexer(mongo_db, block.block_number)

    current_block_filter = {"_chain.valid_to": None}

    bank = list(mongo_db["bank"].find(current_block_filter))
    assert len(bank) == 1
    bank = bank[0]

    tokens = bank["whitelistedTokens"]
    assert len(tokens) == 1

    assert tokens[0] == {
        "tokenName": token_name,
        "tokenAddress": utils.int_to_bytes(token_address),
        "whitelistedAt": block_datetime,
    }


async def test_token_unwhitelisted(
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    token_name = "Fee Token"
    token_address = constants.FEE_TOKEN_ADDRESS

    filters = [
        EventFilter.from_event_name(
            name="TokenUnWhitelisted",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_bank.test_token_unwhitelisted(
        contract=contract,
        contract_events=contract_events,
        client=client,
        token_name=token_name,
        token_address=token_address,
    )
    block = await client.get_block(transaction_receipt.block_hash)
    block_datetime = utils.get_block_datetime_utc(block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    test_utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    current_block_filter = {"_chain.valid_to": None}

    bank = list(mongo_db["bank"].find(current_block_filter))
    assert len(bank) == 1
    bank = bank[0]

    tokens = bank["unWhitelistedTokens"]
    assert len(tokens) == 1

    assert tokens[0] == {
        "tokenName": token_name,
        "tokenAddress": utils.int_to_bytes(token_address),
        "unWhitelistedAt": block_datetime,
    }


@pytest.mark.parametrize(
    "member_address", [constants.ACCOUNT_ADDRESS, config.BANK_ADDRESS]
)
async def test_balance_increased(
    member_address,
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    token_address = constants.FEE_TOKEN_ADDRESS
    amount = 10

    filters = [
        EventFilter.from_event_name(
            name="MemberAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="UserTokenBalanceIncreased",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_bank.test_balance_increased(
        contract=contract,
        contract_events=contract_events,
        client=client,
        member_address=member_address,
        token_address=token_address,
        amount=amount,
    )
    block = await client.get_block(transaction_receipt.block_hash)
    block_datetime = utils.get_block_datetime_utc(block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    test_utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    if member_address == config.BANK_ADDRESS:
        bank = list(mongo_db["bank"].find({"_chain.valid_to": None}))
        assert len(bank) == 1
        balances = bank[0]["balances"]
        transactions = bank[0]["transactions"]
    else:
        members = list(mongo_db["members"].find({"_chain.valid_to": None}))
        assert len(members) == 1
        balances = members[0]["balances"]
        transactions = members[0]["transactions"]

    assert balances == {str(token_address): amount}
    assert transactions == [
        {
            "memberAddress": utils.int_to_bytes(member_address),
            "tokenAddress": utils.int_to_bytes(token_address),
            "timestamp": block_datetime,
            "amount": amount,
        }
    ]


@pytest.mark.parametrize(
    "member_address", [constants.ACCOUNT_ADDRESS, config.BANK_ADDRESS]
)
async def test_balance_decreased(
    member_address,
    run_indexer_process: IndexerProcessRunner,
    contract: Contract,
    contract_events: dict,
    client: AccountClient,
    mongo_client: pymongo.MongoClient,
):
    token_address = constants.FEE_TOKEN_ADDRESS
    # Avoid Error message: SafeUint256: subtraction overflow
    amount = 0

    filters = [
        EventFilter.from_event_name(
            name="MemberAdded",
            address=contract.address,
        ),
        EventFilter.from_event_name(
            name="UserTokenBalanceDecreased",
            address=contract.address,
        ),
    ]

    indexer = run_indexer_process(filters, default_new_events_handler)

    transaction_receipt = await test_bank.test_balance_decreased(
        contract=contract,
        contract_events=contract_events,
        client=client,
        member_address=member_address,
        token_address=token_address,
        amount=amount,
    )
    block = await client.get_block(transaction_receipt.block_hash)
    block_datetime = utils.get_block_datetime_utc(block)

    mongo_db = mongo_client[indexer.id]
    # Wait for the indexer to reach the transaction block_number to be sure
    # our events were processed
    test_utils.wait_for_indexer(mongo_db, transaction_receipt.block_number)

    if member_address == config.BANK_ADDRESS:
        bank = list(mongo_db["bank"].find({"_chain.valid_to": None}))
        assert len(bank) == 1
        balances = bank[0]["balances"]
        transactions = bank[0]["transactions"]
    else:
        members = list(mongo_db["members"].find({"_chain.valid_to": None}))
        assert len(members) == 1
        balances = members[0]["balances"]
        transactions = members[0]["transactions"]

    assert balances == {str(token_address): -amount}
    assert transactions == [
        {
            "memberAddress": utils.int_to_bytes(member_address),
            "tokenAddress": utils.int_to_bytes(token_address),
            "timestamp": block_datetime,
            "amount": -amount,
        }
    ]
