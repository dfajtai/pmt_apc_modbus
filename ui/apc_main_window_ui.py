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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_APC_main_window(object):
    def setupUi(self, APC_main_window):
        if not APC_main_window.objectName():
            APC_main_window.setObjectName(u"APC_main_window")
        APC_main_window.setEnabled(True)
        APC_main_window.resize(821, 635)
        self.actionConnect = QAction(APC_main_window)
        self.actionConnect.setObjectName(u"actionConnect")
        self.actionStart = QAction(APC_main_window)
        self.actionStart.setObjectName(u"actionStart")
        self.actionStop = QAction(APC_main_window)
        self.actionStop.setObjectName(u"actionStop")
        self.actionConnect_2 = QAction(APC_main_window)
        self.actionConnect_2.setObjectName(u"actionConnect_2")
        self.actionStart_2 = QAction(APC_main_window)
        self.actionStart_2.setObjectName(u"actionStart_2")
        self.actionStop_2 = QAction(APC_main_window)
        self.actionStop_2.setObjectName(u"actionStop_2")
        self.actionDisconnect = QAction(APC_main_window)
        self.actionDisconnect.setObjectName(u"actionDisconnect")
        self.actionView_records = QAction(APC_main_window)
        self.actionView_records.setObjectName(u"actionView_records")
        self.actionGenerate_report = QAction(APC_main_window)
        self.actionGenerate_report.setObjectName(u"actionGenerate_report")
        self.actionSearch_session = QAction(APC_main_window)
        self.actionSearch_session.setObjectName(u"actionSearch_session")
        self.centralwidget = QWidget(APC_main_window)
        self.centralwidget.setObjectName(u"centralwidget")
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setObjectName(u"main_layout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setEnabled(True)
        self.tabWidget.setTabsClosable(False)
        self.control_tab = QWidget()
        self.control_tab.setObjectName(u"control_tab")
        self.verticalLayout_3 = QVBoxLayout(self.control_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.control_gb = QGroupBox(self.control_tab)
        self.control_gb.setObjectName(u"control_gb")
        self.verticalLayout = QVBoxLayout(self.control_gb)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.pushButton = QPushButton(self.control_gb)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.control_gb)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setEnabled(False)

        self.verticalLayout.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.control_gb)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setEnabled(False)

        self.verticalLayout.addWidget(self.pushButton_3)

        self.pushButton_4 = QPushButton(self.control_gb)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setEnabled(False)

        self.verticalLayout.addWidget(self.pushButton_4)


        self.verticalLayout_3.addWidget(self.control_gb)

        self.groupBox = QGroupBox(self.control_tab)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.textBrowser = QTextBrowser(self.groupBox)
        self.textBrowser.setObjectName(u"textBrowser")

        self.verticalLayout_2.addWidget(self.textBrowser)


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
        self.config_tab = QWidget()
        self.config_tab.setObjectName(u"config_tab")
        self.verticalLayout_5 = QVBoxLayout(self.config_tab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.config_tab)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.label_2 = QLabel(self.config_tab)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.label_3 = QLabel(self.config_tab)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.label_4 = QLabel(self.config_tab)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.lineEdit = QLineEdit(self.config_tab)
        self.lineEdit.setObjectName(u"lineEdit")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lineEdit)

        self.lineEdit_2 = QLineEdit(self.config_tab)
        self.lineEdit_2.setObjectName(u"lineEdit_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEdit_2)

        self.lineEdit_3 = QLineEdit(self.config_tab)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lineEdit_3)

        self.lineEdit_4 = QLineEdit(self.config_tab)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.lineEdit_4)


        self.verticalLayout_5.addLayout(self.formLayout)

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

        self.main_layout.addWidget(self.tabWidget)

        APC_main_window.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(APC_main_window)
        self.statusbar.setObjectName(u"statusbar")
        APC_main_window.setStatusBar(self.statusbar)

        self.retranslateUi(APC_main_window)

        self.tabWidget.setCurrentIndex(4)


        QMetaObject.connectSlotsByName(APC_main_window)
    # setupUi

    def retranslateUi(self, APC_main_window):
        APC_main_window.setWindowTitle(QCoreApplication.translate("APC_main_window", u"APC Recorder", None))
        self.actionConnect.setText(QCoreApplication.translate("APC_main_window", u"Connect", None))
        self.actionStart.setText(QCoreApplication.translate("APC_main_window", u"Start", None))
        self.actionStop.setText(QCoreApplication.translate("APC_main_window", u"Stop", None))
        self.actionConnect_2.setText(QCoreApplication.translate("APC_main_window", u"Connect", None))
        self.actionStart_2.setText(QCoreApplication.translate("APC_main_window", u"Start", None))
        self.actionStop_2.setText(QCoreApplication.translate("APC_main_window", u"Stop", None))
        self.actionDisconnect.setText(QCoreApplication.translate("APC_main_window", u"Disconnect", None))
        self.actionView_records.setText(QCoreApplication.translate("APC_main_window", u"View records", None))
        self.actionGenerate_report.setText(QCoreApplication.translate("APC_main_window", u"Generate report", None))
        self.actionSearch_session.setText(QCoreApplication.translate("APC_main_window", u"Search session", None))
        self.control_gb.setTitle(QCoreApplication.translate("APC_main_window", u"Control", None))
        self.pushButton.setText(QCoreApplication.translate("APC_main_window", u"Connect", None))
        self.pushButton_2.setText(QCoreApplication.translate("APC_main_window", u"Start", None))
        self.pushButton_3.setText(QCoreApplication.translate("APC_main_window", u"Stop", None))
        self.pushButton_4.setText(QCoreApplication.translate("APC_main_window", u"Disconnect", None))
        self.groupBox.setTitle(QCoreApplication.translate("APC_main_window", u"Log", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.control_tab), QCoreApplication.translate("APC_main_window", u"Control", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.view_tab), QCoreApplication.translate("APC_main_window", u"View", None))
        self.load_session_data.setText(QCoreApplication.translate("APC_main_window", u"Load Session Data", None))
        self.pushButton_5.setText(QCoreApplication.translate("APC_main_window", u"Create Report", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.browse_tab), QCoreApplication.translate("APC_main_window", u"Browse", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.report_tab), QCoreApplication.translate("APC_main_window", u"Report", None))
        self.label.setText(QCoreApplication.translate("APC_main_window", u"TextLabel", None))
        self.label_2.setText(QCoreApplication.translate("APC_main_window", u"TextLabel", None))
        self.label_3.setText(QCoreApplication.translate("APC_main_window", u"TextLabel", None))
        self.label_4.setText(QCoreApplication.translate("APC_main_window", u"TextLabel", None))
        self.pushButton_6.setText(QCoreApplication.translate("APC_main_window", u"PushButton", None))
        self.pushButton_7.setText(QCoreApplication.translate("APC_main_window", u"PushButton", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.config_tab), QCoreApplication.translate("APC_main_window", u"Config", None))
    # retranslateUi

