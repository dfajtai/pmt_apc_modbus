"""
Full example: Matplotlib + Qt6 + transitions FSM
"""

import time
import math
import asyncio
import threading
import random
import sys
import os
from typing import Callable
from collections import deque

import logging
from pathlib import Path

import numpy as np
from scipy.signal import savgol_filter

from transitions import Machine

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ["QT_API"] = "PySide6"

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QTextCursor


from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure


from src.ui.apc_main_window_ui import Ui_APCMainWindow
from src.ui.channel_view_widget_ui import Ui_ChannelViewWidget

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

# ======================================================================
# Data source (UNCHANGED)
# ======================================================================

class AsyncDataSource:
    def __init__(self, signal_amplitude=10, noise_amplitude=5.0,
                 period=1, phase=0.5, maxlen=100):
        self.signal_amplitude = signal_amplitude
        self.noise_amplitude = noise_amplitude
        self.period = period
        self.phase = phase
        self.x_data = deque(maxlen=maxlen)
        self.y_data = deque(maxlen=maxlen)

        self._t0 = None
        self._thread = None
        self._loop = None
        self._stop_event = None

    async def _generate_one(self):
        if self._t0 is None:
            self._t0 = time.monotonic()

        await asyncio.sleep(random.uniform(0.001, 0.2))

        dt = time.monotonic() - self._t0
        noise = (random.random() - 0.5) * 2 * self.noise_amplitude

        v1 = self.signal_amplitude * math.sin(2 * math.pi / self.period * dt + self.phase) + noise
        v2 = self.signal_amplitude * math.cos(2 * math.pi / self.period * dt + self.phase) + noise
        v3 = v1 + v2

        self.x_data.append(dt)
        self.y_data.append((v1, v2, v3))

    async def _main_loop(self):
        while not self._stop_event.is_set():
            await self._generate_one()

    def _thread_func(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()
        self._loop.create_task(self._main_loop())
        self._loop.run_forever()
        self._loop.close()

    def start(self):
        self._thread = threading.Thread(target=self._thread_func, daemon=True)
        self._thread.start()

    def stop(self):
        if self._loop and self._stop_event:
            self._loop.call_soon_threadsafe(self._stop_event.set)
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join()

    def get_data(self):
        return list(self.x_data), list(self.y_data)


# ======================================================================
# Matplotlib canvas
# ======================================================================

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)


# ======================================================================
# Chart widget
# ======================================================================

class CustomChartWidget(QtWidgets.QWidget, Ui_ChannelViewWidget):
    def __init__(self, channel_name: str,
                 canvas: FigureCanvas,
                 get_data_func: Callable,
                 parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.canvas = canvas
        self.realtime_layout.addWidget(self.canvas)
        self.channel_name_label.setText(channel_name)

        self._plot_refs = None
        self._get_data_func = get_data_func

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)

    def update_plot(self):
        xdata, ydata = self._get_data_func()
        if not xdata:
            return

        y1, y2, y3 = zip(*ydata)

        if self._plot_refs is None:
            p1 = self.canvas.axes.plot(xdata, y1, 'r')[0]
            p2 = self.canvas.axes.plot(xdata, y2, 'g')[0]
            p3 = self.canvas.axes.plot(xdata, y3, 'b')[0]
            self._plot_refs = [p1, p2, p3]
        else:
            for data, ref in zip((y1, y2, y3), self._plot_refs):
                ref.set_xdata(xdata)
                ref.set_ydata(data)

        self.canvas.axes.relim()
        self.canvas.axes.autoscale_view()
        self.canvas.draw()


# ======================================================================
# Main window with FSM
# ======================================================================

class MainWindow(QtWidgets.QMainWindow, Ui_APCMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # ------------------------------------------------------------------
        # Data
        # ------------------------------------------------------------------
        self.source = AsyncDataSource(maxlen=100, period=5)
        

        # while len(self.source.x_data) < 30:
        #     time.sleep(0.1)

        # ------------------------------------------------------------------
        # Charts
        # ------------------------------------------------------------------
        wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(wrapper)

        w1 = CustomChartWidget(
            "Channel 1",
            MplCanvas(self),
            get_data_func=self.source.get_data,
            parent=self
        )

        def get_data_channel_2():
            x, y = self.source.get_data()
            if not y:
                return x, []
            y1, y2, y3 = zip(*y)
            y1 = savgol_filter(y1, 21, 3)
            y2 = savgol_filter(y2, 21, 3)
            y3 = savgol_filter(y3, 21, 3)
            return x, list(zip(y1, y2, y3))

        w2 = CustomChartWidget(
            "Channel 2",
            MplCanvas(self),
            get_data_func=get_data_channel_2,
            parent=self
        )

        layout.addWidget(w1)
        layout.addWidget(w2)
        self.view_layout.addWidget(wrapper)

        # ------------------------------------------------------------------
        # Timer
        # ------------------------------------------------------------------
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(lambda: (w1.update_plot(), w2.update_plot()))

        # ------------------------------------------------------------------
        # FSM
        # ------------------------------------------------------------------
        self.machine = Machine(
            model=self,
            states=['disconnected', 'connected', 'measuring'],
            initial='disconnected',
            transitions=[
                dict(trigger='fsm_connect', source='disconnected', dest='connected', after='on_connect'),
                dict(trigger='fsm_start', source='connected', dest='measuring', after='on_start'),
                dict(trigger='fsm_stop', source='measuring', dest='connected', after='on_stop'),
                dict(trigger='fsm_disconnect', source='connected', dest='disconnected', after='on_disconnect'),
            ],
            auto_transitions=False
        )

        # Buttons → FSM
        self.connect_btn.clicked.connect(self.fsm_connect)
        self.start_btn.clicked.connect(self.fsm_start)
        self.stop_btn.clicked.connect(self.fsm_stop)
        self.disconnect_btn.clicked.connect(self.fsm_disconnect)

        self.update_buttons()

        self.logger = self.setup_logging()
        self.logger.info("MainWindow initialized")



    def setup_logging(self) -> logging.Logger:
        # ==================================================
        # MODEL + PROXY
        # ==================================================
        self.log_model = LogTableModel()
        self.log_proxy = LogFilterProxy()
        self.log_proxy.setSourceModel(self.log_model)

        # ==================================================
        # TABLE VIEW
        # ==================================================
        setup_log_table(
            tableview=self.log_tableview,
            model=self.log_model,
            proxy=self.log_proxy
        )

        # ==================================================
        # LEVEL COMBOBOX
        # ==================================================
        populate_log_level_combobox(self.log_level_combobox)

        # ==================================================
        # FILTERS
        # ==================================================
        connect_log_filters(
            proxy=self.log_proxy,
            text_filter_widget=self.log_text_filter,
            level_filter_widget=self.log_level_combobox
        )

        # ==================================================
        # AUTOSCROLL
        # ==================================================
        enable_autoscroll(
            tableview=self.log_tableview,
            model=self.log_model,
            checkbox=self.log_autoscroll_checkbox
        )

        # ==================================================
        # LOGGER
        # ==================================================
        logger = logging.getLogger("APC")
        logger.setLevel(logging.DEBUG)

        if not any(isinstance(h, CallbackLoggingHandler) for h in logger.handlers):
            handler = CallbackLoggingHandler()
            handler.setLevel(logging.DEBUG)

            bridge = QtLogTableBridge(self.log_model)
            handler.add_record_callback(bridge.handle_record)

            logger.addHandler(handler)

        return logger


    # ------------------------------------------------------------------
    # FSM callbacks
    # ------------------------------------------------------------------

    def on_connect(self):
        self.logger.info("FSM: connect")
        self.update_buttons()

    def on_start(self):
        self.logger.info("FSM: start")
        self.timer.start()
        self.source.start()
        self.update_buttons()

    def on_stop(self):
        self.logger.info("FSM: stop")
        self.source.stop()
        self.timer.stop()
        self.update_buttons()

    def on_disconnect(self):
        self.logger.info("FSM: disconnect")
        self.timer.stop()
        self.update_buttons()

    # ------------------------------------------------------------------
    # GUI update from state
    # ------------------------------------------------------------------

    def update_buttons(self):
        s = self.state
        self.connect_btn.setEnabled(s == 'disconnected')
        self.start_btn.setEnabled(s == 'connected')
        self.disconnect_btn.setEnabled(s == 'connected')
        self.stop_btn.setEnabled(s == 'measuring')
        


# ======================================================================
# main
# ======================================================================

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
