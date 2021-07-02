# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'callFunction.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CallFunctionDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(529, 431)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 1, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 1, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.txtMethod = QtWidgets.QLineEdit(self.groupBox)
        self.txtMethod.setObjectName("txtMethod")
        self.gridLayout.addWidget(self.txtMethod, 0, 1, 1, 1)
        self.listMethods = QtWidgets.QListWidget(self.groupBox)
        self.listMethods.setObjectName("listMethods")
        self.gridLayout.addWidget(self.listMethods, 1, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)
        self.txtArgs = QtWidgets.QLineEdit(self.groupBox)
        self.txtArgs.setObjectName("txtArgs")
        self.gridLayout.addWidget(self.txtArgs, 2, 1, 1, 1)
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
        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "主动调用"))
        self.groupBox_2.setTitle(_translate("Dialog", "提示"))
        self.label_3.setText(_translate("Dialog", "参数只做了简单的设置，多个参数以,分割。具体参数类型在js读取转换"))
        self.label.setText(_translate("Dialog", "在自定义脚本中设置重放的函数,在这里主动调用重放函数"))
        self.groupBox.setTitle(_translate("Dialog", "函数重放"))
        self.label_2.setText(_translate("Dialog", "函数名："))
        self.label_4.setText(_translate("Dialog", "参数："))
        self.btnSubmit.setText(_translate("Dialog", "调用"))
        self.btnClear.setText(_translate("Dialog", "清空"))

