from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.selectPackage import Ui_SelectPackageDialog


class selectPackageForm(QDialog,Ui_SelectPackageDialog):
    def __init__(self, parent=None):
        super(selectPackageForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.packageName = ""
        self.txtPackage.textChanged.connect(self.changePackage)

    def changePackage(self,data):
        if data=="" or data=="tmp data":
            return
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
        packageName = self.txtPackage.text()
        if len(packageName) <= 0:
            QMessageBox().information(self, "提示", "未选择package")
            return
        self.packageName = packageName
        self.accept()