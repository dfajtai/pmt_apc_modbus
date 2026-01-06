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


class ApcGuiController:
    """
    Controller that integrates GUI with ApcDataRecorder backend.
    Handles FSM-like state management for GUI buttons.
    """

    def __init__(self, recorder: ApcDataRecorder):
        self.recorder = recorder
        self.recorder.set_state_change_callback(self.on_backend_state_change)

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

    def on_backend_state_change(self, new_state: str):
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
            if self.gui_update_callback:
                self.gui_update_callback()

    # GUI actions that call backend
    async def connect(self):
        try:
            await self.recorder.initialize()
            self.fsm_connect()
        except Exception as e:
            self.recorder.logger.error(f"Connect failed: {e}")
            self.fsm_error()

    async def start_recording(self):
        try:
            await self.recorder.start_recording()
            self.fsm_start()
        except Exception as e:
            self.recorder.logger.error(f"Start recording failed: {e}")
            self.fsm_error()

    async def stop_recording(self):
        try:
            await self.recorder.stop_recording()
            self.fsm_stop()
        except Exception as e:
            self.recorder.logger.error(f"Stop recording failed: {e}")
            self.fsm_error()

    async def disconnect(self):
        try:
            await self.recorder.close_connections()
            self.fsm_disconnect()
        except Exception as e:
            self.recorder.logger.error(f"Disconnect failed: {e}")
            self.fsm_error()


class MainWindow(QtWidgets.QMainWindow, Ui_APCMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Backend
        self.recorder = ApcDataRecorder()
        self.controller = ApcGuiController(self.recorder)

        # Connect controller to GUI updates
        self.controller.set_gui_update_callback(self.update_buttons)

        # Buttons → Controller actions (async)
        self.connect_btn.clicked.connect(lambda: self.run_async(self.controller.connect()))
        self.start_btn.clicked.connect(lambda: self.run_async(self.controller.start_recording()))
        self.stop_btn.clicked.connect(lambda: self.run_async(self.controller.stop_recording()))
        self.disconnect_btn.clicked.connect(lambda: self.run_async(self.controller.disconnect()))

        self.update_buttons()

        self.logger = self.setup_logging()
        self.logger.info("MainWindow initialized")

    def run_async(self, coro):
        """Run async coroutine in thread-safe way."""
        # For simplicity, assume GUI is in main thread, use asyncio.run or thread
        # In real app, use QThread or similar
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()

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

        logger = logging.getLogger("APC_GUI")
        logger.setLevel(logging.DEBUG)

        if not any(isinstance(h, CallbackLoggingHandler) for h in logger.handlers):
            handler = CallbackLoggingHandler()
            handler.setLevel(logging.DEBUG)

            bridge = QtLogTableBridge(self.log_model)
            handler.add_record_callback(bridge.handle_record)

            logger.addHandler(handler)

        # Also add recorder logs to GUI
        self.recorder.add_log_callback(lambda msg: logger.info(msg))

        return logger

    def update_buttons(self):
        s = self.controller.state
        self.connect_btn.setEnabled(s == 'disconnected')
        self.start_btn.setEnabled(s == 'connected')
        self.disconnect_btn.setEnabled(s == 'connected')
        self.stop_btn.setEnabled(s == 'recording')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()