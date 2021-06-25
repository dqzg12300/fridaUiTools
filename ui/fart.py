# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fart.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FartDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(372, 377)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.txtClass = QtWidgets.QLineEdit(self.groupBox)
        self.txtClass.setObjectName("txtClass")
        self.gridLayout.addWidget(self.txtClass, 0, 1, 1, 1)
        self.listClass = QtWidgets.QListWidget(self.groupBox)
        self.listClass.setObjectName("listClass")
        self.gridLayout.addWidget(self.listClass, 1, 1, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnSubmitFart = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmitFart.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmitFart.setObjectName("btnSubmitFart")
        self.horizontalLayout.addWidget(self.btnSubmitFart)
        self.btnSubmitFartClass = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmitFartClass.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmitFartClass.setObjectName("btnSubmitFartClass")
        self.horizontalLayout.addWidget(self.btnSubmitFartClass)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout_3.addWidget(self.label_2, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "fart"))
        self.groupBox.setTitle(_translate("Dialog", "match"))
        self.btnSubmitFart.setText(_translate("Dialog", "fart"))
        self.btnSubmitFartClass.setText(_translate("Dialog", "fartClass"))
        self.label.setText(_translate("Dialog", "类名："))
        self.label_2.setText(_translate("Dialog", "提示：fart无需填写class"))

