import os
import subprocess

from PySide6 import QtCore, QtWidgets



class Runner(QtCore.QObject):
    """
        Class to handle the download process.
    """
    def __init__(self, url, download_type, gui):
        super().__init__()
        self.url = url
        self.download_type = download_type
        self.gui = gui
        self.selected_directory = None


    @QtCore.Slot()
    def on_audio_only_button_click(self):
        """
            Slot function to handle audio only button click event.
        """
        if self.selected_directory and os.path.isdir(f"{self.selected_directory}/DLP_AUDIO"):
            os.mkdir(f"{self.selected_directory}/DLP_AUDIO")

        cmd: str = f"yt-dlp -f bestaudio {self.url}"
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Downloading audio...")



    @QtCore.Slot()
    def on_video_button_click(self):
        """
            Slot function to handle video button click event.
        """
        if self.selected_directory and os.path.isdir(f"{self.selected_directory}/DLP_VIDEO"):
            os.mkdir(f"{self.selected_directory}/DLP_VIDEO")

        cmd: str = f"yt-dlp -f bestvideo+bestaudio {self.url}"
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Downloading video...")


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
            self.gui.dialog_box.appendPlainText(
                f"Selected download directory: {self.selected_directory}"
                )
