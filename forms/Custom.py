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

        self.tabCustomHookList.setColumnCount(3)
        self.tabCustomHookList.setHorizontalHeaderLabels(self.header)
        self.tabCustomHookList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabCustomHookList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabCustomHookList.customContextMenuRequested[QPoint].connect(self.cusTomHookRightMenuShow)
        self.customs=[]
        self.customHooks=[]
        self.initData()



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

    def customAdd(self):
        for item in self.tabCustomList.selectedItems():
            addItemData = self.tabCustomList.item(item.row(), 0).text() + self.tabCustomList.item(item.row(), 1).text()
            for idx in self.customs:
                if addItemData == self.customs[idx]["name"] + self.customs[idx]["fileName"]:
                    self.customHooks.append(self.customs[idx])
                    break
        self.updateTabCustomHook()

    def customRemove(self):
        for item in self.tabCustomList.selectedItems():
            removeItemData = self.tabCustomList.item(item.row(), 0).text() + self.tabCustomList.item(item.row(), 1).text()
            for idx in self.customs:
                if removeItemData==self.customs[idx]["name"]+self.customs[idx]["fileName"]:
                    self.customs.remove(idx)
                    path="./custom/"+self.customs[idx]["name"]
                    if os.path.exists(path):
                        os.remove(path)
                    break
        self.updateTabCustom()

    def hooksRemove(self):
        for item in self.tabCustomHookList.selectedItems():
            removeItemData = self.tabCustomHookList.item(item.row(), 0).text() + self.tabCustomHookList.item(item.row(), 1).text()
            for idx in self.customHooks:
                if removeItemData == self.customHooks[idx]["name"] + self.customHooks[idx]["fileName"]:
                    self.customHooks.remove(idx)
                    break
        self.updateTabCustomHook()

    def initData(self):
        self.customs.clear()
        customPath="./custom/customs.txt"
        if os.path.exists(customPath)==False:
            return
        with open(customPath,"r",encoding="utf-8") as costomFile:
            customData=costomFile.read()
            customs=json.loads(customData)
        if len(customs)<=0:
            return

        for item in customs:
            if os.path.exists("./custom/"+item["fileName"]+".js"):
                self.customs.append(item)
        self.updateTabCustom()

    def updateTabCustom(self):
        self.tabCustomList.clear()
        self.tabCustomList.setColumnCount(3)
        self.tabCustomList.setHorizontalHeaderLabels(self.header)
        for item in self.customs:
            self.tabCustomList.insertRow(0)
            self.tabCustomList.setItem(0, 0, QTableWidgetItem(item["name"]))
            self.tabCustomList.setItem(0, 1, QTableWidgetItem(item["fileName"]))
            self.tabCustomList.setItem(0, 2, QTableWidgetItem(item["bak"]))

    def updateTabCustomHook(self):
        self.tabCustomHookList.clear()
        self.tabCustomHookList.setColumnCount(3)
        self.tabCustomHookList.setHorizontalHeaderLabels(self.header)
        for item in self.customHooks:
            self.tabCustomHookList.insertRow(0)
            self.tabCustomHookList.setItem(0, 0, QTableWidgetItem(item["name"]))
            self.tabCustomHookList.setItem(0, 1, QTableWidgetItem(item["fileName"]))
            self.tabCustomHookList.setItem(0, 2, QTableWidgetItem(item["bak"]))

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
        datestr = datetime.now().strftime('%Y_%m_%d_%H_%M_%S_')
        data={}
        data["name"]=self.txtJsName.text()
        data["fileName"]=datestr+self.txtJsName.text()
        data["bak"]=self.txtBak.text()
        savepath="./custom/"+data["fileName"]+".js"
        with open(savepath,"w",encoding="utf-8") as saveFile:
            saveFile.write(self.txtJsData.toPlainText())
        self.customs.append(data)
        self.save()
        self.updateTabCustom()