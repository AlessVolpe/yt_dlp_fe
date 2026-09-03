from PySide6 import QtCore, QtGui, QtWidgets

from config.constants import ICON_PATH
from modules.runner import Runner


class UserInterface(QtWidgets.QWidget):
    """
        Main GUI class for the application.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp ui")
        self.setWindowIcon(QtGui.QIcon(str(ICON_PATH)))
        self.setMinimumSize(480, 420)
        self.resize(480, 460)

        self.download_directory = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.StandardLocation.DownloadLocation
        )

        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        """
            Build and arrange all widgets in the window.
        """
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_source_section())
        root_layout.addWidget(self._build_divider())
        root_layout.addWidget(self._build_activity_section())
        root_layout.addWidget(self._build_divider())
        root_layout.addLayout(self._build_actions_row())

    def _build_source_section(self):
        """
            Build the URL input and the save-location row beneath it.
        """
        section = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QtWidgets.QLabel("SOURCE", self)
        label.setObjectName("sectionLabel")

        self.url_input = QtWidgets.QLineEdit(self)
        self.url_input.setPlaceholderText("Paste a video or playlist URL...")
        self.url_input.setObjectName("urlInput")
        self.url_input.setFixedHeight(38)

        self.isPlaylistButton = QtWidgets.QCheckBox("Is it a Playlist?", self)
        self.isPlaylistButton.setObjectName("isPlaylistButton")
        self.isPlaylistButton.setChecked(False)
        self.isPlaylistButton.stateChanged.connect(
            lambda: Runner(gui=self).is_playlist_check(self.isPlaylistButton.isChecked())
        )

        location_row = QtWidgets.QHBoxLayout()
        location_row.setContentsMargins(2, 4, 2, 0)

        self.location_label = QtWidgets.QLabel(
            f"Save to: {self.download_directory}", self
        )
        self.location_label.setObjectName("locationLabel")

        change_button = QtWidgets.QPushButton("Change", self)
        change_button.setObjectName("linkButton")
        change_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        change_button.clicked.connect(lambda: Runner(gui=self).open_file_dialog())

        location_row.addWidget(self.location_label)
        location_row.addStretch()
        location_row.addWidget(change_button)

        layout.addWidget(label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.isPlaylistButton)
        layout.addLayout(location_row)

        return section

    def _build_activity_section(self):
        """
            Build the activity log and its status badge.
        """
        section = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(section)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(8)

        header_row = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("ACTIVITY", self)
        label.setObjectName("sectionLabel")

        self.status_badge = QtWidgets.QLabel("Idle", self)
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        header_row.addWidget(label)
        header_row.addStretch()
        header_row.addWidget(self.status_badge)

        self.dialog_box = QtWidgets.QPlainTextEdit(self)
        self.dialog_box.setObjectName("logBox")
        self.dialog_box.setPlaceholderText(
            "Logs will appear here once a download starts"
        )
        self.dialog_box.setReadOnly(True)
        self.dialog_box.setMinimumHeight(140)
        self.dialog_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )

        layout.addLayout(header_row)
        layout.addWidget(self.dialog_box)

        return section

    def _build_actions_row(self):
        """
            Build the audio/video action buttons, right-aligned.
        """
        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 20, 0, 0)
        row.setSpacing(10)

        self.audio_only_button = QtWidgets.QPushButton("Audio only", self)
        self.audio_only_button.setObjectName("secondaryButton")

        self.video_button = QtWidgets.QPushButton("Download video", self)
        self.video_button.setObjectName("primaryButton")

        for button in (self.audio_only_button, self.video_button):
            button.setFixedHeight(38)
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self.audio_only_button.clicked.connect(
            lambda: Runner(
                self.url_input.text(),
                "audio", self).on_audio_only_button_click()
        )
        self.video_button.clicked.connect(
            lambda: Runner(
                self.url_input.text(),
                "video", self).on_video_button_click()
        )

        row.addStretch()
        row.addWidget(self.audio_only_button)
        row.addWidget(self.video_button)

        return row

    def _build_divider(self):
        """
            Build a thin horizontal divider between sections.
        """
        divider = QtWidgets.QFrame(self)
        divider.setObjectName("divider")
        divider.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        return divider

    def _apply_styles(self):
        """
            Apply the dark theme stylesheet to the window.
        """
        self.setStyleSheet("""
            QWidget {
                background-color: #17181c;
                color: #e6e6e6;
                font-size: 13px;
            }
            QLabel#sectionLabel {
                color: #8a8b91;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
            QLabel#locationLabel {
                color: #8a8b91;
                font-size: 12px;
            }
            QLabel#statusBadge {
                background-color: #1f2025;
                border: 1px solid #33343a;
                border-radius: 9px;
                color: #8a8b91;
                font-size: 11px;
                padding: 2px 10px;
            }
            QFrame#divider {
                background-color: #2a2b30;
                border: none;
            }
            QLineEdit#urlInput {
                background-color: #1f2025;
                border: 1px solid #33343a;
                border-radius: 8px;
                padding: 0 12px;
            }
            QLineEdit#urlInput:focus {
                border: 1px solid #e5533d;
            }
            QPlainTextEdit#logBox {
                background-color: #1a1b1f;
                border: 1px solid #2a2b30;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton#linkButton {
                background: transparent;
                border: none;
                color: #e5533d;
                padding: 2px;
            }
            QPushButton#linkButton:hover {
                text-decoration: underline;
            }
            QPushButton#secondaryButton {
                background-color: transparent;
                border: 1px solid #33343a;
                border-radius: 8px;
                padding: 0 16px;
            }
            QPushButton#secondaryButton:hover {
                background-color: #1f2025;
            }
            QPushButton#primaryButton {
                background-color: #e5533d;
                border: 1px solid #e5533d;
                border-radius: 8px;
                color: #ffffff;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton#primaryButton:hover {
                background-color: #d1492f;
            }
            QCheckBox {
                background: transparent;
                color: #e5533d;
            }
        """)

    @QtCore.Slot()
    def on_change_directory_click(self):
        """
            Slot function to handle the "Change" save-location click.
        """
        selected_directory = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select download directory", self.download_directory
        )
        if selected_directory:
            self.download_directory = selected_directory
            self.location_label.setText(f"Save to: {self.download_directory}")
