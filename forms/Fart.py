from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.fart import Ui_FartDialog


class fartForm(QDialog,Ui_FartDialog):
    def __init__(self, parent=None):
        super(fartForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmitFart.clicked.connect(self.submitFart)
        self.btnSubmitFartClass.clicked.connect(self.submitFartClass)
        self.className=""
        self.clearUi()
        self.listClass.itemClicked.connect(self.ClassItemClick)
        self.txtClass.textChanged.connect(self.changeClass)
        self.classes = None

    def initData(self):
        self.listClass.clear()
        for item in self.classes:
            self.listClass.addItem(item)

    def ClassItemClick(self, item):
        self.txtClass.setText(item.text())

    def changeClass(self, data):
        if self.classes==None or len(self.classes)<=0:
            return
        self.listClass.clear()
        if len(data) > 0:
            for item in self.classes:
                if data in item:
                    self.listClass.addItem(item)
        else:
            for item in self.classes:
                self.listClass.addItem(item)

    def clearUi(self):
        self.txtClass.setText("")

    def submitFartClass(self):
        className=self.txtClass.text()
        if len(className)<=0:
            QMessageBox().information(self, "提示", "未填写类名")
            return
        self.className=className
        self.done(1)

    def submitFart(self):
        self.done(2)