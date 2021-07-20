# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fart.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FartDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(353, 446)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        self.btnSubmitFart = QtWidgets.QPushButton(self.groupBox_2)
        self.btnSubmitFart.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmitFart.setObjectName("btnSubmitFart")
        self.gridLayout.addWidget(self.btnSubmitFart, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.txtClasses = QtWidgets.QPlainTextEdit(self.groupBox)
        self.txtClasses.setObjectName("txtClasses")
        self.gridLayout_2.addWidget(self.txtClasses, 0, 1, 1, 2)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)
        self.txtClassesPath = QtWidgets.QLineEdit(self.groupBox)
        self.txtClassesPath.setObjectName("txtClassesPath")
        self.gridLayout_2.addWidget(self.txtClassesPath, 1, 1, 1, 2)
        self.btnSelectClasses = QtWidgets.QPushButton(self.groupBox)
        self.btnSelectClasses.setObjectName("btnSelectClasses")
        self.gridLayout_2.addWidget(self.btnSelectClasses, 2, 1, 1, 1)
        self.btnSubmitFartClass = QtWidgets.QPushButton(self.groupBox)
        self.btnSubmitFartClass.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmitFartClass.setObjectName("btnSubmitFartClass")
        self.gridLayout_2.addWidget(self.btnSubmitFartClass, 2, 2, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 1, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "fart"))
        self.groupBox_2.setTitle(_translate("Dialog", "完整主动调用"))
        self.btnSubmitFart.setText(_translate("Dialog", "调用所用函数"))
        self.groupBox.setTitle(_translate("Dialog", "指定类主动调用"))
        self.label_3.setText(_translate("Dialog", "类列表："))
        self.label.setText(_translate("Dialog", "文件："))
        self.btnSelectClasses.setText(_translate("Dialog", "选择文件"))
        self.btnSubmitFartClass.setText(_translate("Dialog", "调用指定类的函数"))

