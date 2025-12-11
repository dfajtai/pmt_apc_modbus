"""
Some matplotlib and Qt6 code pattern
https://www.pythonguis.com/tutorials/pyqt6-plotting-matplotlib/
"""

import time
import math
import asyncio

import threading

from collections import deque

import sys
import os
import random

os.environ["QT_API"] = "PyQt6"

from PySide6 import QtCore, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure


class AsyncDataSource:
    """Async adatforrás, async + külön thread, asyncio.Event stop flag használatával"""

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
        v3 = v1+v2
        self.y_data.append((v1,v2,v3))
        self.x_data.append(dt)
        
    async def _main_loop(self):
        while not self._stop_event.is_set():
            await self._generate_one()

    def _thread_func(self):
        """Async loop futtatása külön thread-ben"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._stop_event = asyncio.Event()  # itt jön létre, a loop-hoz kötve

        # Indítjuk a coroutine-t task-ként
        self._loop.create_task(self._main_loop())
        self._loop.run_forever()
        self._loop.close()

    def start(self):
        self._thread = threading.Thread(target=self._thread_func, daemon=True)
        self._thread.start()

    def stop(self):
        if self._loop and self._stop_event:
            # cross-thread safe mód: call_soon_threadsafe
            self._loop.call_soon_threadsafe(self._stop_event.set)
            # a loopot is leállítjuk a stop után
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join()

    def get_data(self):
        return list(self.x_data), list(self.y_data)


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.setCentralWidget(self.canvas)

        n_data = 50
        self.source = AsyncDataSource(maxlen=n_data)
        self.source.start()
        
        
        self.update_plot()
        self._plot_refs = None
        
        self.show()

        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot)
               
        
        self.timer.start()

    def update_plot(self):

        xdata, ydata = self.source.get_data()
        if not xdata or not ydata:
            return
        
        self.xdata = xdata
        y1, y2, y3 = zip(*ydata)   # tuple-öket kapsz vissza
        self.y1 = list(y1)
        self.y2 = list(y2)
        self.y3 = list(y3)
        
        
        if self._plot_refs is None:
            # First time we have no plot reference, so do a normal plot.
            # .plot returns a list of line <reference>s, as we're
            # only getting one we can take the first element.
            p1 = self.canvas.axes.plot(self.xdata, self.y1, 'r')[0]
            p2 = self.canvas.axes.plot(self.xdata, self.y2, 'g')[0]
            p3 = self.canvas.axes.plot(self.xdata, self.y3, 'b')[0]
            self._plot_refs = [p1,p2,p3] 
        else:
            # We have a reference, we can use it to update the data for that line.
            for data, plotref in zip([self.y1,self.y2,self.y3],self._plot_refs):
                plotref.set_ydata(data)
                plotref.set_xdata(self.xdata)
            


        # Trigger the canvas to update and redraw.
        self.canvas.axes.relim()
        self.canvas.axes.autoscale_view()
        self.canvas.draw()





    
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    app.exec()