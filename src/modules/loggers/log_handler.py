import logging
from typing import override

from PySide6 import QtCore


class QtLogHandler(QtCore.QObject, logging.Handler):
    """
    A logging handler that re-emits every log record as a Qt signal.

    Bridges the standard `logging` module into Qt's signal/slot system,
    so any part of the app that logs through the standard logging
    interface can have its output show up in the GUI without holding a
    direct reference to the relevant widget.

    Attributes:
        message (QtCore.Signal): Signal emitted with the formatted log
            message (str) for every record handled.

    """

    message = QtCore.Signal(str)

    def __init__(self, level: int = logging.NOTSET) -> None:
        """
        Initialize the handler and set its message formatter.

        Args:
            level (int): The minimum logging level this handler will
                process. Defaults to `logging.NOTSET`.
        """
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self, level)
        self.setFormatter(logging.Formatter("%(message)s"))

    @override
    def emit(self, record: logging.LogRecord) -> None:
        """
        Forward a log record as a Qt signal.

        Called by the logging module for every record; forwards it as a
        Qt signal instead of writing to stdout directly. Safe to call
        from a background thread - Qt queues the delivery onto whichever
        thread this handler lives on.

        Args:
            record (logging.LogRecord): The log record to format and
                emit.

        Returns:
            None
        """
        self.message.emit(self.format(record))
