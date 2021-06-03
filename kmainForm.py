import datetime
import sys

from Crypto.Cipher import ARC2
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStatusBar, QLabel, QMessageBox, QHeaderView
from PyQt5 import uic
import urllib.parse
import platform
import os,re,zlib,hashlib,hmac


class kmainForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUi()

    def initUi(self):
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/kmain.ui", self)
        self.statusBar = QStatusBar()
        self.labStatus = QLabel('当前状态:未连接')
        self.setStatusBar(self.statusBar)
        self.statusBar.addPermanentWidget(self.labStatus, stretch=1)
        self.actionattach.triggered.connect(self.actionAttach)
        self.actionabort.triggered.connect(self.actionAbort)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.btnShowClasses.clicked.connect(self.showClasses)
        self.btnShowExport.clicked.connect(self.showExport)
        self.btnShowStr.clicked.connect(self.showStr)
        self.btnWallbreaker.clicked.connect(self.wallBreaker)
        self.btnFindClassPath.clicked.connect(self.findClassPath)
        self.btnShowMethods.clicked.connect(self.showMethods)
        self.btnDumpPtr.clicked.connect(self.dumpPtr)
        self.btnMatchDump.clicked.connect(self.matchDump)

    #打印输出日志
    def log(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtLogs.appendPlainText(datestr+logstr)
    #启动附加
    def actionAttach(self):
        self.log("actionAttach")
    #是否附加进程了
    def isattack(self):
        if self.labStatus.text().index("未连接"):
            return False
        return True

    #====================start======需要附加后才能使用的功能,基本都是在内存中查数据================================
    def showClasses(self):
        if self.isattack()==False:
            self.log("Error:还未附加进程")
            return
        self.log("查询所有类")

    def showExport(self):
        if self.isattack()==False:
            self.log("Error:还未附加进程")
            return
        self.log("查询so的所有符号")

    def showStr(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("将指定地址以str打印")

    def wallBreaker(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("wallBreaker功能")

    def showMethods(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("wallBreaker功能")

    def findClassPath(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("查找指定类的完整名称")

    def dumpPtr(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("dump指定地址")

    def matchDump(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("指定特征dump内存")
    # ====================end======需要附加后才能使用的功能,基本都是在内存中查数据================================


    def actionAbort(self):
        QMessageBox().about(self, "About",
                            "\nfrida_tools: 缝合怪,常用脚本整合的界面化工具 \nAuthor: https://github.com/dqzg12300")

if __name__=="__main__":
    app=QApplication(sys.argv)
    kmain = kmainForm()
    kmain.show()
    sys.exit(app.exec_())

