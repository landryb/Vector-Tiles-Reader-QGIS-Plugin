# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_connections.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgConnections(object):
    def setupUi(self, DlgConnections):
        DlgConnections.setObjectName("DlgConnections")
        DlgConnections.resize(880, 748)
        DlgConnections.setSizeGripEnabled(True)
        self.gridLayout = QtWidgets.QGridLayout(DlgConnections)
        self.gridLayout.setObjectName("gridLayout")
        self.grpOptions = QtWidgets.QGroupBox(DlgConnections)
        self.grpOptions.setMinimumSize(QtCore.QSize(0, 190))
        self.grpOptions.setObjectName("grpOptions")
        self.gridLayout.addWidget(self.grpOptions, 2, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.chkKeepOpen = QtWidgets.QCheckBox(DlgConnections)
        self.chkKeepOpen.setObjectName("chkKeepOpen")
        self.horizontalLayout.addWidget(self.chkKeepOpen, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.btnAdd = QtWidgets.QPushButton(DlgConnections)
        self.btnAdd.setEnabled(False)
        self.btnAdd.setMinimumSize(QtCore.QSize(80, 0))
        self.btnAdd.setObjectName("btnAdd")
        self.horizontalLayout.addWidget(self.btnAdd)
        self.btnClose = QtWidgets.QPushButton(DlgConnections)
        self.btnClose.setMinimumSize(QtCore.QSize(80, 0))
        self.btnClose.setObjectName("btnClose")
        self.horizontalLayout.addWidget(self.btnClose)
        self.btnHelp = QtWidgets.QPushButton(DlgConnections)
        self.btnHelp.setMinimumSize(QtCore.QSize(80, 0))
        self.btnHelp.setObjectName("btnHelp")
        self.horizontalLayout.addWidget(self.btnHelp)
        self.horizontalLayout.setStretch(0, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 3, 0, 1, 1)
        self.tblLayers = QtWidgets.QTableView(DlgConnections)
        self.tblLayers.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblLayers.setProperty("showDropIndicator", False)
        self.tblLayers.setAlternatingRowColors(True)
        self.tblLayers.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tblLayers.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tblLayers.setSortingEnabled(True)
        self.tblLayers.setCornerButtonEnabled(True)
        self.tblLayers.setObjectName("tblLayers")
        self.tblLayers.horizontalHeader().setMinimumSectionSize(140)
        self.tblLayers.horizontalHeader().setStretchLastSection(True)
        self.tblLayers.verticalHeader().setVisible(False)
        self.gridLayout.addWidget(self.tblLayers, 1, 0, 1, 1)
        self.tabConnections = QtWidgets.QTabWidget(DlgConnections)
        self.tabConnections.setMinimumSize(QtCore.QSize(0, 0))
        self.tabConnections.setAutoFillBackground(False)
        self.tabConnections.setMovable(False)
        self.tabConnections.setObjectName("tabConnections")
        self.tabServer = QtWidgets.QWidget()
        self.tabServer.setObjectName("tabServer")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tabServer)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.grpTilejsonConnections = QtWidgets.QGroupBox(self.tabServer)
        self.grpTilejsonConnections.setObjectName("grpTilejsonConnections")
        self.gridLayout_4.addWidget(self.grpTilejsonConnections, 0, 0, 1, 1)
        self.tabConnections.addTab(self.tabServer, "")
        self.tabFile = QtWidgets.QWidget()
        self.tabFile.setObjectName("tabFile")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.tabFile)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.lblSource = QtWidgets.QLabel(self.tabFile)
        self.lblSource.setObjectName("lblSource")
        self.gridLayout_6.addWidget(self.lblSource, 0, 0, 1, 1)
        self.txtPath = QtWidgets.QLineEdit(self.tabFile)
        self.txtPath.setText("")
        self.txtPath.setPlaceholderText("")
        self.txtPath.setObjectName("txtPath")
        self.gridLayout_6.addWidget(self.txtPath, 0, 1, 1, 1)
        self.btnBrowse = QtWidgets.QPushButton(self.tabFile)
        self.btnBrowse.setObjectName("btnBrowse")
        self.gridLayout_6.addWidget(self.btnBrowse, 0, 2, 1, 1)
        self.tabConnections.addTab(self.tabFile, "")
        self.tabDirectory = QtWidgets.QWidget()
        self.tabDirectory.setObjectName("tabDirectory")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.tabDirectory)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.lblSource_2 = QtWidgets.QLabel(self.tabDirectory)
        self.lblSource_2.setObjectName("lblSource_2")
        self.horizontalLayout_2.addWidget(self.lblSource_2)
        self.txtDirectoryPath = QtWidgets.QLineEdit(self.tabDirectory)
        self.txtDirectoryPath.setText("")
        self.txtDirectoryPath.setPlaceholderText("")
        self.txtDirectoryPath.setObjectName("txtDirectoryPath")
        self.horizontalLayout_2.addWidget(self.txtDirectoryPath)
        self.btnSelectDirectory = QtWidgets.QPushButton(self.tabDirectory)
        self.btnSelectDirectory.setObjectName("btnSelectDirectory")
        self.horizontalLayout_2.addWidget(self.btnSelectDirectory)
        self.tabConnections.addTab(self.tabDirectory, "")
        self.gridLayout.addWidget(self.tabConnections, 0, 0, 1, 1, QtCore.Qt.AlignTop)

        self.retranslateUi(DlgConnections)
        self.tabConnections.setCurrentIndex(0)
        self.btnClose.clicked.connect(DlgConnections.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgConnections)
        DlgConnections.setTabOrder(self.tabConnections, self.tblLayers)
        DlgConnections.setTabOrder(self.tblLayers, self.chkKeepOpen)
        DlgConnections.setTabOrder(self.chkKeepOpen, self.btnAdd)
        DlgConnections.setTabOrder(self.btnAdd, self.btnClose)
        DlgConnections.setTabOrder(self.btnClose, self.btnHelp)
        DlgConnections.setTabOrder(self.btnHelp, self.txtPath)
        DlgConnections.setTabOrder(self.txtPath, self.btnBrowse)
        DlgConnections.setTabOrder(self.btnBrowse, self.txtDirectoryPath)
        DlgConnections.setTabOrder(self.txtDirectoryPath, self.btnSelectDirectory)

    def retranslateUi(self, DlgConnections):
        _translate = QtCore.QCoreApplication.translate
        DlgConnections.setWindowTitle(_translate("DlgConnections", "Add Layer(s) from a Vector Tile Source"))
        self.grpOptions.setTitle(_translate("DlgConnections", "Options"))
        self.chkKeepOpen.setText(_translate("DlgConnections", "Keep dialog open"))
        self.btnAdd.setText(_translate("DlgConnections", "Add"))
        self.btnClose.setText(_translate("DlgConnections", "Close"))
        self.btnHelp.setText(_translate("DlgConnections", "Help"))
        self.grpTilejsonConnections.setTitle(_translate("DlgConnections", "Connections"))
        self.tabConnections.setTabText(self.tabConnections.indexOf(self.tabServer), _translate("DlgConnections", "Online"))
        self.lblSource.setText(_translate("DlgConnections", "Path"))
        self.txtPath.setToolTip(_translate("DlgConnections", "The URL to the TileJSON of the tile service (e.g. http://yourtilehoster.com/index.json)"))
        self.btnBrowse.setText(_translate("DlgConnections", "Browse"))
        self.tabConnections.setTabText(self.tabConnections.indexOf(self.tabFile), _translate("DlgConnections", "MBTile"))
        self.lblSource_2.setText(_translate("DlgConnections", "Path"))
        self.txtDirectoryPath.setToolTip(_translate("DlgConnections", "The URL to the TileJSON of the tile service (e.g. http://yourtilehoster.com/index.json)"))
        self.btnSelectDirectory.setText(_translate("DlgConnections", "Browse"))
        self.tabConnections.setTabText(self.tabConnections.indexOf(self.tabDirectory), _translate("DlgConnections", "Directory"))
