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
        self.selected_directory = self.gui.download_directory
        self.filename = url.split("=")[-1] # Sets filename to the unique yt video ID


    @QtCore.Slot()
    def on_audio_only_button_click(self):
        """
            Slot function to handle audio only button click event.
        """
        cmd = f"yt-dlp -f {self.url} -o {self.selected_directory}/DLP_AUDIO/{self.filename}.mp4"
        self._set_status("Downloading...")
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Downloading audio...")
        self._set_status("Idle")


    @QtCore.Slot()
    def on_video_button_click(self):
        """
            Slot function to handle video button click event.
        """
        cmd = f"yt-dlp -f {self.url} -o {self.selected_directory}/DLP_VIDEO/{self.filename}.mp4"
        self._set_status("Downloading...")
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Downloading video...")
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


    def _set_status(self, text):
        """
            Update the status badge text.
        """
        self.gui.status_badge.setText(text)
