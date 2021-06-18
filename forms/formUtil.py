from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog
from utils import AsmUtil

class matchForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/match.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.className=""
        self.methodName=""
        self.hasMethod = True
        self.chkHasMethod.toggled.connect(self.changeHasMethod)
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()

    def clearUi(self):
        self.txtClass.setText("")
        self.txtMethod.setText("")

    def changeHasMethod(self,chk):
        if chk:
            self.txtMethod.setEnabled(True)
        else:
            self.txtMethod.setEnabled(False)

    def submit(self):
        className=self.txtClass.text()
        methodName=self.txtMethod.text()
        self.className=className
        self.methodName=methodName
        self.hasMethod = self.chkHasMethod.isChecked()
        self.accept()


class match2Form(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/match2.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.methodName = ""
        self.showType=""
        self.hasMethod=True
        self.chkHasMethod.toggled.connect(self.changeHasMethod)
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()

    def clearUi(self):
        self.txtModule.setText("")
        self.txtMethod.setText("")

    def changeHasMethod(self,chk):
        if chk:
            self.txtMethod.setEnabled(True)
        else:
            self.txtMethod.setEnabled(False)

    def submit(self):
        self.moduleName = self.txtModule.text()
        self.methodName = self.txtMethod.text()
        self.showType = self.cmbShowType.currentText()
        self.hasMethod=self.chkHasMethod.isChecked()
        self.accept()

class nativesForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/natives.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.methods= ""

    def submit(self):
        moduleName = self.txtModule.text()
        methods = self.txtMethods.toPlainText()
        if len(moduleName) <= 0 or len(methods) <= 0:
            QMessageBox().information(self, "提示", "模块名或函数为空")
            return
        self.moduleName = moduleName
        self.methods = methods
        self.accept()

class dumpAddressForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/dumpAddress.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address = ""
        self.dumpType=""
        self.size=0
        self.address=0
        self.cmbDumpType.currentIndexChanged.connect(self.changeDumpType)
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()


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

class findClassNameForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/fdclass.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.className = ""

    def submit(self):
        className = self.txtClass.text()
        if len(className) <= 0:
            QMessageBox().information(self, "提示", "类名为空")
            return
        self.className = className
        self.accept()

class tuokeForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/tuoke.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.tuokeType = ""

    def submit(self):
        self.tuokeType = "fart"
        if self.rdoFridaDump.isChecked():
            self.tuokeType="fridadump"
        elif self.rdoDexDump.isChecked():
            self.tuokeType="dexdump"
        self.close()

class callFunctionForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/callfunction.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.methodName = ""

    def submit(self):
        methodName = self.txtMethod.text()
        if len(methodName) <= 0:
            QMessageBox().information(self, "提示", "类名为空")
            return
        self.methodName = methodName
        self.accept()

class patchForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/patch.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address=""
        self.patch=""

    def submit(self):
        moduleName = self.txtModule.text()
        address = self.txtAddress.text()
        patch=self.txtPatch.text()
        if len(moduleName) <= 0 or len(address)<=0 or len(patch)<=0:
            QMessageBox().information(self, "提示", "类名为空")
            return
        self.moduleName = moduleName
        self.address = address
        self.patch = patch
        self.accept()

class selectPackageForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/selectPackage.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.packageName = ""
        self.txtPackage.textChanged.connect(self.changePackage)

    def changePackage(self,data):
        self.listPackages.clear()
        if len(data)>0:
            for item in self.packages:
                if data in item.name:
                    self.listPackages.addItem(item.name)
        else:
            for item in self.packages:
                self.listPackages.addItem(item.name)

    def setPackages(self,packages):
        self.packages=packages
        for item in packages:
            self.listPackages.addItem(item.name)
        self.listPackages.itemClicked.connect(self.listItemClick)

    def listItemClick(self,item):
        self.txtPackage.setText(item.text())

    def submit(self):
        packageName = self.cmbPackages.currentText()
        if len(packageName) <= 0:
            QMessageBox().information(self, "提示", "未选择package")
            return
        self.packageName = packageName
        self.accept()