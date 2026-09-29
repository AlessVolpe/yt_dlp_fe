"""Tests for ``modules.guis.progress_window.ProgressWindow``."""
from __future__ import annotations

import gc
import os
import subprocess
import sys
from typing import Any, List, Tuple
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from config.constants import BASE_DIR
from modules.guis import progress_window as progress_module
from modules.guis.progress_window import ProgressWindow
from modules.guis.user_interface import UserInterface


@pytest.fixture
def window(qtbot: Any, recorded_timers: List[Tuple[int, Any]]) -> ProgressWindow:
    """A window whose deferred timers are recorded instead of scheduled."""
    instance = ProgressWindow()
    qtbot.addWidget(instance)
    return instance


@pytest.mark.gui
class TestAppearance:
    def test_fixed_frameless_topmost_window(self, window: ProgressWindow) -> None:
        assert window.windowTitle() == "yt-dlp ui"
        assert (window.minimumWidth(), window.minimumHeight()) == (320, 130)
        assert (window.maximumWidth(), window.maximumHeight()) == (320, 130)
        flags = window.windowFlags()
        assert flags & QtCore.Qt.WindowType.FramelessWindowHint
        assert flags & QtCore.Qt.WindowType.WindowStaysOnTopHint

    def test_initial_status_text(self, window: ProgressWindow) -> None:
        assert window.status_label.text() == "Checking for yt-dlp updates..."
        assert window.status_label.alignment() == QtCore.Qt.AlignmentFlag.AlignCenter

    def test_progress_bar_is_indeterminate_and_slim(self, window: ProgressWindow) -> None:
        bar = window.progress_bar
        assert (bar.minimum(), bar.maximum()) == (0, 0)
        assert not bar.isTextVisible()
        assert bar.minimumHeight() == bar.maximumHeight() == 6

    def test_dark_theme_is_applied(self, window: ProgressWindow) -> None:
        assert "#17181c" in window.styleSheet() and "#e5533d" in window.styleSheet()


@pytest.mark.unit
class TestUpdateFlow:
    def test_construction_defers_the_update_check_by_100_ms(
        self, window: ProgressWindow, recorded_timers: List[Tuple[int, Any]]
    ) -> None:
        assert recorded_timers == [(100, window._run_update)]

    def test_success_reports_and_schedules_the_hand_over(
        self, window: ProgressWindow, recorded_timers: List[Tuple[int, Any]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        update = MagicMock()
        monkeypatch.setattr(progress_module.Runner, "update_on_startup", staticmethod(update))
        window._run_update()
        update.assert_called_once_with()
        assert window.status_label.text() == "yt-dlp is up to date."
        assert recorded_timers[-1] == (5000, window._finish)

    def test_failure_is_reported_and_does_not_block_startup(
        self, window: ProgressWindow, recorded_timers: List[Tuple[int, Any]], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            progress_module.Runner, "update_on_startup", staticmethod(MagicMock(side_effect=RuntimeError("boom")))
        )
        window._run_update()
        assert window.status_label.text() == "Update check failed: boom"
        assert recorded_timers[-1] == (5000, window._finish)

    @pytest.mark.integration
    def test_update_check_invokes_the_real_command(self, window: ProgressWindow, fake_binaries: Any) -> None:
        window._run_update()
        assert fake_binaries.argvs("yt-dlp") == [["-U"]]
        assert window.status_label.text() == "yt-dlp is up to date."


@pytest.mark.gui
class TestHandOver:
    @pytest.fixture
    def stub_main(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        stub = MagicMock(name="UserInterface")
        monkeypatch.setattr(progress_module, "UserInterface", stub)
        return stub

    def test_main_window_is_created_and_shown_once(self, window: ProgressWindow, stub_main: MagicMock) -> None:
        window._finish()
        stub_main.assert_called_once_with()
        stub_main.return_value.show.assert_called_once_with()
        assert window.main_app is stub_main.return_value

    def test_finished_signal_is_emitted_and_the_splash_is_closed(
        self, qtbot: Any, window: ProgressWindow, stub_main: MagicMock
    ) -> None:
        window.show()
        with qtbot.waitSignal(window.finished, timeout=1000):
            window._finish()
        assert not window.isVisible()

    def test_signal_precedes_window_closure(self, window: ProgressWindow, stub_main: MagicMock) -> None:
        window.show()
        observed: List[bool] = []
        window.finished.connect(lambda: observed.append(window.isVisible()))
        window._finish()
        assert observed == [True]

    def test_real_main_window_becomes_visible(self, qtbot: Any, window: ProgressWindow) -> None:
        window._finish()
        main = next(w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, UserInterface))
        qtbot.addWidget(main)
        assert window.main_app is main
        assert main.isVisible()


_GC_PROBE = """
import gc, sys
from PySide6 import QtWidgets
app = QtWidgets.QApplication([])
from modules.guis.progress_window import ProgressWindow
from modules.guis.user_interface import UserInterface
ProgressWindow._run_update = lambda self: None
splash = ProgressWindow()
splash._finish()
gc.collect()
app.processEvents()
alive = [w for w in app.topLevelWidgets() if isinstance(w, UserInterface) and w.isVisible()]
sys.exit(0 if alive else 3)
"""


@pytest.mark.integration
class TestRegression:
    def test_main_window_survives_garbage_collection_after_the_handover(self) -> None:
        env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": str(BASE_DIR / "src")}
        completed = subprocess.run([sys.executable, "-c", _GC_PROBE], env=env, capture_output=True, timeout=60)
        assert completed.returncode == 0
