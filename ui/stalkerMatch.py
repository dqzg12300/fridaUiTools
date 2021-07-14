# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'stalkerMatch.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_StalkerMatchDialog(object):
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
        self.btnSelectLogPath = QtWidgets.QPushButton(self.groupBox)
        self.btnSelectLogPath.setObjectName("btnSelectLogPath")
        self.gridLayout.addWidget(self.btnSelectLogPath, 0, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.txtSavePath = QtWidgets.QLineEdit(self.groupBox)
        self.txtSavePath.setObjectName("txtSavePath")
        self.gridLayout.addWidget(self.txtSavePath, 1, 1, 1, 1)
        self.txtLogPath = QtWidgets.QLineEdit(self.groupBox)
        self.txtLogPath.setObjectName("txtLogPath")
        self.gridLayout.addWidget(self.txtLogPath, 0, 1, 1, 1)
        self.btnSubmit = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmit.setObjectName("btnSubmit")
        self.gridLayout.addWidget(self.btnSubmit, 2, 2, 1, 1)
        self.btnSelectSavePath = QtWidgets.QPushButton(self.groupBox)
        self.btnSelectSavePath.setObjectName("btnSelectSavePath")
        self.gridLayout.addWidget(self.btnSelectSavePath, 1, 2, 1, 1)
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
        Dialog.setWindowTitle(_translate("Dialog", "stalker日志输出整理"))
        self.groupBox.setTitle(_translate("Dialog", "操作"))
        self.label.setText(_translate("Dialog", "log文件："))
        self.btnSelectLogPath.setText(_translate("Dialog", "选择"))
        self.label_2.setText(_translate("Dialog", "save文件："))
        self.btnSubmit.setText(_translate("Dialog", "开始处理"))
        self.btnSelectSavePath.setText(_translate("Dialog", "选择"))
        self.groupBox_2.setTitle(_translate("Dialog", "结果"))

