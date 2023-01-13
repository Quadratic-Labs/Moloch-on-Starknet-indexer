from unittest.mock import Mock

from pytest import LogCaptureFixture, MonkeyPatch

from dao.indexer import handler


async def test_default_new_events_handler_edge_cases(
    monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
):
    info = Mock()
    event_mock = Mock()
    block_events = Mock(events=[event_mock])
    get_mock = Mock(return_value=None)
    all_events_mock = Mock(get=get_mock)

    monkeypatch.setattr(handler, "ALL_EVENTS", all_events_mock)

    await handler.default_new_events_handler(
        info=info, block_events=block_events, event_classes=None
    )

    get_mock.assert_called_once_with(event_mock.name)

    assert "Cannot find event class for" in caplog.text
