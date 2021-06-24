import os

from PyQt5 import uic
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog, QMenu, QAction, QHeaderView, QTableWidgetItem
from utils import AsmUtil

# class matchForm(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.setWindowOpacity(0.93)
#         uic.loadUi("./ui/match.ui", self)
#         self.btnSubmit.clicked.connect(self.submit)
#         self.className=""
#         self.methodName=""
#         self.hasMethod = True
#         self.chkHasMethod.toggled.connect(self.changeHasMethod)
#         self.btnClear.clicked.connect(self.clearUi)
#         self.clearUi()
#         self.flushCmb()
#         self.listClass.itemClicked.connect(self.ClassItemClick)
#         self.txtClass.textChanged.connect(self.changeClass)
#         self.cmbPackage.currentTextChanged.connect(self.changePackage)
#         self.classes = None
# 
#     def initData(self):
#         self.listClass.clear()
#         for item in self.classes:
#             self.listClass.addItem(item)
# 
#     def flushCmb(self):
#         self.cmbPackage.clear()
#         files = os.listdir("./tmp/")
#         self.cmbPackage.addItem("选择缓存数据")
#         for item in files:
#             if ".classes.txt" in item:
#                 self.cmbPackage.addItem(item.replace(".classes.txt", ""))
# 
#     def ClassItemClick(self, item):
#         self.txtClass.setText(item.text())
# 
#     def changeClass(self, data):
#         if self.classes==None or len(self.classes)<=0:
#             return
#         self.listClass.clear()
#         if len(data) > 0:
#             for item in self.classes:
#                 if data in item:
#                     self.listClass.addItem(item)
#         else:
#             for item in self.classes:
#                 self.listClass.addItem(item)
# 
#     def changePackage(self, data):
#         if data=="" or data=="选择缓存数据":
#             return
#         filepath = "./tmp/" + data + ".classes.txt"
#         with open(filepath, "r", encoding="utf-8") as packageFile:
#             res = packageFile.read()
#             self.classes = res.split("\n")
#         self.initData()
# 
#     def clearUi(self):
#         self.txtClass.setText("")
#         self.txtMethod.setText("")
# 
#     def changeHasMethod(self,chk):
#         if chk:
#             self.txtMethod.setEnabled(True)
#         else:
#             self.txtMethod.setEnabled(False)
# 
#     def submit(self):
#         className=self.txtClass.text()
#         methodName=self.txtMethod.text()
#         self.className=className
#         self.methodName=methodName
#         self.hasMethod = self.chkHasMethod.isChecked()
#         self.accept()

class nativesForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/natives.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.moduleName = ""
        self.methods= ""
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.flushCmb()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.cmbPackage.currentTextChanged.connect(self.changePackage)
        self.modules = None

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
                self.cmbPackage.addItem(item.replace(".modules.txt", ""))

    def ModuleItemClick(self, item):
        self.txtModule.setText(item.text())

    def changeModule(self, data):
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

    def changePackage(self, data):
        if data=="" or data=="选择缓存数据":
            return
        filepath = "./tmp/" + data + ".modules.txt"
        with open(filepath, "r", encoding="utf-8") as packageFile:
            res = packageFile.read()
            self.modules = res.split("\n")
        self.initData()

    def clearUi(self):
        self.txtModule.setText("")
        self.txtMethods.setPlainText("")

    def submit(self):
        moduleName = self.txtModule.text()
        methods = self.txtMethods.toPlainText().replace("\n",",")
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

class tuokeForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/tuoke.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.tuokeType = ""

    def submit(self):
        self.tuokeType = "fart"
        if self.rdoDexDump.isChecked():
            self.tuokeType="FRIDA-DEXDump"
        elif self.rdoDumpDex.isChecked():
            self.tuokeType="dumpdex"
        elif self.rdoDumpDexClass.isChecked():
            self.tuokeType="dumpdexclass"
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
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.flushCmb()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.cmbPackage.currentTextChanged.connect(self.changePackage)
        self.modules = None

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
                self.cmbPackage.addItem(item.replace(".modules.txt", ""))

    def ModuleItemClick(self, item):
        self.txtModule.setText(item.text())

    def changeModule(self, data):
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

    def changePackage(self, data):
        if data=="" or data=="选择缓存数据":
            return
        filepath = "./tmp/" + data + ".modules.txt"
        with open(filepath, "r", encoding="utf-8") as packageFile:
            res = packageFile.read()
            self.modules = res.split("\n")
        self.initData()

    def clearUi(self):
        self.txtModule.setText("libnative-lib.so")
        self.txtAddress.setText("0xE55C")
        self.txtPatch.setText("1F 20 03 D5")

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
        if data=="" or data=="选择缓存数据":
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

class jnitraceForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/jnitrace.ui", self)
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

class zenTracerForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/zenTracer.ui", self)
        self.flushCmb()
        self.traceClass =[]
        self.traceBClass=[]
        self.classes=None
        self.txtClass.textChanged.connect(self.changeClass)
        self.btnClassAdd.clicked.connect(self.classAdd)
        self.listClasses1.itemClicked.connect(self.classes1ItemClick)

        self.txtClassBreak.textChanged.connect(self.changeClassBreak)
        self.btnClassBreakAdd.clicked.connect(self.classBreakAdd)
        self.listClasses2.itemClicked.connect(self.classes2ItemClick)

        self.btnClassFileAdd.clicked.connect(self.classFileAdd)
        self.btnClassStringAdd.clicked.connect(self.classStringAdd)

        self.cmbPackage.currentTextChanged.connect(self.changePackage)

        self.header = ["类名", "类型"]
        self.tabTracer.setColumnCount(2)
        self.tabTracer.setHorizontalHeaderLabels(self.header)
        self.tabTracer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabTracer.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabTracer.customContextMenuRequested[QPoint].connect(self.rightMenuShow)


    def flushCmb(self):
        self.cmbPackage.clear()
        files = os.listdir("./tmp/")
        self.cmbPackage.addItem("选择缓存数据")
        for item in files:
            if ".classes.txt" in item:
                self.cmbPackage.addItem(item.replace(".classes.txt",""))

    def changePackage(self,data):
        if data=="" or data=="选择缓存数据":
            return
        filepath="./tmp/"+data+".classes.txt"
        with open(filepath,"r",encoding="utf-8") as packageFile:
            res=packageFile.read()
            self.classes=res.split("\n")
        self.initData()

    def initData(self):
        self.listClasses1.clear()
        self.listClasses2.clear()
        for item in self.classes:
            self.listClasses1.addItem(item)
            self.listClasses2.addItem(item)

    def changeClass(self,data):
        if self.classes==None or len(self.classes)<=0:
            return
        self.listClasses1.clear()
        if len(data) > 0:
            for item in self.classes:
                if data in item:
                    self.listClasses1.addItem(item)
        else:
            for item in self.classes:
                self.listClasses1.addItem(item)

    def changeClassBreak(self,data):
        self.listClasses2.clear()
        if len(data) > 0:
            for item in self.classes:
                if data in item:
                    self.listClasses2.addItem(item)
        else:
            for item in self.classes:
                self.listClasses2.addItem(item)

    def classes1ItemClick(self,item):
        self.txtClass.setText(item.text())

    def classes2ItemClick(self,item):
        self.txtClassBreak.setText(item.text())

    def classAdd(self):
        className=self.txtClass.text()
        if className in self.traceClass:
            return
        self.traceClass.append(className)
        self.updateTabTracer()

    def classBreakAdd(self):
        className = self.txtClassBreak.text()
        if className in self.traceBClass:
            return
        self.traceBClass.append(className)
        self.updateTabTracer()


    def classFileAdd(self):
        className="java.io.File"
        if className in self.traceClass:
            return
        self.traceClass.append(className)
        self.updateTabTracer()

    def classStringAdd(self):
        className = "java.lang.String"
        if className in self.traceClass:
            return
        self.traceClass.append(className)
        self.updateTabTracer()

    def hooksRemove(self):
        for item in self.tabTracer.selectedItems():
            name=self.tabTracer.item(item.row(),0).text()
            ntype=self.tabTracer.item(item.row(),1).text()
            if ntype=="trace":
                self.traceClass.remove(name)
            else:
                self.traceBClass.remove(name)
            self.tabTracer.removeRow(item.row())

    def clearHooks(self):
        # self.log("清空hook列表")
        self.tabTracer.clear()
        self.tabTracer.setColumnCount(2)
        self.tabTracer.setRowCount(0)
        self.tabTracer.setHorizontalHeaderLabels(self.header)
        self.tabTracer.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def hooksClear(self):
        self.traceClass.clear()
        self.traceBClass.clear()
        self.clearHooks()

    def updateTabTracer(self):
        self.clearHooks()
        line = 0
        for item in self.traceClass:
            self.tabTracer.insertRow(line)
            self.tabTracer.setItem(line, 0, QTableWidgetItem(item))
            self.tabTracer.setItem(line, 1, QTableWidgetItem("trace"))
        for item in self.traceBClass:
            self.tabTracer.insertRow(line)
            self.tabTracer.setItem(line, 0, QTableWidgetItem(item))
            self.tabTracer.setItem(line, 1, QTableWidgetItem("break"))

    def rightMenuShow(self):
        rightMenu = QMenu(self.tabTracer)
        removeAction = QAction(u"删除", self,triggered=self.hooksRemove)
        rightMenu.addAction(removeAction)

        clearAction = QAction(u"清空", self, triggered=self.hooksClear)
        rightMenu.addAction(clearAction)
        rightMenu.exec_(QCursor.pos())

class spawnAttachForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/spawnAttach.ui", self)
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

class stalkerForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/stalker.ui", self)
        self.btnSubmit.clicked.connect(self.submit)
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.flushCmb()
        self.listModule.itemClicked.connect(self.ModuleItemClick)
        self.txtModule.textChanged.connect(self.changeModule)
        self.cmbPackage.currentTextChanged.connect(self.changePackage)
        self.modules = None

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
                self.cmbPackage.addItem(item.replace(".modules.txt", ""))

    def ModuleItemClick(self, item):
        self.txtModule.setText(item.text())

    def changeModule(self, data):
        if self.modules==None or len(self.modules)<=0:
            return
        if data == "" or data == "选择缓存数据":
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
        if data=="" or data=="选择缓存数据":
            return
        filepath = "./tmp/" + data + ".modules.txt"
        with open(filepath, "r", encoding="utf-8") as packageFile:
            res = packageFile.read()
            self.modules = res.split("\n")
        self.initData()

    def clearUi(self):
        self.txtSymbol.setText("")
        self.txtOffset.setText("")
        self.txtModule.setText("")

    def submit(self):
        moduleName = self.txtModule.text()
        offset = self.txtOffset.text()
        symbol= self.txtSymbol.text()
        if len(moduleName) <= 0:
            QMessageBox().information(self, "提示", "模块不能为空")
            return
        if len(offset) <= 0 and len(symbol)<=0:
            QMessageBox().information(self, "提示", "offset和symbol至少填写一项")
            return
        self.moduleName = moduleName
        self.offset = offset
        self.symbol = symbol
        self.accept()

class dumpSoForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/dump_so.ui", self)
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

class fartForm(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/fart.ui", self)
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



