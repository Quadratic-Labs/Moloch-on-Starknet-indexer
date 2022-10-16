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

from .. import config
from indexer.indexer import run_indexer

logger = logging.getLogger("tests")

docker = DockerClient(
    compose_files=["docker-compose.test.yml"],
    compose_project_directory=Path(__file__).parent.parent,
    compose_project_name="indexer-test",
)


# backoff will run the function until no container is restarting
# if a container is not running (exited, paused, stopped) a RuntimeError will be raised
@backoff.on_predicate(backoff.constant, max_time=config.DEFAULT_MAX_BACKOFF_TIME)
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


async def default_events_handler(info: Info, block_events: NewEvents):
    """Handle a group of events grouped by block."""
    logger.debug("Received events for block %s", block_events.block.number)
    for event in block_events.events:
        logger.debug(event)

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

    # Insert multiple documents in one call.
    await info.storage.insert_many("events", events)


def str_to_felt(text):
    b_text = bytes(text, "ascii")
    return int.from_bytes(b_text, "big")


def felt_to_str(felt: Union[int, list[int]]) -> str:
    if isinstance(felt, list):
        if len(felt) == 1:
            felt = felt[0]
        else:
            raise ValueError(
                f"felt should be either an int or a list with a single int element, got: {felt}"
            )

    length = (felt.bit_length() + 7) // 8
    return felt.to_bytes(length, byteorder="big").decode("utf-8")
