# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'channelViewWidget.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_channelViewWidget(object):
    def setupUi(self, channelViewWidget):
        if not channelViewWidget.objectName():
            channelViewWidget.setObjectName(u"channelViewWidget")
        channelViewWidget.setEnabled(True)
        channelViewWidget.resize(413, 305)
        self.widget_layout = QGridLayout(channelViewWidget)
        self.widget_layout.setObjectName(u"widget_layout")
        self.stats_gb = QGroupBox(channelViewWidget)
        self.stats_gb.setObjectName(u"stats_gb")
        self.stats_gb.setMinimumSize(QSize(0, 135))
        self.stats_gb.setMaximumSize(QSize(16777215, 135))
        self.stat_layout = QGridLayout(self.stats_gb)
        self.stat_layout.setObjectName(u"stat_layout")
        self.stat_layout.setContentsMargins(9, 9, -1, -1)
        self.label_9 = QLabel(self.stats_gb)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMinimumSize(QSize(0, 20))
        font = QFont()
        font.setBold(True)
        self.label_9.setFont(font)

        self.stat_layout.addWidget(self.label_9, 4, 0, 1, 1)

        self.label_6 = QLabel(self.stats_gb)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setMinimumSize(QSize(0, 20))

        self.stat_layout.addWidget(self.label_6, 1, 2, 1, 1)

        self.label_8 = QLabel(self.stats_gb)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setMinimumSize(QSize(0, 20))

        self.stat_layout.addWidget(self.label_8, 3, 2, 1, 1)

        self.label_7 = QLabel(self.stats_gb)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setMinimumSize(QSize(0, 20))

        self.stat_layout.addWidget(self.label_7, 2, 2, 1, 1)

        self.label_3 = QLabel(self.stats_gb)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setMinimumSize(QSize(0, 20))
        font1 = QFont()
        font1.setBold(False)
        self.label_3.setFont(font1)
        self.label_3.setIndent(-1)

        self.stat_layout.addWidget(self.label_3, 3, 0, 1, 1)

        self.label_5 = QLabel(self.stats_gb)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMinimumSize(QSize(0, 20))
        self.label_5.setFont(font1)
        self.label_5.setIndent(-1)

        self.stat_layout.addWidget(self.label_5, 2, 0, 1, 1)

        self.sum_count = QLabel(self.stats_gb)
        self.sum_count.setObjectName(u"sum_count")
        self.sum_count.setMinimumSize(QSize(75, 20))
        self.sum_count.setFrameShape(QFrame.Shape.Box)
        self.sum_count.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.sum_count, 3, 1, 1, 1)

        self.sum_count_per_m3 = QLabel(self.stats_gb)
        self.sum_count_per_m3.setObjectName(u"sum_count_per_m3")
        self.sum_count_per_m3.setMinimumSize(QSize(75, 20))
        self.sum_count_per_m3.setFont(font)
        self.sum_count_per_m3.setFrameShape(QFrame.Shape.Box)
        self.sum_count_per_m3.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.sum_count_per_m3, 4, 1, 1, 1)

        self.label = QLabel(self.stats_gb)
        self.label.setObjectName(u"label")
        self.label.setEnabled(True)
        self.label.setMinimumSize(QSize(0, 20))
        font2 = QFont()
        font2.setBold(False)
        font2.setItalic(False)
        self.label.setFont(font2)
        self.label.setIndent(-1)

        self.stat_layout.addWidget(self.label, 1, 0, 1, 1)

        self.sum_volume = QLabel(self.stats_gb)
        self.sum_volume.setObjectName(u"sum_volume")
        self.sum_volume.setMinimumSize(QSize(75, 20))
        self.sum_volume.setFrameShape(QFrame.Shape.Box)
        self.sum_volume.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.sum_volume, 2, 1, 1, 1)

        self.sum_time = QLabel(self.stats_gb)
        self.sum_time.setObjectName(u"sum_time")
        self.sum_time.setMinimumSize(QSize(75, 20))
        self.sum_time.setFrameShape(QFrame.Shape.Box)
        self.sum_time.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.sum_time, 1, 1, 1, 1)

        self.label_12 = QLabel(self.stats_gb)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMinimumSize(QSize(0, 20))

        self.stat_layout.addWidget(self.label_12, 4, 2, 1, 1)

        self.w_time = QLabel(self.stats_gb)
        self.w_time.setObjectName(u"w_time")
        self.w_time.setMinimumSize(QSize(75, 20))
        self.w_time.setFrameShape(QFrame.Shape.Box)
        self.w_time.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.w_time, 1, 3, 1, 1)

        self.w_volume = QLabel(self.stats_gb)
        self.w_volume.setObjectName(u"w_volume")
        self.w_volume.setMinimumSize(QSize(75, 20))
        self.w_volume.setFrameShape(QFrame.Shape.Box)
        self.w_volume.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.w_volume, 2, 3, 1, 1)

        self.w_count = QLabel(self.stats_gb)
        self.w_count.setObjectName(u"w_count")
        self.w_count.setMinimumSize(QSize(75, 20))
        self.w_count.setFrameShape(QFrame.Shape.Box)
        self.w_count.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.w_count, 3, 3, 1, 1)

        self.w_count_per_m3 = QLabel(self.stats_gb)
        self.w_count_per_m3.setObjectName(u"w_count_per_m3")
        self.w_count_per_m3.setMinimumSize(QSize(75, 20))
        self.w_count_per_m3.setFrameShape(QFrame.Shape.Box)
        self.w_count_per_m3.setFrameShadow(QFrame.Shadow.Sunken)

        self.stat_layout.addWidget(self.w_count_per_m3, 4, 3, 1, 1)


        self.widget_layout.addWidget(self.stats_gb, 2, 0, 1, 3)

        self.realtime_gb = QGroupBox(channelViewWidget)
        self.realtime_gb.setObjectName(u"realtime_gb")
        self.realtime_gb.setMinimumSize(QSize(0, 120))
        self.realtime_layout = QVBoxLayout(self.realtime_gb)
        self.realtime_layout.setObjectName(u"realtime_layout")

        self.widget_layout.addWidget(self.realtime_gb, 1, 0, 1, 3)

        self.channel_name_label = QLabel(channelViewWidget)
        self.channel_name_label.setObjectName(u"channel_name_label")
        self.channel_name_label.setMinimumSize(QSize(0, 20))
        self.channel_name_label.setMaximumSize(QSize(16777215, 20))
        font3 = QFont()
        font3.setPointSize(12)
        font3.setBold(True)
        self.channel_name_label.setFont(font3)

        self.widget_layout.addWidget(self.channel_name_label, 0, 0, 1, 1)


        self.retranslateUi(channelViewWidget)

        QMetaObject.connectSlotsByName(channelViewWidget)
    # setupUi

    def retranslateUi(self, channelViewWidget):
        channelViewWidget.setWindowTitle(QCoreApplication.translate("channelViewWidget", u"channelViewWidget", None))
        self.stats_gb.setTitle(QCoreApplication.translate("channelViewWidget", u"Statistics", None))
        self.label_9.setText(QCoreApplication.translate("channelViewWidget", u"\u2211 count / m3", None))
        self.label_6.setText(QCoreApplication.translate("channelViewWidget", u"w. time [HH:mm:ss]", None))
        self.label_8.setText(QCoreApplication.translate("channelViewWidget", u"w. count", None))
        self.label_7.setText(QCoreApplication.translate("channelViewWidget", u"w. volume [m3]", None))
        self.label_3.setText(QCoreApplication.translate("channelViewWidget", u"\u2211 count", None))
        self.label_5.setText(QCoreApplication.translate("channelViewWidget", u"\u2211 volume [m3]", None))
        self.sum_count.setText("")
        self.sum_count_per_m3.setText("")
        self.label.setText(QCoreApplication.translate("channelViewWidget", u"\u2211 time [HH:mm:ss]", None))
        self.sum_volume.setText("")
        self.sum_time.setText("")
        self.label_12.setText(QCoreApplication.translate("channelViewWidget", u"w. count / m3", None))
        self.w_time.setText("")
        self.w_volume.setText("")
        self.w_count.setText("")
        self.w_count_per_m3.setText("")
        self.realtime_gb.setTitle(QCoreApplication.translate("channelViewWidget", u"Realtime Data", None))
        self.channel_name_label.setText(QCoreApplication.translate("channelViewWidget", u"Channel Name", None))
    # retranslateUi

