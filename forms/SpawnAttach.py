import os

from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.spawnAttach import Ui_SpawnAttachDialog


class spawnAttachForm(QDialog,Ui_SpawnAttachDialog):
    def __init__(self, parent=None):
        super(spawnAttachForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.packageName = ""
        self.packages=[]
        self.listPackage.itemClicked.connect(self.packageClick)
        self.flushList()

    def flushList(self):
        self.packages.clear()
        self.listPackage.clear()
        packagePath = "./tmp/spawnPackage.txt"
        if os.path.exists(packagePath):
            with open("./tmp/spawnPackage.txt", "r") as packageFile:
                packageData = packageFile.read()
                packages = packageData.split("\n")
                for item in packages:
                    if item in self.packages:
                        continue
                    self.packages.append(item)
                    self.listPackage.addItem(item)

    def packageClick(self,item):
        self.txtPackage.setText(item.text())

    def submit(self):
        packageName = self.txtPackage.text()
        if len(packageName) <= 0:
            QMessageBox().information(self, "提示", "package为空")
            return
        self.packageName = packageName
        if packageName not in self.packages :
            self.listPackage.addItem(packageName)
            with open("./tmp/spawnPackage.txt","w") as packageFile:
                packageFile.write(packageName+"\n")
        self.accept()