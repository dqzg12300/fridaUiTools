import os

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QMenu, QAction, QHeaderView, QMessageBox

from ui.zenTracer import Ui_ZenTracerDialog


class zenTracerForm(QDialog,Ui_ZenTracerDialog):
    def __init__(self, parent=None):
        super(zenTracerForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.flushCmb()
        self.traceClass =[]
        self.traceBClass=[]
        self.traceMethods=[]
        self.traceBMethods=[]
        self.classes=None
        self.txtClass.textChanged.connect(self.changeClass)
        self.btnClassAdd.clicked.connect(self.classAdd)
        self.listClasses1.itemClicked.connect(self.classes1ItemClick)

        self.txtClassBreak.textChanged.connect(self.changeClassBreak)
        self.btnClassBreakAdd.clicked.connect(self.classBreakAdd)
        self.listClasses2.itemClicked.connect(self.classes2ItemClick)

        self.btnClassFileAdd.clicked.connect(self.classFileAdd)
        self.btnClassStringAdd.clicked.connect(self.classStringAdd)
        self.btnClassBundle.clicked.connect(self.classBundleAdd)
        self.btnClassBase64.clicked.connect(self.classBase64Add)
        self.btnClassStringBuilderAdd.clicked.connect(self.classStringBuildAdd)

        self.btnMethodAdd.clicked.connect(self.methodAdd)
        self.btnMethodBreakAdd.clicked.connect(self.methodBreakAdd)

        self.cmbPackage.currentTextChanged.connect(self.changePackage)

        self.header = ["名称", "类型"]
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
        if self.classes==None or len(self.classes)<=0:
            return
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

    def methodAdd(self):
        if len(self.txtClass.text())<=0:
            QMessageBox().information(self, "提示", "未指定函数所属类")
            return
        methodName = self.txtMethod.text()
        if methodName in self.traceMethods:
            return
        if len(self.txtClass.text())>0:
            methodName=self.txtClass.text()+"->"+methodName
        if self.txtClass.text() not in self.traceClass:
            self.traceClass.append(self.txtClass.text())
        self.traceMethods.append(methodName)
        self.updateTabTracer()

    def methodBreakAdd(self):
        if len(self.txtClassBreak.text())<=0:
            QMessageBox().information(self, "提示", "未指定拉黑函数所属类")
            return
        methodName = self.txtMethodBreak.text()
        if methodName in self.traceBMethods:
            return
        if len(self.txtClassBreak.text())>0:
            methodName=self.txtClassBreak.text()+"->"+methodName
        # if self.txtClassBreak.text() not in self.traceBClass:
        #     self.traceBClass.append(self.txtClassBreak.text())
        self.traceBMethods.append(methodName)
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

    def classBundleAdd(self):
        className = "android.os.Bundle"
        if className in self.traceClass:
            return
        self.traceClass.append(className)
        self.updateTabTracer()

    def classBase64Add(self):
        className = "android.util.Base64"
        if className in self.traceClass:
            return
        self.traceClass.append(className)
        self.updateTabTracer()

    def classStringBuildAdd(self):
        className = "java.lang.StringBuilder"
        if className in self.traceClass:
            return
        self.traceClass.append(className)
        self.updateTabTracer()

    def hooksRemove(self):
        for item in self.tabTracer.selectedItems():
            name=self.tabTracer.item(item.row(),0).text()
            ntype=self.tabTracer.item(item.row(),1).text()
            if ntype=="trace class":
                self.traceClass.remove(name)
            elif ntype=="trace method":
                self.traceMethods.remove(name)
            elif ntype=="break class":
                self.traceBClass.remove(name)
            elif ntype=="break method":
                self.traceBMethods.remove(name)
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
            self.tabTracer.setItem(line, 1, QTableWidgetItem("trace class"))
        for item in self.traceBClass:
            self.tabTracer.insertRow(line)
            self.tabTracer.setItem(line, 0, QTableWidgetItem(item))
            self.tabTracer.setItem(line, 1, QTableWidgetItem("break class"))
        for item in self.traceMethods:
            self.tabTracer.insertRow(line)
            self.tabTracer.setItem(line, 0, QTableWidgetItem(item))
            self.tabTracer.setItem(line, 1, QTableWidgetItem("trace method"))
        for item in self.traceBMethods:
            self.tabTracer.insertRow(line)
            self.tabTracer.setItem(line, 0, QTableWidgetItem(item))
            self.tabTracer.setItem(line, 1, QTableWidgetItem("break method"))

    def rightMenuShow(self):
        rightMenu = QMenu(self.tabTracer)
        removeAction = QAction(u"删除", self,triggered=self.hooksRemove)
        rightMenu.addAction(removeAction)

        clearAction = QAction(u"清空", self, triggered=self.hooksClear)
        rightMenu.addAction(clearAction)
        rightMenu.exec_(QCursor.pos())