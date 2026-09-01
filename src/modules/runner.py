import subprocess

from PySide6 import QtCore



class Runner(QtCore.QObject):
    """
        Class to handle the download process.
    """
    def __init__(self, url, download_type, gui):
        super().__init__()
        self.url = url
        self.download_type = download_type
        self.gui = gui


    @QtCore.Slot()
    def on_audio_only_button_click(self):
        """
            Slot function to handle audio only button click event.
        """
        with subprocess.Popen('echo "Downloading audio..."', shell=True):
            self.gui.dialog_box.appendPlainText("Downloading audio...")



    @QtCore.Slot()
    def on_video_button_click(self):
        """
            Slot function to handle video button click event.
        """
        with subprocess.Popen('echo "Downloading video..."', shell=True):
            self.gui.dialog_box.appendPlainText("Downloading video...")
