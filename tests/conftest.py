import asyncio
import os
from pathlib import Path

import pytest
import requests
from python_on_whales import DockerClient, Container

from requests.adapters import HTTPAdapter, Retry
from starknet_py.contract import Contract
from starknet_py.net.gateway_client import GatewayClient

STARKNET_NETWORK_URL = "http://localhost:5051"

# We have to override the default event_loop to be able to write async fixtures with a session scope
@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def docker_compose_services(request) -> list[Container]:
    docker = DockerClient(
        compose_files=["docker-compose.test.yml"],
        compose_project_directory=Path(__file__).parent.parent,
        compose_project_name="indexer-test",
    )
    docker.compose.up(detach=True)
    # This ensures the docker services are deleted even if the fixture raises an exception
    request.addfinalizer(docker.compose.down)

    containers = docker.compose.ps()
    not_running_containers = [
        container for container in containers if not container.state.running
    ]
    if not_running_containers:
        raise RuntimeError("Some containers are not running:", not_running_containers)

    # starknet-devnet take some time to be ready
    # this will make the is_alive request retries 5 times: after 0.25s, 0.5s, 1s, 2s, 4s
    retry_strategy = Retry(total=5, backoff_factor=0.25)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount(STARKNET_NETWORK_URL, adapter)

    is_alive_response = session.get(os.path.join(STARKNET_NETWORK_URL, "is_alive"))
    is_alive_response.raise_for_status()

    return containers


@pytest.fixture(scope="session")
def client(docker_compose_services) -> GatewayClient:
    return GatewayClient(STARKNET_NETWORK_URL)


@pytest.fixture(scope="session")
def test_contract_file() -> Path:
    tests_dir = Path(__file__).parent
    contract_file = tests_dir / "assets/test_contract.cairo"
    return contract_file


@pytest.fixture(scope="session")
async def contract(client: GatewayClient, test_contract_file: Path) -> Contract:
    deployment_result = await Contract.deploy(
        client=client,
        compilation_source=[str(test_contract_file)],
    )
    await deployment_result.wait_for_acceptance()
    return deployment_result.deployed_contract
