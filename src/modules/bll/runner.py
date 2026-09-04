import logging
import subprocess

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

        cmd = f'yt-dlp -f "{download_format}" -o "{self.selected_directory}/{subfolder}/%(id)s.%(ext)s" "{url}"'

        if self.is_playlist:
            cmd += " --yes-playlist"

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
            self.converter = FormatConverter(
                self.gui,
                self._current_download_type,
                f"{self.selected_directory}/{self._current_subfolder}/{self._current_filename}"
            )
            self.converter.convert_file()
        else:
            self._set_status("Idle")
            self.gui.audio_only_button.setEnabled(True)
            self.gui.video_button.setEnabled(True)

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
