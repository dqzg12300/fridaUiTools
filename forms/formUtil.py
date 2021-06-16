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
        self.flag=False

    def submit(self):
        className=self.txtClass.text()
        methodName=self.txtMethod.text()
        self.className=className
        self.methodName=methodName
        self.flag=True
        self.close()


class match2Form(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/match2.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.flag = False
        self.moduleName = ""
        self.methodName = ""


    def submit(self):
        moduleName = self.txtModule.text()
        methodName = self.txtMethod.text()
        if len(methodName) <= 0:
            QMessageBox().information(self, "提示", "函数名为空")
            return
        self.moduleName = moduleName
        self.methodName = methodName
        self.flag=True
        self.close()

class nativesForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/natives.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.methods= ""
        self.flag=False

    def submit(self):
        moduleName = self.txtModule.text()
        methods = self.txtMethods.toPlainText()
        if len(moduleName) <= 0 or len(methods) <= 0:
            QMessageBox().information(self, "提示", "模块名或函数为空")
            return
        self.moduleName = moduleName
        self.methods = methods
        self.flag=True
        self.close()

class dumpAddressForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/dumpAddress.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address = ""
        self.flag=False

    def submit(self):
        moduleName = self.txtModule.text()
        address = self.txtAddress.text()
        if len(moduleName) <= 0 or len(address) <= 0:
            QMessageBox().information(self, "提示", "模块名或地址为空")
            return
        self.moduleName = moduleName
        self.address = address
        self.flag=True
        self.close()

class findClassNameForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/fdclass.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.className = ""
        self.flag=False

    def submit(self):
        className = self.txtClass.text()
        if len(className) <= 0:
            QMessageBox().information(self, "提示", "类名为空")
            return
        self.className = className
        self.flag=True
        self.close()

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
        self.flag=False

    def submit(self):
        methodName = self.txtMethod.text()
        if len(methodName) <= 0:
            QMessageBox().information(self, "提示", "类名为空")
            return
        self.methodName = methodName
        self.flag=True
        self.close()

class patchForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/patch.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address=""
        self.patch=""
        self.flag=False

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
        self.flag=True
        self.close()

class selectPackageForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/selectPackage.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.packageName = ""
        self.flag=False

    def setPackages(self,packages):
        for item in packages:
            self.cmbPackages.addItem(item.name)

    def submit(self):
        packageName = self.cmbPackages.currentText()
        if len(packageName) <= 0:
            QMessageBox().information(self, "提示", "未选择package")
            return
        self.packageName = packageName
        self.flag=True
        self.close()