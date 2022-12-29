import os

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog

from ui.antiFrida import Ui_antiFrida
from utils import CmdUtil


class antiFridaForm(QDialog,Ui_antiFrida):
    def __init__(self, parent=None):
        super(antiFridaForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.antiType=""
        self.rdoAnti1.toggled.connect(self.anti1)
        self.rdoAnti2.toggled.connect(self.anti2)
        self.rdoAnti3.toggled.connect(self.anti3)
        self.keyword=self.txtKeyword.toPlainText()
        self.txtKeyword.textChanged.connect(self.keywordChanged)

    def keywordChanged(self):
        self.keyword=self.txtKeyword.toPlainText()

    def anti1(self,checked):
        if checked:
            self.antiType+="strstr"
        else:
            self.antiType=self.antiType.replace("strstr","")

    def anti2(self,checked):
        if checked:
            self.antiType += "libc"
        else:
            self.antiType = self.antiType.replace("libc", "")

    def anti3(self,checked):
        if checked:
            self.antiType += "svc"
        else:
            self.antiType = self.antiType.replace("svc", "")




