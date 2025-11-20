import logging

from typing import Callable, List


class CallbackLoggingHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.callbacks: List[Callable[[str], None]] = []

    def add_callback(self, callback: Callable[[str], None]):
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str], None]):
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        for callback in self.callbacks:
            callback(msg)