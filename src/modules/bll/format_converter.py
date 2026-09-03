import subprocess

from pathlib import Path
from PySide6 import QtCore


class FormatConverter(QtCore.QObject):
    def __init__(self, gui, file_path):
        self.gui = gui
        self.file_path = file_path
        super().__init__()

    def convert_audio(self):
        """
            Convert the webm audio file to wav
        """
        cmd = f"ffmpeg -i {self.file_path}.webm {self.file_path}.wav"

        self._set_status("Converting file...")
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Converting audio...")

        try:
            self.gui.dialog_box.appendPlainText("Deleting temporary file...")
            file_path = Path(f"{self.file_path}.webm")
            file_path.unlink()
        except FileNotFoundError:
            self.gui.dialog_box.appendPlainText("File not found.")


    def convert_video(self):
        """
            Convert the webm video file to mp4
        """
        cmd = f"ffmpeg -i {self.file_path}.webm {self.file_path}.mp4"

        self._set_status("Converting file...")
        with subprocess.Popen(cmd, shell=True):
            self.gui.dialog_box.appendPlainText("Converting video...")

        try:
            self.gui.dialog_box.appendPlainText("Deleting temporary file...")
            file_path = Path(f"{self.file_path}.webm")
            file_path.unlink()
        except FileNotFoundError:
            self.gui.dialog_box.appendPlainText("File not found.")




    def _set_status(self, text):
        """
            Update the status badge text.
        """
        self.gui.status_badge.setText(text)