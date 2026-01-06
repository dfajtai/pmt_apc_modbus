# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'apc_main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QStatusBar, QTabWidget,
    QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_APCMainWindow(object):
    def setupUi(self, APCMainWindow):
        if not APCMainWindow.objectName():
            APCMainWindow.setObjectName(u"APCMainWindow")
        APCMainWindow.setEnabled(True)
        APCMainWindow.resize(821, 635)
        self.actionConnect = QAction(APCMainWindow)
        self.actionConnect.setObjectName(u"actionConnect")
        self.actionStart = QAction(APCMainWindow)
        self.actionStart.setObjectName(u"actionStart")
        self.actionStop = QAction(APCMainWindow)
        self.actionStop.setObjectName(u"actionStop")
        self.actionConnect_2 = QAction(APCMainWindow)
        self.actionConnect_2.setObjectName(u"actionConnect_2")
        self.actionStart_2 = QAction(APCMainWindow)
        self.actionStart_2.setObjectName(u"actionStart_2")
        self.actionStop_2 = QAction(APCMainWindow)
        self.actionStop_2.setObjectName(u"actionStop_2")
        self.actionDisconnect = QAction(APCMainWindow)
        self.actionDisconnect.setObjectName(u"actionDisconnect")
        self.actionView_records = QAction(APCMainWindow)
        self.actionView_records.setObjectName(u"actionView_records")
        self.actionGenerate_report = QAction(APCMainWindow)
        self.actionGenerate_report.setObjectName(u"actionGenerate_report")
        self.actionSearch_session = QAction(APCMainWindow)
        self.actionSearch_session.setObjectName(u"actionSearch_session")
        self.centralwidget = QWidget(APCMainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setObjectName(u"main_layout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setUsesScrollButtons(False)
        self.tabWidget.setDocumentMode(False)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setMovable(False)
        self.config_tab = QWidget()
        self.config_tab.setObjectName(u"config_tab")
        self.verticalLayout_5 = QVBoxLayout(self.config_tab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.configLayout = QFormLayout()
        self.configLayout.setObjectName(u"configLayout")
        self.label = QLabel(self.config_tab)
        self.label.setObjectName(u"label")

        self.configLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.label_2 = QLabel(self.config_tab)
        self.label_2.setObjectName(u"label_2")

        self.configLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.label_3 = QLabel(self.config_tab)
        self.label_3.setObjectName(u"label_3")

        self.configLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.label_4 = QLabel(self.config_tab)
        self.label_4.setObjectName(u"label_4")

        self.configLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.lineEdit = QLineEdit(self.config_tab)
        self.lineEdit.setObjectName(u"lineEdit")

        self.configLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lineEdit)

        self.lineEdit_2 = QLineEdit(self.config_tab)
        self.lineEdit_2.setObjectName(u"lineEdit_2")

        self.configLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEdit_2)

        self.lineEdit_3 = QLineEdit(self.config_tab)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.configLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lineEdit_3)

        self.lineEdit_4 = QLineEdit(self.config_tab)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.configLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.lineEdit_4)


        self.verticalLayout_5.addLayout(self.configLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_6 = QPushButton(self.config_tab)
        self.pushButton_6.setObjectName(u"pushButton_6")

        self.horizontalLayout.addWidget(self.pushButton_6)

        self.pushButton_7 = QPushButton(self.config_tab)
        self.pushButton_7.setObjectName(u"pushButton_7")

        self.horizontalLayout.addWidget(self.pushButton_7)


        self.verticalLayout_5.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_5.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.config_tab, "")
        self.control_tab = QWidget()
        self.control_tab.setObjectName(u"control_tab")
        self.verticalLayout_3 = QVBoxLayout(self.control_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.control_gb = QGroupBox(self.control_tab)
        self.control_gb.setObjectName(u"control_gb")
        self.verticalLayout = QVBoxLayout(self.control_gb)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.connect_btn = QPushButton(self.control_gb)
        self.connect_btn.setObjectName(u"connect_btn")

        self.verticalLayout.addWidget(self.connect_btn)

        self.start_btn = QPushButton(self.control_gb)
        self.start_btn.setObjectName(u"start_btn")
        self.start_btn.setEnabled(False)

        self.verticalLayout.addWidget(self.start_btn)

        self.stop_btn = QPushButton(self.control_gb)
        self.stop_btn.setObjectName(u"stop_btn")
        self.stop_btn.setEnabled(False)

        self.verticalLayout.addWidget(self.stop_btn)

        self.disconnect_btn = QPushButton(self.control_gb)
        self.disconnect_btn.setObjectName(u"disconnect_btn")
        self.disconnect_btn.setEnabled(False)

        self.verticalLayout.addWidget(self.disconnect_btn)


        self.verticalLayout_3.addWidget(self.control_gb)

        self.groupBox = QGroupBox(self.control_tab)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.log_tableview = QTableView(self.groupBox)
        self.log_tableview.setObjectName(u"log_tableview")

        self.verticalLayout_2.addWidget(self.log_tableview)

        self.frame = QFrame(self.groupBox)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_5 = QLabel(self.frame)
        self.label_5.setObjectName(u"label_5")

        self.horizontalLayout_2.addWidget(self.label_5)

        self.log_level_combobox = QComboBox(self.frame)
        self.log_level_combobox.setObjectName(u"log_level_combobox")

        self.horizontalLayout_2.addWidget(self.log_level_combobox)

        self.label_6 = QLabel(self.frame)
        self.label_6.setObjectName(u"label_6")

        self.horizontalLayout_2.addWidget(self.label_6)

        self.log_text_filter = QLineEdit(self.frame)
        self.log_text_filter.setObjectName(u"log_text_filter")

        self.horizontalLayout_2.addWidget(self.log_text_filter)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.log_autoscroll_checkbox = QCheckBox(self.frame)
        self.log_autoscroll_checkbox.setObjectName(u"log_autoscroll_checkbox")
        self.log_autoscroll_checkbox.setChecked(True)

        self.horizontalLayout_2.addWidget(self.log_autoscroll_checkbox)


        self.verticalLayout_2.addWidget(self.frame)


        self.verticalLayout_3.addWidget(self.groupBox)

        self.tabWidget.addTab(self.control_tab, "")
        self.view_tab = QWidget()
        self.view_tab.setObjectName(u"view_tab")
        self.view_layout = QVBoxLayout(self.view_tab)
        self.view_layout.setObjectName(u"view_layout")
        self.tabWidget.addTab(self.view_tab, "")
        self.browse_tab = QWidget()
        self.browse_tab.setObjectName(u"browse_tab")
        self.browse_tab.setEnabled(False)
        self.verticalLayout_4 = QVBoxLayout(self.browse_tab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.sessions_table = QTableWidget(self.browse_tab)
        self.sessions_table.setObjectName(u"sessions_table")

        self.verticalLayout_4.addWidget(self.sessions_table)

        self.load_session_data = QPushButton(self.browse_tab)
        self.load_session_data.setObjectName(u"load_session_data")

        self.verticalLayout_4.addWidget(self.load_session_data)

        self.session_data_table = QTableWidget(self.browse_tab)
        self.session_data_table.setObjectName(u"session_data_table")

        self.verticalLayout_4.addWidget(self.session_data_table)

        self.pushButton_5 = QPushButton(self.browse_tab)
        self.pushButton_5.setObjectName(u"pushButton_5")

        self.verticalLayout_4.addWidget(self.pushButton_5)

        self.tabWidget.addTab(self.browse_tab, "")
        self.report_tab = QWidget()
        self.report_tab.setObjectName(u"report_tab")
        self.tabWidget.addTab(self.report_tab, "")

        self.main_layout.addWidget(self.tabWidget)

        APCMainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(APCMainWindow)
        self.statusbar.setObjectName(u"statusbar")
        APCMainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(APCMainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(APCMainWindow)
    # setupUi

    def retranslateUi(self, APCMainWindow):
        APCMainWindow.setWindowTitle(QCoreApplication.translate("APCMainWindow", u"APC Recorder", None))
        self.actionConnect.setText(QCoreApplication.translate("APCMainWindow", u"Connect", None))
        self.actionStart.setText(QCoreApplication.translate("APCMainWindow", u"Start", None))
        self.actionStop.setText(QCoreApplication.translate("APCMainWindow", u"Stop", None))
        self.actionConnect_2.setText(QCoreApplication.translate("APCMainWindow", u"Connect", None))
        self.actionStart_2.setText(QCoreApplication.translate("APCMainWindow", u"Start", None))
        self.actionStop_2.setText(QCoreApplication.translate("APCMainWindow", u"Stop", None))
        self.actionDisconnect.setText(QCoreApplication.translate("APCMainWindow", u"Disconnect", None))
        self.actionView_records.setText(QCoreApplication.translate("APCMainWindow", u"View records", None))
        self.actionGenerate_report.setText(QCoreApplication.translate("APCMainWindow", u"Generate report", None))
        self.actionSearch_session.setText(QCoreApplication.translate("APCMainWindow", u"Search session", None))
        self.label.setText(QCoreApplication.translate("APCMainWindow", u"TextLabel", None))
        self.label_2.setText(QCoreApplication.translate("APCMainWindow", u"TextLabel", None))
        self.label_3.setText(QCoreApplication.translate("APCMainWindow", u"TextLabel", None))
        self.label_4.setText(QCoreApplication.translate("APCMainWindow", u"TextLabel", None))
        self.pushButton_6.setText(QCoreApplication.translate("APCMainWindow", u"PushButton", None))
        self.pushButton_7.setText(QCoreApplication.translate("APCMainWindow", u"PushButton", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.config_tab), QCoreApplication.translate("APCMainWindow", u"Config", None))
        self.control_gb.setTitle(QCoreApplication.translate("APCMainWindow", u"Control", None))
        self.connect_btn.setText(QCoreApplication.translate("APCMainWindow", u"Connect", None))
        self.start_btn.setText(QCoreApplication.translate("APCMainWindow", u"Start", None))
        self.stop_btn.setText(QCoreApplication.translate("APCMainWindow", u"Stop", None))
        self.disconnect_btn.setText(QCoreApplication.translate("APCMainWindow", u"Disconnect", None))
        self.groupBox.setTitle(QCoreApplication.translate("APCMainWindow", u"Log", None))
        self.label_5.setText(QCoreApplication.translate("APCMainWindow", u"Level", None))
        self.label_6.setText(QCoreApplication.translate("APCMainWindow", u"Text", None))
        self.log_autoscroll_checkbox.setText(QCoreApplication.translate("APCMainWindow", u"Autoscroll", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.control_tab), QCoreApplication.translate("APCMainWindow", u"Control", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.view_tab), QCoreApplication.translate("APCMainWindow", u"View", None))
        self.load_session_data.setText(QCoreApplication.translate("APCMainWindow", u"Load Session Data", None))
        self.pushButton_5.setText(QCoreApplication.translate("APCMainWindow", u"Create Report", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.browse_tab), QCoreApplication.translate("APCMainWindow", u"Browse", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.report_tab), QCoreApplication.translate("APCMainWindow", u"Report", None))
    # retranslateUi

