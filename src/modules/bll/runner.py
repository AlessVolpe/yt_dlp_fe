import subprocess

from PySide6 import QtCore, QtWidgets

from bll.format_converter import FormatConverter


class Runner(QtCore.QObject):
    """
        Class to handle the download process.
    """
    def __init__(self, gui, url = None, download_type = None, download_dir = None):
        super().__init__()
        self.gui = gui
        self.url = url
        self.download_type = download_type
        self.selected_directory = download_dir
        self.is_playlist = False


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
        cmd = (
            f'yt-dlp -f "bestaudio/best" '
            f'-o "{self.selected_directory}/DLP_AUDIO/%(id)s.%(ext)s" "{self.url}"'
        )
        if self.is_playlist:
            cmd += " --yes-playlist"

        self._set_status("Downloading...")
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Downloading audio...")

        file_path = f"{self.selected_directory}/DLP_AUDIO/{self.url.split("=")[-1]}"
        FormatConverter(self.gui, file_path).convert_audio()

        self._set_status("Idle")


    @QtCore.Slot()
    def on_video_button_click(self):
        """
            Slot function to handle video button click event.
        """
        cmd = (
            'yt-dlp -f "bestvideo*+bestaudio/best" '
            f'-o "{self.selected_directory}/DLP_VIDEO/%(id)s.%(ext)s" "{self.url}"'
        )
        if self.is_playlist:
            cmd += " --yes-playlist"

        self._set_status("Downloading...")
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Downloading video...")

        file_path = f"{self.selected_directory}/DLP_VIDEO/{self.url.split("=")[-1]}"
        FormatConverter(self.gui, file_path).convert_video()

        self._set_status("Idle")


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
