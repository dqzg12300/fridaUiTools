import os

from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.wifi import Ui_WifiDialog


class wifiForm(QDialog,Ui_WifiDialog):
    def __init__(self, parent=None):
        super(wifiForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.btnClear.clicked.connect(self.clearUi)
        self.address=""
        self.wifi_port=""


    def clearUi(self):
        self.txtAddress.setText("")
        self.txtPort.setText("")

    def submit(self):
        address = self.txtAddress.text()
        port = self.txtPort.text()
        if len(address) <= 0:
            QMessageBox().information(self, "hint", "missing address")
            return
        if len(port) <= 0:
            QMessageBox().information(self, "hint", "missing port")
            return
        self.address = address
        self.port = port
        self.accept()