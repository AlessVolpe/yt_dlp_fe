import sys

from PySide6 import QtWidgets

from modules.progress_window import ProgressWindow


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    progress_window = ProgressWindow()
    progress_window.show()

    sys.exit(app.exec())

