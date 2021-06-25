# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dumpAddress.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DumpAddressDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(372, 407)
        self.gridLayout_3 = QtWidgets.QGridLayout(Dialog)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.txtModule = QtWidgets.QLineEdit(self.groupBox_2)
        self.txtModule.setObjectName("txtModule")
        self.gridLayout_2.addWidget(self.txtModule, 0, 1, 1, 1)
        self.listModule = QtWidgets.QListWidget(self.groupBox_2)
        self.listModule.setObjectName("listModule")
        self.gridLayout_2.addWidget(self.listModule, 1, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.gridLayout_2.addWidget(self.label_2, 2, 0, 1, 1)
        self.txtAddress = QtWidgets.QLineEdit(self.groupBox_2)
        self.txtAddress.setObjectName("txtAddress")
        self.gridLayout_2.addWidget(self.txtAddress, 2, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.gridLayout_2.addWidget(self.label, 3, 0, 1, 1)
        self.txtSize = QtWidgets.QLineEdit(self.groupBox_2)
        self.txtSize.setObjectName("txtSize")
        self.gridLayout_2.addWidget(self.txtSize, 3, 1, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 4, 0, 1, 1)
        self.cmbDumpType = QtWidgets.QComboBox(self.groupBox_2)
        self.cmbDumpType.setObjectName("cmbDumpType")
        self.cmbDumpType.addItem("")
        self.cmbDumpType.addItem("")
        self.gridLayout_2.addWidget(self.cmbDumpType, 4, 1, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnSubmit = QtWidgets.QPushButton(self.groupBox_2)
        self.btnSubmit.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnSubmit.setObjectName("btnSubmit")
        self.horizontalLayout.addWidget(self.btnSubmit)
        self.btnClear = QtWidgets.QPushButton(self.groupBox_2)
        self.btnClear.setMaximumSize(QtCore.QSize(120, 16777215))
        self.btnClear.setObjectName("btnClear")
        self.horizontalLayout.addWidget(self.btnClear)
        self.gridLayout_2.addLayout(self.horizontalLayout, 5, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        self.cmbDumpType.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "dump指定地址"))
        self.groupBox_2.setTitle(_translate("Dialog", "dump"))
        self.label_3.setText(_translate("Dialog", "模块名："))
        self.label_2.setText(_translate("Dialog", "地址："))
        self.label.setText(_translate("Dialog", "长度："))
        self.label_4.setText(_translate("Dialog", "类型："))
        self.cmbDumpType.setItemText(0, _translate("Dialog", "hexdump"))
        self.cmbDumpType.setItemText(1, _translate("Dialog", "string"))
        self.btnSubmit.setText(_translate("Dialog", "提交"))
        self.btnClear.setText(_translate("Dialog", "清空"))

