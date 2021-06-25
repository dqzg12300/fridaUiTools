import os

from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.jnitrace import Ui_JniTraceDialog


class jnitraceForm(QDialog,Ui_JniTraceDialog):
    def __init__(self, parent=None):
        super(jnitraceForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.methodName = ""
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.flushCmb()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.cmbPackage.currentTextChanged.connect(self.changePackage)
        self.modules=None

    def initData(self):
        self.listModule.clear()
        for item in self.modules:
            self.listModule.addItem(item)

    def flushCmb(self):
        self.cmbPackage.clear()
        files = os.listdir("./tmp/")
        self.cmbPackage.addItem("选择缓存数据")
        for item in files:
            if ".modules.txt" in item:
                self.cmbPackage.addItem(item.replace(".modules.txt",""))

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

    def changePackage(self,data):
        if data=="" or data=="选择缓存数据":
            return
        filepath = "./tmp/" + data + ".modules.txt"
        with open(filepath, "r", encoding="utf-8") as packageFile:
            res = packageFile.read()
            self.modules = res.split("\n")
        self.initData()

    def clearUi(self):
        self.txtModule.setText("")
        self.txtMethod.setText("")


    def submit(self):
        if len(self.txtModule.text())<=0 or len(self.txtMethod.text())<=0:
            QMessageBox().information(self, "提示", "模块名或函数为空")
            return
        self.moduleName = self.txtModule.text()
        self.methodName = self.txtMethod.text()
        self.accept()