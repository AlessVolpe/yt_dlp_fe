"""Tests for ``modules.guis.user_interface.UserInterface``."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from modules.bll.runner import Runner
from modules.loggers.log_handler import QtLogHandler

LEFT = QtCore.Qt.MouseButton.LeftButton


@pytest.mark.gui
class TestWindow:
    def test_title_icon_and_geometry(self, main_window: Any) -> None:
        assert main_window.windowTitle() == "yt-dlp ui"
        assert not main_window.windowIcon().isNull()
        assert (main_window.minimumWidth(), main_window.minimumHeight()) == (480, 420)
        assert (main_window.width(), main_window.height()) == (480, 460)

    def test_default_download_directory_is_the_system_downloads_folder(self, main_window: Any) -> None:
        expected = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.StandardLocation.DownloadLocation)
        assert main_window.download_directory == expected

    def test_dark_theme_stylesheet_is_applied(self, main_window: Any) -> None:
        sheet = main_window.styleSheet()
        for token in ("#17181c", "#e5533d", "QLineEdit#urlInput", "QPlainTextEdit#logBox", "QPushButton#primaryButton"):
            assert token in sheet


@pytest.mark.gui
class TestWidgets:
    def test_source_section(self, main_window: Any) -> None:
        assert main_window.url_input.objectName() == "urlInput"
        assert main_window.url_input.placeholderText() == "Paste a video or playlist URL..."
        assert main_window.url_input.text() == ""
        assert main_window.url_input.minimumHeight() == main_window.url_input.maximumHeight() == 38
        assert main_window.location_label.text() == f"Save to: {main_window.download_directory}"
        assert main_window.change_button.text() == "Change"
        assert main_window.change_button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    def test_activity_section(self, main_window: Any) -> None:
        assert main_window.status_badge.text() == "Idle"
        assert main_window.status_badge.alignment() == QtCore.Qt.AlignmentFlag.AlignCenter
        log = main_window.dialog_box
        assert log.isReadOnly()
        assert log.toPlainText() == ""
        assert log.placeholderText() == "Logs will appear here once a download starts"
        assert log.minimumHeight() == 140

    def test_action_buttons(self, main_window: Any) -> None:
        audio, video = main_window.audio_only_button, main_window.video_button
        assert (audio.text(), audio.objectName()) == ("Audio only", "secondaryButton")
        assert (video.text(), video.objectName()) == ("Download video", "primaryButton")
        for button in (audio, video):
            assert button.isEnabled()
            assert button.minimumHeight() == button.maximumHeight() == 38
            assert button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    def test_section_headings_and_dividers(self, main_window: Any) -> None:
        headings = [l.text() for l in main_window.findChildren(QtWidgets.QLabel, "sectionLabel")]
        assert headings == ["SOURCE", "ACTIVITY"]
        dividers = main_window.findChildren(QtWidgets.QFrame, "divider")
        assert len(dividers) == 2
        assert all(d.frameShape() == QtWidgets.QFrame.Shape.HLine and d.maximumHeight() == 1 for d in dividers)

    def test_log_box_is_not_user_editable(self, qtbot: Any, main_window: Any) -> None:
        main_window.show()
        qtbot.keyClicks(main_window.dialog_box, "typed")
        assert main_window.dialog_box.toPlainText() == ""


@pytest.mark.gui
class TestWiring:
    def test_runner_is_bound_to_the_window(self, main_window: Any) -> None:
        assert isinstance(main_window.runner, Runner)
        assert main_window.runner.gui is main_window

    def test_change_button_opens_the_directory_dialog(
        self, qtbot: Any, main_window: Any, stub_file_dialog: type, tmp_path: Path
    ) -> None:
        stub_file_dialog.accept = True
        stub_file_dialog.selection = [str(tmp_path)]
        qtbot.mouseClick(main_window.change_button, LEFT)
        assert main_window.location_label.text() == str(tmp_path)

    @pytest.mark.parametrize(("attribute", "kind"), [("audio_only_button", "audio"), ("video_button", "video")])
    def test_action_buttons_trigger_the_matching_download(
        self, qtbot: Any, main_window: Any, monkeypatch: pytest.MonkeyPatch, attribute: str, kind: str
    ) -> None:
        spy = MagicMock()
        monkeypatch.setattr(main_window.runner, "_start_download", spy)
        qtbot.mouseClick(getattr(main_window, attribute), LEFT)
        spy.assert_called_once_with(kind)

    def test_disabled_buttons_do_not_trigger_downloads(
        self, qtbot: Any, main_window: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spy = MagicMock()
        monkeypatch.setattr(main_window.runner, "_start_download", spy)
        main_window.audio_only_button.setEnabled(False)
        qtbot.mouseClick(main_window.audio_only_button, LEFT)
        spy.assert_not_called()


@pytest.mark.gui
class TestLogging:
    def test_handler_is_attached_to_the_root_logger_at_info_level(self, main_window: Any) -> None:
        root = logging.getLogger()
        assert any(isinstance(h, QtLogHandler) for h in root.handlers)
        assert root.level == logging.INFO

    def test_records_from_any_logger_reach_the_activity_log(self, main_window: Any) -> None:
        logging.getLogger("some.module").info("hello log")
        assert main_window.dialog_box.toPlainText() == "hello log"

    def test_debug_records_are_filtered(self, main_window: Any) -> None:
        logging.getLogger("some.module").debug("too verbose")
        assert main_window.dialog_box.toPlainText() == ""

    def test_records_accumulate_line_by_line(self, main_window: Any) -> None:
        log = logging.getLogger("some.module")
        for text in ("one", "two", "three"):
            log.warning(text)
        assert main_window.dialog_box.toPlainText().splitlines() == ["one", "two", "three"]

    def test_records_from_background_threads_are_marshalled_safely(self, qtbot: Any, main_window: Any) -> None:
        thread = threading.Thread(target=lambda: logging.getLogger("bg").info("from thread"))
        thread.start()
        thread.join()
        qtbot.waitUntil(lambda: "from thread" in main_window.dialog_box.toPlainText(), timeout=5000)

    def test_two_windows_each_receive_the_records(self, qtbot: Any, main_window: Any) -> None:
        from modules.guis.user_interface import UserInterface

        other = UserInterface()
        qtbot.addWidget(other)
        logging.getLogger("x").info("broadcast")
        assert main_window.dialog_box.toPlainText() == other.dialog_box.toPlainText() == "broadcast"
