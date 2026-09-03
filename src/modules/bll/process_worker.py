import logging
import subprocess

from PySide6 import QtCore

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
            self.finished_process.emit(process.returncode)
        except Exception as e:
            self.logger.error(f"Error while running {self._process_name}: {e}")
            self.finished_process.emit(-1)
