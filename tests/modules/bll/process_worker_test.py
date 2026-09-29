"""Tests for ``modules.bll.process_worker.ProcessWorker``.

Most tests invoke ``run()`` synchronously (deterministic, coverage-visible);
a dedicated group exercises the genuine ``QThread`` path.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, Iterable, Iterator, List, Optional

import pytest
from PySide6 import QtCore

from config.constants import MAX_POSITIVE_INTEGER
from config.error_codes import ExitCode
from modules.bll import process_worker
from modules.bll.process_worker import ProcessWorker


class FakeProcess:
    """Minimal `subprocess.Popen` double."""

    def __init__(self, lines: Optional[Iterable[str]] = (), returncode: Optional[int] = 0) -> None:
        self.stdout = None if lines is None else iter(lines)
        self.returncode = returncode
        self.waited = False

    def wait(self) -> None:
        self.waited = True


def install_popen(monkeypatch: pytest.MonkeyPatch, process: Any = None, error: Optional[Exception] = None) -> List[Any]:
    """Patch `subprocess.Popen` in the worker module; return the recorded call list."""
    calls: List[Any] = []

    def _popen(*args: Any, **kwargs: Any) -> Any:
        calls.append((args, kwargs))
        if error is not None:
            raise error
        return process

    monkeypatch.setattr(process_worker.subprocess, "Popen", _popen)
    return calls


@pytest.fixture
def messages(caplog: pytest.LogCaptureFixture) -> Callable[[], List[str]]:
    caplog.set_level(logging.INFO)
    return lambda: [record.getMessage() for record in caplog.records]


@pytest.mark.unit
class TestConstruction:
    def test_logger_is_named_after_the_parent_class(self) -> None:
        parent = QtCore.QObject()
        assert ProcessWorker("cmd", parent=parent).logger.name == "QObjectWorker"

    def test_logger_name_without_parent_is_none_type(self) -> None:
        assert ProcessWorker("cmd").logger.name == "NoneTypeWorker"

    def test_parent_ownership_is_established(self) -> None:
        parent = QtCore.QObject()
        assert ProcessWorker("cmd", parent=parent).parent() is parent

    def test_process_name_is_the_first_token(self) -> None:
        assert ProcessWorker('yt-dlp -f "x" url')._process_name == "yt-dlp"


@pytest.mark.unit
class TestExitCodeNormalisation:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (0, ExitCode.SUCCESS),
            (1, ExitCode.GENERAL_ERROR),
            (-1, ExitCode.PROCESS_FAILED),
            (-2, ExitCode.CANCELED),
            (-3, ExitCode.MISSING_EXECUTABLE),
            (2, 2),
            (127, 127),
            (MAX_POSITIVE_INTEGER, MAX_POSITIVE_INTEGER),
            (MAX_POSITIVE_INTEGER + 1, -(2**31)),
            (4294967295, ExitCode.PROCESS_FAILED),
            (4294967294, ExitCode.CANCELED),
            (4294967293, ExitCode.MISSING_EXECUTABLE),
            (3221225786, 3221225786 - 2**32),
        ],
        ids=["success", "general", "failed", "canceled", "missing", "unmapped-2", "unmapped-127",
             "int32-max", "int32-overflow", "wrap--1", "wrap--2", "wrap--3", "ctrl-c-status"],
    )
    def test_raw_return_codes_are_normalised(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], raw: int, expected: int
    ) -> None:
        install_popen(monkeypatch, FakeProcess(returncode=raw))
        assert run_worker(ProcessWorker("cmd")) == [expected]

    def test_unset_return_code_is_treated_as_general_error(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]]
    ) -> None:
        install_popen(monkeypatch, FakeProcess(returncode=None))
        assert run_worker(ProcessWorker("cmd")) == [ExitCode.GENERAL_ERROR]

    def test_emitted_value_is_always_a_signed_32_bit_integer(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]]
    ) -> None:
        for raw in (0, 5, 2**31, 2**32 - 1):
            install_popen(monkeypatch, FakeProcess(returncode=raw))
            (code,) = run_worker(ProcessWorker("cmd"))
            assert -(2**31) <= code <= 2**31 - 1


@pytest.mark.unit
class TestPopenContract:
    def test_process_is_launched_through_the_shell_with_merged_text_streams(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]]
    ) -> None:
        calls = install_popen(monkeypatch, FakeProcess())
        run_worker(ProcessWorker("echo hi"))
        (args, kwargs), = calls
        assert args == ("echo hi",)
        assert kwargs == {
            "shell": True,
            "stdout": process_worker.subprocess.PIPE,
            "stderr": process_worker.subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
        }

    def test_process_is_waited_for_after_output_is_drained(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]]
    ) -> None:
        process = FakeProcess(["a"])
        install_popen(monkeypatch, process)
        run_worker(ProcessWorker("cmd"))
        assert process.waited


@pytest.mark.unit
class TestOutputForwarding:
    def test_non_empty_lines_are_logged_in_order_and_right_stripped(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], messages: Callable[[], List[str]]
    ) -> None:
        install_popen(monkeypatch, FakeProcess(["first\n", "\n", "  indented  \r\n", "   \n", "last"]))
        run_worker(ProcessWorker("cmd"))
        assert messages() == ["first", "  indented", "last"]

    def test_missing_stdout_pipe_is_tolerated(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], messages: Callable[[], List[str]]
    ) -> None:
        install_popen(monkeypatch, FakeProcess(lines=None, returncode=0))
        assert run_worker(ProcessWorker("cmd")) == [ExitCode.SUCCESS]
        assert messages() == []

    def test_large_output_is_forwarded_completely(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], messages: Callable[[], List[str]]
    ) -> None:
        install_popen(monkeypatch, FakeProcess(f"line {i}\n" for i in range(5000)))
        run_worker(ProcessWorker("cmd"))
        assert len(messages()) == 5000 and messages()[-1] == "line 4999"

    def test_records_use_info_level_on_the_worker_logger(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO)
        install_popen(monkeypatch, FakeProcess(["x"]))
        parent = QtCore.QObject()  # keep alive: Qt deletes children with their parent
        run_worker(ProcessWorker("cmd", parent=parent))
        (record,) = caplog.records
        assert (record.name, record.levelno) == ("QObjectWorker", logging.INFO)


@pytest.mark.unit
class TestFailureHandling:
    def test_launch_failure_emits_minus_one_and_logs_the_cause(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], caplog: pytest.LogCaptureFixture
    ) -> None:
        install_popen(monkeypatch, error=OSError("cannot spawn"))
        assert run_worker(ProcessWorker("yt-dlp --version")) == [ExitCode.PROCESS_FAILED]
        assert "Error while running yt-dlp: cannot spawn" in caplog.text
        assert caplog.records[-1].levelno == logging.ERROR

    def test_error_while_streaming_is_contained(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]], messages: Callable[[], List[str]]
    ) -> None:
        def stream() -> Iterator[str]:
            yield "before\n"
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        install_popen(monkeypatch, FakeProcess(stream()))
        assert run_worker(ProcessWorker("tool arg")) == [-1]
        assert messages()[0] == "before"
        assert messages()[-1].startswith("Error while running tool:")

    def test_signal_is_emitted_exactly_once_per_run(
        self, monkeypatch: pytest.MonkeyPatch, run_worker: Callable[[Any], List[int]]
    ) -> None:
        install_popen(monkeypatch, FakeProcess(["a", "b"]))
        assert len(run_worker(ProcessWorker("cmd"))) == 1


@pytest.mark.integration
class TestRealSubprocess:
    def test_successful_command(
        self, run_worker: Callable[[Any], List[int]], python_command: Callable[[str], str],
        messages: Callable[[], List[str]],
    ) -> None:
        assert run_worker(ProcessWorker(python_command("print('hello')"))) == [ExitCode.SUCCESS]
        assert messages() == ["hello"]

    @pytest.mark.parametrize(("status", "expected"), [(1, ExitCode.GENERAL_ERROR), (2, 2), (42, 42), (255, 255)])
    def test_failure_status_is_propagated(
        self, run_worker: Callable[[Any], List[int]], python_command: Callable[[str], str], status: int, expected: int
    ) -> None:
        assert run_worker(ProcessWorker(python_command(f"import sys; sys.exit({status})"))) == [expected]

    def test_stderr_is_merged_into_the_log(
        self, run_worker: Callable[[Any], List[int]], python_command: Callable[[str], str],
        messages: Callable[[], List[str]],
    ) -> None:
        code = "import sys; print('out'); sys.stderr.write('err\\n'); sys.stderr.flush()"
        run_worker(ProcessWorker(python_command(code)))
        assert sorted(messages()) == ["err", "out"]

    def test_unknown_command_fails_without_raising(
        self, run_worker: Callable[[Any], List[int]], fake_binaries: Any
    ) -> None:
        (code,) = run_worker(ProcessWorker("definitely-not-a-real-binary-xyz"))
        assert code != ExitCode.SUCCESS

    def test_fake_tool_arguments_are_delivered_verbatim(
        self, run_worker: Callable[[Any], List[int]], fake_binaries: Any, tmp_path: Any
    ) -> None:
        run_worker(ProcessWorker(f'ffmpeg -i "{tmp_path}/a b.webm" "{tmp_path}/a b.wav"'))
        assert fake_binaries.argvs("ffmpeg") == [["-i", f"{tmp_path}/a b.webm", f"{tmp_path}/a b.wav"]]


@pytest.mark.integration
class TestThreadedExecution:
    def test_started_worker_emits_from_its_own_thread_and_finishes(
        self, qtbot: Any, python_command: Callable[[str], str]
    ) -> None:
        worker = ProcessWorker(python_command("print('x')"))
        with qtbot.waitSignal(worker.finished_process, timeout=10000) as blocker:
            worker.start()
        assert blocker.args == [ExitCode.SUCCESS]
        assert worker.wait(5000)
        assert worker.isFinished()

    def test_output_is_streamed_before_the_process_terminates(
        self, qtbot: Any, python_command: Callable[[str], str], caplog: pytest.LogCaptureFixture
    ) -> None:
        stamps: List[float] = []

        class Stamp(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                stamps.append(time.monotonic())

        worker = ProcessWorker(python_command("import time; print('early', flush=True); time.sleep(0.8); print('late')"))
        worker.logger.addHandler(Stamp())
        worker.logger.setLevel(logging.INFO)
        with qtbot.waitSignal(worker.finished_process, timeout=10000):
            worker.start()
        finished = time.monotonic()
        worker.wait(5000)
        assert len(stamps) == 2
        assert finished - stamps[0] > 0.5

    def test_several_workers_do_not_interfere(self, qtbot: Any, python_command: Callable[[str], str]) -> None:
        workers = [ProcessWorker(python_command(f"import sys; sys.exit({i})")) for i in range(4)]
        results: dict = {}
        for index, worker in enumerate(workers):
            worker.finished_process.connect(lambda code, i=index: results.__setitem__(i, code))
        for worker in workers:
            worker.start()
        qtbot.waitUntil(lambda: len(results) == 4, timeout=10000)
        for worker in workers:
            worker.wait(5000)
        assert results == {0: ExitCode.SUCCESS, 1: ExitCode.GENERAL_ERROR, 2: 2, 3: 3}
