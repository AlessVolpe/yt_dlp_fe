"""Tests for ``src/main.py`` (application entry point)."""
from __future__ import annotations

import runpy
from typing import Any, Tuple
from unittest.mock import MagicMock

import pytest
from PySide6 import QtWidgets

from config.constants import BASE_DIR
from modules.bll import dependency_checker
from modules.bll.dependency_checker import Dependency
from modules.guis import dependency_error_dialog, progress_window

MAIN = str(BASE_DIR / "src" / "main.py")
MISSING = (Dependency("ffmpeg", "d", "https://example.org"),)


@pytest.fixture
def entry(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Patch every collaborator of ``main.py`` and expose the doubles."""
    app = MagicMock(name="app")
    app.exec.return_value = 7
    doubles = MagicMock()
    doubles.app_cls = MagicMock(name="QApplication", return_value=app)
    doubles.app = app
    doubles.find = MagicMock(name="find_missing_dependencies", return_value=())
    doubles.error_dialog = MagicMock(name="DependencyErrorDialog")
    doubles.progress = MagicMock(name="ProgressWindow")
    for name in ("app_cls", "find", "error_dialog", "progress"):
        doubles.attach_mock(getattr(doubles, name), name)  # record calls in one ordered timeline
    monkeypatch.setattr(QtWidgets, "QApplication", doubles.app_cls)
    monkeypatch.setattr(dependency_checker, "find_missing_dependencies", doubles.find)
    monkeypatch.setattr(dependency_error_dialog, "DependencyErrorDialog", doubles.error_dialog)
    monkeypatch.setattr(progress_window, "ProgressWindow", doubles.progress)
    return doubles


def run_main() -> int:
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(MAIN, run_name="__main__")
    return exit_info.value.code


@pytest.mark.unit
class TestHealthyStartup:
    def test_progress_window_is_shown_and_event_loop_status_is_propagated(self, entry: Any) -> None:
        assert run_main() == 7
        entry.progress.assert_called_once_with()
        entry.progress.return_value.show.assert_called_once_with()
        entry.app.exec.assert_called_once_with()

    def test_dependency_dialog_is_not_shown(self, entry: Any) -> None:
        run_main()
        entry.error_dialog.assert_not_called()

    def test_application_is_created_before_any_window(self, entry: Any) -> None:
        run_main()
        names = [call[0] for call in entry.mock_calls if call[0] in ("app_cls", "progress", "find")]
        assert names.index("app_cls") < names.index("find") < names.index("progress")

    @pytest.mark.parametrize("status", [0, 1, 42])
    def test_exit_status_mirrors_the_event_loop(self, entry: Any, status: int) -> None:
        entry.app.exec.return_value = status
        assert run_main() == status


@pytest.mark.unit
class TestMissingDependencies:
    @pytest.fixture(autouse=True)
    def _missing(self, entry: Any) -> None:
        entry.find.return_value = MISSING

    def test_error_dialog_is_shown_modally_with_the_missing_tools(self, entry: Any) -> None:
        run_main()
        entry.error_dialog.assert_called_once_with(MISSING)
        entry.error_dialog.return_value.exec.assert_called_once_with()

    def test_process_exits_with_status_one(self, entry: Any) -> None:
        assert run_main() == 1

    def test_main_window_and_event_loop_are_never_started(self, entry: Any) -> None:
        run_main()
        entry.progress.assert_not_called()
        entry.app.exec.assert_not_called()


@pytest.mark.unit
def test_importing_the_module_has_no_side_effects(entry: Any) -> None:
    runpy.run_path(MAIN, run_name="not_main")
    entry.app_cls.assert_not_called()
    entry.find.assert_not_called()
