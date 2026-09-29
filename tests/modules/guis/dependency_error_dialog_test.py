"""Tests for ``modules.guis.dependency_error_dialog.DependencyErrorDialog``."""
from __future__ import annotations

from typing import Any, List, Sequence

import pytest
from PySide6 import QtCore, QtWidgets

from modules.bll.dependency_checker import REQUIRED_DEPENDENCIES, Dependency
from modules.guis.dependency_error_dialog import DependencyErrorDialog

LEFT = QtCore.Qt.MouseButton.LeftButton


def build(qtbot: Any, dependencies: Sequence[Dependency]) -> DependencyErrorDialog:
    dialog = DependencyErrorDialog(dependencies)
    qtbot.addWidget(dialog)
    return dialog


def texts(dialog: DependencyErrorDialog, object_name: str) -> List[str]:
    return [label.text() for label in dialog.findChildren(QtWidgets.QLabel, object_name)]


@pytest.mark.gui
class TestWindowProperties:
    def test_title_icon_and_width(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)
        assert dialog.windowTitle() == "YT-DLP frontend: missing dependencies"
        assert not dialog.windowIcon().isNull()
        assert dialog.minimumWidth() == dialog.maximumWidth() == 400

    def test_window_stays_on_top(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)
        assert dialog.windowFlags() & QtCore.Qt.WindowType.WindowStaysOnTopHint

    def test_dark_theme_is_applied(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        assert "#17181c" in build(qtbot, sample_dependencies).styleSheet()


@pytest.mark.gui
class TestContent:
    def test_title_label(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        assert texts(build(qtbot, sample_dependencies), "titleLabel") == ["Required tools not found"]

    def test_one_card_per_dependency(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)
        assert len(dialog.findChildren(QtWidgets.QWidget, "entryCard")) == 2

    def test_card_fields_reflect_the_dependency(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)
        assert texts(dialog, "entryName") == ["alpha-tool", "beta-tool"]
        assert texts(dialog, "entryDescription") == ["Does alpha things", "Does beta things"]

    def test_install_links_are_clickable_anchors(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)
        links = dialog.findChildren(QtWidgets.QLabel, "entryLink")
        assert [l.openExternalLinks() for l in links] == [True, True]
        assert 'href="https://example.org/alpha"' in links[0].text()
        assert "https://example.org/beta</a>" in links[1].text()

    @pytest.mark.parametrize(("count", "phrase"), [(1, "this tool is"), (2, "these tools are")])
    def test_intro_wording_follows_cardinality(self, qtbot: Any, count: int, phrase: str) -> None:
        dependencies = list(REQUIRED_DEPENDENCIES)[:count]
        dialog = build(qtbot, dependencies)
        intro = next(l.text() for l in dialog.findChildren(QtWidgets.QLabel) if "couldn't start" in l.text())
        assert phrase in intro and intro.endswith("system PATH:")

    def test_real_registry_entries_render(self, qtbot: Any) -> None:
        dialog = build(qtbot, REQUIRED_DEPENDENCIES)
        assert texts(dialog, "entryName") == ["yt-dlp", "ffmpeg"]

    def test_empty_input_renders_without_cards(self, qtbot: Any) -> None:
        dialog = build(qtbot, ())
        assert dialog.findChildren(QtWidgets.QWidget, "entryCard") == []
        assert dialog.findChild(QtWidgets.QPushButton, "primaryButton") is not None

    def test_many_dependencies_render_a_card_each(self, qtbot: Any) -> None:
        many = [Dependency(f"tool{i}", "d", f"https://example.org/{i}") for i in range(25)]
        assert len(build(qtbot, many).findChildren(QtWidgets.QWidget, "entryCard")) == 25


@pytest.mark.gui
class TestQuitButton:
    def test_button_is_labelled_and_sized(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)  # keep a reference: children die with the wrapper
        button = dialog.findChild(QtWidgets.QPushButton, "primaryButton")
        assert button.text() == "Quit"
        assert button.minimumHeight() == button.maximumHeight() == 34
        assert button.cursor().shape() == QtCore.Qt.CursorShape.PointingHandCursor

    def test_click_rejects_the_dialog(self, qtbot: Any, sample_dependencies: Sequence[Dependency]) -> None:
        dialog = build(qtbot, sample_dependencies)
        dialog.show()
        button = dialog.findChild(QtWidgets.QPushButton, "primaryButton")
        with qtbot.waitSignal(dialog.rejected, timeout=2000):
            qtbot.mouseClick(button, LEFT)
        assert dialog.result() == QtWidgets.QDialog.DialogCode.Rejected
        assert not dialog.isVisible()

    def test_dialog_is_modal_capable_and_exec_returns_rejected(
        self, qtbot: Any, sample_dependencies: Sequence[Dependency]
    ) -> None:
        dialog = build(qtbot, sample_dependencies)
        button = dialog.findChild(QtWidgets.QPushButton, "primaryButton")
        QtCore.QTimer.singleShot(0, button.click)
        assert dialog.exec() == QtWidgets.QDialog.DialogCode.Rejected
