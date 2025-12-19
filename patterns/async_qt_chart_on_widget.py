"""
Full example: Matplotlib + Qt6 dynamic resizing
"""

import time
import math
import asyncio
import threading

from typing import Callable

from collections import deque

import numpy as np
from scipy.signal import savgol_filter

import sys
import os
import random

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ["QT_API"] = "PySide6"

from PySide6 import QtCore, QtWidgets
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure

from src.ui.apc_main_window_ui import Ui_APCMainWindow
from src.ui.channel_view_widget_ui  import Ui_ChannelViewWidget

class AsyncDataSource:
    def __init__(self, signal_amplitude=10, noise_amplitude=5.0, period=1, phase=0.5, maxlen=100):
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

        self.y_data.append((v1, v2, v3))
        self.x_data.append(dt)

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


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)

        # Important to allow expansion
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)


class CustomChartWidget(QtWidgets.QWidget,Ui_ChannelViewWidget):
    def __init__(self, channel_name: str, 
                 canvas: FigureCanvas, 
                 get_data_func: Callable = None,
                 parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Add canvas to layout
        self.canvas = canvas
        self.realtime_layout.addWidget(self.canvas)
        self.channel_name_label.setText(channel_name)

        # Ensure widget expands
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)

    
        self._plot_refs = None

        self._get_data_func = get_data_func

    
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
            for (data, ref) in zip([y1, y2, y3], self._plot_refs):
                ref.set_xdata(xdata)
                ref.set_ydata(data)

        self.canvas.axes.relim()
        self.canvas.axes.autoscale_view()
        self.canvas.draw()


def sliding_mean(x: np.ndarray, window: int) -> np.ndarray:
    """Fast sliding window mean (moving average)."""
    if window < 1:
        raise ValueError("window must be >= 1")
    # flat filter kernel
    kernel = np.ones(window) / window
    # 'same' keeps output same length as input
    return np.convolve(x, kernel, mode='same')


class MainWindow(QtWidgets.QMainWindow, Ui_APCMainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        n_data = 100
        self.source = AsyncDataSource(maxlen=n_data,period=5)
                
        wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        w1 = CustomChartWidget("Channel 1",MplCanvas(self), parent=self, get_data_func=self.source.get_data)
    

        def get_data_channel_2():
            xdata, ydata = self.source.get_data()
            if not ydata:
                return xdata, []
            y1, y2, y3 = zip(*ydata)
            y1 = savgol_filter(y1, window_length=21, polyorder=3)
            y2 = savgol_filter(y2, window_length=21, polyorder=3)
            y3 = savgol_filter(y3, window_length=21, polyorder=3)

            return xdata, list(zip(y1,y2,y3))

        w2 = CustomChartWidget("Channel 2", MplCanvas(self), parent=self, get_data_func=lambda: get_data_channel_2())

        layout.addWidget(w1)
        layout.addWidget(w2)
        wrapper.setLayout(layout)
        self.view_layout.addWidget(wrapper)
        
        self.source.start()
        while True:
            if len(self.source.x_data)>30:
                break
            time.sleep(0.1)
            

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        def update_both():
            w1.update_plot()
            w2.update_plot()
        self.timer.timeout.connect(update_both)
        self.timer.start()

    

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
