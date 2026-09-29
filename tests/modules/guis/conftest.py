"""Fixtures specific to the GUI test modules."""
from __future__ import annotations

from typing import Any, List, Tuple

import pytest
from PySide6 import QtCore

from modules.bll.dependency_checker import Dependency


@pytest.fixture
def sample_dependencies() -> Tuple[Dependency, ...]:
    """Two synthetic dependencies used to populate the error dialog."""
    return (
        Dependency("alpha-tool", "Does alpha things", "https://example.org/alpha"),
        Dependency("beta-tool", "Does beta things", "https://example.org/beta"),
    )


@pytest.fixture
def recorded_timers(monkeypatch: pytest.MonkeyPatch) -> List[Tuple[int, Any]]:
    """Intercept ``QTimer.singleShot``: record (delay, callback) instead of scheduling."""
    calls: List[Tuple[int, Any]] = []
    monkeypatch.setattr(QtCore.QTimer, "singleShot", staticmethod(lambda ms, callback: calls.append((ms, callback))))
    return calls
