import logging

from pathlib import Path
from PySide6 import QtCore

from bll.process_worker import ProcessWorker


logger = logging.getLogger(__name__)


class FormatConverter(QtCore.QObject):
    def __init__(self, gui, download_type, file_path):
        super().__init__()
        self.gui = gui
        self.download_type = download_type
        self.file_path = file_path

        self._worker = None

    def convert_file(self, download_type):
        """
            Convert the webm to wav if audio or to mp4 if video
        """
        ext = "wav" if download_type == "audio" else "mp4"
        cmd = f"ffmpeg -i {self.file_path}.webm {self.file_path}.{ext}"

        self._set_status("Converting...")
        logger.info(f"Converting the {download_type} webm file to {ext} file")

        self._worker = ProcessWorker(cmd, parent=self)
        self._worker.finished.connect(self._on_conversion_end)
        self._worker.start()

        try:
            self.gui.dialog_box.appendPlainText("Deleting temporary file...")
            file_path = Path(f"{self.file_path}.webm")
            file_path.unlink()
        except FileNotFoundError:
            self.gui.dialog_box.appendPlainText("File not found.")


    def _on_conversion_end(self, exit_code):
        logger.info(f"Conversion finished (exit code: {exit_code})")
        self._set_status("Idle")


    def _set_status(self, text):
        """
            Update the status badge text.
        """
        self.gui.status_badge.setText(text)