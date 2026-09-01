from PySide6 import QtCore, QtWidgets
from src.modules.runner import Runner

class GUI(QtWidgets.QWidget):
    """
        Main GUI class for the application
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT-DLP UI")
        self.setGeometry(100, 100, 800, 600)

        # Set up gui elements
        self.line_edit = QtWidgets.QLineEdit(self)
        self.line_edit.setPlaceholderText("Enter URL here...")

        self.dialog_box = QtWidgets.QPlainTextEdit(self)

        self.audio_only_button = QtWidgets.QPushButton("Download Audio Only", self)
        self.video_button = QtWidgets.QPushButton("Download Video", self)

        # Set up the layout
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.main_layout.addWidget(
            self.line_edit, 0, 0, 1, 2,
            alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
            )
        self.main_layout.addWidget(
            self.dialog_box, 1, 0, 1, 2,
            alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
            )
        self.main_layout.addWidget(
            self.audio_only_button, 2, 0,
            alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
            )
        self.main_layout.addWidget(
            self.video_button, 2, 1,
            alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
            )

        # Set element sizes
        # (temporary solution, will be replaced with a more dynamic layout in the future)
        self.line_edit.setFixedSize(400, 30)
        self.dialog_box.setFixedSize(600, 200)
        self.audio_only_button.setFixedSize(200, 50)
        self.video_button.setFixedSize(200, 50)

        self.dialog_box.setReadOnly(True)

        # Connect button click events to their respective slot functions
        self.audio_only_button.clicked.connect(
            lambda: Runner(
                self.line_edit.text(),
                "audio", self).on_audio_only_button_click()
            )
        self.video_button.clicked.connect(
            lambda: Runner(
                self.line_edit.text(),
                "video", self).on_video_button_click()
            )
