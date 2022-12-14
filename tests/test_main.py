from unittest.mock import AsyncMock, Mock

from apibara.model import EventFilter
from click.testing import CliRunner
from pytest import LogCaptureFixture, MonkeyPatch

from dao import utils
from dao.graphql import main as graphql_main
from dao.indexer import main as indexer_main
from dao.main import cli

from . import config


def test_start_indexer_error(caplog: LogCaptureFixture):
    # Workaround a Click testing bug
    # see https://github.com/pallets/click/issues/824#issuecomment-562581313
    caplog.set_level(10000)

    runner = CliRunner()

    result = runner.invoke(cli, ["start-indexer", "--error-param", "error value"])
    assert result.exit_code == 2


def test_start_indexer(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    # Workaround a Click testing bug
    # See https://github.com/pallets/click/issues/824#issuecomment-562581313
    caplog.set_level(10000)

    runner = CliRunner()

    contract_address = "0x01"
    events = "E1,E2"
    filters = [EventFilter.from_event_name(name, contract_address) for name in events]

    contract = Mock()

    run_indexer_mock = AsyncMock()
    get_contract_mock = AsyncMock(return_value=contract)
    get_contract_events_mock = Mock(return_value=events)

    monkeypatch.setattr(utils, "get_contract", get_contract_mock)
    monkeypatch.setattr(indexer_main, "run_indexer", run_indexer_mock)
    monkeypatch.setattr(utils, "get_contract_events", get_contract_events_mock)

    result = runner.invoke(
        cli,
        [
            "start-indexer",
            "--contract-address",
            contract_address,
            "--events",
            events,
            "--server-url",
            config.APIBARA_URL,
            "--mongo-url",
            config.MONGO_URL,
            "--starknet-network-url",
            config.STARKNET_NETWORK_URL,
            "--restart",
            "--ssl",
        ],
    )

    get_contract_mock.assert_called_once()
    get_contract_events_mock.assert_called_once_with(contract)
    run_indexer_mock.assert_called_once_with(
        server_url=config.APIBARA_URL,
        mongo_url=config.MONGO_URL,
        starknet_network_url=config.STARKNET_NETWORK_URL,
        filters=filters,
        restart=True,
        ssl=True,
    )

    assert result.exit_code == 0


def test_start_graphql_error(caplog: LogCaptureFixture):
    # Workaround a Click testing bug
    # See https://github.com/pallets/click/issues/824#issuecomment-562581313
    caplog.set_level(10000)

    runner = CliRunner()

    result = runner.invoke(cli, ["start-graphql", "--error-param", "error value"])
    assert result.exit_code == 2


def test_start_graphql(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    # Workaround a Click testing bug
    # See https://github.com/pallets/click/issues/824#issuecomment-562581313
    caplog.set_level(10000)

    runner = CliRunner()

    run_graphql_mock = AsyncMock()
    monkeypatch.setattr(graphql_main, "run_graphql", run_graphql_mock)

    db_name = "some_db"
    host, port = config.GRAPHQL_URL.split(":")

    result = runner.invoke(
        cli,
        [
            "start-graphql",
            "--db-name",
            db_name,
            "--mongo-url",
            config.MONGO_URL,
            "--host",
            host,
            "--port",
            port,
        ],
    )

    run_graphql_mock.assert_called_once_with(
        mongo_url=config.MONGO_URL, db_name=db_name, host=host, port=int(port)
    )
    assert result.exit_code == 0
