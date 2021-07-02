import json
import os
from datetime import datetime

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QHeaderView, QMenu, QAction, QTableWidgetItem, QMessageBox

from ui.custom import Ui_CustomDialog


class customForm(QDialog,Ui_CustomDialog):
    def __init__(self, parent=None):
        super(customForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)

        self.header = ["别名", "文件名", "备注"]
        self.tabCustomList.setColumnCount(3)
        self.tabCustomList.setHorizontalHeaderLabels(self.header)
        self.tabCustomList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabCustomList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabCustomList.customContextMenuRequested[QPoint].connect(self.cusTomRightMenuShow)
        self.tabCustomList.itemDoubleClicked.connect(self.cusTomDoubleClicked)
        self.btnClear.clicked.connect(self.UiClear)
        self.tabCustomHookList.setColumnCount(3)
        self.tabCustomHookList.setHorizontalHeaderLabels(self.header)
        self.tabCustomHookList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabCustomHookList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabCustomHookList.customContextMenuRequested[QPoint].connect(self.cusTomHookRightMenuShow)
        self.customs=[]
        self.customHooks=[]
        self.initData()
        self.txtJsName.textChanged.connect(self.jsNameChanged)

    def cusTomDoubleClicked(self,item):
        data=self.customs[item.row()]
        path = "./custom/" + data["fileName"]
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as jsfile:
                jsdata=jsfile.read()
                self.txtJsData.setPlainText(jsdata)
                self.txtJsName.setText(data["name"])
                self.txtBak.setText(data["bak"])
        else:
            QMessageBox().information(self, "提示", "文件" + data["fileName"] + "不存在")

    def UiClear(self):
        self.txtBak.setText("")
        self.txtJsName.setText("")
        self.txtJsFileName.setText("")
        self.txtJsData.setPlainText("")

    # 右键菜单
    def cusTomRightMenuShow(self):
        rightMenu = QMenu(self.tabCustomList)
        removeAction = QAction(u"删除", self, triggered=self.customRemove)
        addAction = QAction(u"添加到hook", self, triggered=self.customAdd)
        rightMenu.addAction(removeAction)
        rightMenu.addAction(addAction)
        rightMenu.exec_(QCursor.pos())

    # 右键菜单
    def cusTomHookRightMenuShow(self):
        rightMenu = QMenu(self.tabCustomHookList)
        removeAction = QAction(u"删除", self, triggered=self.hooksRemove)
        rightMenu.addAction(removeAction)
        rightMenu.exec_(QCursor.pos())

    def jsNameChanged(self):
        self.txtJsFileName.setText(self.txtJsName.text()+".js")

    def customAdd(self):
        for item in self.tabCustomList.selectedItems():
            if item.row()< len(self.customs):
                flag=False
                for cdata in self.customHooks:
                    if cdata["fileName"]==self.customs[item.row()]["fileName"]:
                        flag=True
                        break
                if flag:
                    QMessageBox().information(self, "提示", "文件"+self.customs[item.row()]["fileName"]+",已添加到hook,不能重复添加")
                    continue
                self.customHooks.append(self.customs[item.row()])
                break
        self.updateTabCustomHook()

    def customRemove(self):
        for item in self.tabCustomList.selectedItems():
            if item.row() < len(self.customs):
                print(item.row())
                path = "./custom/" + self.customs[item.row()]["fileName"]
                if os.path.exists(path):
                    os.remove(path)
                self.customs.remove(self.customs[item.row()])
        self.save()
        self.updateTabCustom()

    def hooksRemove(self):
        for item in self.tabCustomHookList.selectedItems():
            if item.row() < len(self.customHooks):
                self.customHooks.remove(self.customHooks[item.row()])
                break
        self.updateTabCustomHook()

    def initData(self):
        self.customs.clear()
        customPath="./custom/customs.txt"
        customs = []
        if os.path.exists(customPath)==False:
            return
        with open(customPath,"r",encoding="utf-8") as costomFile:
            customData=costomFile.read()
            try:
                if len(customData)>0:
                    customs=json.loads(customData)
            except Exception as ex:
                return
        if len(customs)<=0:
            return

        for item in customs:
            if os.path.exists("./custom/"+item["fileName"]):
                self.customs.append(item)
        self.save()
        self.updateTabCustom()

    def updateTabCustom(self):
        self.tabCustomList.clear()
        self.tabCustomList.setColumnCount(3)
        self.tabCustomList.setHorizontalHeaderLabels(self.header)
        self.tabCustomList.setRowCount(len(self.customs))
        line=0
        for item in self.customs:
            self.tabCustomList.setItem(line, 0, QTableWidgetItem(item["name"]))
            self.tabCustomList.setItem(line, 1, QTableWidgetItem(item["fileName"]))
            self.tabCustomList.setItem(line, 2, QTableWidgetItem(item["bak"]))
            line+=1

    def updateTabCustomHook(self):
        self.tabCustomHookList.clear()
        self.tabCustomHookList.setColumnCount(3)
        self.tabCustomHookList.setHorizontalHeaderLabels(self.header)
        self.tabCustomHookList.setRowCount(len(self.customHooks))
        line = 0
        for item in self.customHooks:
            self.tabCustomHookList.setItem(line, 0, QTableWidgetItem(item["name"]))
            self.tabCustomHookList.setItem(line, 1, QTableWidgetItem(item["fileName"]))
            self.tabCustomHookList.setItem(line, 2, QTableWidgetItem(item["bak"]))
            line +=1

    def save(self):
        with open("./custom/customs.txt","w",encoding="utf-8") as customFile:
            customFile.write(json.dumps(self.customs))


    def submit(self):
        if len(self.txtJsName.text())<=0:
            QMessageBox().information(self, "提示", "别名不能为空")
            return
        if len(self.txtJsData.toPlainText())<=0:
            QMessageBox().information(self, "提示", "脚本不能为空")
            return
        data={}
        data["name"]=self.txtJsName.text()
        data["fileName"]=self.txtJsFileName.text()
        data["bak"]=self.txtBak.text()
        savepath="./custom/"+data["fileName"]
        with open(savepath,"w",encoding="utf-8") as saveFile:
            saveFile.write(self.txtJsData.toPlainText())
        flag=False
        for idx in range(len(self.customs)):
            if self.customs[idx]["fileName"]==data["fileName"]:
                self.customs[idx]=data
                flag=True
        if flag==False:
            self.customs.append(data)
        self.save()
        self.updateTabCustom()