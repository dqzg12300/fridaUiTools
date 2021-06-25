# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'natives.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_NativesDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(372, 528)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setMaximumSize(QtCore.QSize(60, 16777215))
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 0, 0, 1, 1)
        self.cmbPackage = QtWidgets.QComboBox(self.groupBox_2)
        self.cmbPackage.setObjectName("cmbPackage")
        self.cmbPackage.addItem("")
        self.gridLayout_2.addWidget(self.cmbPackage, 0, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.txtModule = QtWidgets.QLineEdit(self.groupBox)
        self.txtModule.setObjectName("txtModule")
        self.gridLayout.addWidget(self.txtModule, 0, 1, 1, 1)
        self.listModule = QtWidgets.QListWidget(self.groupBox)
        self.listModule.setObjectName("listModule")
        self.gridLayout.addWidget(self.listModule, 1, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.txtMethods = QtWidgets.QPlainTextEdit(self.groupBox)
        self.txtMethods.setObjectName("txtMethods")
        self.gridLayout.addWidget(self.txtMethods, 2, 1, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnSubmit = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.horizontalLayout.addWidget(self.btnSubmit)
        self.btnClear = QtWidgets.QPushButton(self.groupBox)
        self.btnClear.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnClear.setObjectName("btnClear")
        self.horizontalLayout.addWidget(self.btnClear)
        self.gridLayout.addLayout(self.horizontalLayout, 3, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "批量native"))
        self.groupBox_2.setTitle(_translate("Dialog", "指定缓存数据"))
        self.label_5.setText(_translate("Dialog", "进程名："))
        self.cmbPackage.setItemText(0, _translate("Dialog", "选择缓存数据"))
        self.groupBox.setTitle(_translate("Dialog", "native hook"))
        self.label_2.setText(_translate("Dialog", "模块名："))
        self.label.setText(_translate("Dialog", "函数名："))
        self.btnSubmit.setText(_translate("Dialog", "提交"))
        self.btnClear.setText(_translate("Dialog", "清空"))

