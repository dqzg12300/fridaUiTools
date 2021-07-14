import os

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from ui.stalkerMatch import Ui_StalkerMatchDialog


class stalkerMatchForm(QDialog,Ui_StalkerMatchDialog):
    def __init__(self, parent=None):
        super(stalkerMatchForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.btnSelectLogPath.clicked.connect(self.selectLogPath)
        self.btnSelectSavePath.clicked.connect(self.selectSavePath)
        self.cwd = os.getcwd()

    def selectLogPath(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                "选取文件",
                                                                self.cwd,
                                                                "Text Files (*.txt);;Log Files(*.log);;All Files (*)")
        if fileName_choose == "":
            return
        self.txtLogPath.setText(fileName_choose)
        self.txtSavePath.setText(fileName_choose+"_match.txt")

    def selectSavePath(self):
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                "文件保存",
                                                                self.cwd,  # 起始路径
                                                                "All Files (*);;Text Files (*.txt)")  # 设置文件扩展名过滤,用双分号间隔
        if fileName_choose == "":
            return
        self.txtSavePath.setText(fileName_choose)

    def submit(self):
        if len(self.txtLogPath.text())<=0 or os.path.exists(self.txtLogPath.text())==False:
            QMessageBox().information(self, "提示", "log路径为空或文件不存在")
            return
        if len(self.txtSavePath.text())<=0:
            QMessageBox().information(self, "提示", "save路径为空")
            return
        logfile=open(self.txtLogPath.text(),"r",encoding="utf-8")
        logdata=logfile.read()
        logfile.close()