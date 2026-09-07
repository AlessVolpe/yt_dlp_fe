import logging
import subprocess

from PySide6 import QtCore

from config.constants import MAX_POSITIVE_INTEGER
from config.error_codes import ExitCode
from modules.bll.dependency_checker import is_available


class ProcessWorker(QtCore.QThread):
    finished_process = QtCore.Signal(int)

    def __init__(self, command, parent=None):
        super().__init__(parent)
        logger_name = f"{parent.__class__.__name__}Worker"
        self._command = command
        self.logger = logging.getLogger(logger_name)

        self._process_name = self._command.split(" ")[0]

    def run(self):
        try:
            if not is_available(self._process_name):
                self.logger.error(
                    f"'{self._process_name}' was not found on PATH. "
                    "It may have been uninstalled or moved since the app started"
                )
                self.finished_process.emit(ExitCode.MISSING_EXECUTABLE)
                return

            process = subprocess.Popen(
                self._command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            if process.stdout:
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        self.logger.info(line)

            process.wait()
            raw_code = process.returncode if process.returncode is not None else ExitCode.GENERAL_ERROR
            if raw_code > MAX_POSITIVE_INTEGER:
                raw_code -= 1 << 32

            try:
                return_code = ExitCode(raw_code)
            except ValueError:
                return_code = raw_code

            self.finished_process.emit(return_code)
        except Exception as e:
            self.logger.error(f"Error while running {self._process_name}: {e}")
            self.finished_process.emit(-1)
