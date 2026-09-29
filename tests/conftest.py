"""Shared pytest configuration and fixtures for the yt_dlp_fe test suite.

The suite runs headless (``QT_QPA_PLATFORM=offscreen``) and never touches the
network: ``yt-dlp`` and ``ffmpeg`` are replaced by deterministic fake
executables (see ``tests/fakes``) that are prepended to ``PATH``.
"""
from __future__ import annotations

import json
import logging
import os
import stat
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional

# Must be set before the first QApplication is instantiated.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from hypothesis import HealthCheck, settings

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
TESTS_DIR = Path(__file__).resolve().parent
FAKES_DIR = TESTS_DIR / "fakes"

CONFIG_ENV_VAR = "FAKE_BIN_CONFIG"
_FAKE_TOOLS = {"yt-dlp": "fake_yt_dlp.py", "ffmpeg": "fake_ffmpeg.py"}

settings.register_profile(
    "default",
    max_examples=200,
    deadline=None,
    derandomize=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("default")


class FakeBinaries:
    """Controller for the fake ``yt-dlp``/``ffmpeg`` executables on ``PATH``.

    Attributes:
        bin_dir (Path): Directory holding the launcher scripts.
    """

    def __init__(self, bin_dir: Path, config_path: Path, log_path: Path) -> None:
        self.bin_dir = bin_dir
        self._config_path = config_path
        self._log_path = log_path
        self._config: Dict[str, Any] = {"log": str(log_path)}
        self._flush()

    def configure(self, tool: str, **options: Any) -> None:
        """Merge behaviour options for one fake tool (see the scripts' docstrings)."""
        self._config.setdefault(tool, {}).update(options)
        self._flush()

    def calls(self, tool: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return the recorded invocations, optionally filtered by tool name."""
        if not self._log_path.exists():
            return []
        entries = [
            json.loads(line)
            for line in self._log_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        return [entry for entry in entries if tool is None or entry["tool"] == tool]

    def argvs(self, tool: str) -> List[List[str]]:
        """Return only the argument vectors of the recorded invocations of `tool`."""
        return [entry["argv"] for entry in self.calls(tool)]

    def _flush(self) -> None:
        self._config_path.write_text(json.dumps(self._config), encoding="utf-8")


def _write_launcher(bin_dir: Path, name: str, script: Path) -> None:
    """Create an executable named `name` that runs `script` with this interpreter."""
    if os.name == "nt":
        launcher = bin_dir / f"{name}.cmd"
        launcher.write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    else:
        launcher = bin_dir / name
        launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture(autouse=True)
def _isolate_root_logger() -> Iterator[None]:
    """Restore the root logger after each test.

    `UserInterface` attaches a `QtLogHandler` to the root logger and never
    detaches it; without this guard handlers would accumulate across tests.
    """
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    for handler in list(root.handlers):
        if handler not in handlers:
            root.removeHandler(handler)
    root.setLevel(level)


@pytest.fixture
def fake_binaries(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> FakeBinaries:
    """Install fake ``yt-dlp`` and ``ffmpeg`` executables at the head of ``PATH``."""
    root = tmp_path_factory.mktemp("fake_bin")
    bin_dir = root / "bin"
    bin_dir.mkdir()
    for tool, script in _FAKE_TOOLS.items():
        _write_launcher(bin_dir, tool, FAKES_DIR / script)

    controller = FakeBinaries(bin_dir, root / "config.json", root / "calls.jsonl")
    monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), os.environ.get("PATH", "")]))
    monkeypatch.setenv(CONFIG_ENV_VAR, str(root / "config.json"))
    return controller


@pytest.fixture
def download_dir(tmp_path: Path) -> Path:
    """An empty, per-test download destination."""
    path = tmp_path / "downloads"
    path.mkdir()
    return path


def _drain_threads(runner: Any) -> None:
    """Block until every worker thread owned by `runner` has fully stopped."""
    for attribute in ("_worker", "converter", "_converter"):
        owner = getattr(runner, attribute, None)
        worker = owner if hasattr(owner, "wait") else getattr(owner, "_worker", None)
        if worker is not None:
            worker.wait(5000)


@pytest.fixture
def main_window(qtbot: Any, download_dir: Path) -> Iterator[Any]:
    """A real `UserInterface` whose runner saves into `download_dir`."""
    from modules.guis.user_interface import UserInterface

    window = UserInterface()
    qtbot.addWidget(window)
    window.runner.selected_directory = str(download_dir)
    yield window
    _drain_threads(window.runner)


@pytest.fixture
def wait_idle(qtbot: Any, main_window: Any) -> Callable[..., None]:
    """Return a callable that blocks until the window is back in its idle state."""

    def _wait(timeout: int = 15000) -> None:
        qtbot.waitUntil(
            lambda: main_window.status_badge.text() == "Idle"
            and main_window.audio_only_button.isEnabled()
            and main_window.video_button.isEnabled(),
            timeout=timeout,
        )

    return _wait


@pytest.fixture
def stub_file_dialog(monkeypatch: pytest.MonkeyPatch) -> type:
    """Replace `QFileDialog` with a scripted stand-in.

    Tests configure ``stub.accept`` and ``stub.selection`` and inspect
    ``stub.instances`` afterwards.
    """
    from PySide6 import QtWidgets

    real = QtWidgets.QFileDialog

    class _StubFileDialog:
        FileMode = real.FileMode
        ViewMode = real.ViewMode
        accept = True
        selection: List[str] = []
        instances: List["_StubFileDialog"] = []

        def __init__(self, parent: Any = None) -> None:
            self.parent = parent
            self.directory: Optional[str] = None
            self.file_mode: Any = None
            self.view_mode: Any = None
            type(self).instances.append(self)

        def setDirectory(self, directory: str) -> None:
            self.directory = directory

        def setFileMode(self, mode: Any) -> None:
            self.file_mode = mode

        def setViewMode(self, mode: Any) -> None:
            self.view_mode = mode

        def exec(self) -> bool:
            return type(self).accept

        def selectedFiles(self) -> List[str]:
            return list(type(self).selection)

    monkeypatch.setattr(QtWidgets, "QFileDialog", _StubFileDialog)
    return _StubFileDialog
