import logging
from typing import Callable, List

from PySide6 import QtCore


class CallbackLoggingHandler(QtCore.QObject, logging.Handler):
    """
    Backward compatible:
    - string callbacks still work
    - new record callbacks also supported
    """

    log_record_received = QtCore.Signal(object)

    def __init__(self):
        super().__init__()
        logging.Handler.__init__(self)
        self._string_callbacks: List[Callable[[str], None]] = []
        self._record_callbacks: List[Callable[[logging.LogRecord], None]] = []

    # ----------------------------
    # OLD API (string)
    # ----------------------------
    def add_callback(self, callback: Callable[[str], None]):
        if callback not in self._string_callbacks:
            self._string_callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str], None]):
        if callback in self._string_callbacks:
            self._string_callbacks.remove(callback)

    # ----------------------------
    # NEW API (record)
    # ----------------------------
    def add_record_callback(self, callback: Callable[[logging.LogRecord], None]):
        if callback not in self._record_callbacks:
            self._record_callbacks.append(callback)

    def remove_record_callback(self, callback: Callable[[logging.LogRecord], None]):
        if callback in self._record_callbacks:
            self._record_callbacks.remove(callback)

    # ----------------------------
    # EMIT
    # ----------------------------
    def emit(self, record: logging.LogRecord):
        # Emit signal for Qt
        self.log_record_received.emit(record)

        # structured callbacks
        for cb in self._record_callbacks:
            cb(record)

        # legacy string callbacks
        msg = self.format(record)
        for cb in self._string_callbacks:
            cb(msg)
