from PySide6 import QtCore, QtWidgets

class GUI(QtWidgets.QWidget):
    """
        Main GUI class for the application
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YT-DLP UI")
        self.setGeometry(100, 100, 800, 600)

        # Set up gui elements
        self.label = QtWidgets.QLabel("Enter the URL of the video you want to download:", self)
        self.line_edit = QtWidgets.QLineEdit(self)
        self.line_edit.setPlaceholderText("Enter URL here...")

        self.audio_only_button = QtWidgets.QPushButton("Download Audio Only", self)
        self.video_button = QtWidgets.QPushButton("Download Video", self)

        # Set up the layout
        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.addWidget(
            self.label, 0, 0, 1, 2,
            alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
            )
        self.main_layout.addWidget(
            self.line_edit, 1, 0, 1, 2,
            alignment=QtCore.Qt.AlignmentFlag.AlignHCenter
            )
        self.main_layout.addWidget(self.audio_only_button, 2, 0)
        self.main_layout.addWidget(self.video_button, 2, 1)

        # Set element sizes and connect signals to slots
        self.line_edit.setFixedSize(400, 30)
        self.audio_only_button.setFixedSize(200, 50)
        self.video_button.setFixedSize(200, 50)

        self.audio_only_button.clicked.connect(self.on_audio_only_button_click)
        self.video_button.clicked.connect(self.on_video_button_click)


    @QtCore.Slot()
    def on_audio_only_button_click(self):
        """
            Slot function to handle audio only button click event.
        """
        self.audio_only_button.setText("Downloading...")


    @QtCore.Slot()
    def on_video_button_click(self):
        """
            Slot function to handle video button click event.
        """
        self.video_button.setText("Downloading...")