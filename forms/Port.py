import os

from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.port import Ui_Port
from ui.wifi import Ui_WifiDialog


class portForm(QDialog,Ui_Port):
    def __init__(self, parent=None):
        super(portForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.btnClear.clicked.connect(self.clearUi)


    def clearUi(self):
        self.txtPort.setText("")

    def submit(self):
        port = self.txtPort.text()
        if len(port) <= 0:
            QMessageBox().information(self, "提示", "端口不能为空")
            return
        self.port = port
        self.accept()