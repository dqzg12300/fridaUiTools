from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog


class matchForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/match.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.className=""
        self.methodName=""

    def submit(self):
        className=self.txtClass.text()
        methodName=self.txtMethod.text()
        if len(className)<=0 and len(methodName)<=0:
            QMessageBox().information(self, "提示", "类名和函数名为空")
            return
        self.className=className
        self.methodName=methodName
        self.close()


class match2Form(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/match2.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
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
        self.close()

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
        self.close()

class dumpAddressForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/dumpAddress.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.address = ""

    def submit(self):
        moduleName = self.txtModule.text()
        address = self.txtAddress.text()
        if len(moduleName) <= 0 or len(address) <= 0:
            QMessageBox().information(self, "提示", "模块名或地址为空")
            return
        self.moduleName = moduleName
        self.address = address
        self.close()

class findClassNameForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/fdclass.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.className = ""

    def submit(self):
        className = self.txtClass.text()
        address = self.txtAddress.text()
        if len(className) <= 0:
            QMessageBox().information(self, "提示", "类名为空")
            return
        self.className = className
        self.close()