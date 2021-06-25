from PyQt5.QtWidgets import QDialog

from ui.custom import Ui_CustomDialog


class customForm(QDialog,Ui_CustomDialog):
    def __init__(self, parent=None):
        super(customForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)

    def submit(self):
        self.accept()