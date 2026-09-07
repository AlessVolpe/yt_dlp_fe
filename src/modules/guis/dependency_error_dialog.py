from typing import Sequence

from PySide6 import QtCore, QtGui, QtWidgets

from config.constants import ICON_PATH
from modules.bll.dependency_checker import Dependency


class DependencyErrorDialog(QtWidgets.QDialog):
    """
    Dialog shown when one or more required external tools are missing.

    Lists each missing dependency with a short description and a link to
    its installation instructions, and offers a "Quit" button since the
    app cannot function without them.

    """

    def __init__(self, missing_dependencies: Sequence[Dependency]) -> None:
        """
        Build and style the dialog for the given missing dependencies.

        Args:
            missing_dependencies (Sequence[Dependency]): The dependencies
                that could not be found on the system PATH, to be listed
                in the dialog.
        """
        super().__init__()
        self.setWindowTitle("YT-DLP frontend: missing dependencies")
        self.setWindowIcon(QtGui.QIcon(str(ICON_PATH)))
        self.setFixedWidth(400)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self._build_ui(missing_dependencies)
        self._apply_styles()

    def _build_ui(self, missing_dependencies: Sequence[Dependency]) -> None:
        """
        Build and arrange the dialog's title, intro text, entries, and quit button.

        Args:
            missing_dependencies (Sequence[Dependency]): The dependencies
                to render as entry cards, one per dependency.

        Returns:
            None
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QtWidgets.QLabel("Required tools not found", self)
        title.setObjectName("titleLabel")

        plural = "these tools are" if len(missing_dependencies) > 1 else "this tool is"
        intro = QtWidgets.QLabel(
            f"YT-DLP frontend couldn't start because {plural} missing from your system PATH:",
            self
        )
        intro.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(intro)

        for dependency in missing_dependencies:
            layout.addWidget(self._build_entry(dependency))

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch()

        quit_button = QtWidgets.QPushButton("Quit", self)
        quit_button.setObjectName("primaryButton")
        quit_button.setFixedHeight(34)
        quit_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        quit_button.clicked.connect(self.reject)
        button_row.addWidget(quit_button)

        layout.addLayout(button_row)

    def _build_entry(self, dependency: Dependency) -> QtWidgets.QWidget:
        """
        Build a single card describing one missing dependency.

        Args:
            dependency (Dependency): The missing dependency to describe.

        Returns:
            QtWidgets.QWidget: A styled card widget showing the
                dependency's name, description, and install link.
        """
        entry = QtWidgets.QWidget(self)
        entry.setObjectName("entryCard")
        entry_layout = QtWidgets.QVBoxLayout(entry)
        entry_layout.setContentsMargins(12, 10, 12, 10)
        entry_layout.setSpacing(4)

        name_label = QtWidgets.QLabel(dependency.executable, entry)
        name_label.setObjectName("entryName")

        desc_label = QtWidgets.QLabel(dependency.description, entry)
        desc_label.setWordWrap(True)
        desc_label.setObjectName("entryDescription")

        link_label = QtWidgets.QLabel(
            f'<a href="{dependency.install_url}">{dependency.install_url}</a>', entry
        )
        link_label.setOpenExternalLinks(True)
        link_label.setObjectName("entryLink")
        link_label.setWordWrap(True)

        entry_layout.addWidget(name_label)
        entry_layout.addWidget(desc_label)
        entry_layout.addWidget(link_label)

        return entry

    def _apply_styles(self) -> None:
        """
        Apply the dark theme stylesheet to the dialog.

        Returns:
            None
        """
        self.setStyleSheet("""
            QDialog {
                background-color: #17181c;
                color: #e6e6e6;
                font-size: 13px;
            }
            QLabel#titleLabel {
                font-size: 15px;
                font-weight: 600;
            }
            QWidget#entryCard {
                background-color: #1f2025;
                border: 1px solid #33343a;
                border-radius: 8px;
            }
            QLabel#entryName {
                color: #e5533d;
                font-weight: 600;
            }
            QLabel#entryDescription {
                color: #c7c8cc;
                font-size: 12px;
            }
            QLabel#entryLink a {
                color: #e5533d;
            }
            QPushButton#primaryButton {
                background-color: #e5533d;
                border: 1px solid #e5533d;
                border-radius: 8px;
                color: #ffffff;
                font-weight: 600;
                padding: 0 18px;
            }
            QPushButton#primaryButton:hover {
                background-color: #d1492f;
            }
        """)
