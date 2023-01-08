import os

from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.patch import Ui_PatchDialog
from utils import AsmUtil


class patchForm(QDialog,Ui_PatchDialog):
    def __init__(self, parent=None):
        super(patchForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address=""
        self.patch=""
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.flushCmb()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.cmbPackage.currentTextChanged.connect(self.changePackage)
        self.modules = None
        self.txtPatch.textChanged.connect(self.changePatchCode)
        self.txtPatchAsm.textChanged.connect(self.changePatchAsm)

    def initData(self):
        self.listModule.clear()
        for item in self.modules:
            self.listModule.addItem(item)

    def flushCmb(self):
        self.cmbPackage.clear()
        files = os.listdir("./tmp/")
        self.cmbPackage.addItem("tmp data")
        for item in files:
            if ".modules.txt" in item:
                self.cmbPackage.addItem(item.replace(".modules.txt", ""))

    def ModuleItemClick(self, item):
        self.txtModule.setText(item.text())

    def changeModule(self, data):
        if self.modules==None or len(self.modules)<=0:
            return
        if data=="" or data=="tmp data":
            return
        self.listModule.clear()
        if len(data) > 0:
            for item in self.modules:
                if data in item:
                    self.listModule.addItem(item)
        else:
            for item in self.modules:
                self.listModule.addItem(item)

    def changePackage(self, data):
        if data=="" or data=="tmp data":
            return
        filepath = "./tmp/" + data + ".modules.txt"
        with open(filepath, "r", encoding="utf-8") as packageFile:
            res = packageFile.read()
            self.modules = res.split("\n")
        self.initData()

    def changePatchCode(self,data):
        try:
            codebuff=AsmUtil.StrToHexSplit(data)
            res=AsmUtil.disasm(self.cmbMode.currentIndex(),codebuff)
            self.txtPatchAsm.textChanged.disconnect(self.changePatchAsm)
            self.txtPatchAsm.setText(res)
            self.txtPatchAsm.textChanged.connect(self.changePatchAsm)
        except:
            pass

    def changePatchAsm(self,data):
        try:
            res= AsmUtil.asm(self.cmbMode.currentIndex(),data)
            self.txtPatch.textChanged.disconnect(self.changePatchCode)
            self.txtPatch.setText(res)
            self.txtPatch.textChanged.connect(self.changePatchCode)
        except:
            pass

    def clearUi(self):
        self.txtModule.setText("")
        self.txtAddress.setText("")
        self.txtPatch.setText("")

    def submit(self):
        moduleName = self.txtModule.text()
        address = self.txtAddress.text()
        patch=self.txtPatch.text()
        if len(moduleName) <= 0 or len(address)<=0 or len(patch)<=0:
            QMessageBox().information(self, "hint", "must enter module and address and patch data")
            return
        self.moduleName = moduleName
        self.address = address
        self.patch = patch
        self.accept()