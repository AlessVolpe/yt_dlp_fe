"""Fixtures specific to the business-logic (``bll``) test modules."""
from __future__ import annotations

import os
import shlex
import subprocess
import sys
from types import SimpleNamespace
from typing import Any, Callable, List

import pytest
from PySide6 import QtWidgets


@pytest.fixture
def python_command() -> Callable[[str], str]:
    """Return a builder turning Python source into a shell command string."""

    def _build(source: str) -> str:
        argv = [sys.executable, "-c", source]
        return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)

    return _build


@pytest.fixture
def run_worker() -> Callable[[Any], List[int]]:
    """Return a callable that runs a `ProcessWorker` synchronously.

    Executing ``run()`` on the calling thread keeps the tests deterministic
    and lets coverage observe the worker body.
    """

    def _run(worker: Any) -> List[int]:
        codes: List[int] = []
        worker.finished_process.connect(codes.append)
        worker.run()
        return codes

    return _run


@pytest.fixture
def converter_gui(qtbot: Any) -> SimpleNamespace:
    """Minimal GUI facade exposing only what `FormatConverter` touches."""
    status_badge = QtWidgets.QLabel("Idle")
    dialog_box = QtWidgets.QPlainTextEdit()
    qtbot.addWidget(status_badge)
    qtbot.addWidget(dialog_box)
    return SimpleNamespace(status_badge=status_badge, dialog_box=dialog_box)
