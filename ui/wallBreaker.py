# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Wallbreaker(object):
    def setupUi(self, Wallbreaker):
        Wallbreaker.setObjectName("Wallbreaker")
        Wallbreaker.resize(900, 680)
        self.mainLayout = QtWidgets.QVBoxLayout(Wallbreaker)
        self.mainLayout.setObjectName("mainLayout")

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, Wallbreaker)
        self.splitter.setObjectName("splitter")

        # === 上半部分：查询结果（代码编辑器） ===
        self.groupResult = QtWidgets.QGroupBox(self.splitter)
        self.groupResult.setObjectName("groupResult")
        resultLayout = QtWidgets.QVBoxLayout(self.groupResult)
        resultLayout.setContentsMargins(4, 4, 4, 4)

        try:
            from PyQt5.Qsci import QsciScintilla, QsciLexerJavaScript
            from PyQt5.QtGui import QColor
            self.txtSearchData = QsciScintilla(self.groupResult)
            self.txtSearchData.setReadOnly(True)
            self.txtSearchData.setUtf8(True)
            self.txtSearchData.setMarginWidth(0, "00000")
            self.txtSearchData.setMarginLineNumbers(0, True)
            # 设置深色主题
            self.txtSearchData.setMarginsForegroundColor(QColor("#7a8a9a"))
            self.txtSearchData.setMarginsBackgroundColor(QColor("#263238"))
            self.txtSearchData.setCaretLineVisible(True)
            self.txtSearchData.setCaretLineBackgroundColor(QColor("#2c3b41"))
            self.txtSearchData.setPaper(QColor("#263238"))
            self.txtSearchData.setColor(QColor("#cfd8dc"))
            self.txtSearchData.setSelectionBackgroundColor(QColor("#546e7a"))
            self.txtSearchData.setSelectionForegroundColor(QColor("#ffffff"))
            lexer = QsciLexerJavaScript()
            lexer.setDefaultFont(QtGui.QFont("Consolas", 10))
            # 设置深色主题的语法高亮颜色
            lexer.setDefaultPaper(QColor("#263238"))
            lexer.setDefaultColor(QColor("#cfd8dc"))
            lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.Keyword)  # 关键字
            lexer.setColor(QColor("#f07178"), QsciLexerJavaScript.KeywordSet2)  # 次要关键字
            lexer.setColor(QColor("#c792ea"), QsciLexerJavaScript.Number)  # 数字
            lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.DoubleQuotedString)  # 双引号字符串
            lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.SingleQuotedString)  # 单引号字符串
            lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.Comment)  # 注释
            lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.CommentLine)  # 单行注释
            lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.CommentDoc)  # 文档注释
            lexer.setColor(QColor("#82aaff"), QsciLexerJavaScript.Identifier)  # 标识符
            lexer.setColor(QColor("#89ddff"), QsciLexerJavaScript.Operator)  # 操作符
            lexer.setColor(QColor("#ffcb6b"), QsciLexerJavaScript.UnclosedString)  # 未闭合字符串
            self.txtSearchData.setLexer(lexer)
            self._hasScintilla = True
        except ImportError:
            self.txtSearchData = QtWidgets.QPlainTextEdit(self.groupResult)
            self.txtSearchData.setReadOnly(True)
            self.txtSearchData.setFont(QtGui.QFont("Consolas", 10))
            self._hasScintilla = False

        self.txtSearchData.setObjectName("txtSearchData")
        resultLayout.addWidget(self.txtSearchData)

        # === 下半部分：操作区 ===
        self.groupOp = QtWidgets.QGroupBox(self.splitter)
        self.groupOp.setObjectName("groupOp")
        opLayout = QtWidgets.QGridLayout(self.groupOp)
        opLayout.setContentsMargins(4, 4, 4, 4)

        # 类名输入
        self.label_3 = QtWidgets.QLabel(self.groupOp)
        self.label_3.setObjectName("label_3")
        opLayout.addWidget(self.label_3, 0, 0)
        self.txtClassName = QtWidgets.QLineEdit(self.groupOp)
        self.txtClassName.setObjectName("txtClassName")
        opLayout.addWidget(self.txtClassName, 0, 1)

        # 类列表
        self.listClasses = QtWidgets.QListWidget(self.groupOp)
        self.listClasses.setObjectName("listClasses")
        opLayout.addWidget(self.listClasses, 1, 0, 1, 2)

        # 地址输入
        self.label_4 = QtWidgets.QLabel(self.groupOp)
        self.label_4.setObjectName("label_4")
        opLayout.addWidget(self.label_4, 2, 0)
        self.txtAddress = QtWidgets.QLineEdit(self.groupOp)
        self.txtAddress.setObjectName("txtAddress")
        self.txtAddress.setPlaceholderText("0x1a2b3c")
        opLayout.addWidget(self.txtAddress, 2, 1)

        # 按钮列
        btnLayout = QtWidgets.QVBoxLayout()
        self.btnClassSearch = QtWidgets.QPushButton(self.groupOp)
        self.btnClassSearch.setMinimumSize(QtCore.QSize(120, 36))
        self.btnClassSearch.setObjectName("btnClassSearch")
        btnLayout.addWidget(self.btnClassSearch)

        self.btnClassDump = QtWidgets.QPushButton(self.groupOp)
        self.btnClassDump.setMinimumSize(QtCore.QSize(120, 36))
        self.btnClassDump.setObjectName("btnClassDump")
        btnLayout.addWidget(self.btnClassDump)

        self.btnObjectSearch = QtWidgets.QPushButton(self.groupOp)
        self.btnObjectSearch.setMinimumSize(QtCore.QSize(120, 36))
        self.btnObjectSearch.setObjectName("btnObjectSearch")
        btnLayout.addWidget(self.btnObjectSearch)

        self.btnObjectDump = QtWidgets.QPushButton(self.groupOp)
        self.btnObjectDump.setMinimumSize(QtCore.QSize(120, 36))
        self.btnObjectDump.setObjectName("btnObjectDump")
        btnLayout.addWidget(self.btnObjectDump)

        self.btnFieldRead = QtWidgets.QPushButton(self.groupOp)
        self.btnFieldRead.setMinimumSize(QtCore.QSize(120, 36))
        self.btnFieldRead.setObjectName("btnFieldRead")
        btnLayout.addWidget(self.btnFieldRead)

        self.btnClearUI = QtWidgets.QPushButton(self.groupOp)
        self.btnClearUI.setMinimumSize(QtCore.QSize(120, 36))
        self.btnClearUI.setObjectName("btnClearUI")
        btnLayout.addWidget(self.btnClearUI)

        btnLayout.addStretch(1)
        opLayout.addLayout(btnLayout, 0, 2, 3, 1)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.mainLayout.addWidget(self.splitter)

        # 隐藏的兼容按钮（代码中仍引用）
        self.btnFetchClasses = QtWidgets.QPushButton(Wallbreaker)
        self.btnFetchClasses.setVisible(False)

        self.retranslateUi(Wallbreaker)
        QtCore.QMetaObject.connectSlotsByName(Wallbreaker)

    def retranslateUi(self, Wallbreaker):
        _translate = QtCore.QCoreApplication.translate
        Wallbreaker.setWindowTitle(_translate("Wallbreaker", "Wallbreaker"))
        self.groupResult.setTitle(_translate("Wallbreaker", "查询结果"))
        self.groupOp.setTitle(_translate("Wallbreaker", "操作"))
        self.btnClassSearch.setText(_translate("Wallbreaker", "Class Search"))
        self.btnClassDump.setText(_translate("Wallbreaker", "Class Dump"))
        self.btnObjectSearch.setText(_translate("Wallbreaker", "Object Search"))
        self.btnObjectDump.setText(_translate("Wallbreaker", "Object Dump"))
        self.btnFieldRead.setText(_translate("Wallbreaker", "Field Read"))
        self.btnClearUI.setText(_translate("Wallbreaker", "清空"))
        self.label_4.setText(_translate("Wallbreaker", "地址："))
        self.label_3.setText(_translate("Wallbreaker", "类名："))
