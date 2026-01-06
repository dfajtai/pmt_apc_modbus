import logging
from typing import Callable, List


class CallbackLoggingHandler(logging.Handler):
    """
    Backward compatible:
    - string callbacks still work
    - new record callbacks also supported
    """

    def __init__(self):
        super().__init__()
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
        # structured callbacks
        for cb in self._record_callbacks:
            cb(record)

        # legacy string callbacks
        msg = self.format(record)
        for cb in self._string_callbacks:
            cb(msg)
