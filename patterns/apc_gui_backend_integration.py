"""
GUI integration with ApcDataRecorder FSM backend.
Similar to async_qt_chart_on_widget.py but separated GUI and backend.
"""

import sys
import os
from typing import Callable, Optional
import asyncio
import threading

import logging
from pathlib import Path

from transitions import Machine

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["QT_API"] = "PySide6"

from PySide6 import QtCore, QtWidgets

from src.logic.apc_data_recorder import ApcDataRecorder

from src.ui.apc_main_window_ui import Ui_APCMainWindow
from src.ui.qt_log_table import (
    LogTableModel,
    QtLogTableBridge,
    LogFilterProxy,
    setup_log_table,
    populate_log_level_combobox,
    enable_autoscroll,
    connect_log_filters,
)

from src.services.logging_callback import CallbackLoggingHandler


class BackendThread(QtCore.QThread):
    """
    QThread to run backend operations without blocking GUI.
    """

    # Add failure signals
    connect_failed = QtCore.Signal()
    start_failed = QtCore.Signal()
    stop_failed = QtCore.Signal()
    disconnect_failed = QtCore.Signal()

    # Add success signals
    connect_success = QtCore.Signal()
    start_success = QtCore.Signal()
    stop_success = QtCore.Signal()
    disconnect_success = QtCore.Signal()

    def __init__(self, recorder: ApcDataRecorder):
        super().__init__()
        self.recorder = recorder
        self.loop = None

    @QtCore.Slot()
    def do_connect(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._connect(), self.loop)

    @QtCore.Slot()
    def do_start(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._start(), self.loop)

    @QtCore.Slot()
    def do_stop(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._stop(), self.loop)

    @QtCore.Slot()
    def do_disconnect(self):
        if self.loop:
            asyncio.run_coroutine_threadsafe(self._disconnect(), self.loop)

    async def _connect(self):
        try:
            success = await self.recorder.initialize()
            if success:
                self.recorder.logger.info("Connected successfully")
                self.connect_success.emit()
            else:
                self.connect_failed.emit()
        except Exception as e:
            self.recorder.logger.error(f"Connect failed: {e}")
            self.connect_failed.emit()

    async def _start(self):
        try:
            success = await self.recorder.start_recording()
            if success:
                self.start_success.emit()
            else:
                self.start_failed.emit()
        except Exception as e:
            self.recorder.logger.error(f"Start failed: {e}")
            self.start_failed.emit()

    async def _stop(self):
        try:
            success = await self.recorder.stop_recording()
            if success:
                self.stop_success.emit()
            else:
                self.stop_failed.emit()
        except Exception as e:
            self.recorder.logger.error(f"Stop failed: {e}")
            self.stop_failed.emit()

    async def _disconnect(self):
        try:
            success = await self.recorder.close_connections()
            if success:
                self.disconnect_success.emit()
            else:
                self.disconnect_failed.emit()
        except Exception as e:
            self.recorder.logger.error(f"Disconnect failed: {e}")
            self.disconnect_failed.emit()

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


class ApcGuiController(QtCore.QObject):
    """
    Controller that integrates GUI with ApcDataRecorder backend.
    Handles FSM-like state management for GUI buttons.
    """

    # Signals to communicate with backend thread
    connect_requested = QtCore.Signal()
    start_requested = QtCore.Signal()
    stop_requested = QtCore.Signal()
    disconnect_requested = QtCore.Signal()

    # Signal for state changes
    state_changed = QtCore.Signal(str)

    # Signal for backend state changes (emitted from thread)
    backend_state_changed = QtCore.Signal(str)

    def __init__(self, recorder: ApcDataRecorder):
        super().__init__()
        self.recorder = recorder

        # Connect with queued connection for thread safety
        self.backend_state_changed.connect(self._handle_backend_state_change, QtCore.Qt.QueuedConnection)

        # Local FSM for GUI state (mirrors backend but simpler)
        self.machine = Machine(
            model=self,
            states=['disconnected', 'connected', 'recording', 'error'],
            initial='disconnected',
            transitions=[
                dict(trigger='fsm_connect', source='disconnected', dest='connected'),
                dict(trigger='fsm_start', source='connected', dest='recording'),
                dict(trigger='fsm_stop', source='recording', dest='connected'),
                dict(trigger='fsm_disconnect', source='connected', dest='disconnected'),
                dict(trigger='fsm_error', source='*', dest='error'),
                dict(trigger='fsm_reset', source='error', dest='disconnected'),
            ],
            auto_transitions=False
        )

        self.gui_update_callback: Optional[Callable[[], None]] = None

    def set_gui_update_callback(self, callback: Callable[[], None]):
        self.gui_update_callback = callback

    # GUI actions that emit signals to backend
    def connect(self):
        self.connect_requested.emit()

    def start_recording(self):
        self.start_requested.emit()

    def stop_recording(self):
        self.stop_requested.emit()

    def disconnect(self):
        self.disconnect_requested.emit()

    def _emit_backend_state_change(self, new_state: str):
        self.backend_state_changed.emit(new_state)

    @QtCore.Slot(str)
    def _handle_backend_state_change(self, new_state: str):
        # Map backend states to GUI states
        state_map = {
            'uninitialized': 'disconnected',
            'initialized': 'connected',
            'recording': 'recording',
            'stopped': 'connected',
            'error': 'error'
        }
        gui_state = state_map.get(new_state, 'disconnected')
        if gui_state != self.state:
            # Force transition to match backend
            self.machine.set_state(gui_state)
            self.state_changed.emit(gui_state)
            if self.gui_update_callback:
                self.gui_update_callback()


class MainWindow(QtWidgets.QMainWindow, Ui_APCMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Backend
        self.recorder = ApcDataRecorder(file_logger=True)
        self.controller = ApcGuiController(self.recorder)

        # Call set_state_change_callback after instantiation
        self.recorder.set_state_change_callback(self.controller._emit_backend_state_change)

        # Backend thread
        self.backend_thread = BackendThread(self.recorder)

        # Connect controller signals to backend thread slots
        self.controller.connect_requested.connect(self.backend_thread.do_connect)
        self.controller.start_requested.connect(self.backend_thread.do_start)
        self.controller.stop_requested.connect(self.backend_thread.do_stop)
        self.controller.disconnect_requested.connect(self.backend_thread.do_disconnect)

        # Connect failure signals to controller error trigger
        self.backend_thread.connect_failed.connect(lambda: self.controller.fsm_error())
        self.backend_thread.start_failed.connect(lambda: self.controller.fsm_error())
        self.backend_thread.stop_failed.connect(lambda: self.controller.fsm_error())
        self.backend_thread.disconnect_failed.connect(lambda: self.controller.fsm_error())

        # Remove success signal connections to avoid double triggering
        # self.backend_thread.connect_success.connect(lambda: self.controller.fsm_connect())
        # self.backend_thread.start_success.connect(lambda: self.controller.fsm_start())
        # self.backend_thread.stop_success.connect(lambda: self.controller.fsm_stop())
        # self.backend_thread.disconnect_success.connect(lambda: self.controller.fsm_disconnect())

        self.backend_thread.start()  # Start the backend in thread

        # Connect state change signal to update buttons
        self.controller.state_changed.connect(self.update_buttons)

        # Connect controller to GUI updates
        self.controller.set_gui_update_callback(self.update_buttons)

        # Buttons → Controller actions (now sync, since backend is in thread)
        self.connect_btn.clicked.connect(self.controller.connect)
        self.start_btn.clicked.connect(self.controller.start_recording)
        self.stop_btn.clicked.connect(self.controller.stop_recording)
        self.disconnect_btn.clicked.connect(self.controller.disconnect)

        self.update_buttons()

        # Setup logging
        self.logger = self.setup_logging()
        self.logger.info("MainWindow initialized")

        # Move bridge to main thread
        self.bridge.moveToThread(QtCore.QThread.currentThread())

    def closeEvent(self, event):
        # Stop the backend thread on close
        if self.backend_thread.isRunning():
            self.backend_thread.loop.call_soon_threadsafe(self.backend_thread.loop.stop)
            self.backend_thread.wait()
            self.backend_thread.loop.close()  # Properly close the loop
        event.accept()

    def setup_logging(self) -> logging.Logger:
        # Similar to the example
        self.log_model = LogTableModel()
        self.log_proxy = LogFilterProxy()
        self.log_proxy.setSourceModel(self.log_model)

        setup_log_table(
            tableview=self.log_tableview,
            model=self.log_model,
            proxy=self.log_proxy
        )

        self.log_tableview.setSortingEnabled(True)  # Enable sorting

        populate_log_level_combobox(self.log_level_combobox)
        connect_log_filters(
            proxy=self.log_proxy,
            text_filter_widget=self.log_text_filter,
            level_filter_widget=self.log_level_combobox
        )

        enable_autoscroll(
            tableview=self.log_tableview,
            model=self.log_model,
            checkbox=self.log_autoscroll_checkbox
        )

        # Use the recorder's logger as the single logger
        logger = self.recorder.logger
        logger.setLevel(logging.DEBUG)

        # Add stream handler for terminal/console output
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.DEBUG)
            logger.addHandler(stream_handler)

        # Always create bridge
        self.bridge = QtLogTableBridge(self.log_model)

        # Add GUI handler
        if not any(isinstance(h, CallbackLoggingHandler) for h in logger.handlers):
            handler = CallbackLoggingHandler()
            handler.setLevel(logging.DEBUG)

            handler.add_record_callback(self.bridge.handle_record)

            logger.addHandler(handler)
        else:
            # If handler already exists, add callback to it
            for h in logger.handlers:
                if isinstance(h, CallbackLoggingHandler):
                    h.add_record_callback(self.bridge.handle_record)
                    break

        # Also add recorder logs to GUI
        # self.recorder.add_log_callback(lambda msg: logger.info(msg))  # Removed to avoid duplication

        return logger

    def update_buttons(self, state=None):
        s = state if state else self.controller.state
        self.connect_btn.setEnabled(s == 'disconnected')
        self.start_btn.setEnabled(s == 'connected')
        self.disconnect_btn.setEnabled(s == 'connected')
        self.stop_btn.setEnabled(s == 'recording')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()