from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.dump_so import Ui_DumpSoDialog


class dumpSoForm(QDialog,Ui_DumpSoDialog):
    def __init__(self, parent=None):
        super(dumpSoForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.modules=None

    def initData(self):
        self.listModule.clear()
        for item in self.modules:
            self.listModule.addItem(item)

    def ModuleItemClick(self,item):
        self.txtModule.setText(item.text())

    def changeModule(self,data):
        if self.modules==None or len(self.modules)<=0:
            return
        if data=="" or data=="选择缓存数据":
            return
        self.listModule.clear()
        if len(data) > 0:
            for item in self.modules:
                if data in item:
                    self.listModule.addItem(item)
        else:
            for item in self.modules:
                self.listModule.addItem(item)

    def clearUi(self):
        self.txtModule.setText("")


    def submit(self):
        if len(self.txtModule.text())<=0 or len(self.txtModule.text())<=0:
            QMessageBox().information(self, "提示", "模块名或函数为空")
            return
        self.moduleName = self.txtModule.text()
        self.accept()
