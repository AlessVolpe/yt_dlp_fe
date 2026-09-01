import sys

from PySide6 import QtWidgets
from modules.GUI import GUI


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = GUI()
    widget.show()

    sys.exit(app.exec())
