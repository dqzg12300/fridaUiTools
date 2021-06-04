# coding=utf-8
import datetime
import sys

from PyQt5 import uic, QtWidgets, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStatusBar, QLabel, QMessageBox, QHeaderView, \
    QTableWidgetItem

from utils import LogUtil
import json,os

from forms import formUtil

class kmainForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUi()
        self.hooksData={}
        self.updateCmbHooks()
        with open("./config/type.json","r",encoding="utf8") as typeFile:
            self.typeData=json.loads(typeFile.read())

    def initUi(self):
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/kmain.ui", self)
        self.statusBar = QStatusBar()
        self.labStatus = QLabel('当前状态:未连接')
        self.setStatusBar(self.statusBar)
        self.statusBar.addPermanentWidget(self.labStatus, stretch=1)
        self.actionattach.triggered.connect(self.actionAttach)
        self.actionabort.triggered.connect(self.actionAbort)

        self.btnShowClasses.clicked.connect(self.showClasses)
        self.btnShowExport.clicked.connect(self.showExport)
        self.btnShowStr.clicked.connect(self.showStr)
        self.btnWallbreaker.clicked.connect(self.wallBreaker)
        self.btnFindClassPath.clicked.connect(self.findClassPath)
        self.btnShowMethods.clicked.connect(self.showMethods)
        self.btnDumpPtr.clicked.connect(self.dumpPtr)
        self.btnMatchDump.clicked.connect(self.matchDump)
        self.chkNetwork.toggled.connect(self.hookNetwork)
        self.chkJni.toggled.connect(self.hookJNI)
        self.chkJavaFile.toggled.connect(self.hookJavaFile)
        self.chkJavaEnc.toggled.connect(self.hookJavaEnc)
        self.chkJavaString.toggled.connect(self.hookJavaString)
        self.chkSec.toggled.connect(self.hookSec)
        self.chkSslPining.toggled.connect(self.hookSslPining)

        self.btnMatchMethod.clicked.connect(self.matchMethod)
        self.btnMatchSoMethod.clicked.connect(self.matchSoMethod)

        self.btnNatives.clicked.connect(self.hookNatives)
        self.btnStalker.clicked.connect(self.stalker)
        self.btnCustom.clicked.connect(self.custom)
        self.outlogger= LogUtil.Logger('all.log',level='debug')

        self.btnSaveHooks.clicked.connect(self.saveHooks)
        self.btnImportHooks.clicked.connect(self.importHooks)
        self.btnLoadHooks.clicked.connect(self.loadHooks)
        self.btnClearHooks.clicked.connect(self.clearHooks)

        header=["功能","类名","函数","备注"]
        self.tabHooks.setColumnCount(4)
        self.tabHooks.setHorizontalHeaderLabels(header)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.mfrom = formUtil.matchFrom()
        self.m2from = formUtil.match2From()

    #打印操作日志
    def log(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtLogs.appendPlainText(datestr+logstr)

    # 打印输出日志
    def outlog(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtoutLogs.appendPlainText(datestr+logstr)
        self.outlogger.logger.debug(logstr)

    #启动附加
    def actionAttach(self):
        self.log("actionAttach")
    #是否附加进程了
    def isattack(self):
        if self.labStatus.text().index("未连接"):
            return False
        return True

    #====================start======需要附加后才能使用的功能,基本都是在内存中查数据================================
    def showClasses(self):
        if self.isattack()==False:
            self.log("Error:还未附加进程")
            return
        self.log("查询所有类")

    def showExport(self):
        if self.isattack()==False:
            self.log("Error:还未附加进程")
            return
        self.log("查询so的所有符号")

    def showStr(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("将指定地址以str打印")

    def wallBreaker(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("wallBreaker功能")

    def showMethods(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("wallBreaker功能")

    def findClassPath(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("查找指定类的完整名称")

    def dumpPtr(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("dump指定地址")

    def matchDump(self):
        if self.isattack() == False:
            self.log("Error:还未附加进程")
            return
        self.log("指定特征dump内存")
    # ====================end======需要附加后才能使用的功能,基本都是在内存中查数据================================

    # ====================start======附加前使用的功能,基本都是在内存中查数据================================

    def hook_add(self,chk,typeStr):
        if chk:
            self.hooksData[typeStr]=self.typeData[typeStr]
            self.updateTabHooks()
        else:
            self.hooksData.pop(typeStr)
            self.updateTabHooks()

    def hookNetwork(self,checked):
        typeStr = "network"
        self.hook_add(checked,typeStr)
        if checked:
            self.log("hook网络相关")
        else:
            self.log("取消hook网络相关")

    def hookJNI(self,checked):
        typeStr = "jni"
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook jni")
        else:
            self.log("取消hook jni")

    def hookJavaFile(self,checked):
        typeStr = "javaFile"
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook java的文件类所有函数")
        else:
            self.log("取消hook java的文件类所有函数")

    def hookJavaEnc(self,checked):
        typeStr = "javaEnc"
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook java的算法加解密所有函数")
        else:
            self.log("取消hook java的算法加解密所有函数")

    def hookJavaString(self,checked):
        typeStr = "javaString"
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook java的String所有函数")
        else:
            self.log("取消hook java的String所有函数")

    def hookSec(self,checked):
        typeStr = "javaSec"
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook并导出证书")
        else:
            self.log("取消hook并导出证书")

    def hookSslPining(self,checked):
        typeStr = "sslpining"
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook证书锁定")
        else:
            self.log("取消hook证书锁定")

    def matchMethod(self):
        self.mfrom.show()
        className=self.mfrom.className
        methodName=self.mfrom.methodName
        if len(className)<=0 and len(methodName)<=0:
            return
        self.log("根据函数名trace hook")
        matchHook={"class":className,"method":methodName,"bak":"匹配指定类中的指定函数.无类名则hook所有类中的指定函数.无函数名则hook类的所有函数"}
        typeStr="match_java"
        self.hooksData[typeStr] = []
        self.hooksData[typeStr].append(matchHook)
        self.updateTabHooks()

    def matchClassName(self):
        self.log("根据类名trace hook")

    def matchSoMethod(self):
        self.log("根据so的函数名trace hook")

    def hookNatives(self):
        self.log("批量hook native函数")

    def stalker(self):
        self.log("stalker")

    def custom(self):
        self.log("custom")

    def saveHooks(self):
        self.log("保存hook列表")
        saveHooks=self.txtSaveHooks.text()
        if len(saveHooks)<=0:
            self.log("未填写保存的别名")
            QMessageBox().information(self, "提示", "未填写别名")
            return
        filepath="./hooks/"+saveHooks+".json"
        with open(filepath,"w",encoding="utf8") as hooksFile:
            jsondata=json.dumps(self.hooksData)
            hooksFile.write(jsondata)
            self.log("成功保存到"+filepath)
            self.updateCmbHooks()
            QMessageBox().information(self,"提示","保存成功")

    #加载hook列表后。这里刷新下checked
    def refreshChecks(self):
        for key in self.hooksData:
            if key=="network":
                self.chkNetwork.setChecked(True)
            elif key=="jni":
                self.chkJni.setChecked(True)
            elif key=="javaFile":
                self.chkJavaFile.setChecked(True)
            elif key=="javaEnc":
                self.chkJavaEnc.setChecked(True)
            elif key=="javaString":
                self.chkJavaString.setChecked(True)
            elif key=="javaSec":
                self.chkSec.setChecked(True)
            elif key=="sslpining":
                self.chkSslPining.setChecked(True)

    def loadJson(self,filepath):
        with open(filepath, "r", encoding="utf8") as hooksFile:
            data = hooksFile.read()
            self.hooksData = json.loads(data)
            self.updateTabHooks()
            self.refreshChecks()

    def loadHooks(self):
        name=self.cmbHooks.currentText()
        if name:
            self.clearHooks()
            filepath="./hooks/"+name+".json"
            self.log("加载"+filepath)
            self.loadJson(filepath)
            self.log("成功加载" + filepath)

    def importHooks(self):
        filepath = QtWidgets.QFileDialog.getOpenFileName(self, "open files")
        if filepath[0]:
            self.log("导入json文件"+filepath[0])
            self.loadJson(filepath[0])
            self.log("成功导入文件" + filepath[0])

    def clearHooks(self):
        self.log("清空hook列表")
        self.tabHooks.clear()
        header = ["功能", "类名", "函数", "备注"]
        self.tabHooks.setColumnCount(4)
        self.tabHooks.setRowCount(0)
        self.tabHooks.setHorizontalHeaderLabels(header)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    #更新加载hook列表
    def updateCmbHooks(self):
        for name in os.listdir("./hooks"):
            if name.index(name)>=0:
                self.cmbHooks.addItem(name.replace(".json",""))

    #更新hooks列表界面
    def updateTabHooks(self):
        self.clearHooks()
        line=0
        for item in self.hooksData:
            self.tabHooks.insertRow(line)
            self.tabHooks.setItem(line, 0, QTableWidgetItem(item))
            self.tabHooks.setItem(line, 1, QTableWidgetItem(self.hooksData[item]["class"]))
            self.tabHooks.setItem(line, 2, QTableWidgetItem(self.hooksData[item]["method"]))
            self.tabHooks.setItem(line, 3, QTableWidgetItem(self.hooksData[item]["bak"]))

    # ====================end======附加前使用的功能,基本都是在内存中查数据================================

    def actionAbort(self):
        QMessageBox().about(self, "About",
                            "\nfrida_tools: 缝合怪,常用脚本整合的界面化工具 \nAuthor: https://github.com/dqzg12300")

if __name__=="__main__":
    app=QApplication(sys.argv)
    kmain = kmainForm()
    kmain.show()
    sys.exit(app.exec_())

