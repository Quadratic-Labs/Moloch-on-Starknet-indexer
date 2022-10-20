import asyncio
import logging
from multiprocessing import Process
from multiprocessing.sharedctypes import Value
import os
from pathlib import Path
from typing import Union

import backoff
import requests
from grpc.aio import AioRpcError
from grpc_requests.aio import AsyncClient
from python_on_whales import Container, DockerClient
from apibara import Info, NewEvents, EventFilter
from pymongo.database import Database

from .. import config
from indexer.indexer import run_indexer

logger = logging.getLogger("tests")

docker = DockerClient(
    compose_files=["docker-compose.test.yml"],
    compose_project_directory=Path(__file__).parent.parent,
    compose_project_name="indexer-test",
)


def raise_timeout_error(details: dict):
    # TODO: better error message
    raise TimeoutError(details["target"].__name__)


# backoff will run the function until no container is restarting
# if a container is not running (exited, paused, stopped) a RuntimeError will be raised
@backoff.on_predicate(
    backoff.constant,
    max_time=config.DEFAULT_MAX_BACKOFF_TIME,
    on_giveup=raise_timeout_error,
)
async def wait_for_docker_services():
    containers = docker.compose.ps()

    not_running_containers: list[Container] = []
    restarting_containers: list[Container] = []

    RUNNING = "running"
    RESTARTING = "restarting"

    for container in containers:
        if container.state.status == RESTARTING:
            restarting_containers.append(container)
        elif container.state.status != RUNNING:
            not_running_containers.append(container)

    if not_running_containers:
        raise RuntimeError(
            "Some containers are not running: {}".format(
                ",".join(
                    [
                        f"{container.name}={container.state.status}"
                        for container in not_running_containers
                    ]
                )
            )
        )

    return not restarting_containers


# TODO: use a more specific exception than RequestException
@backoff.on_exception(
    backoff.constant,
    requests.RequestException,
    max_time=config.DEFAULT_MAX_BACKOFF_TIME,
)
async def wait_for_devnet():
    # TODO: think about using a async client here
    url = os.path.join(config.STARKNET_NETWORK_URL, "is_alive")
    is_alive_response = requests.get(url, timeout=1)
    is_alive_response.raise_for_status()


@backoff.on_exception(
    backoff.constant, AioRpcError, max_time=config.DEFAULT_MAX_BACKOFF_TIME
)
async def wait_for_apibara():
    grpc_client = AsyncClient(config.APIBARA_URL, ssl=False)
    node_service = await grpc_client.service("apibara.node.v1alpha1.Node")
    return await node_service.Status()


@backoff.on_predicate(
    backoff.constant,
    max_time=config.WAIT_FOR_INDEXER_BACKOFF_TIME,
    on_giveup=raise_timeout_error,
)
def wait_for_indexer(mongo_db: Database, block_number: int):
    """Wait for the indexer until it reaches a given block_number

    It could be used during tests to ensure some events were processed before
    reading the mongo db
    """
    document = mongo_db["_apibara"].find_one({"indexer_id": mongo_db.name})
    indexed_to = document["indexed_to"]

    logger.debug(
        "Waiting for indexer to reach block_number=%s, it's now at block_number=%s",
        block_number,
        indexed_to,
    )

    return indexed_to >= block_number


async def default_new_events_handler_test(info: Info, block_events: NewEvents):
    """Handle a group of events grouped by block."""
    logger.debug("Received events for block %s", block_events.block.number)
    events = [
        {
            "timestamp": block_events.block.timestamp,
            "transaction_hash": event.transaction_hash,
            "address": event.address,
            "data": event.data,
            "name": event.name,
        }
        for event in block_events.events
    ]

    logger.debug("Writing to 'events' collection: %s", events)

    # Insert multiple documents in one call.
    await info.storage.insert_many("events", events)


def str_to_felt(text: str) -> int:
    if len(text) > 31:
        raise ValueError(
            f"Cannot convert '{text}' to felt because it has more than 31 chars ({len(text)})"
        )
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")


def felt_to_str(felt: int) -> str:
    length = (felt.bit_length() + 7) // 8
    return felt.to_bytes(length, byteorder="big").decode("utf-8")


def int_to_uint256(a: int) -> tuple:
    """Takes in value, returns uint256-ish tuple."""
    return (a & ((1 << 128) - 1), a >> 128)


def int_to_uint256_dict(a: int) -> dict[str, int]:
    """Takes int value, returns uint256-ish dict."""
    low, high = int_to_uint256(a)
    return {"low": low, "high": high}


def uint256_dict_to_int(a: dict[str, int]) -> int:
    """Takes uint256-ish dict value, returns int value."""
    return uint256_to_int((a["low"], a["high"]))


def uint256_to_int(uint: tuple) -> int:
    """Takes in uint256-ish tuple, returns value."""
    return uint[0] + (uint[1] << 128)


def int_to_bytes(a: int) -> bytes:
    length = (a.bit_length() + 7) // 8
    return a.to_bytes(length, byteorder="big")


def bytes_to_int(a: bytes) -> int:
    return int.from_bytes(a, "big")
