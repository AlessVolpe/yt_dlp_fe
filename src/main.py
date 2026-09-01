import sys

from PySide6 import QtWidgets
from modules.user_interface import UserInterface


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = UserInterface()
    widget.show()

    sys.exit(app.exec())
