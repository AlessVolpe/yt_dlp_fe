import logging
import subprocess
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from modules.bll.format_converter import FormatConverter
from modules.bll.process_worker import ProcessWorker

logger = logging.getLogger(__name__)


class Runner(QtCore.QObject):
    """
        Class to handle the download process.
    """

    def __init__(self, gui, download_dir=None):
        super().__init__()
        self.gui = gui
        self.selected_directory = download_dir
        self.is_playlist = False
        self._worker = None
        self._converter = None

    @QtCore.Slot()
    def is_playlist_check(self, state):
        """
            Slot function to check if a playlist is provided.
        """
        self.is_playlist = state

    @QtCore.Slot()
    def on_audio_only_button_click(self):
        """
            Slot function to handle audio only button click event.
        """
        self._start_download("audio")

    @QtCore.Slot()
    def on_video_button_click(self):
        """
            Slot function to handle video button click event.
        """
        self._start_download("video")

    @QtCore.Slot()
    def _start_download(self, download_type):
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
    def _on_download_end(self, exit_code):
        logger.info(f"Download finished (exit code: {exit_code})")

        if exit_code == 0:
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

    def _convert_playlist_files(self):
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
        self._playlist_files_to_convert = [str(f.with_suffix("")) for f in webm_files]
        self._convert_next_playlist_file()

    def _convert_next_playlist_file(self):
        if not self._playlist_files_to_convert:
            self._end_all_downloads()
            return

        file_path = self._playlist_files_to_convert.pop(0)
        self._converter = FormatConverter(self.gui, self._current_download_type, file_path)
        self._converter.finished_conversion.connect(self._convert_next_playlist_file)
        self._converter.convert_file()

    def _end_all_downloads(self):
        self._set_status("Idle")
        self.gui.audio_only_button.setEnabled(True)
        self.gui.video_button.setEnabled(True)

    def _build_cmd(self, cmd, output_path, url) -> str:
        if self.is_playlist:
            cmd += " --yes-playlist"
            output_path += "/%(playlist_id)s/%(id)s.%(ext)s"
        else:
            cmd += " --no-playlist"
            output_path += "/%(id)s.%(ext)s"

        cmd += f' -o "{output_path}" "{url}"'
        return cmd

    @QtCore.Slot()
    def open_file_dialog(self):
        """
            Function to open a file dialog to select the download directory.
        """
        dialog = QtWidgets.QFileDialog(self.gui)
        dialog.setDirectory(QtCore.QDir.homePath())
        dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.Detail)

        if dialog.exec():
            self.selected_directory = dialog.selectedFiles()[0]
            self.gui.location_label.setText(self.selected_directory)

    @staticmethod
    def update_on_startup():
        cmd = "yt-dlp -U"
        with subprocess.Popen(cmd, shell=True):
            pass

    def _set_status(self, text):
        """
            Update the status badge text.
        """
        self.gui.status_badge.setText(text)
