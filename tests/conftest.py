import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Process
from pathlib import Path

import pymongo
import pytest
import requests
from apibara import EventFilter
from python_on_whales import Container
from starknet_py.contract import Contract
from starknet_py.net.account.account_client import AccountClient
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair

from indexer.indexer import run_indexer
from .utils import (
    docker,
    wait_for_apibara,
    wait_for_devnet,
    wait_for_docker_services,
    default_events_handler,
)
from . import config


def pytest_addoption(parser):
    parser.addoption("--keep-docker-services", action="store_true", default=False)


@dataclass
class Account:
    address: int
    private_key: int
    public_key: int


# We have to override the default event_loop to be able to write async fixtures with a session scope
# TODO: think about using a different event_loop instead of overriding as suggested by the asyncio-pytest docs
@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def docker_compose_services(request: pytest.FixtureRequest) -> list[Container]:
    docker.compose.up(detach=True)

    # This ensures the docker services are deleted even if the fixture raises an exception
    # Pass --keep-docker-services to the pytest command to prevent taking them down,
    # which will make integration tests run faster
    if not request.config.option.keep_docker_services:
        request.addfinalizer(docker.compose.down)

    await wait_for_docker_services()

    # Run the wait functions concurrently using asyncio tasks
    wait_for_devnet_task = asyncio.create_task(wait_for_devnet())
    wait_for_apibara_task = asyncio.create_task(wait_for_apibara())

    await wait_for_devnet_task
    await wait_for_apibara_task

    return docker.compose.ps()


@pytest.fixture(scope="session")
def account() -> Account:
    url = os.path.join(config.STARKNET_NETWORK_URL, "predeployed_accounts")
    predeployed_accounts = requests.get(url, timeout=5).json()
    first_account = predeployed_accounts[0]

    return Account(
        address=int(first_account["address"], 16),
        private_key=int(first_account["private_key"], 16),
        public_key=int(first_account["public_key"], 16),
    )


@pytest.fixture(scope="session")
def client(docker_compose_services, account) -> AccountClient:
    client = GatewayClient(config.STARKNET_NETWORK_URL)

    return AccountClient(
        address=account.address,
        client=client,
        # I don't know why we have to pass the chain_id/chain
        chain=StarknetChainId.TESTNET,
        key_pair=KeyPair(account.private_key, account.public_key),
        # Version 0 (default) is deprecated, and raises exception when invoking get_nonce
        supported_tx_version=1,
    )


@pytest.fixture(scope="session")
def test_contract_file() -> Path:
    tests_dir = Path(__file__).parent
    contract_file = tests_dir / "assets/test_contract.cairo"
    return contract_file


@pytest.fixture
async def contract(client: AccountClient, test_contract_file: Path) -> Contract:
    deployment_result = await Contract.deploy(
        client=client,
        compilation_source=[str(test_contract_file)],
    )
    await deployment_result.wait_for_acceptance()
    return deployment_result.deployed_contract


@pytest.fixture
async def indexer(
    contract: Contract, docker_compose_services, request: pytest.FixtureRequest
):
    filters = [
        EventFilter.from_event_name(
            name="increase_balance_called",
            address=contract.address,
        ),
    ]

    indexer_id = request.node.name + "_" + datetime.now().strftime("%Y_%m_%d_%H_%I_%M")

    # TODO: is it safe to run the indexer like so ?
    indexer_process = Process(
        target=lambda: asyncio.run(
            run_indexer(
                server_url=config.APIBARA_URL,
                mongo_url=config.MONGO_URL,
                indexer_id=indexer_id,
                new_events_handler=default_events_handler,
                filters=filters,
                restart=True,
            ),
        )
    )

    # To be accessed by the tests if needed, ex: to infer the mongodb database name
    indexer_process.indexer_id = indexer_id

    indexer_process.start()

    yield indexer_process

    indexer_process.terminate()


@pytest.fixture(scope="session")
def mongo_client(docker_compose_services) -> pymongo.MongoClient:
    return pymongo.MongoClient(config.MONGO_URL)