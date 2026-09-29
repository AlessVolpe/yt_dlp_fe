"""Tests for ``modules.loggers.log_handler.QtLogHandler``."""
from __future__ import annotations

import logging
import threading
from typing import Any, Iterator, List

import pytest
from PySide6 import QtCore

from modules.loggers.log_handler import QtLogHandler


class Receiver(QtCore.QObject):
    """Records the payload and the thread in which the slot executed."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: List[str] = []
        self.threads: List[QtCore.QThread] = []

    @QtCore.Slot(str)
    def on_message(self, text: str) -> None:
        self.messages.append(text)
        self.threads.append(QtCore.QThread.currentThread())


@pytest.fixture
def attached() -> Iterator[Any]:
    """Yield ``(logger, handler, receiver)`` with an isolated, propagation-free logger."""
    logger = logging.getLogger("log_handler_test")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = QtLogHandler()
    receiver = Receiver()
    handler.message.connect(receiver.on_message)
    logger.addHandler(handler)
    yield logger, handler, receiver
    logger.removeHandler(handler)


@pytest.mark.unit
class TestConstruction:
    def test_is_both_a_qobject_and_a_logging_handler(self) -> None:
        handler = QtLogHandler()
        assert isinstance(handler, QtCore.QObject) and isinstance(handler, logging.Handler)

    def test_default_level_is_notset(self) -> None:
        assert QtLogHandler().level == logging.NOTSET

    def test_explicit_level_is_stored(self) -> None:
        assert QtLogHandler(logging.WARNING).level == logging.WARNING

    def test_formatter_emits_the_bare_message(self) -> None:
        assert QtLogHandler().formatter._fmt == "%(message)s"


@pytest.mark.unit
class TestEmission:
    def test_message_is_forwarded_as_a_signal(self, attached: Any) -> None:
        logger, _, receiver = attached
        logger.info("hello")
        assert receiver.messages == ["hello"]

    def test_records_are_delivered_in_order(self, attached: Any) -> None:
        logger, _, receiver = attached
        for index in range(50):
            logger.info("m%d", index)
        assert receiver.messages == [f"m{i}" for i in range(50)]

    def test_lazy_arguments_are_interpolated(self, attached: Any) -> None:
        logger, _, receiver = attached
        logger.info("%s-%d", "a", 3)
        assert receiver.messages == ["a-3"]

    @pytest.mark.parametrize("text", ["", "multi\nline", "  padded  ", "ünïcödé ✓", "%literal percent"])
    def test_payload_is_preserved_verbatim(self, attached: Any, text: str) -> None:
        logger, _, receiver = attached
        logger.info("%s", text)
        assert receiver.messages == [text]

    def test_level_and_logger_name_are_not_part_of_the_message(self, attached: Any) -> None:
        logger, _, receiver = attached
        logger.error("boom")
        assert receiver.messages == ["boom"]

    def test_exception_traceback_is_appended_by_the_formatter(self, attached: Any) -> None:
        logger, _, receiver = attached
        try:
            raise ValueError("bad value")
        except ValueError:
            logger.exception("failed")
        assert receiver.messages[0].startswith("failed\nTraceback")
        assert "ValueError: bad value" in receiver.messages[0]


@pytest.mark.unit
class TestLevelFiltering:
    def test_records_below_the_handler_level_are_dropped(self, attached: Any) -> None:
        logger, handler, receiver = attached
        handler.setLevel(logging.WARNING)
        logger.info("dropped")
        logger.warning("kept")
        assert receiver.messages == ["kept"]

    def test_removed_handler_no_longer_emits(self, attached: Any) -> None:
        logger, handler, receiver = attached
        logger.removeHandler(handler)
        logger.info("silent")
        assert receiver.messages == []

    def test_multiple_subscribers_all_receive_the_message(self, attached: Any) -> None:
        logger, handler, first = attached
        second = Receiver()
        handler.message.connect(second.on_message)
        logger.info("fan-out")
        assert first.messages == second.messages == ["fan-out"]


@pytest.mark.integration
class TestThreadSafety:
    def test_emission_from_a_plain_thread_is_delivered_on_the_receiver_thread(self, qtbot: Any, attached: Any) -> None:
        logger, _, receiver = attached
        worker = threading.Thread(target=lambda: logger.info("from worker"))
        worker.start()
        worker.join()
        qtbot.waitUntil(lambda: receiver.messages == ["from worker"], timeout=5000)
        assert receiver.threads == [QtCore.QThread.currentThread()]

    def test_concurrent_producers_lose_no_records(self, qtbot: Any, attached: Any) -> None:
        logger, _, receiver = attached
        producers = [
            threading.Thread(target=lambda n=n: [logger.info("t%d-%d", n, i) for i in range(100)])
            for n in range(4)
        ]
        for producer in producers:
            producer.start()
        for producer in producers:
            producer.join()
        qtbot.waitUntil(lambda: len(receiver.messages) == 400, timeout=10000)
        assert len(set(receiver.messages)) == 400
