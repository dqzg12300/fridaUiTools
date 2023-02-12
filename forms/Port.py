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
        self.fridaName=""
        self.port="6666"


    def clearUi(self):
        self.txtPort.setText("")
        self.txtFridaName.setText("")

    def submit(self):
        port = self.txtPort.text()
        if len(self.txtFridaName.text()) <= 0:
            QMessageBox().information(self, "hint", "missing FridaName")
            return
        self.port = port
        self.fridaName = self.txtFridaName.text()
        self.accept()