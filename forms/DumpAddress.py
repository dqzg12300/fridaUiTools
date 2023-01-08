from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.dumpAddress import Ui_DumpAddressDialog

class dumpAddressForm(QDialog,Ui_DumpAddressDialog):
    def __init__(self, parent=None):
        super(dumpAddressForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address = ""
        self.dumpType=""
        self.size=0
        self.address=0
        self.cmbDumpType.currentIndexChanged.connect(self.changeDumpType)
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.modules = None

    def initData(self):
        self.listModule.clear()
        for item in self.modules:
            self.listModule.addItem(item)

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

    def clearUi(self):
        self.txtSize.setText("0x30")
        self.txtAddress.setText("")
        self.txtModule.setText("")

    def changeDumpType(self,idx):
        if idx==1:
            self.txtSize.setEnabled(False)
        else:
            self.txtSize.setEnabled(True)

    def submit(self):
        moduleName = self.txtModule.text()
        address = self.txtAddress.text()
        size=self.txtSize.text()
        if len(address) <= 0:
            QMessageBox().information(self, "提示", "地址不能为空")
            return
        self.dumpType=self.cmbDumpType.currentText()
        try:
            if self.dumpType=="hexdump":
                if len(size)<=0:
                    QMessageBox().information(self, "提示", "长度不能为空")
                    return
                else:
                    if "0x" in size:
                        self.size = int(size, 16)
                    else:
                        self.size = int(size)
            self.moduleName = moduleName
            if "0x" in address:
                self.address = int(address,16)
            else:
                self.address = int(address)
        except Exception as ex:
            QMessageBox().information(self, "提示", "地址或长度格式输入错误")
            return
        self.accept()