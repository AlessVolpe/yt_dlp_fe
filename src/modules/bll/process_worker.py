import logging
import subprocess
from typing import Optional

from PySide6 import QtCore

from config.constants import MAX_POSITIVE_INTEGER
from config.error_codes import ExitCode


class ProcessWorker(QtCore.QThread):
    """
    Background thread that runs a shell command and streams its output.

    Executes the given command in a subprocess, forwarding every non-empty
    line of its combined stdout/stderr output to a logger in real time,
    and emits a Qt signal carrying the process' exit code once it
    terminates (or -1 if launching/monitoring the process raised an
    exception).

    Attributes:
        finished_process (QtCore.Signal): Signal emitted with the exit
            code (int) once the subprocess has finished running.
    """

    finished_process = QtCore.Signal(int)

    def __init__(self, command: str, parent: Optional[QtCore.QObject] = None) -> None:
        """
        Initialize the worker with the command it will run.

        Args:
            command (str): The full shell command to execute.
            parent (Optional[QtCore.QObject]): The parent QObject that
                owns this worker; also used to build the logger's name.
                Defaults to None.
        """
        super().__init__(parent)
        logger_name = f"{parent.__class__.__name__}Worker"
        self._command = command
        self.logger = logging.getLogger(logger_name)

        self._process_name = self._command.split(" ")[0]

    def run(self) -> None:
        """
        Run the stored command in a subprocess and emit its exit code.

        Launches the command via `subprocess.Popen`, logging every
        non-empty line of its output as it is produced. Once the process
        exits, normalizes the raw return code (converting an unsigned
        32-bit value back to its signed representation) and maps it to an
        `ExitCode` member when possible before emitting it through
        `finished_process`. Any exception raised while running the
        command is logged and results in `finished_process` being
        emitted with -1 instead.

        Returns:
            None
        """
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
