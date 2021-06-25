# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wallBreaker.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Wallbreaker(object):
    def setupUi(self, Wallbreaker):
        Wallbreaker.setObjectName("Wallbreaker")
        Wallbreaker.resize(822, 612)
        self.gridLayout_4 = QtWidgets.QGridLayout(Wallbreaker)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.groupBox = QtWidgets.QGroupBox(Wallbreaker)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.txtSearchData = QtWidgets.QPlainTextEdit(self.groupBox)
        self.txtSearchData.setReadOnly(True)
        self.txtSearchData.setObjectName("txtSearchData")
        self.gridLayout.addWidget(self.txtSearchData, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(Wallbreaker)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.btnClassSearch = QtWidgets.QPushButton(self.groupBox_2)
        self.btnClassSearch.setMinimumSize(QtCore.QSize(0, 40))
        self.btnClassSearch.setObjectName("btnClassSearch")
        self.verticalLayout.addWidget(self.btnClassSearch)
        self.btnClassDump = QtWidgets.QPushButton(self.groupBox_2)
        self.btnClassDump.setMinimumSize(QtCore.QSize(0, 40))
        self.btnClassDump.setObjectName("btnClassDump")
        self.verticalLayout.addWidget(self.btnClassDump)
        self.btnObjectSearch = QtWidgets.QPushButton(self.groupBox_2)
        self.btnObjectSearch.setMinimumSize(QtCore.QSize(0, 40))
        self.btnObjectSearch.setObjectName("btnObjectSearch")
        self.verticalLayout.addWidget(self.btnObjectSearch)
        self.btnObjectDump = QtWidgets.QPushButton(self.groupBox_2)
        self.btnObjectDump.setMinimumSize(QtCore.QSize(0, 40))
        self.btnObjectDump.setObjectName("btnObjectDump")
        self.verticalLayout.addWidget(self.btnObjectDump)
        self.btnClearUI = QtWidgets.QPushButton(self.groupBox_2)
        self.btnClearUI.setMinimumSize(QtCore.QSize(0, 40))
        self.btnClearUI.setObjectName("btnClearUI")
        self.verticalLayout.addWidget(self.btnClearUI)
        self.gridLayout_3.addLayout(self.verticalLayout, 0, 2, 4, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout_3.addWidget(self.label_4, 3, 0, 1, 1)
        self.txtAddress = QtWidgets.QLineEdit(self.groupBox_2)
        self.txtAddress.setObjectName("txtAddress")
        self.gridLayout_3.addWidget(self.txtAddress, 3, 1, 1, 1)
        self.txtClassName = QtWidgets.QLineEdit(self.groupBox_2)
        self.txtClassName.setObjectName("txtClassName")
        self.gridLayout_3.addWidget(self.txtClassName, 0, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.listClasses = QtWidgets.QListWidget(self.groupBox_2)
        self.listClasses.setObjectName("listClasses")
        self.gridLayout_3.addWidget(self.listClasses, 1, 1, 1, 1)
        self.gridLayout_4.addWidget(self.groupBox_2, 1, 0, 1, 1)

        self.retranslateUi(Wallbreaker)
        QtCore.QMetaObject.connectSlotsByName(Wallbreaker)

    def retranslateUi(self, Wallbreaker):
        _translate = QtCore.QCoreApplication.translate
        Wallbreaker.setWindowTitle(_translate("Wallbreaker", "Wallbreaker"))
        self.groupBox.setTitle(_translate("Wallbreaker", "查询结果"))
        self.groupBox_2.setTitle(_translate("Wallbreaker", "操作"))
        self.btnClassSearch.setText(_translate("Wallbreaker", "classsearch"))
        self.btnClassDump.setText(_translate("Wallbreaker", "classdump"))
        self.btnObjectSearch.setText(_translate("Wallbreaker", "objectsearch"))
        self.btnObjectDump.setText(_translate("Wallbreaker", "objectdump"))
        self.btnClearUI.setText(_translate("Wallbreaker", "清空"))
        self.label_4.setText(_translate("Wallbreaker", "地址："))
        self.label_3.setText(_translate("Wallbreaker", "类名："))

