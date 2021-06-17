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
        self.th = TraceThread.Runthread(self.hooksData,"")
        self.updateCmbHooks()
        self.outlogger = LogUtil.Logger('all.logs', level='debug')
        with open("./config/type.json","r",encoding="utf8") as typeFile:
            self.typeData=json.loads(typeFile.read())

    def initUi(self):
        self.setWindowOpacity(0.93)
        uic.loadUi("./ui/kmain.ui", self)

        self.statusBar = QStatusBar()
        self.labStatus = QLabel('当前状态:未连接')
        self.setStatusBar(self.statusBar)
        self.statusBar.addPermanentWidget(self.labStatus, stretch=1)
        self.labPackage = QLabel('')
        self.statusBar.addPermanentWidget(self.labPackage, stretch=2)

        self.actionAttach.triggered.connect(self.actionAttachStart)
        self.actionSpawn.triggered.connect(self.actionSpawnStart)
        self.actionAttachName.triggered.connect(self.actionAttachNameStart)
        self.actionabort.triggered.connect(self.actionAbort)
        self.actionStop.setEnabled(False)
        self.actionStop.triggered.connect(self.taskOver)
        self.btnShowExport.clicked.connect(self.showExport)
        self.btnWallbreaker.clicked.connect(self.wallBreaker)
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

        self.btnSaveHooks.clicked.connect(self.saveHooks)
        self.btnImportHooks.clicked.connect(self.importHooks)
        self.btnLoadHooks.clicked.connect(self.loadHooks)
        self.btnClearHooks.clicked.connect(self.clearHooks)
        self.header = ["功能", "类名/模块名", "函数", "备注"]
        self.tabHooks.setColumnCount(4)
        self.tabHooks.setHorizontalHeaderLabels(self.header)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.dumpForm = formUtil.dumpAddressForm()
        self.mform = formUtil.matchForm()
        self.m2form = formUtil.match2Form()

    def closeEvent(self, event):
        self.th.quit()

    #打印操作日志
    def log(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtLogs.appendPlainText(datestr+logstr)

    # 打印输出日志
    def outlog(self,logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtoutLogs.appendPlainText(datestr+logstr)
        self.outlogger.logger.debug(logstr)
        if "default.js init hook success" in logstr:
            QMessageBox().information(self, "提示", "附加进程成功")

    def taskOver(self):
        self.log("附加进程结束")
        self.changeAttachStatus(False)
        QMessageBox().information(self, "提示", "成功停止附加进程")

    def attachOver(self,name):
        self.labPackage.setText(name)

    #启动附加
    def actionAttachStart(self):
        self.log("actionAttach")
        try:
            # 查下进程。能查到说明frida_server开启了
            device = frida.get_usb_device()
            process = device.enumerate_processes()
            print(process)
            self.changeAttachStatus(True)
            self.th = TraceThread.Runthread(self.hooksData, "")
            self.th.taskOverSignel.connect(self.taskOver)
            self.th.loggerSignel.connect(self.log)
            self.th.outloggerSignel.connect(self.outlog)
            self.th.loadAppInfoSignel.connect(self.loadAppInfo)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.start()
            if len(self.hooksData) <= 0:
                # QMessageBox().information(self, "提示", "未设置hook选项")
                self.log("未设置hook选项")
        except Exception as ex:
            self.log("附加异常.err:" + str(ex))
            QMessageBox().information(self, "提示", "附加进程失败." + str(ex))

    #spawn的方式附加进程
    def actionSpawnStart(self):
         pass

    #修改ui的状态表现
    def changeAttachStatus(self,isattach):
        if isattach:
            self.menuAttach.setEnabled(False)
            self.actionStop.setEnabled(True)
            self.labStatus.setText("当前状态:已连接")
        else:
            self.menuAttach.setEnabled(True)
            self.actionStop.setEnabled(False)
            self.labStatus.setText("当前状态:未连接")
            self.labPackage.setText("")

    #根据进程名进行附加进程
    def actionAttachNameStart(self):
        self.log("actionAttachName")
        try:
            device = frida.get_usb_device()
            process= device.enumerate_processes()
            selectPackageForm = formUtil.selectPackageForm()
            selectPackageForm.setPackages(process)
            res=selectPackageForm.exec()
            if res==0:
                return
            self.changeAttachStatus(True)
            self.th = TraceThread.Runthread(self.hooksData, selectPackageForm.packageName)
            self.th.taskOverSignel.connect(self.taskOver)
            self.th.loggerSignel.connect(self.log)
            self.th.outloggerSignel.connect(self.outlog)
            self.th.loadAppInfoSignel.connect(self.loadAppInfo)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.start()
        except Exception as ex:
            self.log("附加异常.err:"+str(ex))
            QMessageBox().information(self, "提示", "附加进程失败."+str(ex))


    #是否附加进程了
    def isattach(self):
        if "未连接" in self.labStatus.text():
            return False
        return True

    #====================start======需要附加后才能使用的功能,基本都是在内存中查数据================================

    def showMethods(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("查询所有类和函数")

        res=self.mform.exec()
        # className为空则是打印所有class。methodName为空则打印所有函数
        if res==0:
            return
        postdata={"className":self.mform.className,"methodName":self.mform.methodName,"hasMethod":self.mform.hasMethod}
        self.th.showMethods(postdata)

    def showExport(self):
        if self.isattach()==False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("查询so的所有符号")

        res=self.m2form.exec()
        if res==0:
            return
        #moduleName为空则是打印所有module。methodName为空则打印所有符号
        postdata={"moduleName":self.m2form.moduleName,"methodName":self.m2form.methodName,"showType":self.m2form.showType,"hasMethod":self.m2form.hasMethod}
        self.th.showExport(postdata)



    def wallBreaker(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("wallBreaker功能")
        QMessageBox().information(self, "提示", "待开发")


    def dumpPtr(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("dump指定地址")
        res= self.dumpForm.exec()
        print("res:",res)
        if res==0:
            return
        #设置了module就会以module为基址再加上address去dump。如果不设置module。就会直接dump指定的address
        postdata = {"moduleName": self.dumpForm.moduleName, "address": self.dumpForm.address,
                    "dumpType": self.dumpForm.dumpType,
                    "size": self.dumpForm.size}
        self.th.dumpPtr(postdata)

    def matchDump(self):
        if self.isattach() == False:
            self.log("Error:还未附加进程")
            QMessageBox().information(self, "提示", "未附加进程")
            return
        self.log("指定特征dump内存")
        QMessageBox().information(self, "提示", "待开发")

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
        typeStr = "r0capture"
        self.hook_add(checked,typeStr)
        if checked:
            self.log("hook网络相关")
        else:
            self.log("取消hook网络相关")

    def hookJNI(self,checked):
        typeStr = "jnitrace"
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
        mform = formUtil.matchForm()
        res=mform.exec()
        if res==0:
            return
        self.log("根据函数名trace hook")
        matchHook={"class":mform.className,"method":mform.methodName,"bak":"匹配指定类中的指定函数.无类名则hook所有类中的指定函数.无函数名则hook类的所有函数"}
        typeStr="match_java"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(matchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(matchHook)
        self.updateTabHooks()

    def matchSoMethod(self):
        m2form = formUtil.match2Form()
        res=m2form.exec()
        if res==0:
            return
        self.log("根据so的函数名trace hook")
        matchHook = {"class": m2form.moduleName, "method": m2form.methodName, "bak": "匹配so中的函数."}
        typeStr = "match_native"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(matchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(matchHook)
        self.updateTabHooks()

    def hookNatives(self):
        nativesForm = formUtil.nativesForm()
        res=nativesForm.exec()
        if res==0:
            return
        self.log("批量hook native的sub函数")
        matchHook = {"class": nativesForm.moduleName, "method": nativesForm.methods, "bak": "批量匹配sub函数,使用较通用的方式打印参数."}
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
        tform = formUtil.tuokeForm()
        res=tform.exec()
        if res==0:
            return
        self.log("使用脱壳"+tform.tuokeType)
        self.hooksData["tuoke"] = {"class": tform.tuokeType, "method": "", "bak": "使用大佬开源的脱壳方法."}
        self.updateTabHooks()

    def patch(self):
        pform = formUtil.patchForm()
        res=pform.exec()
        if res==0:
            return
        self.log("pathch替换模块:"+pform.moduleName+"地址:" + pform.address+"的数据为"+pform.patch)
        patchHook = {"class": pform.moduleName, "method": pform.address+"|"+pform.patch, "bak": "替换指定地址的二进制数据."}
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
            if key=="r0capture":
                self.chkNetwork.setChecked(True)
            elif key=="jnitrace":
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
    #导入hook的json文件
    def importHooks(self):
        filepath = QtWidgets.QFileDialog.getOpenFileName(self, "open files")
        if filepath[0]:
            self.log("导入json文件"+filepath[0])
            self.loadJson(filepath[0])
            self.log("成功导入文件" + filepath[0])

    #清除hook列表
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

    #附加成功后取出app的信息展示
    def loadAppInfo(self,appinfo):
        info= json.loads(appinfo)
        print(info)

    # ====================end======附加前使用的功能,基本都是在内存中查数据================================
    #关于我
    def actionAbort(self):
        QMessageBox().about(self, "About",
                            "\nfrida_tools: 缝合怪,常用脚本整合的界面化工具 \nAuthor: https://github.com/dqzg12300")

if __name__=="__main__":
    app=QApplication(sys.argv)
    kmain = kmainForm()
    kmain.show()
    sys.exit(app.exec_())

