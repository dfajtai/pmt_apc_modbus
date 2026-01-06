import logging
from pathlib import Path
import time
from dataclasses import dataclass

from PySide6 import QtCore
from PySide6.QtWidgets import QAbstractItemView, QTableView

import logging
import time
from dataclasses import dataclass
from PySide6 import QtCore, QtGui


@dataclass
class LogRow:
    timestamp: float
    level: str
    source: str
    message: str


class LogTableModel(QtCore.QAbstractTableModel):

    HEADERS = ["Time", "Level", "Source", "Message"]

    def __init__(self, max_rows=2000):
        super().__init__()
        self._rows: list[LogRow] = []
        self._max_rows = max_rows

    # --------------------------------------------------
    # Qt mandatory
    # --------------------------------------------------

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.HEADERS)

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.HEADERS[section]

    # --------------------------------------------------
    # DATA + ROLES
    # --------------------------------------------------

    def data(self, index, role):
        if not index.isValid():
            return None

        row = self._rows[index.row()]
        col = index.column()

        # ---- display ----
        if role == QtCore.Qt.DisplayRole:
            if col == 0:
                return time.strftime("%H:%M:%S", time.localtime(row.timestamp))
            if col == 1:
                return row.level
            if col == 2:
                return row.source
            if col == 3:
                return row.message

        # ---- sorting (IMPORTANT) ----
        if role == QtCore.Qt.UserRole:
            if col == 0:
                return row.timestamp
            if col == 1:
                return row.level
            if col == 2:
                return row.source
            if col == 3:
                return row.message

        # ---- coloring ----
        if role == QtCore.Qt.ForegroundRole:
            if row.level == "ERROR":
                return QtGui.QBrush(QtCore.Qt.red)
            if row.level == "WARNING":
                return QtGui.QBrush(QtCore.Qt.darkYellow)
            if row.level == "DEBUG":
                return QtGui.QBrush(QtCore.Qt.gray)

        return None

    # --------------------------------------------------
    # APPEND
    # --------------------------------------------------

    @QtCore.Slot(object)
    def append(self, record: LogRow):
        self.beginInsertRows(
            QtCore.QModelIndex(),
            len(self._rows),
            len(self._rows)
        )

        self._rows.append(record)

        if len(self._rows) > self._max_rows:
            self._rows.pop(0)

        self.endInsertRows()


class QtLogTableBridge(QtCore.QObject):
    log_received = QtCore.Signal(object)

    def __init__(self, model: LogTableModel):
        super().__init__()
        self.log_received.connect(model.append)

    def handle_record(self, record: logging.LogRecord):
        row = LogRow(
            timestamp=record.created,
            level=record.levelname,
            source=record.name,
            message=record.getMessage()
        )
        self.log_received.emit(row)


class LogFilterProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_filter = ""
        self.level_filter = "ALL"

    def set_text_filter(self, text):
        self.text_filter = text.lower()
        self.invalidateFilter()

    def set_level_filter(self, level):
        self.level_filter = level
        self.invalidateFilter()

    def filterAcceptsRow(self, row, parent):
        model = self.sourceModel()

        msg = model.index(row, 3).data()
        level = model.index(row, 1).data()

        if self.level_filter != "ALL" and level != self.level_filter:
            return False

        if self.text_filter and self.text_filter not in msg.lower():
            return False

        return True
    

def enable_autoscroll(
    tableview: QtCore.QObject,
    model: QtCore.QAbstractItemModel,
    checkbox: QtCore.QObject
):
    """
    Scroll tableview to bottom when new rows are inserted
    if checkbox is checked.
    """

    def _auto_scroll(*_):
        if checkbox.isChecked():
            tableview.scrollToBottom()

    checkbox.stateChanged.connect(
    lambda state: tableview.scrollToBottom() if state else None
    )

    model.rowsInserted.connect(_auto_scroll)


def enable_sorting(tableview, proxy_model):
    """
    Enable sorting on tableview using UserRole (timestamp).
    """
    tableview.setModel(proxy_model)
    tableview.setSortingEnabled(True)
    proxy_model.setSortRole(QtCore.Qt.UserRole)

    # default: time ascending
    tableview.sortByColumn(0, QtCore.Qt.AscendingOrder)


def populate_log_level_combobox(combobox):
    combobox.blockSignals(True)
    combobox.clear()

    combobox.addItem("ALL")
    combobox.addItem("DEBUG")
    combobox.addItem("INFO")
    combobox.addItem("WARNING")
    combobox.addItem("ERROR")
    combobox.addItem("CRITICAL")

    combobox.setCurrentText("ALL")
    combobox.blockSignals(False)


def connect_log_filters(
    proxy: LogFilterProxy,
    text_filter_widget,
    level_filter_widget
):
    """
    Connect filter UI elements to proxy model.
    """

    text_filter_widget.textChanged.connect(
        proxy.set_text_filter
    )

    level_filter_widget.currentTextChanged.connect(
        proxy.set_level_filter
    )

def setup_log_table(
    tableview,
    model: LogTableModel,
    proxy: LogFilterProxy
):
    """
    Standard visual setup for log table view.
    """

    proxy.setSourceModel(model)
    proxy.setSortRole(QtCore.Qt.UserRole)

    tableview.setModel(proxy)
    tableview.setSortingEnabled(True)
    tableview.horizontalHeader().setStretchLastSection(True)
    tableview.verticalHeader().hide()
    tableview.setSelectionBehavior(QAbstractItemView.SelectRows)
    tableview.setAlternatingRowColors(True)

    tableview.sortByColumn(0, QtCore.Qt.AscendingOrder)