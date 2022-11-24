from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QMessageBox, QHeaderView, QTableWidgetItem, QMenu, QAction

from ui.searchMemory import Ui_searchMemory


class searchMemoryForm(QDialog,Ui_searchMemory):
    def __init__(self, parent=None):
        super(searchMemoryForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSearch.clicked.connect(self.search)
        self.btnHexDump.clicked.connect(self.hexDump)
        self.btnCString.clicked.connect(self.cstring)
        self.btnReadBlock.clicked.connect(self.readBlock)
        self.btnWriteBlock.clicked.connect(self.writeBlock)
        self.btnExecBlock.clicked.connect(self.execBlock)

        self.searchHistory= []
        self.searchResult=""

        self.header = ["值", "地址","备注"]

        self.tabHistory.clear()
        self.tabHistory.setColumnCount(3)
        self.tabHistory.setRowCount(0)
        self.tabHistory.setHorizontalHeaderLabels(self.header)
        self.tabHistory.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabHistory.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabHistory.customContextMenuRequested[QPoint].connect(self.rightMenuShow)

        self.txtResult.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabHistory.customContextMenuRequested[QPoint].connect(self.logRightMenuShow)

        self.th = None

    def setBreak(self,protect):
        base = self.txtBase.text()
        baseSize = self.txtSize.text()
        if len(base) <= 0:
            QMessageBox.warning(self, "提示", "请输入起始地址")
            return
        if len(baseSize) <= 0:
            QMessageBox.warning(self, "提示", "请输入范围大小")
            return
        if baseSize.startswith("0x"):
            size = int(baseSize, 16)
        else:
            size = int(baseSize)
        postdata = {"start": base, "size": size, "protect": protect}
        self.th.setBreak(postdata)

    def readBlock(self):
        self.setBreak("wx")

    def writeBlock(self):
        self.setBreak("rx")

    def execBlock(self):
        self.setBreak("rw")

    def logRightMenuShow(self):
        rightMenu = QMenu(self.tabHooks)
        clearAction = QAction(u"清空", self, triggered=self.clearResultLog)
        rightMenu.addAction(clearAction)
        rightMenu.exec_(QCursor.pos())

    def rightMenuShow(self):
        rightMenu = QMenu(self.tabHooks)
        reSearchAction = QAction(u"重新查询", self, triggered=self.reSearch)
        clearAction = QAction(u"清空", self, triggered=self.clearHistory)
        rightMenu.addAction(reSearchAction)
        rightMenu.addAction(clearAction)
        rightMenu.exec_(QCursor.pos())

    def reSearch(self):
        pass

    def clearHistory(self):
        self.tabHistory.clearContents()
        self.tabHistory.setRowCount(0)
        self.tabHistory.setHorizontalHeaderLabels(self.header)

    def cstring(self):
        base = self.txtBase.text()
        if len(base) <= 0:
            QMessageBox.warning(self, "提示", "请输入起始地址")
            return
        self.th.getInfo({"start": base, "type": "CString"})

    def hexDump(self):
        base = self.txtBase.text()
        baseSize = self.txtSize.text()
        if len(base) <= 0:
            QMessageBox.warning(self, "提示", "请输入起始地址")
            return
        if len(baseSize) <= 0:
            QMessageBox.warning(self, "提示", "请输入范围大小")
            return
        if baseSize.startswith("0x"):
            size = int(baseSize, 16)
        else:
            size=int(baseSize)
        self.th.getInfo({"start": base, "size": size,"type":"hexdump"})

    def appendHistory(self,data):
        historyData=eval(data)
        for line in historyData:
            self.tabHistory.insertRow(0)
            self.tabHistory.setItem(0, 0, QTableWidgetItem(line["value"]))
            self.tabHistory.setItem(0, 1, QTableWidgetItem(line["key"]))
            self.tabHistory.setItem(0, 2, QTableWidgetItem(line["bak"]))
        # self.appendResult(str(data))
        QMessageBox.information(self, "提示", f"搜索完成,检索到{len(historyData)}条结果")

    def appendResult(self, result):
        self.searchResult += result+"\n"
        self.txtResult.setText(self.searchResult)

    def search(self):
        input=self.txtInput.text()
        if len(input) == 0:
            QMessageBox.warning(self, "提示", "请输入搜索内容")
            return
        base=self.txtBase.text()
        baseSize=self.txtSize.text()
        value=input
        size=0
        if self.rdoInt.isChecked():
            size = 1
            if input > 0xff:
                size = 2
            elif input > 0xffff:
                size = 4
            elif input > 0xffffffff:
                size = 8
        elif self.rdoStr.isChecked():
            size=""
        protect="rw"
        if self.txtProtect.text()!="":
            protect=self.txtProtect.text()

        if len(base) <= 0:
            postdata = {"protect":protect, "value": value, "size": size,"bak":self.txtBak.text()}
            self.th.newScanProtect(postdata)
        else:
            if len(size) <= 0:
                QMessageBox.warning(self, "提示", "请输入范围大小")
                return
            postdata={"start":base,"end":base+baseSize,"value":value,"size":size,"bak":self.txtBak.text()}
            self.th.newScanByAddress(postdata)

