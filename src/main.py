import sys

from PySide6 import QtWidgets

from modules.bll.dependency_checker import find_missing_dependencies
from modules.guis.dependency_error_dialog import DependencyErrorDialog
from modules.guis.progress_window import ProgressWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    missing_dependencies = find_missing_dependencies()
    if missing_dependencies:
        DependencyErrorDialog(missing_dependencies).exec()
        sys.exit(1)

    progress_window = ProgressWindow()
    progress_window.show()

    sys.exit(app.exec())
