# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tuoke.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TuokeDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(375, 353)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.rdoDumpDex = QtWidgets.QRadioButton(self.groupBox)
        self.rdoDumpDex.setObjectName("rdoDumpDex")
        self.gridLayout_2.addWidget(self.rdoDumpDex, 0, 0, 1, 1)
        self.rdoDumpDexClass = QtWidgets.QRadioButton(self.groupBox)
        self.rdoDumpDexClass.setObjectName("rdoDumpDexClass")
        self.gridLayout_2.addWidget(self.rdoDumpDexClass, 0, 1, 1, 1)
        self.rdoDexDump = QtWidgets.QRadioButton(self.groupBox)
        self.rdoDexDump.setChecked(False)
        self.rdoDexDump.setObjectName("rdoDexDump")
        self.gridLayout_2.addWidget(self.rdoDexDump, 1, 0, 1, 1)
        self.rdoFart = QtWidgets.QRadioButton(self.groupBox)
        self.rdoFart.setObjectName("rdoFart")
        self.gridLayout_2.addWidget(self.rdoFart, 1, 1, 1, 1)
        self.rdoCookieDump = QtWidgets.QRadioButton(self.groupBox)
        self.rdoCookieDump.setChecked(True)
        self.rdoCookieDump.setObjectName("rdoCookieDump")
        self.gridLayout_2.addWidget(self.rdoCookieDump, 2, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 1, 0, 1, 1)
        self.btnSubmit = QtWidgets.QPushButton(Dialog)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.gridLayout_3.addWidget(self.btnSubmit, 2, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "脱壳"))
        self.groupBox_2.setTitle(_translate("Dialog", "提示"))
        self.label.setText(_translate("Dialog", "fart在功能里主动调用功能耗时很长"))
        self.label_2.setText(_translate("Dialog", "dump_dex需要使用spawn附加"))
        self.label_3.setText(_translate("Dialog", "dump_dex_class需要在功能的按钮触发dump"))
        self.groupBox.setTitle(_translate("Dialog", "脱壳相关"))
        self.rdoDumpDex.setText(_translate("Dialog", "dump_dex"))
        self.rdoDumpDexClass.setText(_translate("Dialog", "dump_dex_class"))
        self.rdoDexDump.setText(_translate("Dialog", "FRIDA-DEXDump"))
        self.rdoFart.setText(_translate("Dialog", "fart"))
        self.rdoCookieDump.setText(_translate("Dialog", "mCookieDump"))
        self.btnSubmit.setText(_translate("Dialog", "提交"))

