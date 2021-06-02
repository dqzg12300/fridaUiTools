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
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/kmain.ui",self)
        self.statusBar=QStatusBar()
        self.labStatus = QLabel('当前状态:未连接')
        self.setStatusBar(self.statusBar)
        self.statusBar.addPermanentWidget(self.labStatus, stretch=1)
        self.actionattach.triggered.connect(self.actionAttach)
        self.actionabort.triggered.connect(self.actionAbort)
        self.initUi()

    def initUi(self):
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # pass

    #打印输出日志
    def log(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtLogs.appendPlainText(datestr+logstr)

    def actionAttach(self):
        self.log("actionAttach")

    def actionAbort(self):
        QMessageBox().about(self, "About",
                            "\nfrida_tools: 缝合怪,常用脚本整合的界面化工具 \nAuthor: https://github.com/dqzg12300")

if __name__=="__main__":
    app=QApplication(sys.argv)
    kmain = kmainForm()
    kmain.show()
    sys.exit(app.exec_())

