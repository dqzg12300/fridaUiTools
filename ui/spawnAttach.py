# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'spawnAttach.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SpawnAttachDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(326, 297)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(Dialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.txtPackage = QtWidgets.QLineEdit(Dialog)
        self.txtPackage.setObjectName("txtPackage")
        self.gridLayout.addWidget(self.txtPackage, 0, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(Dialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.listPackage = QtWidgets.QListWidget(Dialog)
        self.listPackage.setObjectName("listPackage")
        self.gridLayout.addWidget(self.listPackage, 1, 1, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnSubmit = QtWidgets.QPushButton(Dialog)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.horizontalLayout.addWidget(self.btnSubmit)
        self.btnClear = QtWidgets.QPushButton(Dialog)
        self.btnClear.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnClear.setObjectName("btnClear")
        self.horizontalLayout.addWidget(self.btnClear)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 1, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "spawnAttach"))
        self.label.setText(_translate("Dialog", "包名："))
        self.label_2.setText(_translate("Dialog", "历史："))
        self.btnSubmit.setText(_translate("Dialog", "提交"))
        self.btnClear.setText(_translate("Dialog", "清除历史"))

