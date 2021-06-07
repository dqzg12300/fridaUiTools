# coding=utf-8
import datetime
import sys

from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStatusBar, QLabel, QMessageBox, QHeaderView, \
    QTableWidgetItem

from utils import LogUtil
import json,os,threading,frida

from forms import formUtil
import TraceThread

class kmainForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUi()
        self.hooksData={}
        self.updateCmbHooks()
        self.outlogger = LogUtil.Logger('all.log', level='debug')
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

        self.btnFindMethod.clicked.connect(self.findMethod)
        self.btnShowExport.clicked.connect(self.showExport)
        self.btnFindExport.clicked.connect(self.findExport)
        self.btnDumpStr.clicked.connect(self.dumpStr)
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
        self.btnTuoke.clicked.connect(self.tuoke)
        self.btnPatch.clicked.connect(self.patch)
        self.btnCallFunction.clicked.connect(self.callFunction)

        self.btnSaveHooks.clicked.connect(self.saveHooks)
        self.btnImportHooks.clicked.connect(self.importHooks)
        self.btnLoadHooks.clicked.connect(self.loadHooks)
        self.btnClearHooks.clicked.connect(self.clearHooks)
        self.header = ["功能", "类名/模块名", "函数", "备注"]
        self.tabHooks.setColumnCount(4)
        self.tabHooks.setHorizontalHeaderLabels(self.header)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.mform = formUtil.matchForm()
        self.m2form = formUtil.match2Form()
        self.nativesForm=formUtil.nativesForm()
        self.dumpForm = formUtil.dumpAddressForm()
        self.findClassForm=formUtil.findClassNameForm()
        self.tform=formUtil.tuokeForm()
        self.callForm=formUtil.callFunctionForm()
        self.pform=formUtil.patchForm()



    #打印操作日志
    def log(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtLogs.appendPlainText(datestr+logstr)

    # 打印输出日志
    def outlog(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtoutLogs.appendPlainText(datestr+logstr)
        self.outlogger.logger.debug(logstr)

    def taskOver(self):
        self.log("附加进程结束")
        self.actionattach.setText("启动附加")
        self.labStatus.setText("当前状态:未连接")

    #启动附加
    def actionAttach(self):
        self.log("actionAttach")
        if self.isattach():
            self.actionattach.setText("启动附加")
            self.labStatus.setText("当前状态:未连接")
            if "th" in self:
                self.th.quit()
        else:
            self.actionattach.setText("停止")
            self.labStatus.setText("当前状态:已连接")
            # self.th = TraceThread.Runthread(self.hooksData)
            # self.th.taskOverSignel.connect(self.taskOver)
            # self.th.loggerSignel.connect(self.log)
            # self.th.outloggerSignel.connect(self.outlog)
            # self.th.start()
    #是否附加进程了
    def isattach(self):
        if "未连接" in self.labStatus.text():
            return False
        return True

    #====================start======需要附加后才能使用的功能,基本都是在内存中查数据================================
    def findMethod(self):
        if self.isattach()==False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("查询所有类")
        self.mform.className = ""
        self.mform.methodName = ""
        self.mform.show()
        self.mform.exec_()
        className = self.mform.className
        methodName = self.mform.methodName
        if len(className) <= 0 and len(methodName) <= 0:
            return

    def showExport(self):
        if self.isattach()==False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("查询so的所有符号")


    def findExport(self):
        if self.isattach()==False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("搜索so的指定符号")
        self.m2form.moduleName = ""
        self.m2form.methodName = ""
        self.m2form.show()
        self.m2form.exec_()
        moduleName = self.m2form.moduleName
        methodName = self.m2form.methodName
        if len(moduleName) <= 0 and len(methodName) <= 0:
            return

    def dumpStr(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("将指定地址以str打印")
        self.dumpForm.moduleName = ""
        self.dumpForm.methodName = ""
        self.dumpForm.show()
        self.dumpForm.exec_()
        moduleName = self.dumpForm.moduleName
        methodName = self.dumpForm.methodName
        if len(moduleName) <= 0 and len(methodName) <= 0:
            return

    def wallBreaker(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("wallBreaker功能")
        QMessageBox().information(self, "提示", "待开发")

    def showMethods(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("wallBreaker功能")

    def findClassPath(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("查找指定类的完整名称")
        self.findClassForm.className = ""
        self.findClassForm.show()
        self.findClassForm.exec_()
        className = self.findClassForm.className
        if len(className) <= 0:
            return

    def dumpPtr(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("dump指定地址")
        self.dumpForm.moduleName = ""
        self.dumpForm.methodName = ""
        self.dumpForm.show()
        self.dumpForm.exec_()
        moduleName = self.dumpForm.moduleName
        methodName = self.dumpForm.methodName
        if len(moduleName) <= 0 and len(methodName) <= 0:
            return

    def matchDump(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("指定特征dump内存")
        QMessageBox().information(self, "提示", "待开发")

    def callFunction(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.callForm.methodName = ""
        self.callForm.show()
        self.callForm.exec_()
        methodName = self.callForm.methodName
        if len(methodName) <= 0:
            return

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
        self.mform.className=""
        self.mform.methodName=""
        self.mform.show()
        self.mform.exec_()
        className=self.mform.className
        methodName=self.mform.methodName
        if len(className)<=0 and len(methodName)<=0:
            return
        self.log("根据函数名trace hook")
        matchHook={"class":className,"method":methodName,"bak":"匹配指定类中的指定函数.无类名则hook所有类中的指定函数.无函数名则hook类的所有函数"}
        typeStr="match_java"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(matchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(matchHook)
        self.updateTabHooks()

    def matchSoMethod(self):
        self.m2form.moduleName=""
        self.m2form.methodName=""
        self.m2form.show()
        self.m2form.exec_()
        moduleName = self.m2form.moduleName
        methodName = self.m2form.methodName
        if len(moduleName) <= 0 and len(methodName) <= 0:
            return
        self.log("根据so的函数名trace hook")
        matchHook = {"class": moduleName, "method": methodName, "bak": "匹配so中的函数."}
        typeStr = "match_native"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(matchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(matchHook)
        self.updateTabHooks()

    def hookNatives(self):
        self.nativesForm.moduleName = ""
        self.nativesForm.methods = ""
        self.nativesForm.show()
        self.nativesForm.exec_()
        moduleName = self.nativesForm.moduleName
        methods = self.nativesForm.methods
        if len(moduleName) <= 0 and len(methods) <= 0:
            return
        self.log("批量hook native的sub函数")
        matchHook = {"class": moduleName, "method": methods, "bak": "批量匹配sub函数,使用较通用的方式打印参数."}
        typeStr = "match_sub"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(matchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(matchHook)
        self.updateTabHooks()

    def stalker(self):
        self.log("stalker")
        QMessageBox().information(self, "提示", "待开发")

    def custom(self):
        self.log("custom")
        QMessageBox().information(self, "提示", "待开发")

    def tuoke(self):
        self.tform.tuokeType = ""
        self.tform.show()
        self.tform.exec_()
        tuokeType = self.tform.tuokeType
        if len(tuokeType) <= 0 :
            return
        self.log("使用脱壳"+tuokeType)
        self.hooksData["tuoke"] = {"class": tuokeType, "method": "", "bak": "使用大佬开源的脱壳方法."}
        self.updateTabHooks()

    def patch(self):
        self.pform.moduleName = ""
        self.pform.address = ""
        self.pform.patch = ""
        self.pform.show()
        self.pform.exec_()
        moduleName = self.pform.moduleName
        address=self.pform.address
        patch=self.pform.patch
        if len(moduleName) <= 0 or len(address) <= 0 or len(patch) <= 0:
            return
        self.log("pathch替换模块:"+moduleName+"地址:" + address+"的数据为"+patch)
        patchHook = {"class": moduleName, "method": address+"|"+patch, "bak": "替换指定地址的二进制数据."}
        typeStr = "patch"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(patchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(patchHook)
        self.updateTabHooks()

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

        self.tabHooks.setColumnCount(4)
        self.tabHooks.setRowCount(0)
        self.tabHooks.setHorizontalHeaderLabels(self.header)
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
            if isinstance(self.hooksData[item],list):
                for itemLine in self.hooksData[item]:
                    self.tabHooks.insertRow(line)
                    self.tabHooks.setItem(line, 0, QTableWidgetItem(item))
                    self.tabHooks.setItem(line, 1, QTableWidgetItem(itemLine["class"]))
                    self.tabHooks.setItem(line, 2, QTableWidgetItem(itemLine["method"]))
                    self.tabHooks.setItem(line, 3, QTableWidgetItem(itemLine["bak"]))
            else:
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

