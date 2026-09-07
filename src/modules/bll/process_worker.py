import logging
import subprocess

from PySide6 import QtCore

from config.constants import MAX_POSITIVE_INTEGER


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
            return_code = process.returncode if process.returncode else -1
            if return_code > MAX_POSITIVE_INTEGER:
                return_code -= 1 << 32

            self.finished_process.emit(return_code)
        except Exception as e:
            self.logger.error(f"Error while running {self._process_name}: {e}")
            self.finished_process.emit(-1)
