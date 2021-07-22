# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fartBin.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FartBinDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(728, 556)
        self.gridLayout_2 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setMaximumSize(QtCore.QSize(16777215, 150))
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txtDexPath = QtWidgets.QLineEdit(self.groupBox)
        self.txtDexPath.setObjectName("txtDexPath")
        self.gridLayout.addWidget(self.txtDexPath, 0, 1, 1, 1)
        self.btnSelectDexPath = QtWidgets.QPushButton(self.groupBox)
        self.btnSelectDexPath.setObjectName("btnSelectDexPath")
        self.gridLayout.addWidget(self.btnSelectDexPath, 0, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.txtBinPath = QtWidgets.QLineEdit(self.groupBox)
        self.txtBinPath.setObjectName("txtBinPath")
        self.gridLayout.addWidget(self.txtBinPath, 1, 1, 1, 1)
        self.btnSelectBinPath = QtWidgets.QPushButton(self.groupBox)
        self.btnSelectBinPath.setObjectName("btnSelectBinPath")
        self.gridLayout.addWidget(self.btnSelectBinPath, 1, 2, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnSubmitJar = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmitJar.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmitJar.setObjectName("btnSubmitJar")
        self.horizontalLayout.addWidget(self.btnSubmitJar)
        self.btnSubmit = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.horizontalLayout.addWidget(self.btnSubmit)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.txtResult = QtWidgets.QPlainTextEdit(self.groupBox_2)
        self.txtResult.setObjectName("txtResult")
        self.gridLayout_3.addWidget(self.txtResult, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.groupBox_2, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "fart处理bin数据"))
        self.groupBox.setTitle(_translate("Dialog", "操作"))
        self.label.setText(_translate("Dialog", "dex文件："))
        self.btnSelectDexPath.setText(_translate("Dialog", "选择"))
        self.label_2.setText(_translate("Dialog", "bin文件："))
        self.btnSelectBinPath.setText(_translate("Dialog", "选择"))
        self.btnSubmitJar.setText(_translate("Dialog", "使用jar生成dex"))
        self.btnSubmit.setText(_translate("Dialog", "开始处理"))
        self.groupBox_2.setTitle(_translate("Dialog", "结果"))

