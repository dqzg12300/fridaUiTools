from PyQt5.QtWidgets import QDialog

from ui.tuoke import Ui_TuokeDialog


class tuokeForm(QDialog,Ui_TuokeDialog):
    def __init__(self, parent=None):
        super(tuokeForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.tuokeType = ""

    def submit(self):
        self.tuokeType = "fart"
        if self.rdoDexDump.isChecked():
            self.tuokeType="FRIDA-DEXDump"
        elif self.rdoDumpDex.isChecked():
            self.tuokeType="dumpdex"
        elif self.rdoDumpDexClass.isChecked():
            self.tuokeType="dumpdexclass"
        elif self.rdoCookieDump.isChecked():
            self.tuokeType="cookieDump"
        self.accept()