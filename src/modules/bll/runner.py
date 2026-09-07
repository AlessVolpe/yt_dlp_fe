from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from PySide6 import QtCore, QtWidgets

from config.error_codes import ExitCode
from modules.bll.format_converter import FormatConverter
from modules.bll.process_worker import ProcessWorker

if TYPE_CHECKING:
    from modules.guis.user_interface import UserInterface

logger = logging.getLogger(__name__)


class Runner(QtCore.QObject):
    """
    Class to handle the download process.

    Builds and runs the `yt-dlp` subprocess calls that download audio or
    video (optionally as a full playlist), then hands each downloaded
    file off to a `FormatConverter` for conversion, updating the GUI's
    status badge and buttons as the process progresses.
    """

    def __init__(self, gui: UserInterface, download_dir: Optional[str] = None) -> None:
        """
        Initialize the runner.

        Args:
            gui (UserInterface): The main window, used to read user
                input, update the status badge/log, and toggle buttons.
            download_dir (Optional[str]): The directory downloads are
                saved into. Defaults to None.
        """
        super().__init__()
        self.gui = gui
        self.selected_directory = download_dir
        self.is_playlist = False
        self._worker: Optional[ProcessWorker] = None
        self._converter: Optional[FormatConverter] = None

    @QtCore.Slot()
    def is_playlist_check(self, state: bool) -> None:
        """
        Slot function to check if a playlist is provided.

        Args:
            state (bool): Whether the "Is it a Playlist?" checkbox is
                currently checked.

        Returns:
            None
        """
        self.is_playlist = state

    @QtCore.Slot()
    def on_audio_only_button_click(self) -> None:
        """Slot function to handle audio only button click event.

        Returns:
            None

        """
        self._start_download("audio")

    @QtCore.Slot()
    def on_video_button_click(self) -> None:
        """
        Slot function to handle video button click event.

        Returns:
            None
        """
        self._start_download("video")

    @QtCore.Slot()
    def _start_download(self, download_type: str) -> None:
        """
        Build and launch the yt-dlp download command in the background.

        Clears the activity log, reads the URL from the GUI, builds the
        appropriate `yt-dlp` command for the requested download type,
        disables the action buttons, and starts a `ProcessWorker` to run
        the download.

        Args:
            download_type (str): Either "audio" or "video".

        Returns:
            None
        """
        self.gui.dialog_box.clear()
        url = self.gui.url_input.text()
        filename = url.split("=")[-1]
        download_format = "bestaudio/best" if download_type == "audio" else "bestvideo*+bestaudio/best"
        subfolder = "DLP_AUDIO" if download_type == "audio" else "DLP_VIDEO"

        cmd = self._build_cmd(
            f'yt-dlp -f "{download_format}"', f"{self.selected_directory}/{subfolder}", url
        )

        self._set_status("Downloading...")
        self.gui.audio_only_button.setEnabled(False)
        self.gui.video_button.setEnabled(False)
        logger.info(f"Starting {download_type} download: {url}")

        # Store attributes to use AFTER the download finishes
        self._current_download_type = download_type
        self._current_filename = filename
        self._current_subfolder = subfolder

        self._worker = ProcessWorker(cmd, parent=self)
        self._worker.finished_process.connect(self._on_download_end)
        self._worker.start()

    @QtCore.Slot(int)
    def _on_download_end(self, exit_code: int) -> None:
        """
        Handle the completion of the yt-dlp download process.

        On success, either converts every file downloaded for a
        playlist, or converts the single downloaded file. On failure,
        skips straight to resetting the GUI.

        Args:
            exit_code (int): The exit code returned by the yt-dlp
                subprocess.

        Returns:
            None
        """
        logger.info(f"Download finished (exit code: {exit_code})")

        if exit_code == ExitCode.SUCCESS:
            if self.is_playlist:
                self._convert_playlist_files()
            else:
                self.converter = FormatConverter(
                    self.gui,
                    self._current_download_type,
                    f"{self.selected_directory}/{self._current_subfolder}/{self._current_filename}"
                )
                self.converter.finished_conversion.connect(self._end_all_downloads)
                self.converter.convert_file()
        else:
            self._end_all_downloads()

    def _convert_playlist_files(self) -> None:
        """
        Queue every downloaded playlist file for sequential conversion.

        Scans the download subfolder for `.webm` files, sorts them by
        their numeric playlist-index subfolder (falling back to
        alphabetical order), and kicks off conversion of the first file
        in the queue. If no files are found, skips straight to resetting
        the GUI.

        Returns:
            None
        """
        root = Path(self.selected_directory) / self._current_subfolder
        webm_files = sorted(
            root.glob("**/*.webm"),
            key=lambda f: int(f.parent.name) if f.parent.name.isdigit() else f.parent.name
        )

        if not webm_files:
            logger.info("No playlist files found to convert.")
            self._end_all_downloads()
            return

        logger.info(f"Converting {len(webm_files)} webm file(s)...")
        self._playlist_files_to_convert: List[str] = [str(f.with_suffix("")) for f in webm_files]
        self._convert_next_playlist_file()

    def _convert_next_playlist_file(self) -> None:
        """
        Convert the next queued playlist file, one at a time.

        Pops the next file path off `_playlist_files_to_convert` and
        converts it, re-invoking itself once that conversion finishes.
        Once the queue is empty, resets the GUI.

        Returns:
            None
        """
        if not self._playlist_files_to_convert:
            self._end_all_downloads()
            return

        file_path = self._playlist_files_to_convert.pop(0)
        self._converter = FormatConverter(self.gui, self._current_download_type, file_path)
        self._converter.finished_conversion.connect(self._convert_next_playlist_file)
        self._converter.convert_file()

    def _end_all_downloads(self) -> None:
        """
        Reset the GUI back to its idle state.

        Sets the status badge back to "Idle" and re-enables the download
        action buttons.

        Returns:
            None
        """
        self._set_status("Idle")
        self.gui.audio_only_button.setEnabled(True)
        self.gui.video_button.setEnabled(True)

    def _build_cmd(self, cmd: str, output_path: str, url: str) -> str:
        """
        Build the full yt-dlp command string for a download.

        Appends playlist-related flags and the appropriate output
        template depending on whether a playlist download was requested,
        then appends the output path and URL arguments.

        Args:
            cmd (str): The base `yt-dlp` command (including the format
                selector) to extend.
            output_path (str): The destination folder for the downloaded
                file(s), without the output filename template.
            url (str): The video or playlist URL to download.

        Returns:
            str: The complete, ready-to-run `yt-dlp` command string.
        """
        if self.is_playlist:
            cmd += " --yes-playlist"
            output_path += "/%(playlist_id)s/%(playlist_index)s - %(id)s.%(ext)s"
        else:
            cmd += " --no-playlist"
            output_path += "/%(id)s.%(ext)s"

        cmd += f' -o "{output_path}" "{url}"'
        return cmd

    @QtCore.Slot()
    def open_file_dialog(self) -> None:
        """
        Open a file dialog to select the download directory.

        Updates `selected_directory` and the GUI's location label if the
        user confirms a selection.

        Returns:
            None
        """
        dialog = QtWidgets.QFileDialog(self.gui)
        dialog.setDirectory(QtCore.QDir.homePath())
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.Detail)

        if dialog.exec():
            self.selected_directory = dialog.selectedFiles()[0]
            self.gui.location_label.setText(self.selected_directory)

    @staticmethod
    def update_on_startup() -> None:
        """
        Trigger a fire-and-forget `yt-dlp -U` self-update check.

        Returns:
            None
        """
        cmd = "yt-dlp -U"
        with subprocess.Popen(cmd, shell=True):
            pass

    def _set_status(self, text: str) -> None:
        """
        Update the status badge text.

        Args:
            text (str): The new text to display on the status badge.

        Returns:
            None
        """
        self.gui.status_badge.setText(text)
