# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'callFunction.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(326, 136)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.txtMethod = QtWidgets.QLineEdit(Dialog)
        self.txtMethod.setObjectName("txtMethod")
        self.gridLayout.addWidget(self.txtMethod, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.btnSubmit = QtWidgets.QPushButton(Dialog)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.gridLayout.addWidget(self.btnSubmit, 1, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "主动调用"))
        self.label_2.setText(_translate("Dialog", "函数名："))
        self.btnSubmit.setText(_translate("Dialog", "提交"))

