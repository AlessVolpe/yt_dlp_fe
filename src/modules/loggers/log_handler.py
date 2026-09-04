import logging
from typing import override

from PySide6 import QtCore


class QtLogHandler(QtCore.QObject, logging.Handler):
    """
        A logging handler that re-emits every log as a Qt signal,
        so any part of the app that can log through `stdout` and
        have it show up in the GUI without holding a direct
        reference to the widget.
    """
    message = QtCore.Signal(str)

    def __init__(self, level=logging.NOTSET):
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self, level)
        self.setFormatter(logging.Formatter("%(message)s"))

    @override
    def emit(self, record):
        """
            Called by the logging module for every record; forward
            it as a Qt signal instead of writing to stdout directly.
            Safe to call from a background thread - Qt queues the
            delivery onto whichever thread this handler lives on.
        """
        self.message.emit(self.format(record))
