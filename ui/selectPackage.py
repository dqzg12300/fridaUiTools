# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'selectPackage.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_SelectPackageDialog(object):
    def setupUi(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(326, 264)
        self.gridLayout = QtWidgets.QGridLayout(dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.btnSubmit = QtWidgets.QPushButton(dialog)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.gridLayout.addWidget(self.btnSubmit, 2, 2, 1, 1)
        self.label_2 = QtWidgets.QLabel(dialog)
        self.label_2.setMaximumSize(QtCore.QSize(100, 16777215))
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.listPackages = QtWidgets.QListWidget(dialog)
        self.listPackages.setObjectName("listPackages")
        self.gridLayout.addWidget(self.listPackages, 1, 2, 1, 1)
        self.txtPackage = QtWidgets.QLineEdit(dialog)
        self.txtPackage.setObjectName("txtPackage")
        self.gridLayout.addWidget(self.txtPackage, 0, 2, 1, 1)

        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def retranslateUi(self, dialog):
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("dialog", "进程选择"))
        self.btnSubmit.setText(_translate("dialog", "提交"))
        self.label_2.setText(_translate("dialog", "进程选择："))

