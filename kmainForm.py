# coding=utf-8
import datetime
import re
import sys
from time import sleep

from PyQt5 import uic, QtWidgets,QtCore
from PyQt5.QtCore import Qt, QPoint, QTranslator
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStatusBar, QLabel, QMessageBox, QHeaderView, \
    QTableWidgetItem, QMenu, QAction, QActionGroup, qApp

from forms import SelectPackage
from forms.AntiFrida import antiFridaForm
from forms.CallFunction import callFunctionForm
from forms.Custom import customForm
from forms.DumpAddress import dumpAddressForm
from forms.DumpSo import dumpSoForm
from forms.Fart import fartForm
from forms.FartBin import fartBinForm
from forms.JniTrace import jnitraceForm
from forms.Natives import nativesForm
from forms.Patch import patchForm
from forms.Port import portForm
from forms.SearchMemory import searchMemoryForm
from forms.SpawnAttach import spawnAttachForm
from forms.Stalker import stalkerForm
from forms.StalkerOp import stalkerMatchForm
from forms.Tuoke import tuokeForm
from forms.Wallbreaker import wallBreakerForm
from forms.Wifi import wifiForm
from forms.ZenTracer import zenTracerForm
from ui.kmain import Ui_MainWindow
from utils import LogUtil, CmdUtil, FileUtil
import json, os, threading, frida
import platform

import TraceThread
from utils.IniUtil import IniConfig

conf=IniConfig()

def restart_real_live():
    qApp.exit(1207)

class kmainForm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(kmainForm, self).__init__(parent)
        self.setupUi(self)
        self.initUi()
        self.hooksData = {}
        self.th = TraceThread.Runthread(self.hooksData, "", False,self.connType)
        self.updateCmbHooks()
        self.outlogger = LogUtil.Logger('all.txt', level='debug')


    def initUi(self):
        self.setWindowOpacity(0.93)
        # 日志目录
        if os.path.exists("./logs") == False:
            os.makedirs("./logs")
        if os.path.exists("./pcap") == False:
            os.makedirs("./pcap")
        # 缓存数据目录 modules  classes
        if os.path.exists("./tmp") == False:
            os.makedirs("./tmp")
        # 从手机下载dumpdex脱壳的数据
        if os.path.exists("./dumpdex") == False:
            os.makedirs("./dumpdex")
        if os.path.exists("./fartdump") == False:
            os.makedirs("./fartdump")
        # 自定义脚本目录
        if os.path.exists("./custom") == False:
            os.makedirs("./custom")
        # 保存当前hook策略的目录
        if os.path.exists("./hooks") == False:
            os.makedirs("./hooks")

        projectPath = os.path.dirname(os.path.abspath(__file__))
        if platform.system() != "Windows":
            CmdUtil.execCmd("chmod 0777 " + projectPath + "/sh/linux/*")
            CmdUtil.execCmd("chmod 0777 " + projectPath + "/sh/mac/*")
        self.statusBar = QStatusBar()
        self._translate = QtCore.QCoreApplication.translate
        self.labStatus = QLabel(self._translate("kmainForm",'当前状态:未连接'))
        self.setStatusBar(self.statusBar)
        self.statusBar.addPermanentWidget(self.labStatus, stretch=1)
        self.labPackage = QLabel('')
        self.statusBar.addPermanentWidget(self.labPackage, stretch=2)

        self.languageGroup = QActionGroup(self)
        self.languageGroup.addAction(self.actionChina)
        self.languageGroup.addAction(self.actionEnglish)

        self.fridaName = conf.read("kmain", "frida_name")
        self.customPort = conf.read("kmain", "usb_port")
        self.address=conf.read("kmain", "wifi_addr")
        self.wifi_port = conf.read("kmain", "wifi_port")
        language = conf.read("kmain", "language")
        if language == "China":
            self.actionChina.setChecked(True)
        else:
            self.actionEnglish.setChecked(True)


        if self.actionChina.isChecked():
            typePath="./config/type.json"
        else:
            typePath = "./config/type_en.json"
        with open(typePath, "r", encoding="utf8") as typeFile:
            self.typeData = json.loads(typeFile.read())

        self.actionAttach.triggered.connect(self.actionAttachStart)
        self.actionSpawn.triggered.connect(self.actionSpawnStart)
        self.actionAttachName.triggered.connect(self.actionAttachNameStart)
        self.actionabort.triggered.connect(self.actionAbort)
        self.actionStop.setEnabled(False)
        self.actionStop.triggered.connect(self.StopAttach)
        self.actionClearTmp.triggered.connect(self.ClearTmp)
        self.actionClearLogs.triggered.connect(self.ClearLogs)
        self.actionClearOutlog.triggered.connect(self.ClearOutlog)
        self.actionPushFartSo.triggered.connect(self.PushFartSo)
        self.actionClearHookJson.triggered.connect(self.ClearHookJson)
        self.actionPullDumpDexRes.triggered.connect(self.PullDumpDex)
        self.actionPushFridaServer.triggered.connect(self.PushFridaServer)
        self.actionPushFridaServerX86.triggered.connect(self.PushFridaServerX86)
        self.actionPullFartRes.triggered.connect(self.PullFartRes)
        self.actionFrida32Start.triggered.connect(self.Frida32Start)
        self.actionFrida64Start.triggered.connect(self.Frida64Start)
        self.actionSuC.triggered.connect(self.ChangeSuC)
        self.actionSu0.triggered.connect(self.ChangeSu0)
        self.actionMks0.triggered.connect(self.ChangeMks0)
        self.adbHeadGroup = QActionGroup(self)
        self.adbHeadGroup.addAction(self.actionMks0)
        self.adbHeadGroup.addAction(self.actionSuC)
        self.adbHeadGroup.addAction(self.actionSu0)

        self.actionFridax86Start.triggered.connect(self.FridaX86Start)
        self.actionFridax64Start.triggered.connect(self.FridaX64Start)
        self.actionPullApk.triggered.connect(self.PullApk)

        self.connectHeadGroup = QActionGroup(self)
        self.connectHeadGroup.addAction(self.actionWifi)
        self.connectHeadGroup.addAction(self.actionUsb)
        self.actionWifi.triggered.connect(self.WifiConn)
        self.actionUsb.triggered.connect(self.UsbConn)
        self.actionVer14.triggered.connect(self.ChangeVer14)
        self.actionVer15.triggered.connect(self.ChangeVer15)
        self.actionVer16.triggered.connect(self.ChangeVer16)
        self.actionEnglish.triggered.connect(self.ChangeEnglish)
        self.actionChina.triggered.connect(self.ChangeChina)

        self.actionChangePort.triggered.connect(self.ChangePort)
        self.verGroup = QActionGroup(self)
        self.verGroup.addAction(self.actionVer14)
        self.verGroup.addAction(self.actionVer15)
        self.verGroup.addAction(self.actionVer16)

        self.btnDumpPtr.clicked.connect(self.dumpPtr)
        self.btnDumpSo.clicked.connect(self.dumpSo)
        self.btnFart.clicked.connect(self.dumpFart)
        self.btnDumpDex.clicked.connect(self.dumpDex)
        self.btnWallbreaker.clicked.connect(self.wallBreaker)
        self.btnCallFunction.clicked.connect(self.callFunction)

        self.chkNetwork.toggled.connect(self.hookNetwork)
        self.chkJni.toggled.connect(self.hookJNI)
        self.chkJavaEnc.toggled.connect(self.hookJavaEnc)
        self.chkHookEvent.toggled.connect(self.hookEvent)
        self.chkRegisterNative.toggled.connect(self.hookRegisterNative)
        self.chkArtMethod.toggled.connect(self.hookArtMethod)
        self.chkLibArt.toggled.connect(self.hookLibArm)
        self.chkSslPining.toggled.connect(self.hookSslPining)

        self.chkAntiDebug.toggled.connect(self.hookAntiDebug)
        self.chkNewJnitrace.toggled.connect(self.hookNewJnitrace)

        self.btnMatchMethod.clicked.connect(self.matchMethod)

        self.btnNatives.clicked.connect(self.hookNatives)
        self.btnStalker.clicked.connect(self.stalker)
        self.btnCustom.clicked.connect(self.custom)
        self.btnTuoke.clicked.connect(self.tuoke)
        self.btnPatch.clicked.connect(self.patch)

        self.txtModule.textChanged.connect(self.changeModule)
        self.txtClass.textChanged.connect(self.changeClass)
        self.txtSymbol.textChanged.connect(self.changeSymbol)
        self.txtMethod.textChanged.connect(self.changeMethod)

        self.btnSaveHooks.clicked.connect(self.saveHooks)
        self.btnImportHooks.clicked.connect(self.importHooks)
        self.btnLoadHooks.clicked.connect(self.loadHooks)
        self.btnClearHooks.clicked.connect(self.clearHooks)
        if self.actionChina.isChecked():
            self.header = ["名称", "类名/模块名", "函数", "备注"]
        else:
            self.header = ["name", "class or func", "func", "bak"]
        self.tabHooks.setColumnCount(4)
        self.tabHooks.setHorizontalHeaderLabels(self.header)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabHooks.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabHooks.customContextMenuRequested[QPoint].connect(self.rightMenuShow)

        self.btnMethod.clicked.connect(self.searchMethod)
        self.btnExport.clicked.connect(self.searchExport)
        self.btnSymbol.clicked.connect(self.searchSymbol)
        self.btnSymbolClear.clicked.connect(self.clearSymbol)
        self.btnMethodClear.clicked.connect(self.clearMethod)
        self.txtMethod.textChanged.connect(self.changeMethod)
        self.txtSymbol.textChanged.connect(self.changeSymbol)

        self.btnFlush.clicked.connect(self.appInfoFlush)
        self.btnFartOpBin.clicked.connect(self.fartOpBin)
        self.btnOpStalkerLog.clicked.connect(self.stalkerOpLog)
        # self.btnOpFartLog.clicked.connect(self.fartOpLog)
        self.btnMemSearch.clicked.connect(self.searchMem)
        self.btnAntiFrida.clicked.connect(self.antiFrida)



        self.dumpForm = dumpAddressForm()
        self.jniform = jnitraceForm()
        self.newJniform=jnitraceForm()
        self.zenTracerForm = zenTracerForm()
        self.nativesForm = nativesForm()
        self.spawnAttachForm = spawnAttachForm()
        self.stalkerForm = stalkerForm()
        self.pform = patchForm()
        self.dumpSoForm = dumpSoForm()
        self.fartForm = fartForm()
        self.wallBreakerForm = wallBreakerForm()
        self.customForm = customForm()
        self.callFunctionForm = callFunctionForm()
        self.fartBinForm = fartBinForm()
        self.stalkerMatchForm = stalkerMatchForm()
        self.wifiForm=wifiForm()
        self.portForm = portForm()
        self.searchMemForm= searchMemoryForm()
        self.antiFdForm=antiFridaForm()

        self.modules = None
        self.classes = None
        self.symbols = None
        self.methods = None

        self.chkNetwork.tag = "r0capture"
        self.chkJni.tag = "jnitrace"
        self.chkJavaEnc.tag = "javaEnc"
        self.chkSslPining.tag = "sslpining"
        self.chkRegisterNative.tag = "RegisterNative"
        self.chkArtMethod.tag = "ArtMethod"
        self.chkLibArt.tag = "libArt"
        self.chkHookEvent.tag = "hookEvent"
        self.connType="usb"

        self.curFridaVer = "14.2.18"
        self.actionVer14.setChecked(True)


        # 16.0.8  15.1.9  14.2.18
        # res=CmdUtil.execCmdData("frida --version")
        # if "15." in res:
        #     self.curFridaVer = "15.1.9"
        #     self.actionVer15.setChecked(True)
        # elif "14." in res:
        #     self.curFridaVer = "14.2.18"
        #     self.actionVer14.setChecked(True)
        # elif "16." in res:
        #     self.curFridaVer = "16.0.8"
        #     self.actionVer16.setChecked(True)
        # else:
        #     self.curFridaVer = "15.1.9"
        #     self.actionVer15.setChecked(True)

    def clearSymbol(self):
        self.listSymbol.clear()

    def clearMethod(self):
        self.listMethod.clear()

    def changeMethod(self, data):
        self.listMethod.clear()
        if len(data) > 0:
            for item in self.methods:
                if data in item:
                    self.listMethod.addItem(item)
        else:
            for item in self.methods:
                self.listMethod.addItem(item)

    def changeSymbol(self, data):
        self.listSymbol.clear()
        if len(data) > 0:
            for item in self.symbols:
                if data in item["name"]:
                    self.listSymbol.addItem(item["name"])
        else:
            for item in self.symbols:
                self.listSymbol.addItem(item["name"])

    def searchExport(self):
        if len(self.txtModule.text()) <= 0:
            QMessageBox().information(self, "hint", self._translate("kmainForm","未填写模块名称"))
            return
        postdata = {"type": "export", "baseName": self.txtModule.text().split("----")[0]}
        self.th.searchInfo(postdata)

    def searchSymbol(self):
        if len(self.txtModule.text()) <= 0:
            QMessageBox().information(self, "hint", self._translate("kmainForm","未填写模块名称"))
            return
        postdata = {"type": "symbol", "baseName": self.txtModule.text().split("----")[0]}
        self.th.searchInfo(postdata)

    def searchMethod(self):
        if len(self.txtClass.text()) <= 0:
            QMessageBox().information(self, "hint",self._translate("kmainForm","未填写类型名称"))
            return
        postdata = {"type": "method", "baseName": self.txtClass.text()}
        self.th.searchInfo(postdata)

    def hooksRemove(self):
        for item in self.tabHooks.selectedItems():
            # 因为patch是多个的。所以移除的时候要注意。不然会全部移掉的。
            if self.tabHooks.item(item.row(), 0).text() == "patch":
                removeItemData = self.tabHooks.item(item.row(), 1).text() + self.tabHooks.item(item.row(), 2).text()
                for idx in range(len(self.hooksData["patch"])):
                    hookItem = self.hooksData["patch"][idx]
                    if hookItem["class"] + hookItem["method"] == removeItemData:
                        self.hooksData["patch"].pop(idx)
            else:
                self.hooksData.pop(self.tabHooks.item(item.row(), 0).text())
        self.updateTabHooks()
        self.refreshChecks()

    # 右键菜单
    def rightMenuShow(self):
        rightMenu = QMenu(self.tabHooks)
        removeAction = QAction(self._translate("kmainForm","删除"), self, triggered=self.hooksRemove)
        rightMenu.addAction(removeAction)
        rightMenu.exec_(QCursor.pos())

    # 打印操作日志
    def log(self, logstr):
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        self.txtLogs.appendPlainText(datestr + logstr)

    # 打印输出日志
    def outlog(self, logstr):
        if self.actionConsoleLog.isChecked()==False:
            datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
            self.txtoutLogs.appendPlainText(datestr + logstr)
        self.outlogger.logger.debug(logstr)
        if "default.js init hook success" in logstr:
            QMessageBox().information(self, "hint", self._translate("kmainForm","附加进程成功"))

    # 线程调用脚本结束，并且触发结束信号
    def StopAttach(self):
        self.th.quit()

    def ClearTmp(self):
        path = "./tmp/"
        ls = os.listdir(path)
        for i in ls:
            c_path = os.path.join(path, i)
            os.remove(c_path)

    def ClearLogs(self):
        path = "./logs/"
        ls = os.listdir(path)
        for i in ls:
            c_path = os.path.join(path, i)
            try:
                os.remove(c_path)
            except:
                pass

    def ClearOutlog(self):
        self.txtoutLogs.setPlainText("")

    def PushFartSo(self):
        # 有些手机是用su 0来执行shell命令的。不太懂怎么判断是哪种。
        res = CmdUtil.adbshellCmd("mkdir /data/local/tmp/fart")
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint",self._translate("kmainForm", "操作失败.") + res)
            return
        res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/fart")
        self.log(res)
        if "invalid" in res:
            QMessageBox().information(self, "hint",self._translate("kmainForm",  "设置权限失败。可能是su权限错误，请先cmd切换"))
            return
        res = CmdUtil.adbshellCmd("mkdir /sdcard/fart")
        self.log(res)
        res = CmdUtil.adbshellCmd("chmod 0777 /sdcard/fart")
        self.log(res)

        res = CmdUtil.execCmd("adb push ./lib/fart.so /data/local/tmp/fart/fart.so")
        self.log(res)
        if "file pushed" not in res:
            QMessageBox().information(self, "hint",self._translate("kmainForm", "上传失败,可能未连接设备.")+res)
            return

        res = CmdUtil.execCmd("adb push ./exec/r0gson.dex /data/local/tmp/r0gson.dex")
        self.log(res)
        res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/gson.jar")
        self.log(res)


        res = CmdUtil.execCmd("adb push ./lib/fart64.so /data/local/tmp/fart/fart64.so")
        self.log(res)

        res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/fart/fart.so")
        self.log(res)
        res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/fart/fart64.so")
        self.log(res)
        # 因为好像有些手机不能直接push到/data/app目录。所以先放tmp再拷贝过去
        res = CmdUtil.adbshellCmd("cp /data/local/tmp/fart/fart.so /data/app/")
        self.log(res)
        res = CmdUtil.adbshellCmd("cp /data/local/tmp/fart/fart64.so /data/app/")
        self.log(res)
        QMessageBox().information(self, "hint", self._translate("kmainForm","上传完成"))

    def PullDumpDex(self):
        cmd = ""
        if len(self.th.attachName) > 0:
            pname = self.th.attachName
        else:
            self.spawnAttachForm.flushList()
            res = self.spawnAttachForm.exec()
            if res == 0:
                return
            pname = self.spawnAttachForm.packageName
        cmd = "adb pull /data/data/%s/files/dump_dex_%s ./dumpdex/%s/" % (pname, pname, pname)
        res = CmdUtil.execCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", self._translate("kmainForm","下载失败.") + res)
            return
        if "not found" in res:
            QMessageBox().information(self, "hint",self._translate("kmainForm","下载失败.没有连接设备") )
            return
        QMessageBox().information(self, "hint", self._translate("kmainForm","下载完成") )

    def PushFridaServer(self):
        try:
            name32=""
            name64=""
            if self.fridaName!="":
                name32=self.fridaName+"32"
                name64=self.fridaName+"64"

            res = CmdUtil.execCmd(f"adb push ./exec/frida-server-{self.curFridaVer}-android-arm /data/local/tmp/"+name32)
            self.log(res)
            if "error" in res:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传失败.") + res)
                return
            res = CmdUtil.execCmd(f"adb push ./exec/frida-server-{self.curFridaVer}-android-arm64 /data/local/tmp/"+name64)
            self.log(res)
            if "file pushed" not in res:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传失败,可能未连接设备.") + res)
                return
            if self.fridaName!="":
                res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/"+self.fridaName+"*")
            else:
                res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/frida*")
            self.log(res)
            if "invalid" in res:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传完成，但是设置权限失败。可能是su权限错误，请先cmd切换."))
            else:
                QMessageBox().information(self, "hint", self._translate("kmainForm", "上传完成."))
        except Exception as ex:
            QMessageBox().information(self, "hint",  self._translate("kmainForm", "上传异常.") + str(ex))

    def PushFridaServerX86(self):
        try:
            res = CmdUtil.execCmd(f"adb push ./exec/frida-server-{self.curFridaVer}-android-x86 /data/local/tmp")
            self.log(res)
            if "error" in res:
                QMessageBox().information(self, "hint", self._translate("kmainForm", "上传失败.") + res)
                return
            res = CmdUtil.execCmd(f"adb push ./exec/frida-server-{self.curFridaVer}-android-x86_64 /data/local/tmp")
            self.log(res)
            if "file pushed" and "bytes in" not in res:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传失败,可能未连接设备.")   + res)
                return
            res = CmdUtil.adbshellCmd("chmod 0777 /data/local/tmp/frida*")
            self.log(res)
            if "invalid" in res:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传完成，但是设置权限失败。可能是su权限错误，请先cmd切换."))
            else:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传完成."))
        except Exception as ex:
            QMessageBox().information(self, "hint", self._translate("kmainForm", "上传异常.") + str(ex))

    def PullFartRes(self):
        cmd = ""
        if len(self.th.attachName) > 0:
            pname = self.th.attachName
        else:
            self.spawnAttachForm.flushList()
            res = self.spawnAttachForm.exec()
            if res == 0:
                return
            pname = self.spawnAttachForm.packageName
        cmd = "rm /sdcard/fart -rf"
        res = CmdUtil.adbshellCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
            return
        cmd = "mkdir -p /sdcard/fart/%s " % pname
        res = CmdUtil.adbshellCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
            return
        cmd = "cp /data/data/%s/fart/ /sdcard/fart/%s/ -rf" % (pname, pname)
        res = CmdUtil.adbshellCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
            return
        cmd = "adb pull /sdcard/fart/%s/ ./fartdump/%s/" % (pname, pname)
        res = CmdUtil.execCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
            return
        if "not found" in res:
            QMessageBox().information(self, "hint",self._translate("kmainForm",  "下载失败.没有连接设备") )
            return
        QMessageBox().information(self, "hint", self._translate("kmainForm",  "下载完成"))

    def PullApk(self):
        cmdtp = "grep"
        if platform.system() == "Windows":
            cmdtp = "findstr"
        cmd = "adb shell dumpsys window | %s mCurrentFocus" % cmdtp
        res = CmdUtil.execCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
            return
        lines=res.split("\n")
        for tmpline in lines:
            if len(tmpline)>0:
                line=tmpline
        line = re.split(r"[ /]", res)
        if len(line) < 5:
            QMessageBox().information(self, "hint",  self._translate("kmainForm", "匹配失败,") + res)
            return
        packageName = line[4]
        if "StatusBar" in packageName:
            QMessageBox().information(self, "hint",self._translate("kmainForm", "匹配失败,手机可能锁屏中,请解锁"))
            return
        cmd = "adb shell dumpsys activity -p %s|%s baseDir" % (packageName, cmdtp)
        res = CmdUtil.execCmd(cmd)
        self.log(res)
        if "baseDir" not in res:
            QMessageBox().information(self, "hint",self._translate("kmainForm", "匹配失败,可能未连接手机"))
            return
        lines = res.split("\n")
        for tmpline in lines:
            if packageName in tmpline:
                line = tmpline
        match = re.search(r"baseDir=(/data/app/%s.+)" % packageName, line)
        if match == None:
            QMessageBox().information(self, "hint",self._translate("kmainForm", "匹配失败,") + res)
            return
        baseDir = match.group(1)
        if os.path.exists("./apks") == False:
            os.makedirs("./apks")
        cmd = "adb pull %s ./apks/%s.apk" % (baseDir, packageName)
        res = CmdUtil.execCmd(cmd)
        self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
            return
        QMessageBox().information(self, "hint", packageName +self._translate("kmainForm", ".apk下载成功"))



    def ReplaceSh(self,rfile,wfile,name):
        data = FileUtil.readFile(rfile)
        adb = "adb"
        if platform.system() == "Darwin":
            adb = "%adb%"
        if self.connType == "wifi":
            data = data.replace("%fridaName%", name + " -l 0.0.0.0:" + self.wifi_port)

            data=data.replace("%customPort%",f"{adb} forward tcp:{self.customPort} tcp:{self.customPort}")
        elif self.connType == "usb":
            if self.customPort!=None and len(self.customPort)>0:
                data = data.replace("%fridaName%", name + " -l 0.0.0.0:" + self.customPort)
                data=data.replace("%customPort%",f"{adb} forward tcp:{self.customPort} tcp:{self.customPort}")
            else:
                data = data.replace("%fridaName%", name)
                data = data.replace("%customPort%","")
        if self.actionSu0.isChecked():
            data = data.replace("%sumod%", "su 0")
        elif self.actionSuC.isChecked():
            data = data.replace("%sumod%", "su -c")
        elif self.actionMks0.isChecked():
            data = data.replace("%sumod%", "mks 0")
        
        if platform.system()=="Darwin":
            adbPath= CmdUtil.execCmdData("which adb")
            data=data.replace("%adb%",adbPath.replace("\n",""))
        if self.fridaName != None and len(self.fridaName) > 0:
            data = data.replace("%fName%", self.fridaName)
        FileUtil.writeFile(wfile,data)

    def ShStart(self, name):
        projectPath = os.path.abspath("./")

        if platform.system() == "Windows":
            shfile = "%s\\sh\\tmp\\frida_win.tmp"% (projectPath)
            savefile="%s\\sh\\tmp\\frida_win.bat"% (projectPath)
            self.ReplaceSh(shfile,savefile,name)
            cmd = r"start " + savefile
        elif platform.system() == 'Linux':
            shfile = "%s/sh/tmp/frida_linux.tmp"% (projectPath)
            savefile = "%s/sh/tmp/frida_linux.sh" % (projectPath)
            self.ReplaceSh(shfile, savefile, name)
            CmdUtil.execCmd("chmod 0777 " + projectPath + "/sh/tmp/*")
            cmd = "gnome-terminal -e 'bash -c \"%s; exec bash\"'" % savefile
        else:
            shfile = "%s/sh/tmp/frida_mac.tmp"% (projectPath)
            savefile = "%s/sh/tmp/frida_mac.sh" % (projectPath)
            self.ReplaceSh(shfile, savefile, name)
            CmdUtil.execCmd("chmod 0777 " + projectPath + "/sh/tmp/*")
            cmd = "bash -c " + savefile
        os.system(cmd)

    def ChangeVer14(self, checked):
        if checked==False:
            return
        self.curFridaVer="14.2.18"

    def ChangeVer15(self, checked):
        if checked==False:
            return
        self.curFridaVer = "15.1.9"

    def ChangeVer16(self, checked):
        if checked==False:
            return
        self.curFridaVer = "16.0.8"

    def ChangeEnglish(self,checked):
        if checked==False:
            return
        conf.write("kmain","language","English")
        reply = QMessageBox.question(self,
                                     "hint",
                                     self._translate("kmainForm","是否立刻重启应用生效？"),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply:
            restart_real_live()
    def ChangeChina(self,checked):
        if checked==False:
            return
        conf.write("kmain", "language", "China")
        reply = QMessageBox.question(self,
                                     "hint",
                                     self._translate("kmainForm", "是否立刻重启应用生效？"),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply:
            restart_real_live()
    
    def Frida32Start(self):
        if self.fridaName !=None and len(self.fridaName)>0:
            name=self.fridaName+"32"
        else:
            name=f"frida-server-{self.curFridaVer}-android-arm"
        self.ShStart(name)

    def Frida64Start(self):
        if self.fridaName !=None and len(self.fridaName)>0:
            name=self.fridaName+"64"
        else:
            name=f"frida-server-{self.curFridaVer}-android-arm64"
        self.ShStart(name)

    def FridaX86Start(self):
        if self.fridaName !=None and len(self.fridaName)>0:
            name=self.fridaName+"64"
        else:
            name=f"frida-server-{self.curFridaVer}-android-x86"
        self.ShStart(name)

    def FridaX64Start(self):
        if self.fridaName !=None and len(self.fridaName)>0:
            name=self.fridaName+"64"
        else:
            name=f"frida-server-{self.curFridaVer}-android-x86_64"
        self.ShStart(name)

    def changeCmdType(self,data):
        CmdUtil.cmdhead = data

    def ChangeSuC(self, checked):
        if checked==False:
            return
        self.changeCmdType(self.actionSuC.text())

    def ChangeSu0(self, checked):
        if checked==False:
            return
        self.changeCmdType(self.actionSu0.text())

    def ChangeMks0(self,checked):
        if checked==False:
            return
        self.changeCmdType(self.actionMks0.text())

    def ClearHookJson(self):
        path = "./hooks/"
        ls = os.listdir(path)
        for i in ls:
            c_path = os.path.join(path, i)
            try:
                os.remove(c_path)
            except:
                pass
        self.updateCmbHooks()

    # 进程结束时的状态切换，和打印e
    def taskOver(self):
        self.log("附加进程结束")
        self.changeAttachStatus(False)
        QMessageBox().information(self, "hint",self._translate("kmainForm","成功停止附加进程") )


    # 这是附加结束时的状态栏显示包名
    def attachOver(self, name):
        if "ERROR" in name:
            QMessageBox().information(self, "hint",self._translate("kmainForm","附加失败.")+name)
            self.changeAttachStatus(False)
            return
        tmppath = "./tmp/spawnPackage.txt"
        mode = "r+"
        if os.path.exists(tmppath) == False:
            mode = "w+"
        with open(tmppath, mode) as packageFile:
            packageData = packageFile.read()
            fsize = packageFile.tell()
            packageFile.seek(fsize)
            if name not in packageData:
                packageFile.write(name + "\n")
        self.labPackage.setText(name)

    def getFridaDevice(self):
        if self.connType=="usb":
            if self.customPort != None and len(self.customPort) > 0:
                str_host = "127.0.0.1:%s" % (self.customPort)
                manager = frida.get_device_manager()
                device = manager.add_remote_device(str_host)
                return device
            else:
                return frida.get_usb_device()
        elif self.connType=="wifi":
            str_host = "%s:%s" % (self.address, self.wifi_port)
            manager = frida.get_device_manager()
            device = manager.add_remote_device(str_host)
            return device

    # 启动附加
    def actionAttachStart(self):
        self.log("actionAttach")
        try:
            if self.connType=="wifi":
                if len(self.address)<8 or len(self.wifi_port)<0:
                    QMessageBox().information(self, "hint", self._translate("kmainForm","当前为wifi连接,但是未设置地址或端口"))
                    return

            # 查下进程。能查到说明frida_server开启了
            device = self.getFridaDevice()
            device.enumerate_processes()
            self.changeAttachStatus(True)
            self.th = TraceThread.Runthread(self.hooksData, "", False,self.connType)
            self.th.address=self.address
            self.th.port=self.wifi_port
            self.th.customPort=self.customPort
            self.th.taskOverSignel.connect(self.taskOver)
            self.th.loggerSignel.connect(self.log)
            self.th.outloggerSignel.connect(self.outlog)
            self.th.loadAppInfoSignel.connect(self.loadAppInfo)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.searchAppInfoSignel.connect(self.searchAppInfoRes)
            self.th.searchMemorySignel.connect(self.searchMemResp)
            self.th.setBreakSignel.connect(self.setBreakResp)
            self.th.attachType="attachCurrent"
            self.th.start()
            if len(self.hooksData) <= 0:
                # QMessageBox().information(self, "提示", "未设置hook选项")
                self.log(self._translate("kmainForm","未设置hook选项"))
        except Exception as ex:
            self.log(self._translate("kmainForm","附加异常")+".err:" + str(ex))
            QMessageBox().information(self, "hint", self._translate("kmainForm","附加异常")+"." + str(ex))

    # spawn的方式附加进程
    def actionSpawnStart(self):
        self.log("actionSpawnStart")
        self.spawnAttachForm.flushList()
        res = self.spawnAttachForm.exec()
        if res == 0:
            return
        try:
            if self.connType=="wifi" and (len(self.address)<8 or len(self.wifi_port)<=0):
                QMessageBox().information(self, "hint",self._translate("kmainForm","当前为wifi连接,但是未设置地址或端口"))
                return
            # 查下进程。能查到说明frida_server开启了
            device = self.getFridaDevice()
            device.enumerate_processes()
            self.changeAttachStatus(True)
            self.th = TraceThread.Runthread(self.hooksData, self.spawnAttachForm.packageName, True,self.connType)
            self.th.address=self.address
            self.th.port=self.wifi_port
            self.th.customPort = self.customPort
            self.th.taskOverSignel.connect(self.taskOver)
            self.th.loggerSignel.connect(self.log)
            self.th.outloggerSignel.connect(self.outlog)
            self.th.loadAppInfoSignel.connect(self.loadAppInfo)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.searchAppInfoSignel.connect(self.searchAppInfoRes)
            self.th.searchMemorySignel.connect(self.searchMemResp)
            self.th.attachType="spawn"

            self.th.start()
            if len(self.hooksData) <= 0:
                # QMessageBox().information(self, "提示", "未设置hook选项")
                self.log(self._translate("kmainForm","未设置hook选项"))
        except Exception as ex:
            self.log(self._translate("kmainForm","附加异常")+".err:" + str(ex))
            QMessageBox().information(self, "hint", self._translate("kmainForm","附加异常.") + str(ex))

    # 修改ui的状态表现
    def changeAttachStatus(self, isattach):
        if isattach:
            self.menuAttach.setEnabled(False)
            self.actionStop.setEnabled(True)
            self.labStatus.setText( self._translate("kmainForm","当前状态:已连接") )
        else:
            self.menuAttach.setEnabled(True)
            self.actionStop.setEnabled(False)
            self.labStatus.setText(self._translate("kmainForm","当前状态:未连接") )
            self.labPackage.setText("")

    # 根据进程名进行附加进程
    def actionAttachNameStart(self):
        self.log("actionAttachName")
        try:
            if self.connType=="wifi" and (len(self.address)<8 or len(self.wifi_port)):
                QMessageBox().information(self, "hint", self._translate("kmainForm","当前为wifi连接,但是未设置地址或端口"))
                return
            device = self.getFridaDevice()
            process = device.enumerate_processes()
            selectPackageForm = SelectPackage.selectPackageForm()
            selectPackageForm.setPackages(process)
            res = selectPackageForm.exec()
            if res == 0:
                return
            self.changeAttachStatus(True)
            self.th = TraceThread.Runthread(self.hooksData, selectPackageForm.packageName, False,self.connType)
            self.th.address=self.address
            self.th.port=self.wifi_port
            self.th.taskOverSignel.connect(self.taskOver)
            self.th.loggerSignel.connect(self.log)
            self.th.outloggerSignel.connect(self.outlog)
            self.th.loadAppInfoSignel.connect(self.loadAppInfo)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.searchAppInfoSignel.connect(self.searchAppInfoRes)
            self.th.searchMemorySignel.connect(self.searchMemResp)
            self.th.attachType = "attach"
            self.th.start()
        except Exception as ex:
            self.log(self._translate("kmainForm","附加异常")+".err:" + str(ex))
            QMessageBox().information(self, "hint", self._translate("kmainForm","附加异常.") + str(ex))

    def ChangePort(self):
        self.portForm.txtFridaName.setText(self.fridaName)
        self.portForm.txtPort.setText(self.customPort)
        res=self.portForm.exec()
        if res==0:
            return
        self.fridaName = self.portForm.fridaName
        self.customPort = self.portForm.port
        conf.write("kmain", "frida_name", self.fridaName)
        conf.write("kmain", "usb_port", self.customPort)

    def WifiConn(self):
        self.wifiForm.txtAddress.setText(self.address)
        self.wifiForm.txtPort.setText(self.wifi_port)
        res=self.wifiForm.exec()
        if res==0 :
            return
        self.connType="wifi"
        self.address=self.wifiForm.address
        self.wifi_port=self.wifiForm.port
        conf.write("kmain", "wifi_addr", self.address)
        conf.write("kmain", "wifi_port", self.wifi_port)
    def UsbConn(self):
        self.connType="usb"
        self.actionUsb.setChecked(True)
        self.actionWifi.setChecked(False)

    # 是否附加进程了
    def isattach(self):
        if "未连接" in self.labStatus.text():
            self.log(self._translate("kmainForm", "Error:还未附加进程"))
            QMessageBox().information(self, "hint", self._translate("kmainForm", "Error:未附加进程"))
            return False
        return True

    # ====================start======需要附加后才能使用的功能,基本都是在内存中查数据================================



    def dumpPtr(self):
        if self.isattach() == False:
            return
        if self.modules == None or len(self.modules) <= 0:
            self.log(self._translate("kmainForm", "Error:未附加进程或操作太快,请稍等"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","Error:未附加进程或操作太快,请稍等"))
            return
        mods = []
        for item in self.modules:
            mods.append(item["name"])
        self.log(self._translate("kmainForm","dump指定地址"))
        self.dumpForm.modules = mods
        self.dumpForm.initData()
        res = self.dumpForm.exec()
        if res == 0:
            return
        # 设置了module就会以module为基址再加上address去dump。如果不设置module。就会直接dump指定的address
        postdata = {"moduleName": self.dumpForm.moduleName, "address": self.dumpForm.address,
                    "dumpType": self.dumpForm.dumpType,
                    "size": self.dumpForm.size}
        self.th.dumpPtr(postdata)

    def dumpSo(self):
        if self.isattach() == False:
            return
        if self.modules == None or len(self.modules) <= 0:
            self.log(self._translate("kmainForm","Error:未附加进程或操作太快,请稍等"))
            QMessageBox().information(self, "hint",self._translate("kmainForm", "Error:未附加进程或操作太快,请稍等"))
            return
        mods = []
        for item in self.modules:
            mods.append(item["name"])
        self.log("dump so")
        self.dumpSoForm.modules = mods
        self.dumpSoForm.initData()
        res = self.dumpSoForm.exec()
        if res == 0:
            return
        postdata = {"moduleName": self.dumpSoForm.moduleName}
        self.th.dumpSoPtr(postdata)

    def dumpFart(self):
        if self.isattach() == False:
            return
        if "tuoke" not in self.hooksData:
            self.log(self._translate("kmainForm", "Error:未勾选脱壳脚本"))
            QMessageBox().information(self, "hint",self._translate("kmainForm", "Error:未勾选脱壳脚本"))
            return
        if self.hooksData["tuoke"]["class"] != "fart":
            self.log(self._translate("kmainForm", "Error:未勾选fart脱壳脚本"))
            QMessageBox().information(self, "hint",self._translate("kmainForm", "Error:未勾选fart脱壳脚本"))
            return
        CmdUtil.adbshellCmd("mkdir /data/data/"+self.labPackage.text()+"/fart/")
        res = self.fartForm.exec()
        if res == 0:
            return
        t1 = threading.Thread(target=self.th.fart, args=(res, self.fartForm.classes))
        t1.start()

    def dumpDex(self):
        if self.isattach() == False:
            return
        if "tuoke" not in self.hooksData:
            self.log(self._translate("kmainForm", "Error:未勾选脱壳脚本"))
            QMessageBox().information(self, "hint", self._translate("kmainForm", "Error:未勾选脱壳脚本"))
            return
        if self.hooksData["tuoke"]["class"] != "dumpdexclass":
            self.log(self._translate("kmainForm", "Error:未勾选dumpdexclass脱壳脚本"))
            QMessageBox().information(self, "hint", self._translate("kmainForm", "Error:未勾选dumpdexclass脱壳脚本"))
            return
        t1 = threading.Thread(target=self.th.dumpdex)
        t1.start()

    def wallBreaker(self):
        if self.isattach() == False:
            return
        if self.classes == None or len(self.classes) <= 0:
            self.log(self._translate("kmainForm", "Error:未附加进程或操作太快,请稍等"))
            QMessageBox().information(self, "hint",self._translate("kmainForm", "未附加进程或操作太快,请稍等") )
            return
        self.wallBreakerForm.classes = self.classes
        self.wallBreakerForm.api = self.th.default_script.exports
        self.wallBreakerForm.initData()
        self.wallBreakerForm.show()

    def callFunction(self):
        if self.isattach() == False:
            return
        if "custom" not in self.hooksData:
            self.log(self._translate("kmainForm","Error:未使用自定义脚本,无主动调用函数"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","Error:未使用自定义脚本,无主动调用函数"))
            return
        if len(self.th.customCallFuns) <= 0:
            self.log(self._translate("kmainForm","Error:自定义脚本中未找到主动调用函数"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","Error:自定义脚本中未找到主动调用函数"))
            return
        self.callFunctionForm.api = self.th.default_script.exports
        self.callFunctionForm.callMethods = self.th.customCallFuns
        self.callFunctionForm.initData()
        self.callFunctionForm.show()

    def setBreakResp(self,pdata):
        self.searchMemForm.my_message_handler(pdata)

    def searchMemResp(self, typeName,data):
        if typeName == "searchMem":
            self.searchMemForm.appendHistory(data)
        elif typeName == "hexdump":
            self.searchMemForm.appendResult("\n"+data)
        else:
            self.searchMemForm.appendResult(data)
    def searchMem(self):
        if self.isattach() == False:
            return
        self.searchMemForm.th = self.th
        self.searchMemForm.init()
        self.searchMemForm.show()


    # ====================end======需要附加后才能使用的功能,基本都是在内存中查数据================================

    # ====================start======附加前使用的功能,基本都是在内存中查数据================================

    def hook_add(self, chk, typeStr):
        if chk:
            self.hooksData[typeStr] = self.typeData[typeStr]
            self.updateTabHooks()
        else:
            if typeStr in self.hooksData:
                self.hooksData.pop(typeStr)
                self.updateTabHooks()

    def chk_hook_insert(self,checked,typeStr,msg):
        self.hook_add(checked, typeStr)
        if checked:
            self.log("hook "+msg)
        else:
            self.log(self._translate("kmainForm","取消hook ")+msg)

    def hookJNI(self, checked):
        typeStr = "jnitrace"
        if checked:
            self.log("hook jni")
        else:
            self.log(self._translate("kmainForm","取消hook jni"))
            if typeStr in self.hooksData:
                self.hooksData.pop(typeStr)
                self.updateTabHooks()
            return
        self.jniform.flushCmb()
        res = self.jniform.exec()
        if res == 0:
            self.chkJni.setChecked(False)
            return
        jniHook = {"class": self.jniform.moduleName, "method": self.jniform.methodName,
                   "offset":self.jniform.offset,
                   "bak": self._translate("kmainForm","jni trace(不打印详细参数和返回值结果)")}
        self.hooksData[typeStr] = jniHook
        self.updateTabHooks()

    def hookNetwork(self, checked):
        self.chk_hook_insert(checked,"r0capture",self._translate("kmainForm","网络相关"))

    def hookJavaEnc(self, checked):
        self.chk_hook_insert(checked, "javaEnc", self._translate("kmainForm","java的算法加解密所有函数"))

    def hookEvent(self, checked):
        self.chk_hook_insert(checked, "hookEvent",self._translate("kmainForm", "控件的点击事件"))

    def hookRegisterNative(self, checked):
        self.chk_hook_insert(checked, "RegisterNative", "RegisterNative")

    def hookArtMethod(self, checked):
        self.chk_hook_insert(checked, "ArtMethod", "ArtMethod")

    def hookLibArm(self, checked):
        self.chk_hook_insert(checked, "libArm", "libArm")

    def hookSslPining(self, checked):
        self.chk_hook_insert(checked, "sslpining", "sslpining")

    def hookAntiDebug(self,checked):
        self.chk_hook_insert(checked, "anti_debug",self._translate("kmainForm", "简单一键反调试"))

    def hookNewJnitrace(self,checked):
        typeStr = "FCAnd_jnitrace"
        if checked:
            self.log("hook jni")
        else:
            self.log(self._translate("kmainForm", "取消hook jni"))
            if typeStr in self.hooksData:
                self.hooksData.pop(typeStr)
                self.updateTabHooks()
            return
        self.newJniform.checkData=False
        self.newJniform.flushCmb()
        res = self.newJniform.exec()
        if res == 0:
            self.chkJni.setChecked(False)
            return
        jniHook = {"class": self.newJniform.moduleName, "method": self.newJniform.methodName,
                   "offset":self.newJniform.offset,
                   "bak": self._translate("kmainForm","FCAnd_jnitrace有详细的打印细节")}
        self.hooksData[typeStr] = jniHook
        self.updateTabHooks()
        # self.chk_hook_insert(checked, "FCAnd_jnitrace", "新的jnitrace")

    def matchMethod(self):
        self.zenTracerForm.flushCmb()
        self.zenTracerForm.exec()
        self.log(self._translate("kmainForm","根据函数名trace hook"))
        if len(self.zenTracerForm.traceClass) <= 0:
            return
        # matchHook={"class":mform.className,"method":mform.methodName,"bak":"匹配指定类中的指定函数.无类名则hook所有类中的指定函数.无函数名则hook类的所有函数"}
        typeStr = "ZenTracer"
        stack = ""
        hookInit = ""
        isMatch = ""
        isMatchMethod = ""
        if self.zenTracerForm.chkStack.isChecked():
            stack = "1"
        if self.zenTracerForm.chkInit.isChecked():
            hookInit = "1"
        if self.zenTracerForm.chkMatch.isChecked():
            isMatch = "1"
        if self.zenTracerForm.chkMatchMethod.isChecked():
            isMatchMethod = "1"
        classNames = ",".join(self.zenTracerForm.traceClass)
        methodNames = ",".join(self.zenTracerForm.traceMethods)
        matchHook = {"class": classNames, "method": methodNames,
                     "bak": self._translate("kmainForm","ZenTracer的改造功能,匹配类和函数进行批量hook"),
                     "traceClass": self.zenTracerForm.traceClass, "traceBClass": self.zenTracerForm.traceBClass,
                     "traceMethod": self.zenTracerForm.traceMethods, "traceBMethod": self.zenTracerForm.traceBMethods,
                     "stack": stack, "hookInit": hookInit, "isMatch": isMatch, "isMatchMethod": isMatchMethod}
        self.hooksData[typeStr] = matchHook
        self.updateTabHooks()

    def hookNatives(self):
        self.nativesForm.flushCmb()
        res = self.nativesForm.exec()
        if res == 0:
            return
        self.log(self._translate("kmainForm","批量hook native的sub函数"))
        matchHook = {"class": self.nativesForm.moduleName, "method": self.nativesForm.methods,
                     "bak":self._translate("kmainForm","批量匹配sub函数,使用较通用的方式打印参数.") }
        typeStr = "match_sub"
        self.hooksData[typeStr] = matchHook
        self.updateTabHooks()

    def stalker(self):
        self.log("stalker")
        self.stalkerForm.flushCmb()
        res = self.stalkerForm.exec()
        if res == 0:
            return
        method = self.stalkerForm.symbol + " " + self.stalkerForm.offset
        matchHook = {"class": self.stalkerForm.moduleName, "method": method.strip(),
                     "bak": self._translate("kmainForm","参考自项目sktrace.trace汇编并打印寄存器值"),
                     "symbol": self.stalkerForm.symbol, "offset": self.stalkerForm.offset}
        typeStr = "stakler"
        self.hooksData[typeStr] = matchHook
        self.updateTabHooks()

    def custom(self):
        self.log("custom")
        self.customForm.initData()
        self.customForm.exec()
        if len(self.customForm.customHooks) > 0:
            self.hooksData["custom"] = []
            for item in self.customForm.customHooks:
                self.hooksData["custom"].append({"class": item["name"], "method": item["fileName"],
                                                 "bak": item["bak"], "fileName": item["fileName"]})
                self.updateTabHooks()
        else:
            if "custom" in self.hooksData:
                self.hooksData.pop("custom")
                self.updateTabHooks()

    def tuoke(self):
        tform = tuokeForm()
        res = tform.exec()
        if res == 0:
            return
        self.log(self._translate("kmainForm","使用脱壳") + tform.tuokeType)
        self.hooksData["tuoke"] = {"class": tform.tuokeType, "method": "", "bak": self.typeData[tform.tuokeType]["bak"]}
        self.updateTabHooks()

    def patch(self):
        self.pform.flushCmb()
        res = self.pform.exec()
        if res == 0:
            return
        self.log("pathch module:" + self.pform.moduleName + "\taddress:" + self.pform.address + "\tdata:" + self.pform.patch)
        patchHook = {"class": self.pform.moduleName, "method": self.pform.address + "|" + self.pform.patch,
                     "bak": self._translate("kmainForm","替换指定地址的二进制数据."), "address": self.pform.address, "code": self.pform.patch}
        typeStr = "patch"
        if typeStr in self.hooksData:
            self.hooksData[typeStr].append(patchHook)
        else:
            self.hooksData[typeStr] = []
            self.hooksData[typeStr].append(patchHook)
        self.updateTabHooks()

    def antiFrida(self):
        self.antiFdForm.exec()
        if self.antiFdForm.antiType=="":
            return
        hookData = {"class": self.antiFdForm.antiType, "method": self.antiFdForm.keyword,"isExitThread":self.antiFdForm.chkExitThread.isChecked(),
                     "bak": self._translate("kmainForm","简单的过frida检测."), "address": self.pform.address, "code": self.pform.patch}
        typeStr = "antiFrida"
        self.hooksData[typeStr]=hookData
        CmdUtil.adbshellCmd("touch /data/local/tmp/maps && chmod 777 /data/local/tmp/maps")
        self.updateTabHooks()

    def saveHooks(self):
        self.log(self._translate("kmainForm","保存hook列表"))
        if len(self.hooksData) <= 0:
            QMessageBox().information(self, "hint", self._translate("kmainForm","未设置hook项,无法保存"))
            return
        saveHooks = self.txtSaveHooks.text()
        if len(saveHooks) <= 0:
            self.log(self._translate("kmainForm","未填写保存的别名"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","未填写保存的别名"))
            return
        filepath = "./hooks/" + saveHooks + ".json"
        with open(filepath, "w", encoding="utf8") as hooksFile:
            jsondata = json.dumps(self.hooksData)
            hooksFile.write(jsondata)
            self.log(self._translate("kmainForm","成功保存到") + filepath)
            self.updateCmbHooks()
            QMessageBox().information(self, "hint", self._translate("kmainForm","成功保存到") + filepath)

    # 加载hook列表后。这里刷新下checked
    def refreshChecks(self):
        self.chkNetwork.setChecked(self.chkNetwork.tag in self.hooksData)
        self.chkJni.setChecked(self.chkJni.tag in self.hooksData)
        self.chkJavaEnc.setChecked(self.chkJavaEnc.tag in self.hooksData)
        self.chkSslPining.setChecked(self.chkSslPining.tag in self.hooksData)
        self.chkRegisterNative.setChecked(self.chkRegisterNative.tag in self.hooksData)
        self.chkArtMethod.setChecked(self.chkArtMethod.tag in self.hooksData)
        self.chkLibArt.setChecked(self.chkLibArt.tag in self.hooksData)

    def loadJson(self, filepath):
        if os.path.exists(filepath)==False:
            return
        with open(filepath, "r", encoding="utf8") as hooksFile:
            data = hooksFile.read()
            self.hooksData = json.loads(data)
            self.updateTabHooks()
            self.refreshChecks()

    def loadHooks(self):
        name = self.cmbHooks.currentText()
        if name:
            self.clearHooks()
            filepath = "./hooks/" + name + ".json"
            self.log(self._translate("kmainForm","加载")  + filepath)
            self.loadJson(filepath)
            self.log(self._translate("kmainForm","成功加载")  + filepath)

    # 导入hook的json文件
    def importHooks(self):
        filepath = QtWidgets.QFileDialog.getOpenFileName(self, "open files")
        if filepath[0]:
            self.log(self._translate("kmainForm","导入json文件") + filepath[0])
            self.loadJson(filepath[0])
            self.log(self._translate("kmainForm","成功导入文件")  + filepath[0])

    # 清除hook列表
    def clearHooks(self):
        # self.log("清空hook列表")
        self.tabHooks.clear()
        self.tabHooks.setColumnCount(4)
        self.tabHooks.setRowCount(0)
        self.tabHooks.setHorizontalHeaderLabels(self.header)
        self.tabHooks.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.updateCmbHooks()

    # 更新加载hook列表
    def updateCmbHooks(self):
        self.cmbHooks.clear()
        self.cmbHooks.addItem("select hook list")
        for name in os.listdir("./hooks"):
            if name.index(name) >= 0:
                self.cmbHooks.addItem(name.replace(".json", ""))

    # 更新hooks列表界面
    def updateTabHooks(self):
        self.clearHooks()
        line = 0
        for item in self.hooksData:
            if isinstance(self.hooksData[item], list):
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

    def changeModule(self, data):
        if self.modules == None:
            return
        self.listModules.clear()
        if len(data) > 0:
            for item in self.modules:
                data = data.split("----")[0]
                if data.upper() in item["name"].upper():
                    self.listModules.addItem(item["name"] + "----" + item["base"])
        else:
            for item in self.modules:
                self.listModules.addItem(item["name"] + "----" + item["base"])

    def changeClass(self, data):
        if self.modules == None:
            return
        self.listClasses.clear()
        if len(data) > 0:
            for item in self.classes:
                if data.upper() in item.upper():
                    self.listClasses.addItem(item)
        else:
            for item in self.classes:
                self.listClasses.addItem(item)

    def changeSymbol(self, data):
        if self.symbols == None:
            return
        self.listSymbol.clear()
        if len(data) > 0:
            for item in self.symbols:
                if data.upper() in item["name"].upper():
                    self.listSymbol.addItem(item["name"])
        else:
            for item in self.symbols:
                self.listSymbol.addItem(item["name"])

    def changeMethod(self, data):
        if self.methods == None:
            return
        self.listMethod.clear()
        if len(data) > 0:
            for item in self.methods:
                if data.upper() in item.upper():
                    self.listMethod.addItem(item)
        else:
            for item in self.methods:
                self.listMethod.addItem(item)

    def listModuleClick(self, item):
        self.txtModule.setText(item.text())

    def listClassClick(self, item):
        self.txtClass.setText(item.text())

    # 附加成功后取出app的信息展示
    def loadAppInfo(self, appinfo):
        self.listModules.clear()
        self.listClasses.clear()
        info = json.loads(appinfo)
        self.modules = info["modules"]
        self.classes = info["classes"]

        for module in info["modules"]:
            self.listModules.addItem(module["name"] + "----" + module["base"])

        for item in info["classes"]:
            self.listClasses.addItem(item)

        self.listModules.itemClicked.connect(self.listModuleClick)
        self.listClasses.itemClicked.connect(self.listClassClick)
        packageName = self.labPackage.text()

        with open("./tmp/" + packageName + ".classes.txt", "w+", encoding="utf-8") as packageTmpFile:
            for item in info["classes"]:
                packageTmpFile.write(item + "\n")
        spawnpath = ".spawn" if info["spawn"] == "1" else ""
        with open("./tmp/" + packageName + ".modules" + spawnpath + ".txt", "w+", encoding="utf-8") as packageTmpFile:
            for module in info["modules"]:
                packageTmpFile.write(module["name"] + "\n")

    def searchAppInfoRes(self, appinfo):
        info = json.loads(appinfo)
        searchTyep = info["type"]
        self.searchType = searchTyep
        if searchTyep == "export" or searchTyep == "symbol":
            self.listSymbol.clear()
            self.symbols = info[searchTyep]
            for item in info[searchTyep]:
                self.listSymbol.addItem(item["name"])
        elif searchTyep == "method":
            self.listMethod.clear()
            self.methods = info[searchTyep]
            for method in info[searchTyep]:
                self.listMethod.addItem(method)


    # ====================end======附加前使用的功能,基本都是在内存中查数据================================
    # 关于我
    def actionAbort(self):
        QMessageBox().about(self, "About",
                            self._translate("kmainForm","\nfridaUiTools: 缝合怪,常用脚本整合的界面化工具 \nAuthor: https://github.com/dqzg12300"))

    def appInfoFlush(self):
        res = CmdUtil.exec("adb shell dumpsys window")
        m1 = re.search("mCurrentFocus=Window\\{(.+?)\\}", res)
        if m1 == None:
            self.log(res)
            self.log(self._translate("kmainForm","未找到焦点窗口数据，可能未连接手机"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","未找到焦点窗口数据，可能未连接手机"))
            return
        m1sp = m1.group(1).split(" ")
        if len(m1sp) < 3:
            self.log(m1.group(1))
            self.log(self._translate("kmainForm","焦点数据格式不正确"))
            QMessageBox().information(self, "hint",self._translate("kmainForm","焦点数据格式不正确"))
            return
        m1data = m1sp[2]
        if m1data == "StatusBar":
            self.log(self._translate("kmainForm","请解锁屏幕"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","请解锁屏幕"))
            return
        m1dataSp = m1data.split("/")
        if len(m1dataSp) < 2:
            self.log(m1)
            self.log(self._translate("kmainForm","焦点数据格式不正确"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","焦点数据格式不正确"))
            return
        self.txtProcessName.setText(m1dataSp[0])
        self.txtCurrentFocus.setText(m1dataSp[1])
        res = CmdUtil.exec("adb shell dumpsys activity -p " + self.txtProcessName.text())
        m2 = re.search(r" (\d+?):%s/" % m1dataSp[0], res)
        if m2 == None:
            return
        self.txtPid.setText(m2.group(1))
        m3 = re.search(r"android.intent.action.MAIN.+?cmp=(%s.+) " % self.txtProcessName.text(), res)
        if m3 == None:
            return
        self.txtComponent.setText(m3.group(1))
        m4 = re.search(r"baseDir=(/data/app/%s.+)" % self.txtProcessName.text(), res)
        if m4 == None:
            return
        self.txtBaseDir.setText(m4.group(1))

    def fartOpBin(self):
        self.fartBinForm.show()

    def stalkerOpLog(self):
        self.stalkerMatchForm.show()

    # 不关闭的话，mac下调试时退出会出现无法关闭进程
    def closeEvent(self, event):
        if platform.system() =='Darwin':
            CmdUtil.execCmd(CmdUtil.cmdhead + "\"pkill -9 frida\"")


def getTrans():
    trans = QTranslator()
    trans.load('./ui/kmain.qm')
    app.installTranslator(trans)
    qmNames=[
        "kmain.qm","antiFrida.qm","callFunction.qm","custom.qm","dump_so.qm","dumpAddress.qm",
        "fart.qm","fartBin.qm","fdClass.qm","jnitrace.qm","natives.qm","patch.qm","port.qm",
        "searchMemory.qm","selectPackage.qm","spawnAttach.qm","stalker.qm","stalkerMatch.qm",
        "tuoke.qm","wallBreaker.qm","wifi.qm","zenTracer.qm","kmainForm.qm"
             ]
    transList=[]
    for qmName in qmNames:
        qmPath="./ui/"+qmName
        trans = QTranslator()
        trans.load(qmPath)
        transList.append(trans)
    formQmNames = ["Custom.qm","FartBin.qm","SearchMemory.qm","Wallbreaker.qm","ZenTracer.qm"]
    for qmName in formQmNames:
        qmPath = "./forms/" + qmName
        trans = QTranslator()
        trans.load(qmPath)
        transList.append(trans)
    return transList




if __name__ == "__main__":
    current_exit_code = 1207
    app = QApplication(sys.argv)
    while current_exit_code == 1207:
        language=conf.read("kmain","language")
        # changeTranslator(language=="English")
        transList= getTrans()
        if language=="English":
            for trans in transList:
                app.installTranslator(trans)
        else:
            for trans in transList:
                app.removeTranslator(trans)
        kmain = kmainForm()
        kmain.show()
        current_exit_code=app.exec_()
        kmain=None
    sys.exit(current_exit_code)



