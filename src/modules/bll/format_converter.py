from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PySide6 import QtCore

from config.error_codes import ExitCode
from modules.bll.process_worker import ProcessWorker

if TYPE_CHECKING:
    from modules.guis.user_interface import UserInterface

logger = logging.getLogger(__name__)


class FormatConverter(QtCore.QObject):
    """
    Converts a downloaded media file to its final format via ffmpeg.

    Given the base path of a file that yt-dlp downloaded as `.webm`,
    converts it to `.wav` (for audio downloads) or `.mp4` (for video
    downloads) by running `ffmpeg` in a background `ProcessWorker`, then
    removes the original `.webm` file once the conversion succeeds.

    Attributes:
        finished_conversion (QtCore.Signal): Signal emitted once the
            conversion attempt (successful, failed, or skipped) has
            completed.
    """

    finished_conversion = QtCore.Signal()

    def __init__(
            self,
            gui: UserInterface,
            download_type: str,
            file_path: str,
            is_playlist: bool = False,
    ) -> None:
        """
        Initialize the converter for a single downloaded file.

        Args:
            gui (UserInterface): The main window, used to update the
                status badge and append messages to the activity log.
            download_type (str): Either "audio" or "video"; determines
                the target format ("wav" or "mp4").
            file_path (str): The downloaded file's path, without its
                extension.
            is_playlist (bool): Whether this file is part of a playlist
                batch; only affects the wording of log messages. Defaults
                to False.
        """
        super().__init__()
        self.gui = gui
        self.download_type = download_type
        self.file_path = file_path
        self.is_playlist = is_playlist

        self._worker: Optional[ProcessWorker] = None

    def convert_file(self) -> None:
        """
        Convert the downloaded webm file to wav (audio) or mp4 (video).

        If no `.webm` file exists at `file_path`, assumes no conversion
        is needed and emits `finished_conversion` immediately. Otherwise,
        starts a background `ProcessWorker` running `ffmpeg` to perform
        the conversion asynchronously.

        Returns:
            None
        """
        source = Path(f"{self.file_path}.webm")
        if not source.exists():
            logger.info(f"{self.file_path} was not downloaded as .webm file - no conversion needed")
            self.finished_conversion.emit()
            return

        ext = "wav" if self.download_type == "audio" else "mp4"
        cmd = f'ffmpeg -i "{source}" "{self.file_path}.{ext}"'

        self._set_status("Converting...")
        logger.info(f"Converting the {self.download_type} webm file to {ext} file")

        self._worker = ProcessWorker(cmd, parent=self)
        self._worker.finished_process.connect(self._on_conversion_end)
        self._worker.start()

    def _on_conversion_end(self, exit_code: int) -> None:
        """
        Handle the completion of the ffmpeg conversion process.

        Deletes the original `.webm` file when the conversion succeeded,
        then emits `finished_conversion` regardless of the outcome.

        `finished_process` is emitted from inside `ProcessWorker.run()`,
        a hair before its underlying OS thread has actually unwound.
        This `FormatConverter` has no Qt parent, so it - and the
        `ProcessWorker` QThread it parents - is destroyed the instant
        whoever holds it (e.g. a playlist conversion loop) drops the
        last Python reference, which can happen synchronously from
        within this very slot. Waiting for the worker here closes that
        window: it guarantees the QThread is fully stopped before this
        object can be torn down, regardless of how quickly the caller
        chains into the next conversion. Without it, destroying a
        QThread Qt still considers running aborts the process (seen on
        Windows as STATUS_STACK_BUFFER_OVERRUN). The wait is effectively
        instant here, since the thread is already finishing.

        Args:
            exit_code (int): The exit code returned by the ffmpeg
                subprocess.

        Returns:
            None
        """
        logger.info(f"Conversion finished (exit code: {exit_code})")

        if self._worker is not None:
            self._worker.wait()

        if exit_code == ExitCode.SUCCESS:
            try:
                self.gui.dialog_box.appendPlainText(
                    f"Deleting temporary {"file" if self.is_playlist is True else "files"}...")
                file_path = Path(f"{self.file_path}.webm")
                file_path.unlink()
            except FileNotFoundError:
                self.gui.dialog_box.appendPlainText("Temporary file not found.")

        self.finished_conversion.emit()

    def _set_status(self, text: str) -> None:
        """
        Update the status badge text.

        Args:
            text (str): The new text to display on the status badge.

        Returns:
            None
        """
        self.gui.status_badge.setText(text)
