import os

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from ui.fartBin import Ui_FartBinDialog
from utils import FartUtil, CmdUtil
from utils.FartUtil import FartThread


class fartBinForm(QDialog,Ui_FartBinDialog):
    def __init__(self, parent=None):
        super(fartBinForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.btnSelectBinPath.clicked.connect(self.selectBinPath)
        self.btnSelectDexPath.clicked.connect(self.selectDexPath)
        self.btnSubmitJar.clicked.connect(self.submitJar)
        self.examplePath = os.getcwd()+"/example/"

    def selectBinPath(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                "选取文件",
                                                                self.examplePath,
                                                                "Bin Files (*.bin);;All Files (*)")
        if fileName_choose == "":
            return
        self.txtBinPath.setText(fileName_choose)

    def selectDexPath(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                "选取文件",
                                                                self.examplePath,  # 起始路径
                                                                "Dex Files (*.dex);;All Files (*)")  # 设置文件扩展名过滤,用双分号间隔
        if fileName_choose == "":
            return
        self.txtDexPath.setText(fileName_choose)

    def appendLog(self,data):
        self.txtResult.appendPlainText(data)

    def submit(self):
        if len(self.txtDexPath.text()) <= 0 or os.path.exists(self.txtDexPath.text()) == False:
            QMessageBox().information(self, "提示", "dex路径为空或文件不存在")
            return
        if len(self.txtBinPath.text())<=0 or os.path.exists(self.txtBinPath.text())==False:
            QMessageBox().information(self, "提示", "bin路径为空或文件不存在")
            return

        self.th= FartThread(self.txtDexPath.text(),self.txtBinPath.text())
        self.th.loggerSignel.connect(self.appendLog)
        self.th.start()

    def submitJar(self):
        if len(self.txtDexPath.text()) <= 0 or os.path.exists(self.txtDexPath.text()) == False:
            QMessageBox().information(self, "提示", "dex路径为空或文件不存在")
            return
        if len(self.txtBinPath.text())<=0 or os.path.exists(self.txtBinPath.text())==False:
            QMessageBox().information(self, "提示", "bin路径为空或文件不存在")
            return
        filepath,fileext= os.path.splitext(self.txtDexPath.text())
        cmd="java -jar ./exec/dexfixer.jar %s %s %s"%(self.txtDexPath.text(),self.txtBinPath.text(),filepath+"_repair"+fileext)
        res=CmdUtil.exec(cmd)
        if "error" in res:
            QMessageBox().information(self, "提示", "修复文件异常,"+res)
            return
        QMessageBox().information(self, "提示", res)