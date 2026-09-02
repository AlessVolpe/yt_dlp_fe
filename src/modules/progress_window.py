import time

from PySide6 import QtCore, QtWidgets

from modules.runner import Runner
from modules.user_interface import UserInterface


class ProgressWindow(QtWidgets.QWidget):
    """
        Small window shown on startup while yt-dlp is checked for updates.
        Runs the update, then closes itself so the main window can appear.
    """

    finished = QtCore.Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp ui")
        self.setFixedSize(320, 130)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self._build_ui()
        self._apply_styles()

        """
            Defer the update call until after the window has painted, so the
            progress bar is actually visible instead of the window appearing
            frozen for the duration of the (blocking) update call.
        """
        QtCore.QTimer.singleShot(100, self._run_update)

    def _build_ui(self):
        """
            Build and arrange the status label and progress bar.
        """
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.status_label = QtWidgets.QLabel("Checking for yt-dlp updates...", self)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)

        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch()

    def _apply_styles(self):
        """
            Apply the same dark theme used across the app.
        """
        self.setStyleSheet("""
            QWidget {
                background-color: #17181c;
                color: #e6e6e6;
                font-size: 13px;
            }
            QLabel#statusLabel {
                color: #c7c8cc;
                font-size: 12px;
            }
            QProgressBar#progressBar {
                background-color: #1f2025;
                border: 1px solid #33343a;
                border-radius: 3px;
            }
            QProgressBar#progressBar::chunk {
                background-color: #e5533d;
                border-radius: 3px;
            }
        """)

    def _run_update(self):
        """
            Trigger the yt-dlp update check and report the result.
        """
        try:
            Runner.update_on_startup()
            self.status_label.setText("yt-dlp is up to date.")
        except Exception as exc:
            self.status_label.setText(f"Update check failed: {exc}")

        QtCore.QTimer.singleShot(5000, self._finish)

    def _finish(self):
        """
            Emit the finished signal and close the window.
        """
        self.finished.emit()
        self.close()
        main_app = UserInterface()
        main_app.show()