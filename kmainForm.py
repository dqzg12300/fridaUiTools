# coding=utf-8
import datetime
import re
import sys
from time import sleep

from PyQt5 import uic, QtWidgets,QtCore
from PyQt5.QtCore import Qt, QPoint, QTranslator, QUrl
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor, QDesktopServices
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStatusBar, QLabel, QMessageBox, QHeaderView, \
    QTableWidgetItem, QMenu, QAction, QActionGroup, qApp, QLineEdit

from forms import SelectPackage
from forms.AntiFrida import antiFridaForm
from forms.CallFunction import callFunctionForm
from forms.Custom import customForm
from forms.DumpAddress import dumpAddressForm
from forms.AiSettings import aiSettingsForm
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
from utils import LogUtil, CmdUtil, FileUtil, GumTraceUtil
from utils.AiUtil import AiService, AiWorker
import json, os, threading, frida
import platform

import TraceThread
from utils.IniUtil import IniConfig

conf=IniConfig()
ACTIVE_TRANSLATORS = []

def restart_real_live():
    qApp.exit(1207)

class kmainForm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(kmainForm, self).__init__(parent)
        self.setupUi(self)
        self.aiService = AiService(conf)
        self.aiWorker = None
        self.liveOutputLogBuffer = []
        self.currentLogMode = "live"
        self.loadedLogPath = ""
        self.loadedLogContent = ""
        self.language = conf.read("kmain", "language") or "China"
        self.currentAppInfoSnapshot = {}
        self.attachedAppInfoSnapshot = {}
        self.hooksData = {}
        self.initUi()
        self.th = TraceThread.Runthread(self.hooksData, "", False, self.connType)
        self.th.usb_device_id = self.selectedDeviceSerial()
        self.updateCmbHooks()
        self.outlogger = LogUtil.Logger('all.txt', level='debug')

    def initUi(self):
        self.setWindowOpacity(0.93)
        self.resize(1480, 980)
        self.setMinimumSize(1280, 880)
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
        if self.language == "China":
            self.actionChina.setChecked(True)
        else:
            self.actionEnglish.setChecked(True)
        self.loadTypeData()

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
        self.actionPushGumTrace = QAction(self)
        self.actionPushGumTrace.setObjectName("actionPushGumTrace")
        self.actionPushGumTrace.triggered.connect(self.PushGumTraceLib)
        self.menu.insertAction(self.actionPullDumpDexRes, self.actionPushGumTrace)

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

        self.chkRootBypass = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkRootBypass.setObjectName("chkRootBypass")
        self.chkRootBypass.setText(self._translate("kmainForm", "root bypass"))
        self.gridLayout_5.addWidget(self.chkRootBypass, 2, 2, 1, 1)
        self.chkRootBypass.toggled.connect(self.hookRootBypass)

        self.chkWebViewDebug = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkWebViewDebug.setObjectName("chkWebViewDebug")
        self.chkWebViewDebug.setText(self._translate("kmainForm", "webview debug"))
        self.gridLayout_5.addWidget(self.chkWebViewDebug, 2, 3, 1, 1)
        self.chkWebViewDebug.toggled.connect(self.hookWebViewDebug)

        self.chkOkHttpLogger = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkOkHttpLogger.setObjectName("chkOkHttpLogger")
        self.chkOkHttpLogger.setText(self._translate("kmainForm", "okhttp logger"))
        self.gridLayout_5.addWidget(self.chkOkHttpLogger, 3, 0, 1, 2)
        self.chkOkHttpLogger.toggled.connect(self.hookOkHttpLogger)

        self.chkSharedPrefsWatch = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkSharedPrefsWatch.setObjectName("chkSharedPrefsWatch")
        self.chkSharedPrefsWatch.setText(self._translate("kmainForm", "shared prefs"))
        self.gridLayout_5.addWidget(self.chkSharedPrefsWatch, 3, 2, 1, 1)
        self.chkSharedPrefsWatch.toggled.connect(self.hookSharedPrefsWatch)

        self.chkSQLiteLogger = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkSQLiteLogger.setObjectName("chkSQLiteLogger")
        self.chkSQLiteLogger.setText(self._translate("kmainForm", "sqlite logger"))
        self.gridLayout_5.addWidget(self.chkSQLiteLogger, 3, 3, 1, 1)
        self.chkSQLiteLogger.toggled.connect(self.hookSQLiteLogger)

        self.chkClipboardMonitor = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkClipboardMonitor.setObjectName("chkClipboardMonitor")
        self.chkClipboardMonitor.setText(self._translate("kmainForm", "clipboard monitor"))
        self.gridLayout_5.addWidget(self.chkClipboardMonitor, 4, 0, 1, 2)
        self.chkClipboardMonitor.toggled.connect(self.hookClipboardMonitor)

        self.chkIntentMonitor = QtWidgets.QCheckBox(self.groupBox_2)
        self.chkIntentMonitor.setObjectName("chkIntentMonitor")
        self.chkIntentMonitor.setText(self._translate("kmainForm", "intent monitor"))
        self.gridLayout_5.addWidget(self.chkIntentMonitor, 4, 2, 1, 2)
        self.chkIntentMonitor.toggled.connect(self.hookIntentMonitor)

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
        self.tabHooks.setColumnCount(4)
        self.refreshHookHeaders()
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
        self.btnPullGumTraceLog = QtWidgets.QPushButton(self.groupBox_9)
        self.btnPullGumTraceLog.setObjectName("btnPullGumTraceLog")
        self.btnPullGumTraceLog.setMaximumSize(QtCore.QSize(180, 60))
        self.gridLayout_15.addWidget(self.btnPullGumTraceLog, 0, 2, 1, 1)
        self.btnPullGumTraceLog.clicked.connect(self.pullGumTraceLog)
        # self.btnOpFartLog.clicked.connect(self.fartOpLog)
        self.btnMemSearch.clicked.connect(self.searchMem)
        self.btnAntiFrida.clicked.connect(self.antiFrida)



        self.dumpForm = dumpAddressForm()
        self.jniform = jnitraceForm()
        self.newJniform = jnitraceForm()
        self.zenTracerForm = zenTracerForm()
        self.nativesForm = nativesForm()
        self.spawnAttachForm = spawnAttachForm()
        self.stalkerForm = stalkerForm()
        self.pform = patchForm()
        self.dumpSoForm = dumpSoForm()
        self.fartForm = fartForm()
        self.wallBreakerForm = wallBreakerForm()
        self.customForm = customForm(self)
        self.callFunctionForm = callFunctionForm()
        self.fartBinForm = fartBinForm()
        self.stalkerMatchForm = stalkerMatchForm()
        self.wifiForm = wifiForm()
        self.portForm = portForm()
        self.aiSettingsForm = aiSettingsForm(self)
        self.searchMemForm = searchMemoryForm()
        self.antiFdForm = antiFridaForm()

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
        self.chkLibArt.tag = "libArm"
        self.chkHookEvent.tag = "hookEvent"
        self.chkRootBypass.tag = "root_bypass"
        self.chkWebViewDebug.tag = "webview_debug"
        self.chkOkHttpLogger.tag = "okhttp_logger"
        self.chkSharedPrefsWatch.tag = "shared_prefs_watch"
        self.chkSQLiteLogger.tag = "sqlite_logger"
        self.chkClipboardMonitor.tag = "clipboard_monitor"
        self.chkIntentMonitor.tag = "intent_monitor"
        self.connType = "usb"
        self.selectedDeviceId = ""
        self.logPanelVisible = True
        self.lastMainSplitterSizes = [760, 420]

        self.actionattach = QtWidgets.QAction(self)
        self.actionattach.setText("attach")
        self.actionattach.setToolTip("attach by packageName")
        self.actionattach.triggered.connect(self.actionAttachNameStart)
        self.toolBar.addAction(self.actionattach)

        self.actionattachF = QtWidgets.QAction(self)
        self.actionattachF.setText("attachF")
        self.actionattachF.setToolTip("attach current top app")
        self.actionattachF.triggered.connect(self.actionAttachStart)
        self.toolBar.addAction(self.actionattachF)

        self.actionspawn = QtWidgets.QAction(self)
        self.actionspawn.setText("spawn")
        self.actionspawn.triggered.connect(self.actionSpawnStart)
        self.toolBar.addAction(self.actionspawn)

        self.actionstop = QtWidgets.QAction(self)
        self.actionstop.setText("stop")
        self.actionstop.triggered.connect(self.StopAttach)
        self.toolBar.addAction(self.actionstop)

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

        self.initSmartLayout()
        self.initLogTools()
        self.initSettingsMenu()
        self.initGumTraceWorkspace()
        self.loadGumTraceConfig()
        self.retranslateDynamicUi()
        self.refreshDeviceList()
        self.refreshOverviewCards()

    def isEnglish(self):
        return self.language == "English"

    def trText(self, zh_text, en_text):
        return en_text if self.isEnglish() else zh_text

    def selectedDeviceSerial(self):
        if hasattr(self, "cmbDevices"):
            return (self.cmbDevices.currentData() or "").strip()
        return (self.selectedDeviceId or "").strip()

    def selectedDeviceLabel(self):
        if hasattr(self, "cmbDevices") and self.cmbDevices.currentIndex() >= 0:
            return self.cmbDevices.currentText().strip()
        return self.selectedDeviceSerial()

    def updateSelectedDevice(self, serial):
        self.selectedDeviceId = (serial or "").strip()
        if self.selectedDeviceId:
            os.environ["ANDROID_SERIAL"] = self.selectedDeviceId
        elif "ANDROID_SERIAL" in os.environ:
            os.environ.pop("ANDROID_SERIAL")

    def refreshDeviceList(self):
        if not hasattr(self, "cmbDevices"):
            return
        previous = self.selectedDeviceSerial()
        previous_env = os.environ.pop("ANDROID_SERIAL", None)
        try:
            devices_output = CmdUtil.exec("adb devices")
        finally:
            if previous_env is not None:
                os.environ["ANDROID_SERIAL"] = previous_env
        devices = []
        for line in devices_output.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = re.split(r"\s+", line)
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
        self.cmbDevices.blockSignals(True)
        self.cmbDevices.clear()
        for serial in devices:
            self.cmbDevices.addItem(serial, serial)
        target = previous if previous in devices else (devices[0] if devices else "")
        if target:
            self.cmbDevices.setCurrentIndex(devices.index(target))
        self.cmbDevices.blockSignals(False)
        self.updateSelectedDevice(target)
        if hasattr(self, "labDeviceStatus"):
            if target:
                self.labDeviceStatus.setText(self.trText("当前设备：", "Current device: ") + target)
            else:
                self.labDeviceStatus.setText(self.trText("当前设备：未检测到已连接设备", "Current device: no connected device detected"))
        self.updateCurrentAppInfoTable()
        self.refreshOverviewCards()

    def onDeviceChanged(self):
        self.updateSelectedDevice(self.selectedDeviceSerial())
        if hasattr(self, "labDeviceStatus"):
            current = self.selectedDeviceSerial()
            self.labDeviceStatus.setText((self.trText("当前设备：", "Current device: ") + current) if current else self.trText("当前设备：未检测到已连接设备", "Current device: no connected device detected"))
        self.updateCurrentAppInfoTable()
        self.refreshOverviewCards()

    def toggleLogDock(self):
        self.setLogPanelVisible(not self.logPanelVisible)

    def showLogDock(self, target_tab=None):
        if target_tab is not None:
            self.groupLogs.setCurrentWidget(target_tab)
        self.setLogPanelVisible(True)
        if hasattr(self, "logDock"):
            self.logDock.raise_()

    def onLogDockVisibilityChanged(self, visible):
        self.logPanelVisible = visible
        if hasattr(self, "actionToggleLogDock"):
            self.actionToggleLogDock.setText(self.trText("隐藏日志侧边栏", "Hide log sidebar") if visible else self.trText("显示日志侧边栏", "Show log sidebar"))

    def setLogPanelVisible(self, visible):
        self.logPanelVisible = visible
        if not hasattr(self, "logDock"):
            return
        if visible:
            self.logDock.show()
        else:
            self.logDock.hide()
        self.onLogDockVisibilityChanged(self.logDock.isVisible())



    def loadTypeData(self):
        typePath = "./config/type_en.json" if self.isEnglish() else "./config/type.json"
        with open(typePath, "r", encoding="utf8") as typeFile:
            self.typeData = json.loads(typeFile.read())

    def valueText(self, value, default="-"):
        if value is None:
            return default
        text = str(value).strip()
        return text if len(text) > 0 else default

    def boolText(self, value):
        if value is None or value == "":
            return "-"
        return self.trText("是", "Yes") if bool(value) else self.trText("否", "No")

    def setupInfoTable(self, table):
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([
            self.trText("字段", "Field"),
            self.trText("值", "Value"),
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        table.setWordWrap(True)

    def setInfoTableRows(self, table, rows):
        valid_rows = [(self.valueText(key), self.valueText(value)) for key, value in rows if self.valueText(value) != "-"]
        table.clearContents()
        table.setRowCount(len(valid_rows))
        for row, (key, value) in enumerate(valid_rows):
            keyItem = QTableWidgetItem(key)
            valueItem = QTableWidgetItem(value)
            keyItem.setToolTip(key)
            valueItem.setToolTip(value)
            table.setItem(row, 0, keyItem)
            table.setItem(row, 1, valueItem)
        table.resizeRowsToContents()

    def configureInfoTabs(self):
        if self.tab_6.layout() is None:
            self.tab6Layout = QtWidgets.QVBoxLayout(self.tab_6)
            self.tab6Layout.setContentsMargins(10, 10, 10, 10)
            self.tab6Layout.setSpacing(12)
        else:
            self.tab6Layout = self.tab_6.layout()

        self.labAppWorkbenchHint = QLabel(self.tab_6)
        self.labAppWorkbenchHint.setWordWrap(True)
        self.labAppWorkbenchHint.setObjectName("sectionHint")
        self.tab6Layout.addWidget(self.labAppWorkbenchHint)
        self.groupBox_8.setParent(self.tab_6)

        self.deviceBarWidget = QtWidgets.QWidget(self.groupBox_8)
        self.deviceBarLayout = QtWidgets.QHBoxLayout(self.deviceBarWidget)
        self.deviceBarLayout.setContentsMargins(0, 0, 0, 0)
        self.deviceBarLayout.setSpacing(8)
        self.labDeviceSelector = QLabel(self.deviceBarWidget)
        self.cmbDevices = QtWidgets.QComboBox(self.deviceBarWidget)
        self.cmbDevices.setMinimumWidth(260)
        self.cmbDevices.currentIndexChanged.connect(self.onDeviceChanged)
        self.btnRefreshDevices = QtWidgets.QPushButton(self.deviceBarWidget)
        self.btnRefreshDevices.setCursor(Qt.PointingHandCursor)
        self.btnRefreshDevices.clicked.connect(self.refreshDeviceList)
        self.labDeviceStatus = QLabel(self.deviceBarWidget)
        self.labDeviceStatus.setObjectName("summaryCaption")
        self.labDeviceStatus.setWordWrap(True)
        self.deviceBarLayout.addWidget(self.labDeviceSelector)
        self.deviceBarLayout.addWidget(self.cmbDevices, 1)
        self.deviceBarLayout.addWidget(self.btnRefreshDevices)
        self.deviceBarLayout.addWidget(self.labDeviceStatus, 2)
        self.gridLayout_17.removeWidget(self.frame_3)
        self.gridLayout_17.addWidget(self.deviceBarWidget, 0, 0, 1, 1)
        self.gridLayout_17.addWidget(self.frame_3, 1, 0, 1, 1)

        self.currentAppExtraGroup = QtWidgets.QGroupBox(self.tab_6)
        self.currentAppExtraGroup.setObjectName("currentAppExtraGroup")
        self.currentAppExtraLayout = QtWidgets.QVBoxLayout(self.currentAppExtraGroup)
        self.currentAppExtraLayout.setContentsMargins(10, 12, 10, 10)
        self.currentAppExtraLayout.setSpacing(8)
        self.labCurrentAppInfoHint = QLabel(self.currentAppExtraGroup)
        self.labCurrentAppInfoHint.setWordWrap(True)
        self.labCurrentAppInfoHint.setObjectName("panelHint")
        self.currentAppExtraLayout.addWidget(self.labCurrentAppInfoHint)
        self.currentAppInfoTable = QtWidgets.QTableWidget(self.currentAppExtraGroup)
        self.currentAppInfoTable.setObjectName("currentAppInfoTable")
        self.currentAppExtraLayout.addWidget(self.currentAppInfoTable)
        self.setupInfoTable(self.currentAppInfoTable)

        self.appInfoSplitter = QtWidgets.QSplitter(Qt.Horizontal, self.tab_6)
        self.appInfoSplitter.setChildrenCollapsible(False)
        self.appInfoSplitter.addWidget(self.groupBox_8)
        self.appInfoSplitter.addWidget(self.currentAppExtraGroup)
        self.appInfoSplitter.setStretchFactor(0, 5)
        self.appInfoSplitter.setStretchFactor(1, 6)
        self.tab6Layout.addWidget(self.appInfoSplitter, 1)

        self.gridLayout_16.setContentsMargins(10, 12, 10, 10)
        self.gridLayout_16.setSpacing(8)
        self.labAttachedInfoHint = QLabel(self.groupBox_7)
        self.labAttachedInfoHint.setWordWrap(True)
        self.labAttachedInfoHint.setObjectName("panelHint")
        self.gridLayout_16.addWidget(self.labAttachedInfoHint, 0, 0, 1, 1)
        self.attachInfoTable = QtWidgets.QTableWidget(self.groupBox_7)
        self.attachInfoTable.setObjectName("attachInfoTable")
        self.gridLayout_16.addWidget(self.attachInfoTable, 1, 0, 1, 1)
        self.setupInfoTable(self.attachInfoTable)

    def buildCurrentAppInfoRows(self):
        data = self.currentAppInfoSnapshot or {}
        if len(data) <= 0:
            return []
        return [
            (self.trText("连接设备", "Selected device"), self.selectedDeviceLabel()),
            (self.trText("包名", "Package"), data.get("packageName")),
            (self.trText("进程名", "Process"), data.get("processName")),
            ("PID", data.get("pid")),
            (self.trText("当前焦点", "Current focus"), data.get("currentFocus")),
            (self.trText("启动页面", "Launch component"), data.get("component")),
            (self.trText("base 路径", "Base path"), data.get("baseDir")),
            (self.trText("APK 路径", "APK path"), data.get("apkPath")),
            (self.trText("数据目录", "Data dir"), data.get("dataDir")),
            (self.trText("主 ABI", "Primary ABI"), data.get("primaryCpuAbi")),
            (self.trText("版本名", "Version name"), data.get("versionName")),
            (self.trText("版本号", "Version code"), data.get("versionCode")),
            ("targetSdk", data.get("targetSdk")),
            ("UID", data.get("uid")),
            (self.trText("可调试", "Debuggable"), self.boolText(data.get("debuggable"))),
            (self.trText("允许备份", "Allow backup"), self.boolText(data.get("allowBackup"))),
            (self.trText("包标记", "Package flags"), data.get("pkgFlags")),
            (self.trText("设备 ABI 列表", "Device ABI list"), data.get("deviceAbiList")),
        ]

    def updateCurrentAppInfoTable(self):
        if hasattr(self, "currentAppInfoTable"):
            self.setupInfoTable(self.currentAppInfoTable)
            self.setInfoTableRows(self.currentAppInfoTable, self.buildCurrentAppInfoRows())

    def buildAttachedInfoRows(self):
        data = self.attachedAppInfoSnapshot or {}
        if len(data) <= 0:
            return []
        runtime = data.get("runtime", {})
        package = data.get("package", {})
        module_count = runtime.get("moduleCount") or len(data.get("modules", []))
        class_count = runtime.get("classCount") or len(data.get("classes", []))
        return [
            (self.trText("附加包名", "Attached package"), data.get("packageName") or package.get("packageName") or self.labPackage.text()),
            (self.trText("附加方式", "Attach mode"), data.get("attachType")),
            (self.trText("连接方式", "Connection"), data.get("connectionType")),
            (self.trText("Frida 版本", "Frida version"), data.get("fridaVersion")),
            (self.trText("Hook 数量", "Hook count"), data.get("hookCount")),
            (self.trText("进程 PID", "Process PID"), runtime.get("processId")),
            (self.trText("进程架构", "Process arch"), runtime.get("arch")),
            (self.trText("指针大小", "Pointer size"), runtime.get("pointerSize")),
            (self.trText("页面大小", "Page size"), runtime.get("pageSize")),
            (self.trText("模块数量", "Module count"), module_count),
            (self.trText("Java 类数量", "Java class count"), class_count),
            (self.trText("已附加调试器", "Debugger attached"), self.boolText(runtime.get("debuggerAttached"))),
            (self.trText("当前目录", "Current dir"), runtime.get("currentDir")),
            (self.trText("临时目录", "Temp dir"), runtime.get("tmpDir")),
            (self.trText("应用名称", "App label"), package.get("appLabel")),
            (self.trText("版本名", "Version name"), package.get("versionName")),
            (self.trText("版本号", "Version code"), package.get("versionCode")),
            (self.trText("进程名", "Process"), package.get("processName")),
            ("targetSdk", package.get("targetSdk")),
            ("minSdk", package.get("minSdk")),
            ("UID", package.get("uid")),
            (self.trText("可调试", "Debuggable"), self.boolText(package.get("debuggable"))),
            (self.trText("允许备份", "Allow backup"), self.boolText(package.get("allowBackup"))),
            (self.trText("仅测试包", "Test only"), self.boolText(package.get("testOnly"))),
            (self.trText("源 APK", "Source APK"), package.get("sourceDir")),
            (self.trText("数据目录", "Data dir"), package.get("dataDir")),
            (self.trText("Native 库目录", "Native lib dir"), package.get("nativeLibraryDir")),
            ("Task Affinity", package.get("taskAffinity")),
            (self.trText("Application 类", "Application class"), package.get("className")),
            (self.trText("Android 版本", "Android version"), package.get("androidVersion")),
            (self.trText("设备信息", "Device"), " / ".join([item for item in [self.valueText(package.get("brand"), ""), self.valueText(package.get("model"), ""), self.valueText(package.get("device"), "")] if len(item) > 0])),
            (self.trText("支持 ABI", "Supported ABIs"), package.get("supportedAbis")),
            (self.trText("代码签名策略", "Code-signing policy"), runtime.get("codeSigningPolicy")),
            (self.trText("附加信息异常", "Attach info error"), data.get("packageError")),
        ]

    def updateAttachedInfoTable(self):
        if hasattr(self, "attachInfoTable"):
            self.setupInfoTable(self.attachInfoTable)
            self.setInfoTableRows(self.attachInfoTable, self.buildAttachedInfoRows())

    def initSmartLayout(self):
        self.resize(1320, 860)
        self.setMinimumSize(1080, 760)
        self.tabWidget.setDocumentMode(False)
        self.groupLogs.setDocumentMode(False)
        self.groupLogs.setTabPosition(QtWidgets.QTabWidget.North)
        self.groupLogs.setUsesScrollButtons(True)

        self.groupBox.setMinimumWidth(0)
        self.groupBox_2.setMinimumWidth(0)
        for button in [self.btnDumpSo, self.btnDumpPtr, self.btnDumpDex, self.btnFart,
                       self.btnWallbreaker, self.btnCallFunction, self.btnMemSearch,
                       self.btnMatchMethod, self.btnNatives, self.btnStalker, self.btnTuoke,
                       self.btnCustom, self.btnPatch, self.btnAntiFrida]:
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)

        self.gridLayout_6.removeWidget(self.groupBox)
        self.gridLayout_6.removeWidget(self.groupBox_2)
        self.gridLayout_6.removeWidget(self.groupLogs)

        self.mainLeftWidget = QtWidgets.QWidget(self.tab_2)
        self.mainLeftLayout = QtWidgets.QVBoxLayout(self.mainLeftWidget)
        self.mainLeftLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLeftLayout.setSpacing(10)
        self.mainLeftLayout.addWidget(self.groupBox)
        self.mainLeftLayout.addWidget(self.groupBox_2)
        self.gridLayout_6.addWidget(self.mainLeftWidget, 0, 0, 1, 1)

        self.configureClassicMainPanels()
        self.configureInfoTabs()
        self.configureAttachExplorerTab()
        self.configureAssistTab()
        self.configureLogWidgets()
        self.initLogDock()
        self.setLogPanelVisible(True)

    def configureClassicMainPanels(self):
        self.gridLayout_4.setContentsMargins(9, 9, 9, 9)
        self.gridLayout_7.setContentsMargins(9, 9, 9, 9)
        self.gridLayout_4.setHorizontalSpacing(6)
        self.gridLayout_4.setVerticalSpacing(6)
        self.gridLayout_7.setHorizontalSpacing(6)
        self.gridLayout_7.setVerticalSpacing(6)

        self.labAiFeatureStatusMain = QLabel(self.groupBox_2)
        self.labAiFeatureStatusMain.setWordWrap(True)
        self.labAiFeatureStatusMain.setObjectName("aiStateLabel")
        self.gridLayout_7.addWidget(self.labAiFeatureStatusMain, 1, 0, 1, 1)

        self.btnGumTracePanel = QtWidgets.QPushButton(self.groupBox_2)
        self.btnGumTracePanel.setMinimumHeight(40)
        self.btnGumTracePanel.setCursor(Qt.PointingHandCursor)
        self.btnGumTracePanel.clicked.connect(self.openGumTraceWorkspace)
        self.horizontalLayout.addWidget(self.btnGumTracePanel)

    def createSummaryCard(self, title, value, accent_color):
        card = QtWidgets.QFrame(self.mainRootWidget)
        card.setObjectName("summaryCard")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)
        titleLabel = QLabel(title, card)
        titleLabel.setObjectName("summaryTitle")
        valueLabel = QLabel(value, card)
        valueLabel.setWordWrap(True)
        valueLabel.setObjectName("summaryValue")
        valueLabel.setStyleSheet("color: %s;" % accent_color)
        card.titleLabel = titleLabel
        card.valueLabel = valueLabel
        layout.addWidget(titleLabel)
        layout.addWidget(valueLabel)
        layout.addStretch(1)
        return card

    def configureAttachExplorerTab(self):
        self.gridLayout_14.removeItem(self.horizontalLayout_2)
        self.gridLayout_14.removeItem(self.horizontalLayout_3)
        self.gridLayout_14.removeWidget(self.groupBox_7)

        self.attachWorkbenchHeader = QLabel(self.tab)
        self.attachWorkbenchHeader.setObjectName("sectionHint")
        self.attachWorkbenchHeader.setWordWrap(True)
        self.gridLayout_14.addWidget(self.attachWorkbenchHeader, 0, 0, 1, 1)

        self.nativeActionGroup = QtWidgets.QGroupBox(self.tab)
        self.nativeActionGroup.setObjectName("panelCard")
        self.nativeActionLayout = QtWidgets.QVBoxLayout(self.nativeActionGroup)
        self.nativeActionLayout.setContentsMargins(10, 12, 10, 10)
        self.nativeActionLayout.setSpacing(10)
        for button in [self.btnExport, self.btnSymbol, self.btnSymbolClear]:
            self.verticalLayout.removeWidget(button)
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)
            self.nativeActionLayout.addWidget(button)
        self.nativeActionLayout.addStretch(1)

        self.javaActionGroup = QtWidgets.QGroupBox(self.tab)
        self.javaActionGroup.setObjectName("panelCard")
        self.javaActionLayout = QtWidgets.QVBoxLayout(self.javaActionGroup)
        self.javaActionLayout.setContentsMargins(10, 12, 10, 10)
        self.javaActionLayout.setSpacing(10)
        for button in [self.btnMethod, self.btnMethodClear]:
            self.verticalLayout_2.removeWidget(button)
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)
            self.javaActionLayout.addWidget(button)
        self.javaActionLayout.addStretch(1)

        self.nativeExplorerWidget = QtWidgets.QWidget(self.tab)
        self.nativeExplorerLayout = QtWidgets.QHBoxLayout(self.nativeExplorerWidget)
        self.nativeExplorerLayout.setContentsMargins(0, 0, 0, 0)
        self.nativeExplorerLayout.setSpacing(12)
        self.nativeExplorerLayout.addWidget(self.groupBox_3, 5)
        self.nativeExplorerLayout.addWidget(self.nativeActionGroup, 2)
        self.nativeExplorerLayout.addWidget(self.groupBox_5, 5)

        self.javaExplorerWidget = QtWidgets.QWidget(self.tab)
        self.javaExplorerLayout = QtWidgets.QHBoxLayout(self.javaExplorerWidget)
        self.javaExplorerLayout.setContentsMargins(0, 0, 0, 0)
        self.javaExplorerLayout.setSpacing(12)
        self.javaExplorerLayout.addWidget(self.groupBox_4, 5)
        self.javaExplorerLayout.addWidget(self.javaActionGroup, 2)
        self.javaExplorerLayout.addWidget(self.groupBox_6, 5)

        self.attachExplorerSplitter = QtWidgets.QSplitter(Qt.Vertical, self.tab)
        self.attachExplorerSplitter.setChildrenCollapsible(False)
        self.attachExplorerSplitter.addWidget(self.nativeExplorerWidget)
        self.attachExplorerSplitter.addWidget(self.javaExplorerWidget)
        self.attachExplorerSplitter.addWidget(self.groupBox_7)
        self.attachExplorerSplitter.setStretchFactor(0, 4)
        self.attachExplorerSplitter.setStretchFactor(1, 4)
        self.attachExplorerSplitter.setStretchFactor(2, 5)
        self.attachExplorerSplitter.setSizes([240, 240, 320])
        self.gridLayout_14.addWidget(self.attachExplorerSplitter, 1, 0, 1, 1)

    def configureAssistTab(self):
        self.gridLayout_19.removeWidget(self.groupBox_9)
        self.gridLayout_19.removeWidget(self.groupBox_10)
        self.groupBox_9.hide()
        self.groupBox_10.setObjectName("panelCard")

        self.btnOpenGumTraceDir = QtWidgets.QPushButton(self.groupBox_10)
        self.btnOpenGumTraceDir.clicked.connect(self.openGumTraceLogDirectory)
        self.btnOpenGumTraceDir.setMinimumHeight(40)
        self.btnOpenGumTraceWorkspace = QtWidgets.QPushButton(self.groupBox_10)
        self.btnOpenGumTraceWorkspace.clicked.connect(self.openGumTraceWorkspace)
        self.btnOpenGumTraceWorkspace.setMinimumHeight(40)
        self.btnAssistUploadGumTrace = QtWidgets.QPushButton(self.groupBox_10)
        self.btnAssistUploadGumTrace.clicked.connect(self.PushGumTraceLib)
        self.btnAssistUploadGumTrace.setMinimumHeight(40)

        self.groupBox10Layout = QtWidgets.QVBoxLayout(self.groupBox_10)
        self.groupBox10Layout.setContentsMargins(16, 18, 16, 16)
        self.groupBox10Layout.setSpacing(10)
        self.labAssistGumTraceHint = QLabel(self.groupBox_10)
        self.labAssistGumTraceHint.setWordWrap(True)
        self.labAssistGumTraceHint.setObjectName("panelHint")
        self.groupBox10Layout.addWidget(self.labAssistGumTraceHint)
        self.labAssistGumTraceRemote = QLabel(self.groupBox_10)
        self.labAssistGumTraceRemote.setWordWrap(True)
        self.labAssistGumTraceRemote.setObjectName("summaryCaption")
        self.groupBox10Layout.addWidget(self.labAssistGumTraceRemote)
        self.labAssistGumTraceLocal = QLabel(self.groupBox_10)
        self.labAssistGumTraceLocal.setWordWrap(True)
        self.labAssistGumTraceLocal.setObjectName("summaryCaption")
        self.groupBox10Layout.addWidget(self.labAssistGumTraceLocal)
        self.labAssistGumTraceFilters = QLabel(self.groupBox_10)
        self.labAssistGumTraceFilters.setWordWrap(True)
        self.labAssistGumTraceFilters.setObjectName("summaryCaption")
        self.groupBox10Layout.addWidget(self.labAssistGumTraceFilters)
        for button in [self.btnPullGumTraceLog, self.btnOpenGumTraceDir, self.btnAssistUploadGumTrace, self.btnOpenGumTraceWorkspace]:
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            self.groupBox10Layout.addWidget(button)
        self.groupBox10Layout.addStretch(1)
        self.gridLayout_19.addWidget(self.groupBox_10, 0, 0, 1, 1)


    def buildButtonCard(self, title, description, buttons, columns=2):
        card = QtWidgets.QGroupBox(title, self)
        card.setObjectName("panelCard")
        cardLayout = QtWidgets.QVBoxLayout(card)
        cardLayout.setContentsMargins(12, 14, 12, 12)
        cardLayout.setSpacing(10)
        hint = QLabel(description, card)
        hint.setWordWrap(True)
        hint.setObjectName("panelHint")
        card.hintLabel = hint
        cardLayout.addWidget(hint)
        card.buttonGrid = QtWidgets.QGridLayout()
        card.buttonGrid.setHorizontalSpacing(10)
        card.buttonGrid.setVerticalSpacing(10)
        card.cardButtons = buttons
        card.defaultColumns = columns
        for button in buttons:
            button.setMinimumHeight(42)
            button.setCursor(Qt.PointingHandCursor)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        cardLayout.addLayout(card.buttonGrid)
        if not hasattr(self, "responsiveButtonCards"):
            self.responsiveButtonCards = []
        self.responsiveButtonCards.append(card)
        self.layoutButtonCard(card)
        return card

    def layoutButtonCard(self, card):
        if not hasattr(card, "buttonGrid"):
            return
        while card.buttonGrid.count():
            item = card.buttonGrid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(card)
        width = card.width() or card.parentWidget().width()
        if width < 260:
            columns = 1
        else:
            columns = min(card.defaultColumns, len(card.cardButtons))
        for index, button in enumerate(card.cardButtons):
            button.setMinimumWidth(0)
            card.buttonGrid.addWidget(button, index // columns, index % columns)
        for col in range(columns):
            card.buttonGrid.setColumnStretch(col, 1)

    def rebuildResponsiveCards(self):
        for card in getattr(self, "responsiveButtonCards", []):
            self.layoutButtonCard(card)

    def configureCommonToolsPanel(self):
        self.gridLayout_4.setContentsMargins(12, 16, 12, 12)
        self.gridLayout_4.setHorizontalSpacing(12)
        self.gridLayout_4.setVerticalSpacing(12)
        for button in [self.btnDumpSo, self.btnDumpPtr, self.btnDumpDex, self.btnFart,
                       self.btnWallbreaker, self.btnCallFunction, self.btnMemSearch]:
            self.gridLayout_4.removeWidget(button)

        self.labCommonSummary = QLabel(
            self._translate("kmainForm", "将常用附加后操作拆分为“导出/脱壳”和“分析/调用”两组，窗口缩放时保持更均衡的按钮尺寸。"),
            self.groupBox,
        )
        self.labCommonSummary.setWordWrap(True)
        self.labCommonSummary.setObjectName("sectionHint")
        self.gridLayout_4.addWidget(self.labCommonSummary, 0, 0, 1, 4)

        self.dumpCard = self.buildButtonCard(
            self._translate("kmainForm", "导出 / 脱壳"),
            self._translate("kmainForm", "聚合 so、指针、dex 与 fart 等导出能力，适合附加后快速取证或脱壳。"),
            [self.btnDumpSo, self.btnDumpPtr, self.btnDumpDex, self.btnFart],
            2,
        )
        self.inspectCard = self.buildButtonCard(
            self._translate("kmainForm", "分析 / 调用"),
            self._translate("kmainForm", "保留对象探测、主动调用与内存检索入口，方便围绕目标对象继续深入。"),
            [self.btnWallbreaker, self.btnCallFunction, self.btnMemSearch],
            2,
        )
        self.gridLayout_4.addWidget(self.dumpCard, 1, 0, 1, 2)
        self.gridLayout_4.addWidget(self.inspectCard, 1, 2, 1, 2)

    def configureHookPanel(self):
        self.gridLayout_7.setContentsMargins(12, 16, 12, 12)
        self.gridLayout_7.setHorizontalSpacing(12)
        self.gridLayout_7.setVerticalSpacing(12)
        self.gridLayout_7.removeItem(self.gridLayout_5)
        self.gridLayout_7.removeItem(self.horizontalLayout)

        self.labHookSummary = QLabel(
            self._translate("kmainForm", "主页只保留高频 Hook 预设和工具入口；复杂模块统一进入工具中心，避免把配置挤在一个界面里。"),
            self.groupBox_2,
        )
        self.labHookSummary.setWordWrap(True)
        self.labHookSummary.setObjectName("sectionHint")
        self.gridLayout_7.addWidget(self.labHookSummary, 0, 0, 1, 1)

        self.labAiFeatureStatusMain = QLabel(self.groupBox_2)
        self.labAiFeatureStatusMain.setWordWrap(True)
        self.labAiFeatureStatusMain.setObjectName("aiStateLabel")
        self.gridLayout_7.addWidget(self.labAiFeatureStatusMain, 1, 0, 1, 1)

        self.quickScriptGroup = QtWidgets.QGroupBox(self._translate("kmainForm", "常用 Hook 预设"), self.groupBox_2)
        self.quickScriptGroup.setObjectName("panelCard")
        self.quickScriptLayout = QtWidgets.QVBoxLayout(self.quickScriptGroup)
        self.quickScriptLayout.setContentsMargins(12, 14, 12, 12)
        self.quickScriptLayout.setSpacing(10)
        self.labQuickScriptHint = QLabel(
            self._translate("kmainForm", "把最常用的 Hook 开关放在主页，适合快速试错；更复杂的链路放到工具中心。"),
            self.quickScriptGroup,
        )
        self.labQuickScriptHint.setWordWrap(True)
        self.labQuickScriptHint.setObjectName("panelHint")
        self.quickScriptLayout.addWidget(self.labQuickScriptHint)
        self.gridLayout_5.setHorizontalSpacing(12)
        self.gridLayout_5.setVerticalSpacing(8)
        self.quickScriptLayout.addLayout(self.gridLayout_5)

        for button in [self.btnMatchMethod, self.btnNatives, self.btnStalker, self.btnTuoke, self.btnCustom, self.btnPatch, self.btnAntiFrida]:
            self.horizontalLayout.removeWidget(button)
            button.hide()

        self.advancedToolGroup = QtWidgets.QGroupBox(self._translate("kmainForm", "工具中心"), self.groupBox_2)
        self.advancedToolGroup.setObjectName("panelCard")
        self.advancedToolLayout = QtWidgets.QVBoxLayout(self.advancedToolGroup)
        self.advancedToolLayout.setContentsMargins(12, 14, 12, 12)
        self.advancedToolLayout.setSpacing(10)
        self.labAdvancedToolHint = QLabel(
            self._translate("kmainForm", "GumTrace、自定义脚本、Native/Java 浏览、Patch、脱壳等能力统一从这里进入，不再占用主页主区域。"),
            self.advancedToolGroup,
        )
        self.labAdvancedToolHint.setWordWrap(True)
        self.labAdvancedToolHint.setObjectName("panelHint")
        self.advancedToolLayout.addWidget(self.labAdvancedToolHint)

        self.advancedButtonsGrid = QtWidgets.QGridLayout()
        self.advancedButtonsGrid.setHorizontalSpacing(10)
        self.advancedButtonsGrid.setVerticalSpacing(10)
        self.cmdOpenCustom = self.buildToolLauncher(self.advancedToolGroup, self.custom)
        self.cmdOpenGumTrace = self.buildToolLauncher(self.advancedToolGroup, self.openGumTraceWorkspace)
        self.cmdOpenInspector = self.buildToolLauncher(self.advancedToolGroup, lambda: self.tabWidget.setCurrentWidget(self.tab))
        self.cmdOpenAssist = self.buildToolLauncher(self.advancedToolGroup, lambda: self.tabWidget.setCurrentWidget(self.tab_7))
        self.cmdPatch = self.buildToolLauncher(self.advancedToolGroup, self.patch)
        self.cmdStalker = self.buildToolLauncher(self.advancedToolGroup, self.stalker)
        self.cmdTuoke = self.buildToolLauncher(self.advancedToolGroup, self.tuoke)
        self.cmdAiSettings = self.buildToolLauncher(self.advancedToolGroup, self.openAiSettings)
        self.advancedButtons = [
            self.cmdOpenCustom,
            self.cmdOpenGumTrace,
            self.cmdOpenInspector,
            self.cmdOpenAssist,
            self.cmdPatch,
            self.cmdStalker,
            self.cmdTuoke,
            self.cmdAiSettings,
        ]
        self.advancedToolLayout.addLayout(self.advancedButtonsGrid)

        self.hookPanelWidget = QtWidgets.QWidget(self.groupBox_2)
        self.hookPanelLayout = QtWidgets.QHBoxLayout(self.hookPanelWidget)
        self.hookPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.hookPanelLayout.setSpacing(12)
        self.hookPanelLayout.addWidget(self.quickScriptGroup, 5)
        self.hookPanelLayout.addWidget(self.advancedToolGroup, 6)
        self.gridLayout_7.addWidget(self.hookPanelWidget, 2, 0, 1, 1)
        self.rebuildAdvancedToolGrid()

    def rebuildAdvancedToolGrid(self):
        if not hasattr(self, "advancedButtonsGrid"):
            return
        while self.advancedButtonsGrid.count():
            item = self.advancedButtonsGrid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self.advancedToolGroup)
        width = self.advancedToolGroup.width() or self.groupBox_2.width()
        columns = 1 if width < 520 else 2
        for index, button in enumerate(self.advancedButtons):
            self.advancedButtonsGrid.addWidget(button, index // columns, index % columns)
        for col in range(columns):
            self.advancedButtonsGrid.setColumnStretch(col, 1)

    def buildToolLauncher(self, parent, callback):
        button = QtWidgets.QCommandLinkButton(parent)
        button.clicked.connect(callback)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumHeight(64)
        button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        return button

    def initLogDock(self):
        if hasattr(self, "logDock"):
            return
        self.logDock = QtWidgets.QDockWidget(self)
        self.logDock.setObjectName("logDock")
        self.logDock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.logDock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable |
            QtWidgets.QDockWidget.DockWidgetMovable |
            QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.logDock.setMinimumWidth(360)
        self.logDock.setWidget(self.groupLogs)
        self.addDockWidget(Qt.RightDockWidgetArea, self.logDock)
        self.logDock.visibilityChanged.connect(self.onLogDockVisibilityChanged)
        self.actionToggleLogDock = QAction(self)
        self.actionToggleLogDock.triggered.connect(self.toggleLogDock)
        self.toolBar.addAction(self.actionToggleLogDock)
        self.onLogDockVisibilityChanged(True)


    def configureLogWidgets(self):
        for editor in [self.txtLogs, self.txtoutLogs]:
            editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            editor.setPlaceholderText(self._translate("kmainForm", "日志将在这里滚动显示..."))
        self.tabHooks.setAlternatingRowColors(True)
        self.tabHooks.verticalHeader().setVisible(False)
        self.txtAiAnalysis.setPlaceholderText(self._translate("kmainForm", "AI 分析结果会显示在这里")) if hasattr(self, "txtAiAnalysis") else None

    def applyWorkbenchTheme(self):
        self.setStyleSheet("""
        QMainWindow, QDialog {
            background: #f4f7fb;
        }
        QGroupBox {
            background: #ffffff;
            border: 1px solid #d7dfeb;
            border-radius: 10px;
            margin-top: 14px;
            font-weight: 600;
            color: #16324a;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 4px;
        }
        QPushButton {
            background: #eef4ff;
            border: 1px solid #c8d7ee;
            border-radius: 8px;
            padding: 10px 12px;
        }
        QPushButton:hover {
            background: #deebff;
            border-color: #8fb2f0;
        }
        QPushButton:pressed {
            background: #d3e4ff;
        }
        QPushButton:disabled {
            background: #eef1f4;
            color: #93a0b0;
            border-color: #d6dce5;
        }
        QCommandLinkButton {
            background: #f8fbff;
            border: 1px solid #d7dfeb;
            border-radius: 10px;
            text-align: left;
            padding: 10px 14px;
            color: #16324a;
        }
        QCommandLinkButton:hover {
            background: #edf5ff;
            border-color: #91b4ec;
        }
        QCommandLinkButton::description {
            color: #60738a;
        }
        QCheckBox {
            spacing: 8px;
            padding: 4px 0;
        }
        QLineEdit, QPlainTextEdit, QTableWidget, QListWidget, QComboBox {
            background: #fbfcff;
            border: 1px solid #cfd8e5;
            border-radius: 8px;
            padding: 6px;
            selection-background-color: #4f8cff;
        }
        QTableWidget {
            gridline-color: #e5ecf5;
            alternate-background-color: #f5f9ff;
        }
        QHeaderView::section {
            background: #eef4ff;
            border: none;
            border-right: 1px solid #d9e3f0;
            padding: 6px;
            font-weight: 600;
        }
        QTabWidget::pane {
            border: 1px solid #d7dfeb;
            background: #ffffff;
            border-radius: 10px;
            top: -1px;
        }
        QTabBar::tab {
            background: #e9eff8;
            border: 1px solid #d0dbe9;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            padding: 8px 16px;
            margin-right: 4px;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #1b5fd1;
        }
        QToolBar, QMenuBar, QStatusBar {
            background: #ffffff;
        }
        QDockWidget {
            background: #ffffff;
            border-top: 1px solid #d7dfeb;
        }
        QDockWidget::title {
            background: #eef4ff;
            text-align: left;
            padding: 6px 12px;
            color: #16324a;
            font-weight: 600;
        }
        QFrame#summaryCard {
            background: #ffffff;
            border: 1px solid #d7dfeb;
            border-radius: 12px;
        }
        QLabel#panelHint, QLabel#sectionHint, QLabel#aiStateLabel, QLabel#summaryCaption {
            color: #60738a;
        }
        QLabel#summaryTitle {
            color: #60738a;
            font-weight: 600;
        }
        QLabel#summaryValue {
            font-size: 18px;
            font-weight: 700;
            color: #16324a;
        }
        QLabel#summaryValueCompact {
            color: #16324a;
            font-weight: 600;
        }
        QScrollArea {
            border: none;
            background: transparent;
        }
        """)

    def initLogTools(self):
        self.aiAnalysisTab = QtWidgets.QWidget()
        self.aiAnalysisTab.setObjectName("aiAnalysisTab")
        self.aiAnalysisLayout = QtWidgets.QVBoxLayout(self.aiAnalysisTab)
        self.aiAnalysisLayout.setContentsMargins(8, 8, 8, 8)
        self.aiAnalysisToolbar = QtWidgets.QHBoxLayout()
        self.aiAnalysisToolbar.setContentsMargins(0, 0, 0, 0)
        self.labLogStatus = QLabel(self._translate("kmainForm", "当前日志：实时输出"))
        self.aiAnalysisToolbar.addWidget(self.labLogStatus)
        self.aiAnalysisToolbar.addStretch(1)
        self.btnOpenLogFile = QtWidgets.QPushButton(self._translate("kmainForm", "打开日志文件"))
        self.btnRestoreLiveLog = QtWidgets.QPushButton(self._translate("kmainForm", "恢复实时日志"))
        self.btnAnalyzeLog = QtWidgets.QPushButton(self._translate("kmainForm", "AI 分析日志"))
        self.aiAnalysisToolbar.addWidget(self.btnOpenLogFile)
        self.aiAnalysisToolbar.addWidget(self.btnRestoreLiveLog)
        self.aiAnalysisToolbar.addWidget(self.btnAnalyzeLog)
        self.aiAnalysisLayout.addLayout(self.aiAnalysisToolbar)
        self.txtAiAnalysis = QtWidgets.QPlainTextEdit(self.aiAnalysisTab)
        self.txtAiAnalysis.setReadOnly(True)
        self.aiAnalysisLayout.addWidget(self.txtAiAnalysis)
        self.groupLogs.addTab(self.aiAnalysisTab, self._translate("kmainForm", "AI 分析"))

        self.outputLogToolbarWidget = QtWidgets.QWidget(self.tab_5)
        self.outputLogToolbarLayout = QtWidgets.QHBoxLayout(self.outputLogToolbarWidget)
        self.outputLogToolbarLayout.setContentsMargins(0, 0, 0, 0)
        self.labOutputLogView = QLabel(self._translate("kmainForm", "输出日志视图"))
        self.outputLogToolbarLayout.addWidget(self.labOutputLogView)
        self.outputLogToolbarLayout.addStretch(1)
        self.gridLayout_2.addWidget(self.outputLogToolbarWidget, 0, 0, 1, 1)
        self.gridLayout_2.removeWidget(self.txtoutLogs)
        self.gridLayout_2.addWidget(self.txtoutLogs, 1, 0, 1, 1)

        for button in [self.btnOpenLogFile, self.btnRestoreLiveLog, self.btnAnalyzeLog]:
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(38)
        self.txtAiAnalysis.setPlaceholderText(self._translate("kmainForm", "AI 分析结果会显示在这里"))
        self.btnOpenLogFile.clicked.connect(self.openLogFile)
        self.btnRestoreLiveLog.clicked.connect(self.restoreLiveLog)
        self.btnAnalyzeLog.clicked.connect(self.analyzeLogWithAi)

    def initSettingsMenu(self):
        self.menuSettings = self.menubar.addMenu(self._translate("kmainForm", "设置"))
        self.actionAiSettings = QAction(self._translate("kmainForm", "AI 设置"), self)
        self.actionAiSettings.triggered.connect(self.openAiSettings)
        self.menuSettings.addAction(self.actionAiSettings)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionAiSettings)


    def initGumTraceWorkspace(self):
        self.gumTraceTab = QtWidgets.QWidget()
        self.gumTraceTab.setObjectName("gumTraceTab")
        self.gumTraceTabLayout = QtWidgets.QVBoxLayout(self.gumTraceTab)
        self.gumTraceTabLayout.setContentsMargins(12, 12, 12, 12)
        self.gumTraceTabLayout.setSpacing(12)
        self.labGumTraceWorkbenchHint = QLabel(self.gumTraceTab)
        self.labGumTraceWorkbenchHint.setWordWrap(True)
        self.labGumTraceWorkbenchHint.setObjectName("sectionHint")
        self.gumTraceTabLayout.addWidget(self.labGumTraceWorkbenchHint)

        self.gumTraceSplitter = QtWidgets.QSplitter(Qt.Horizontal, self.gumTraceTab)
        self.gumTraceSplitter.setChildrenCollapsible(False)
        self.gumTraceTabLayout.addWidget(self.gumTraceSplitter, 1)

        self.gumTraceConfigGroup = QtWidgets.QGroupBox(self.gumTraceSplitter)
        self.gumTraceConfigGroup.setObjectName("panelCard")
        self.gumTraceConfigLayout = QtWidgets.QVBoxLayout(self.gumTraceConfigGroup)
        self.gumTraceConfigLayout.setContentsMargins(12, 14, 12, 12)
        self.gumTraceConfigLayout.setSpacing(10)
        self.labGumTraceConfigHint = QLabel(self.gumTraceConfigGroup)
        self.labGumTraceConfigHint.setWordWrap(True)
        self.labGumTraceConfigHint.setObjectName("panelHint")
        self.gumTraceConfigLayout.addWidget(self.labGumTraceConfigHint)

        self.gumTraceFormLayout = QtWidgets.QFormLayout()
        self.gumTraceFormLayout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.gumTraceFormLayout.setHorizontalSpacing(12)
        self.gumTraceFormLayout.setVerticalSpacing(10)
        self.txtGumTraceName = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceFileName = QLineEdit(self.gumTraceConfigGroup)
        self.cmbGumTraceMode = QtWidgets.QComboBox(self.gumTraceConfigGroup)
        self.cmbGumTraceMode.addItem("manual", GumTraceUtil.MODE_MANUAL)
        self.cmbGumTraceMode.addItem("offset", GumTraceUtil.MODE_OFFSET)
        self.cmbGumTraceMode.addItem("export", GumTraceUtil.MODE_EXPORT)
        self.txtGumTraceTraceModules = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceTriggerModule = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceOffsets = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceExports = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceOutput = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceAllowedThreads = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceThreadId = QLineEdit(self.gumTraceConfigGroup)
        self.txtGumTraceOptions = QLineEdit(self.gumTraceConfigGroup)
        self.gumTraceFormLayout.addRow("Alias", self.txtGumTraceName)
        self.gumTraceFormLayout.addRow("File", self.txtGumTraceFileName)
        self.gumTraceFormLayout.addRow("Mode", self.cmbGumTraceMode)
        self.gumTraceFormLayout.addRow("Trace modules", self.txtGumTraceTraceModules)
        self.gumTraceFormLayout.addRow("Trigger module", self.txtGumTraceTriggerModule)
        self.gumTraceFormLayout.addRow("Offsets", self.txtGumTraceOffsets)
        self.gumTraceFormLayout.addRow("Exports", self.txtGumTraceExports)
        self.gumTraceFormLayout.addRow("Output", self.txtGumTraceOutput)
        self.gumTraceFormLayout.addRow("Allowed threads", self.txtGumTraceAllowedThreads)
        self.gumTraceFormLayout.addRow("GumTrace thread", self.txtGumTraceThreadId)
        self.gumTraceFormLayout.addRow("Options", self.txtGumTraceOptions)
        self.gumTraceConfigLayout.addLayout(self.gumTraceFormLayout)

        self.gumTraceCheckLayout = QtWidgets.QHBoxLayout()
        self.chkGumTraceStopOnLeave = QtWidgets.QCheckBox(self.gumTraceConfigGroup)
        self.chkGumTraceAllowRepeat = QtWidgets.QCheckBox(self.gumTraceConfigGroup)
        self.chkGumTraceAutoAddHook = QtWidgets.QCheckBox(self.gumTraceConfigGroup)
        self.chkGumTraceOpenDir = QtWidgets.QCheckBox(self.gumTraceConfigGroup)
        for checkbox in [self.chkGumTraceStopOnLeave, self.chkGumTraceAllowRepeat, self.chkGumTraceAutoAddHook, self.chkGumTraceOpenDir]:
            self.gumTraceCheckLayout.addWidget(checkbox)
        self.gumTraceCheckLayout.addStretch(1)
        self.gumTraceConfigLayout.addLayout(self.gumTraceCheckLayout)

        self.gumTraceActionLayout = QtWidgets.QGridLayout()
        self.gumTraceActionLayout.setHorizontalSpacing(10)
        self.gumTraceActionLayout.setVerticalSpacing(10)
        self.btnGumTraceSaveConfig = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        self.btnGumTracePreview = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        self.btnGumTraceSaveCustom = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        self.btnGumTraceActivate = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        self.btnGumTraceOpenCustom = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        self.btnGumTraceUpload = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        self.btnGumTraceDownload = QtWidgets.QPushButton(self.gumTraceConfigGroup)
        action_buttons = [self.btnGumTraceSaveConfig, self.btnGumTracePreview, self.btnGumTraceSaveCustom, self.btnGumTraceActivate, self.btnGumTraceOpenCustom, self.btnGumTraceUpload, self.btnGumTraceDownload]
        for index, button in enumerate(action_buttons):
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)
            self.gumTraceActionLayout.addWidget(button, index // 2, index % 2)
        self.gumTraceConfigLayout.addLayout(self.gumTraceActionLayout)
        self.gumTraceConfigLayout.addStretch(1)

        self.gumTracePreviewGroup = QtWidgets.QGroupBox(self.gumTraceSplitter)
        self.gumTracePreviewGroup.setObjectName("panelCard")
        self.gumTracePreviewLayout = QtWidgets.QVBoxLayout(self.gumTracePreviewGroup)
        self.gumTracePreviewLayout.setContentsMargins(12, 14, 12, 12)
        self.gumTracePreviewLayout.setSpacing(10)
        self.labGumTracePreviewHint = QLabel(self.gumTracePreviewGroup)
        self.labGumTracePreviewHint.setWordWrap(True)
        self.labGumTracePreviewHint.setObjectName("panelHint")
        self.gumTracePreviewLayout.addWidget(self.labGumTracePreviewHint)
        self.labGumTracePreviewSummary = QLabel(self.gumTracePreviewGroup)
        self.labGumTracePreviewSummary.setWordWrap(True)
        self.labGumTracePreviewSummary.setObjectName("summaryCaption")
        self.gumTracePreviewLayout.addWidget(self.labGumTracePreviewSummary)
        self.txtGumTracePreview = QtWidgets.QPlainTextEdit(self.gumTracePreviewGroup)
        self.txtGumTracePreview.setReadOnly(True)
        self.gumTracePreviewLayout.addWidget(self.txtGumTracePreview, 1)
        self.gumTraceSplitter.setStretchFactor(0, 5)
        self.gumTraceSplitter.setStretchFactor(1, 6)
        self.tabWidget.addTab(self.gumTraceTab, "")

        self.txtGumTraceName.textChanged.connect(self.syncGumTraceFileName)
        self.cmbGumTraceMode.currentIndexChanged.connect(self.updateGumTraceModeFields)
        self.btnGumTraceSaveConfig.clicked.connect(self.saveGumTraceConfig)
        self.btnGumTracePreview.clicked.connect(self.renderGumTracePreview)
        self.btnGumTraceSaveCustom.clicked.connect(self.applyGumTraceScript)
        self.btnGumTraceActivate.clicked.connect(self.applyGumTraceScriptAndActivate)
        self.btnGumTraceOpenCustom.clicked.connect(self.custom)
        self.btnGumTraceUpload.clicked.connect(self.PushGumTraceLib)
        self.btnGumTraceDownload.clicked.connect(self.pullGumTraceLog)
        for widget in [self.txtGumTraceName, self.txtGumTraceFileName, self.txtGumTraceTraceModules, self.txtGumTraceTriggerModule, self.txtGumTraceOffsets, self.txtGumTraceExports, self.txtGumTraceOutput, self.txtGumTraceAllowedThreads, self.txtGumTraceThreadId, self.txtGumTraceOptions]:
            widget.textChanged.connect(self.renderGumTracePreview)
        for checkbox in [self.chkGumTraceStopOnLeave, self.chkGumTraceAllowRepeat, self.chkGumTraceAutoAddHook, self.chkGumTraceOpenDir]:
            checkbox.stateChanged.connect(self.renderGumTracePreview)
        self.cmbGumTraceMode.currentIndexChanged.connect(self.renderGumTracePreview)
        self.updateGumTraceModeFields()

    def syncGumTraceFileName(self):
        name = self.txtGumTraceName.text().strip()
        current = self.txtGumTraceFileName.text().strip()
        if not name:
            return
        if len(current) <= 0 or current.startswith("gumtrace_") or current == current.lower().replace(" ", "_"):
            normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower() or "gumtrace_script"
            self.txtGumTraceFileName.setText(normalized + ".js")

    def updateGumTraceModeFields(self):
        mode = self.cmbGumTraceMode.currentData()
        self.txtGumTraceOffsets.setEnabled(mode == GumTraceUtil.MODE_OFFSET)
        self.txtGumTraceExports.setEnabled(mode == GumTraceUtil.MODE_EXPORT)

    def currentGumTraceConfig(self):
        return {
            "name": self.txtGumTraceName.text().strip() or self.trText("GumTrace 配置脚本", "GumTrace profile script"),
            "fileName": self.txtGumTraceFileName.text().strip() or "gumtrace_script.js",
            "mode": self.cmbGumTraceMode.currentData() or GumTraceUtil.MODE_MANUAL,
            "traceModuleWhitelist": self.txtGumTraceTraceModules.text().strip(),
            "triggerModuleName": self.txtGumTraceTriggerModule.text().strip() or "libtarget.so",
            "triggerOffsets": self.txtGumTraceOffsets.text().strip(),
            "triggerExports": self.txtGumTraceExports.text().strip(),
            "traceOutputPath": self.txtGumTraceOutput.text().strip() or "/data/local/tmp/gumtrace.log",
            "allowedThreadIds": self.txtGumTraceAllowedThreads.text().strip(),
            "traceThreadId": self.txtGumTraceThreadId.text().strip() or "0",
            "traceOptions": self.txtGumTraceOptions.text().strip() or "0",
            "stopTraceOnLeave": self.chkGumTraceStopOnLeave.isChecked(),
            "allowRepeatedTrace": self.chkGumTraceAllowRepeat.isChecked(),
            "autoAddHook": self.chkGumTraceAutoAddHook.isChecked(),
            "openDirAfterDownload": self.chkGumTraceOpenDir.isChecked(),
        }

    def loadGumTraceConfig(self):
        config_data = conf.read_section("gumtrace")
        if not hasattr(self, "gumTraceTab"):
            return
        self.txtGumTraceName.setText(config_data.get("name", "GumTrace Live Profile"))
        self.txtGumTraceFileName.setText(config_data.get("filename", "gumtrace_live_profile.js"))
        mode = config_data.get("mode", GumTraceUtil.MODE_MANUAL)
        index = max(0, self.cmbGumTraceMode.findData(mode))
        self.cmbGumTraceMode.setCurrentIndex(index)
        self.txtGumTraceTraceModules.setText(config_data.get("tracemodulewhitelist", "libtarget.so"))
        self.txtGumTraceTriggerModule.setText(config_data.get("triggermodulename", "libtarget.so"))
        self.txtGumTraceOffsets.setText(config_data.get("triggeroffsets", "0x1234"))
        self.txtGumTraceExports.setText(config_data.get("triggerexports", "SSL_read,SSL_write"))
        self.txtGumTraceOutput.setText(config_data.get("traceoutputpath", "/data/local/tmp/gumtrace.log"))
        self.txtGumTraceAllowedThreads.setText(config_data.get("allowedthreadids", ""))
        self.txtGumTraceThreadId.setText(config_data.get("tracethreadid", "0"))
        self.txtGumTraceOptions.setText(config_data.get("traceoptions", "0"))
        self.chkGumTraceStopOnLeave.setChecked(config_data.get("stoptraceonleave", "True") != "False")
        self.chkGumTraceAllowRepeat.setChecked(config_data.get("allowrepeatedtrace", "False") == "True")
        self.chkGumTraceAutoAddHook.setChecked(config_data.get("autoaddhook", "True") != "False")
        self.chkGumTraceOpenDir.setChecked(config_data.get("opendirafterdownload", "True") != "False")
        self.updateGumTraceModeFields()
        self.renderGumTracePreview()

    def saveGumTraceConfig(self):
        config_data = self.currentGumTraceConfig()
        for key, value in config_data.items():
            conf.write("gumtrace", key, value)
        self.renderGumTracePreview()
        QMessageBox().information(self, "hint", self.trText("GumTrace 配置已保存", "GumTrace settings saved"))

    def renderGumTracePreview(self):
        config_data = self.currentGumTraceConfig()
        script = GumTraceUtil.build_gumtrace_script(config_data)
        self.txtGumTracePreview.setPlainText(script)
        summary = self.trText("模式：", "Mode: ") + str(config_data["mode"]) + "\n" + self.trText("模块白名单：", "Trace modules: ") + (config_data["traceModuleWhitelist"] or "-") + "\n" + self.trText("线程过滤：", "Thread filter: ") + (config_data["allowedThreadIds"] or self.trText("不限", "all"))
        self.labGumTracePreviewSummary.setText(summary)
        self.refreshOverviewCards()
        return script

    def syncCustomHooksToMain(self):
        if len(self.customForm.customHooks) > 0:
            self.hooksData["custom"] = []
            for item in self.customForm.customHooks:
                self.hooksData["custom"].append({"class": item["name"], "method": item["fileName"], "bak": item["bak"], "fileName": item["fileName"]})
        elif "custom" in self.hooksData:
            self.hooksData.pop("custom")
        self.updateTabHooks()

    def applyGumTraceScript(self):
        script = self.renderGumTracePreview()
        config_data = self.currentGumTraceConfig()
        self.customForm.initData()
        save_path = self.customForm.upsertCustomScript({"name": config_data["name"], "fileName": config_data["fileName"], "bak": self.trText("由 GumTrace 配置面板生成", "Generated by GumTrace workbench")}, script, add_to_hook=False)
        self.customForm.openCustomScript(config_data["fileName"])
        QMessageBox().information(self, "hint", self.trText("GumTrace 脚本已保存：", "GumTrace script saved: ") + save_path)
        self.refreshOverviewCards()

    def applyGumTraceScriptAndActivate(self):
        script = self.renderGumTracePreview()
        config_data = self.currentGumTraceConfig()
        self.customForm.initData()
        add_to_hook = self.chkGumTraceAutoAddHook.isChecked()
        save_path = self.customForm.upsertCustomScript({"name": config_data["name"], "fileName": config_data["fileName"], "bak": self.trText("由 GumTrace 配置面板生成", "Generated by GumTrace workbench")}, script, add_to_hook=add_to_hook)
        self.customForm.openCustomScript(config_data["fileName"])
        if add_to_hook:
            self.syncCustomHooksToMain()
        QMessageBox().information(self, "hint", self.trText("GumTrace 脚本已生成并更新：", "GumTrace script generated and updated: ") + save_path)
        self.refreshOverviewCards()

    def openGumTraceWorkspace(self):
        self.tabWidget.setCurrentWidget(self.gumTraceTab)

    def openGumTraceLogDirectory(self):
        local_dir = os.path.abspath("./logs/gumtrace")
        if os.path.exists(local_dir) is False:
            os.makedirs(local_dir)
        QDesktopServices.openUrl(QUrl.fromLocalFile(local_dir))

    def refreshOverviewCards(self):
        if hasattr(self, "labAssistGumTraceRemote"):
            self.labAssistGumTraceRemote.setText(self.trText("默认远端日志：", "Default remote log: ") + (self.txtGumTraceOutput.text().strip() if hasattr(self, "txtGumTraceOutput") else "/data/local/tmp/gumtrace.log"))
            self.labAssistGumTraceLocal.setText(self.trText("本地下载目录：", "Local download dir: ") + os.path.abspath("./logs/gumtrace"))
            self.labAssistGumTraceFilters.setText(self.trText("线程 / 模块过滤：", "Thread / module filters: ") + (self.txtGumTraceAllowedThreads.text().strip() or self.trText("不限", "all")) + " / " + (self.txtGumTraceTraceModules.text().strip() or "-"))
        if hasattr(self, "labLogStatus"):
            if self.currentLogMode == "file" and self.loadedLogPath:
                self.labLogStatus.setText(self.trText("当前日志：", "Current log: ") + os.path.basename(self.loadedLogPath))
            else:
                self.labLogStatus.setText(self.trText("当前日志：实时输出", "Current log: live output"))

    def refreshAiState(self):
        available = self.aiService.is_available()
        missing_message = self.aiService.missing_message("English" if self.isEnglish() else "China")
        self.btnAnalyzeLog.setEnabled(available)
        self.customForm.refreshAiState()
        if hasattr(self, "labAiFeatureStatusMain"):
            if available:
                self.labAiFeatureStatusMain.setText(self.trText("AI 能力：已配置，可在“自定义”模块生成 Hook，并在日志页签执行 AI 分析。", "AI ready: use the Custom module to generate hooks and the log tab to run AI analysis."))
            else:
                self.labAiFeatureStatusMain.setText(self.trText("AI 能力：", "AI status: ") + missing_message)
        if hasattr(self, "aiSummaryCard"):
            self.aiSummaryCard.valueLabel.setText(self.trText("已配置，可写 Hook 与分析日志", "Configured for hook generation and log analysis") if available else missing_message)
        if hasattr(self, "txtAiAnalysis") and not available:
            self.txtAiAnalysis.setPlainText(missing_message)
        self.refreshOverviewCards()

    def openAiSettings(self):
        self.aiSettingsForm.loadConfig()
        res = self.aiSettingsForm.exec()
        if res == 0:
            return
        self.refreshAiState()

    def currentLogText(self):
        if self.currentLogMode == "file":
            return self.loadedLogContent
        return "\n".join(self.liveOutputLogBuffer)

    def openLogFile(self):
        filepath = QFileDialog.getOpenFileName(self, self.trText("打开日志文件", "Open log file"), "./logs", "Log Files (*.txt *.log);;All Files (*)")
        if not filepath[0]:
            return
        with open(filepath[0], "r", encoding="utf-8", errors="ignore") as log_file:
            self.loadedLogContent = log_file.read()
        self.loadedLogPath = filepath[0]
        self.currentLogMode = "file"
        self.txtoutLogs.setPlainText(self.loadedLogContent)
        self.showLogDock(self.tab_5)
        self.labLogStatus.setText(self.trText("当前日志：", "Current log: ") + os.path.basename(filepath[0]))
        self.log(self.trText("已加载日志文件：", "Loaded log file: ") + filepath[0])
        self.refreshOverviewCards()

    def restoreLiveLog(self):
        self.currentLogMode = "live"
        self.loadedLogPath = ""
        self.loadedLogContent = ""
        self.txtoutLogs.setPlainText("\n".join(self.liveOutputLogBuffer))
        self.labLogStatus.setText(self.trText("当前日志：实时输出", "Current log: live output"))
        self.showLogDock(self.tab_5)
        self.refreshOverviewCards()

    def analyzeLogWithAi(self):
        if not self.aiService.is_available():
            self.refreshAiState()
            QMessageBox().information(self, "hint", self.aiService.missing_message("English" if self.isEnglish() else "China"))
            return
        content = self.currentLogText()
        if len(content.strip()) <= 0:
            QMessageBox().information(self, "hint", self.trText("当前没有可分析的日志内容", "There is no log content available for AI analysis"))
            return
        self.btnAnalyzeLog.setEnabled(False)
        self.btnAnalyzeLog.setText(self.trText("分析中...", "Analyzing..."))
        self.txtAiAnalysis.setPlainText(self.trText("AI 正在分析日志，请稍候...", "AI is analyzing the log, please wait..."))
        self.showLogDock(self.aiAnalysisTab)
        self.aiWorker = AiWorker(self.aiService.analyze_log, content)
        self.aiWorker.success.connect(self.onAiAnalysisSuccess)
        self.aiWorker.error.connect(self.onAiAnalysisFailed)
        self.aiWorker.start()

    def onAiAnalysisSuccess(self, result):
        self.btnAnalyzeLog.setEnabled(self.aiService.is_available())
        self.btnAnalyzeLog.setText(self.trText("AI 分析日志", "AI analyze log"))
        self.txtAiAnalysis.setPlainText(result)
        self.showLogDock(self.aiAnalysisTab)

    def onAiAnalysisFailed(self, message):
        self.btnAnalyzeLog.setEnabled(self.aiService.is_available())
        self.btnAnalyzeLog.setText(self.trText("AI 分析日志", "AI analyze log"))
        self.txtAiAnalysis.setPlainText(message)
        self.showLogDock(self.aiAnalysisTab)
        QMessageBox().information(self, "hint", message)

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
        appinfo = self.th.default_api.searchinfo("export", self.txtModule.text().split("----")[0])
        self.searchAppInfoRes(appinfo)

    def searchSymbol(self):
        if len(self.txtModule.text()) <= 0:
            QMessageBox().information(self, "hint", self._translate("kmainForm","未填写模块名称"))
            return
        appinfo=self.th.default_api.searchinfo("symbol", self.txtModule.text().split("----")[0])
        self.searchAppInfoRes(appinfo)

    def searchMethod(self):
        if len(self.txtClass.text()) <= 0:
            QMessageBox().information(self, "hint",self._translate("kmainForm","未填写类型名称"))
            return
        appinfo=self.th.default_api.searchinfo("method", self.txtClass.text())
        self.searchAppInfoRes(appinfo)

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
        datestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S   ')
        line = datestr + logstr
        self.liveOutputLogBuffer.append(line)
        if len(self.liveOutputLogBuffer) > 5000:
            self.liveOutputLogBuffer = self.liveOutputLogBuffer[-5000:]
        if self.actionConsoleLog.isChecked() == False and self.currentLogMode == "live":
            self.txtoutLogs.appendPlainText(line)
        self.outlogger.logger.debug(logstr)
        if "default.js init hook success" in logstr:
            QMessageBox().information(self, "hint", self._translate("kmainForm", "附加进程成功"))

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
        self.liveOutputLogBuffer = []
        self.loadedLogContent = ""
        self.loadedLogPath = ""
        self.currentLogMode = "live"
        self.txtoutLogs.setPlainText("")
        if hasattr(self, "labLogStatus"):
            self.labLogStatus.setText(self._translate("kmainForm", "当前日志：实时输出"))

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

    def PushFridaServerNormal(self,arch):
        try:
            name32=""
            name64=""
            if self.fridaName!="":
                name32=self.fridaName+"32"
                name64=self.fridaName+"64"
            if arch=="arm":
                arch32="arm"
                arch64="arm64"
            elif arch=="x86":
                arch32="x86"
                arch64="x86_64"

            res = CmdUtil.execCmd(f"adb push ./exec/frida-server-{self.curFridaVer}-android-{arch32} /data/local/tmp/"+name32)
            self.log(res)
            if "error" in res:
                QMessageBox().information(self, "hint",self._translate("kmainForm", "上传失败.") + res)
                return
            res = CmdUtil.execCmd(f"adb push ./exec/frida-server-{self.curFridaVer}-android-{arch64} /data/local/tmp/"+name64)
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

    def PushFridaServer(self):
        self.PushFridaServerNormal("arm")

    def PushFridaServerX86(self):
        self.PushFridaServerNormal("x86")

    def PushGumTraceLib(self):
        local_path = "./exec/libGumTrace.so"
        remote_path = "/data/local/tmp/libGumTrace.so"
        if os.path.exists(local_path) is False:
            QMessageBox().information(self, "hint", self.trText("未找到 GumTrace 库文件：", "GumTrace library not found: ") + local_path)
            return
        try:
            res = CmdUtil.execCmd(f"adb push {local_path} {remote_path}")
            self.log(res)
            if "file pushed" not in res and "KB/s" not in res:
                QMessageBox().information(self, "hint", self.trText("上传 GumTrace 失败，可能未连接设备。", "Failed to upload GumTrace. The device may not be connected.") + res)
                return
            chmod_res = CmdUtil.adbshellCmd(f"chmod 0777 {remote_path}")
            self.log(chmod_res)
            if "invalid" in chmod_res:
                QMessageBox().information(self, "hint", self.trText("GumTrace 上传完成，但设置权限失败。请确认 su/cmd 切换是否正确。", "GumTrace upload finished, but chmod failed. Check the selected su/cmd mode."))
                return
            QMessageBox().information(self, "hint", self.trText("GumTrace 上传完成。默认已放到 /data/local/tmp/libGumTrace.so；若 dlopen 失败，可尝试 adb shell setenforce 0。", "GumTrace uploaded to /data/local/tmp/libGumTrace.so. If dlopen fails, try: adb shell setenforce 0."))
        except Exception as ex:
            QMessageBox().information(self, "hint", self.trText("上传 GumTrace 异常：", "Unexpected GumTrace upload error: ") + str(ex))

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
        QMessageBox().information(self, "hint", self._translate("kmainForm",  "下载完成.输出结果在目录./fartdump/%s/") % pname)

    def pullGumTraceLog(self):
        package_candidates = []
        for package_name in [self.labPackage.text().strip(), self.txtProcessName.text().strip()]:
            if len(package_name) > 0 and package_name not in package_candidates:
                package_candidates.append(package_name)
        remote_patterns = ["/data/local/tmp/gumtrace*.log", "/sdcard/gumtrace*.log"]
        if hasattr(self, "txtGumTraceOutput"):
            custom_output = self.txtGumTraceOutput.text().strip()
            if len(custom_output) > 0 and custom_output not in remote_patterns:
                remote_patterns.insert(0, custom_output)
        for package_name in package_candidates:
            remote_patterns.append(f"/data/data/{package_name}/files/gumtrace*.log")
            remote_patterns.append(f"/data/user/0/{package_name}/files/gumtrace*.log")
        search_cmd = "for p in %s; do if [ -f \"$p\" ]; then echo \"$p\"; fi; done | head -n 1" % " ".join(remote_patterns)
        search_res = CmdUtil.adbshellCmd(search_cmd)
        self.log(search_res)
        remote_path = self.firstShellOutputLine(search_res)
        if len(remote_path) <= 0:
            QMessageBox().information(self, "hint", self.trText("未找到 GumTrace 日志。默认会搜索 /data/local/tmp、/sdcard 以及当前包名的 files 目录。", "No GumTrace log was found. Searched /data/local/tmp, /sdcard and the current package files directories."))
            return

        export_path = remote_path
        if not (remote_path.startswith("/sdcard/") or remote_path.startswith("/data/local/tmp/")):
            export_dir = "/sdcard/gumtrace_export"
            export_path = export_dir + "/" + os.path.basename(remote_path)
            export_res = CmdUtil.adbshellCmd("mkdir -p %s && cp %s %s && chmod 0666 %s" % (export_dir, remote_path, export_path, export_path))
            self.log(export_res)
            if "No such file" in export_res or "not found" in export_res:
                QMessageBox().information(self, "hint", self.trText("复制 GumTrace 日志到 /sdcard 失败：", "Failed to copy GumTrace log to /sdcard: ") + export_res)
                return

        local_dir = "./logs/gumtrace"
        if os.path.exists(local_dir) is False:
            os.makedirs(local_dir)
        base_name = os.path.basename(export_path)
        name_root, name_ext = os.path.splitext(base_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = os.path.join(local_dir, "%s_%s%s" % (name_root, timestamp, name_ext or ".log"))
        pull_res = CmdUtil.execCmd("adb pull %s %s" % (export_path, local_path))
        self.log(pull_res)
        if "does not exist" in pull_res or "error" in pull_res.lower() or "failed" in pull_res.lower():
            QMessageBox().information(self, "hint", self.trText("下载 GumTrace 日志失败：", "Failed to download GumTrace log: ") + pull_res)
            return
        self.refreshOverviewCards()
        QMessageBox().information(self, "hint", self.trText("GumTrace 日志下载完成：", "GumTrace log downloaded: ") + local_path)
        should_open_dir = hasattr(self, "chkGumTraceOpenDir") and self.chkGumTraceOpenDir.isChecked()
        if should_open_dir:
            self.openGumTraceLogDirectory()

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

        pathRes= CmdUtil.execCmdData("adb shell pm path %s" % packageName)
        pathRes=pathRes.replace("package:","")
        if os.path.exists("./apks") == False:
            os.makedirs("./apks")
            
        for path in pathRes.split("\n"):
            if "apk" not in path:
                continue
            cmd = "adb pull %s ./apks/%s.apk" % (path, packageName)
            res = CmdUtil.execCmd(cmd)
            self.log(res)
        if "error" in res:
            QMessageBox().information(self, "hint", res)
        else:
            QMessageBox().information(self, "hint", packageName +self._translate("kmainForm", ".apk下载成功.输出结果在目录./apks/"))


    def ReplaceSh(self,rfile,wfile,name):
        data = FileUtil.readFile(rfile)
        adb = "adb"
        if platform.system() == "Darwin":
            adb = "%adb%"
        if self.connType == "wifi":
            data = data.replace("%fridaName%", name + " -l 0.0.0.0:" + self.wifi_port)

            data=data.replace("%customPort%",f"{adb} forward tcp:{self.wifi_port} tcp:{self.wifi_port}")
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
            if adbPath=="":
                adbPath="adb"
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

    def refreshHookHeaders(self):
        if self.isEnglish():
            self.header = ["name", "class or func", "func", "bak"]
        else:
            self.header = ["名称", "类名/模块名", "函数", "备注"]
        self.tabHooks.setHorizontalHeaderLabels(self.header)

    def refreshHookMetadataLanguage(self):
        preset_keys = {
            "r0capture", "javaEnc", "hookEvent", "RegisterNative", "ArtMethod", "libArm",
            "sslpining", "anti_debug", "root_bypass", "webview_debug", "okhttp_logger",
            "shared_prefs_watch", "sqlite_logger", "clipboard_monitor", "intent_monitor",
        }
        for key in preset_keys:
            if key in self.hooksData and key in self.typeData and isinstance(self.hooksData[key], dict):
                self.hooksData[key]["bak"] = self.typeData[key].get("bak", self.hooksData[key].get("bak", ""))

    def refreshChildTranslations(self):
        for form in [self.customForm, self.aiSettingsForm]:
            if hasattr(form, "refreshTranslations"):
                form.refreshTranslations()

    def retranslateDynamicUi(self):
        self.refreshHookHeaders()
        self.groupBox.setTitle(self.trText("功能(附加进程后使用)", "Functions (post-attach)"))
        self.groupBox_2.setTitle(self.trText("hook多选(附加进程前使用)", "Hook selection (pre-attach)"))
        if hasattr(self, "labAiFeatureStatusMain"):
            self.labAiFeatureStatusMain.setText(
                self.trText("AI 状态：已配置后可在“自定义”中写 Hook，并在日志页中分析日志。", "AI status: once configured, use Custom to write hooks and analyze logs in the log tabs.")
                if self.aiService.is_available() else
                self.trText("AI 状态：", "AI status: ") + self.aiService.missing_message("English" if self.isEnglish() else "China")
            )
        if hasattr(self, "btnGumTracePanel"):
            self.btnGumTracePanel.setText(self.trText("GumTrace", "GumTrace"))
        self.chkRootBypass.setText("root bypass")
        self.chkWebViewDebug.setText("webview debug")
        self.chkOkHttpLogger.setText("okhttp logger")
        self.chkSharedPrefsWatch.setText("shared prefs")
        self.chkSQLiteLogger.setText("sqlite logger")
        self.chkClipboardMonitor.setText("clipboard monitor")
        self.chkIntentMonitor.setText("intent monitor")
        self.attachWorkbenchHeader.setText(self.trText("将 Native 与 Java 搜索流程拆分为上下两层，并把查询动作单独收纳为工具卡片，查模块、符号、类和函数时更聚焦。", "Native and Java exploration are split into two focused layers, with action buttons grouped into tool cards for cleaner module, symbol, class and method searches."))
        self.groupBox_7.setTitle(self.trText("附加进程逆向信息", "Attached process RE info"))
        self.labAttachedInfoHint.setText(self.trText("这里汇总 Frida 运行时、应用包信息、模块/类数量和调试属性，便于附加后快速判断分析切入点。", "This panel summarizes Frida runtime data, package metadata, module/class counts and debug-related flags to help pick an analysis entry point quickly."))
        self.labAppWorkbenchHint.setText(self.trText("支持先选择目标手机，再刷新前台应用与扩展元数据。默认会选中第一个已连接设备。", "Choose the target device first, then refresh the foreground app and extended metadata. The first connected device is selected by default."))
        self.currentAppExtraGroup.setTitle(self.trText("当前前台应用补充信息", "Foreground app extra info"))
        self.labCurrentAppInfoHint.setText(self.trText("这里基于 dumpsys / pm 输出补充显示版本、ABI、调试标记、数据目录等信息。", "This panel augments dumpsys / pm results with version, ABI, debug flags and data-path details."))
        self.labDeviceSelector.setText(self.trText("连接手机：", "Device:")) if hasattr(self, "labDeviceSelector") else None
        self.btnRefreshDevices.setText(self.trText("刷新设备", "Refresh devices")) if hasattr(self, "btnRefreshDevices") else None
        self.groupLogs.setTabText(self.groupLogs.indexOf(self.aiAnalysisTab), self.trText("AI 分析", "AI Analysis"))
        self.labOutputLogView.setText(self.trText("输出日志视图", "Output log view"))
        self.txtLogs.setPlaceholderText(self.trText("日志将在这里滚动显示...", "Logs will stream here..."))
        self.txtoutLogs.setPlaceholderText(self.trText("日志将在这里滚动显示...", "Logs will stream here..."))
        self.txtAiAnalysis.setPlaceholderText(self.trText("AI 分析结果会显示在这里", "AI analysis output will appear here"))
        self.btnOpenLogFile.setText(self.trText("打开日志文件", "Open log file"))
        self.btnRestoreLiveLog.setText(self.trText("恢复实时日志", "Restore live log"))
        self.btnAnalyzeLog.setText(self.trText("AI 分析日志", "AI analyze log"))
        self.actionAiSettings.setText(self.trText("AI 设置", "AI Settings"))
        self.logDock.setWindowTitle(self.trText("日志 / Hook / AI 侧边栏", "Logs / Hooks / AI sidebar")) if hasattr(self, "logDock") else None
        self.actionToggleLogDock.setText(self.trText("隐藏日志侧边栏", "Hide log sidebar")) if hasattr(self, "actionToggleLogDock") else None
        self.menuSettings.setTitle(self.trText("设置", "Settings"))
        self.groupLogs.setTabText(self.groupLogs.indexOf(self.tab_3), self.trText("操作日志", "Operation log"))
        self.groupLogs.setTabText(self.groupLogs.indexOf(self.tab_5), self.trText("输出日志", "Output log"))
        self.groupLogs.setTabText(self.groupLogs.indexOf(self.tab_4), self.trText("当前hook列表", "Current hook list"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), self.trText("主界面", "Main"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), self.trText("附加进程信息", "Attach process info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), self.trText("应用信息", "App info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_7), self.trText("辅助功能", "Assist work"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.gumTraceTab), self.trText("GumTrace 工作台", "GumTrace workbench"))
        self.btnDumpPtr.setText(self.trText("dump指定地址", "dump address"))
        self.btnDumpDex.setText(self.trText("dump_dex加载class后调用", "dump dex after class load"))
        self.btnCallFunction.setText(self.trText("函数重放", "function replay"))
        self.btnMemSearch.setText(self.trText("内存搜索", "memory search"))
        self.btnNatives.setText(self.trText("批量native", "multiple native"))
        self.btnTuoke.setText(self.trText("脱壳", "unpack"))
        self.btnCustom.setText(self.trText("自定义", "custom"))
        self.btnAntiFrida.setText(self.trText("frida检测", "frida check"))
        self.chkJavaEnc.setText(self.trText("java加解密", "java encrypt"))
        self.label.setText(self.trText("别名：", "Alias:"))
        self.label_2.setText(self.trText("别名：", "Alias:"))
        self.btnSaveHooks.setText(self.trText("保存列表", "Save list"))
        self.btnImportHooks.setText(self.trText("导入JSON", "Import JSON"))
        self.btnLoadHooks.setText(self.trText("加载记录", "Load record"))
        self.btnClearHooks.setText(self.trText("清空列表", "Clear list"))
        self.groupBox_3.setTitle(self.trText("module列表", "Module list"))
        self.groupBox_4.setTitle(self.trText("java类列表", "Java class list"))
        self.groupBox_5.setTitle(self.trText("符号", "Symbols"))
        self.groupBox_6.setTitle(self.trText("java函数", "Java methods"))
        self.nativeActionGroup.setTitle(self.trText("Native 查询动作", "Native query actions"))
        self.javaActionGroup.setTitle(self.trText("Java 查询动作", "Java query actions"))
        self.btnSymbolClear.setText(self.trText("清空", "Clear"))
        self.btnMethod.setText(self.trText("查询函数", "Search methods"))
        self.btnMethodClear.setText(self.trText("清空", "Clear"))
        self.groupBox_8.setTitle(self.trText("手机当前应用信息", "Current foreground app info"))
        self.label_8.setText(self.trText("提示：这里显示的是移动端当前app的信息，非附加的app信息", "Tip: this panel shows the current foreground app on the device, not necessarily the attached app."))
        self.label_12.setText(self.trText("启动页面：", "Launch component:"))
        self.btnFlush.setText(self.trText("刷新", "Refresh"))
        self.label_9.setText(self.trText("当前视图：", "Current focus:"))
        self.label_10.setText(self.trText("进程名：", "Process name:"))
        self.label_11.setText(self.trText("进程id：", "PID:"))
        self.label_13.setText(self.trText("base路径：", "Base path:"))
        self.groupBox_10.setTitle(self.trText("GumTrace 与日志工具", "GumTrace and log tools"))
        self.labAssistGumTraceHint.setText(self.trText("辅助页只保留 GumTrace 相关能力：上传动态库、下载日志、打开本地目录，以及跳转到 GumTrace 工作台。", "The assist page now keeps only GumTrace-related actions: upload the library, download logs, open the local directory and jump to the GumTrace workbench."))
        self.btnPullGumTraceLog.setText(self.trText("下载GumTrace日志", "download GumTrace log"))
        self.btnOpenGumTraceDir.setText(self.trText("打开本地日志目录", "open local log directory"))
        self.btnAssistUploadGumTrace.setText(self.trText("上传 GumTrace 库", "upload GumTrace library"))
        self.btnOpenGumTraceWorkspace.setText(self.trText("打开 GumTrace 面板", "open GumTrace workbench"))
        self.gumTraceConfigGroup.setTitle(self.trText("GumTrace 可视化配置", "Visual GumTrace configuration"))
        self.gumTracePreviewGroup.setTitle(self.trText("脚本预览与产物摘要", "Script preview and artifact summary"))
        self.labGumTraceWorkbenchHint.setText(self.trText("这里提供 GumTrace 专用配置面板：可视化设置触发模式、线程过滤、模块白名单、输出路径，并一键生成符合 custom 模块格式的脚本。", "This dedicated GumTrace workbench lets you configure trigger mode, thread filters, module whitelists and output paths visually, then generate scripts that match the custom-module format in one click."))
        self.labGumTraceConfigHint.setText(self.trText("推荐流程：先选触发模式，再填写模块白名单与线程过滤；若是 offset/export 模式，补充触发模块和偏移/导出名，最后生成并加入当前 Hook 列表。", "Recommended flow: choose a trigger mode, fill module whitelist and thread filters, then add trigger module plus offsets/exports for offset/export modes before generating and activating the script."))
        self.labGumTracePreviewHint.setText(self.trText("右侧会实时预览生成的脚本。保存配置只写入本地 conf.ini；生成脚本则写入 custom 仓库，可按需加入当前 Hook 列表。", "The right side previews the generated script. Saving settings only updates local conf.ini, while generating writes into the custom repository and can optionally add the script to the active hook list."))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceName).setText(self.trText("脚本别名：", "Alias:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceFileName).setText(self.trText("脚本文件：", "Filename:"))
        self.gumTraceFormLayout.labelForField(self.cmbGumTraceMode).setText(self.trText("触发模式：", "Trigger mode:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceTraceModules).setText(self.trText("模块白名单：", "Module whitelist:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceTriggerModule).setText(self.trText("触发模块：", "Trigger module:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceOffsets).setText(self.trText("偏移列表：", "Offsets:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceExports).setText(self.trText("导出列表：", "Exports:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceOutput).setText(self.trText("日志输出：", "Output log:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceAllowedThreads).setText(self.trText("线程过滤：", "Allowed TIDs:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceThreadId).setText(self.trText("GumTrace 线程：", "GumTrace thread:"))
        self.gumTraceFormLayout.labelForField(self.txtGumTraceOptions).setText(self.trText("运行选项：", "Trace options:"))
        self.txtGumTraceName.setPlaceholderText(self.trText("例如：SSL 读写触发追踪", "Example: SSL read/write trace profile"))
        self.txtGumTraceFileName.setPlaceholderText(self.trText("例如：gumtrace_ssl_profile.js", "Example: gumtrace_ssl_profile.js"))
        self.txtGumTraceTraceModules.setPlaceholderText(self.trText("多个模块用逗号分隔，例如：libssl.so,libcrypto.so", "Comma-separated modules, e.g. libssl.so,libcrypto.so"))
        self.txtGumTraceTriggerModule.setPlaceholderText(self.trText("例如：libssl.so", "Example: libssl.so"))
        self.txtGumTraceOffsets.setPlaceholderText(self.trText("多个偏移用逗号分隔，例如：0x1234,0x1888", "Comma-separated offsets, e.g. 0x1234,0x1888"))
        self.txtGumTraceExports.setPlaceholderText(self.trText("多个导出名用逗号分隔，例如：SSL_read,SSL_write", "Comma-separated exports, e.g. SSL_read,SSL_write"))
        self.txtGumTraceOutput.setPlaceholderText(self.trText("例如：/data/local/tmp/gumtrace_ssl.log", "Example: /data/local/tmp/gumtrace_ssl.log"))
        self.txtGumTraceAllowedThreads.setPlaceholderText(self.trText("可填线程ID列表，例如：1234,0x5678；留空则不过滤", "Optional TID list, e.g. 1234,0x5678; leave empty to disable filtering"))
        self.txtGumTraceThreadId.setPlaceholderText(self.trText("默认 0 表示由 GumTrace 自行处理", "Default 0 lets GumTrace decide"))
        self.txtGumTraceOptions.setPlaceholderText(self.trText("默认 0，可按 GumTrace 需要填写其他值", "Default 0; change only if your GumTrace build needs it"))
        self.chkGumTraceStopOnLeave.setText(self.trText("函数返回后自动停止追踪", "Stop trace on leave"))
        self.chkGumTraceAllowRepeat.setText(self.trText("允许重复触发追踪", "Allow repeated tracing"))
        self.chkGumTraceAutoAddHook.setText(self.trText("生成后自动加入当前 Hook 列表", "Auto add to active hook list"))
        self.chkGumTraceOpenDir.setText(self.trText("下载日志后自动打开目录", "Open directory after download"))
        self.btnGumTraceSaveConfig.setText(self.trText("保存配置", "Save config"))
        self.btnGumTracePreview.setText(self.trText("刷新预览", "Refresh preview"))
        self.btnGumTraceSaveCustom.setText(self.trText("仅写入脚本仓库", "Save to script library"))
        self.btnGumTraceActivate.setText(self.trText("生成并加入当前 Hook", "Generate and activate"))
        self.btnGumTraceOpenCustom.setText(self.trText("打开自定义模块", "Open Custom module"))
        self.btnGumTraceUpload.setText(self.trText("上传 GumTrace 库", "Upload GumTrace library"))
        self.btnGumTraceDownload.setText(self.trText("下载 GumTrace 日志", "Download GumTrace log"))
        self.menufile.setTitle(self.trText("文件", "file"))
        self.menuedit.setTitle(self.trText("执行", "run"))
        self.menuAttach.setTitle(self.trText("附加进程", "attach"))
        self.menu_frida_server.setTitle(self.trText("启动frida-server", "start frida-server"))
        self.menuhelp.setTitle(self.trText("帮助", "help"))
        self.menu.setTitle(self.trText("上传与下载", "upload and download"))
        self.menucmd.setTitle(self.trText("cmd切换", "change cmd"))
        self.menu_2.setTitle(self.trText("连接方式", "connect type"))
        self.menufrida.setTitle(self.trText("frida切换", "frida ver"))
        self.menu_3.setTitle(self.trText("语言", "language"))
        self.actionabort.setText(self.trText("关于我", "About"))
        self.actionStop.setText(self.trText("停止", "Stop"))
        self.action.setText(self.trText("附加当前进程", "Attach current process"))
        self.action.setToolTip(self.trText("附加当前进程", "Attach current process"))
        self.action_2.setText(self.trText("附加指定进程", "Attach named process"))
        self.action_2.setToolTip(self.trText("附加指定进程", "Attach named process"))
        self.actionspwan.setText(self.trText("spwan附加", "Spawn attach"))
        self.actionspwan.setToolTip(self.trText("spwan附加", "Spawn attach"))
        self.actionAttach.setText(self.trText("附加当前进程", "Attach current process"))
        self.actionAttachName.setText(self.trText("附加指定进程", "Attach named process"))
        self.actionSpawn.setText(self.trText("spawn附加", "Spawn attach"))
        self.actionClearTmp.setText(self.trText("清空缓存数据", "Clear cache"))
        self.actionClearLogs.setText(self.trText("清空日志文件", "Clear log files"))
        self.actionClearOutlog.setText(self.trText("清空输出日志", "Clear output log"))
        self.actionPushFartSo.setText(self.trText("上传fart.so,gson.jar到设备", "Upload fart.so and gson.dex"))
        self.actionPushGumTrace.setText(self.trText("上传GumTrace库到设备", "Upload GumTrace library"))
        self.actionClearHookJson.setText(self.trText("清空json列表", "Clear hook JSON list"))
        self.actionPullDumpDexRes.setText(self.trText("下载dump_dex结果", "Download dump_dex result"))
        self.actionPushFridaServer.setText(self.trText("上传frida-server(arm,arm64)", "Upload frida-server (arm, arm64)"))
        self.actionPushFridaServerX86.setText(self.trText("上传frida-server(x86,x64)", "Upload frida-server (x86, x64)"))
        self.actionPullFartRes.setText(self.trText("下载fart脱壳结果", "Download fart result"))
        self.actionPullApk.setText(self.trText("下载当前应用apk", "Download current APK"))
        self.actionUsb.setText(self.trText("usb连接", "USB"))
        self.actionWifi.setText(self.trText("wifi连接", "WiFi"))
        self.actionChangePort.setText(self.trText("修改默认端口", "Change default port"))
        self.actionConsoleLog.setText(self.trText("关闭输出日志", "Disable output log"))
        self.actionChina.setText(self.trText("中文", "Chinese"))
        self.actionEnglish.setText("English")
        self.actionattach.setText("attach")
        self.actionattach.setToolTip("attach by packageName")
        self.actionattachF.setText("attachF")
        self.actionattachF.setToolTip("attach current top app")
        self.actionspawn.setText("spawn")
        self.actionstop.setText("stop")
        self.cmbGumTraceMode.setItemText(0, self.trText("手动启动", "Manual"))
        self.cmbGumTraceMode.setItemText(1, self.trText("偏移触发", "Offset trigger"))
        self.cmbGumTraceMode.setItemText(2, self.trText("导出触发", "Export trigger"))
        self.labStatus.setText(self.trText("当前状态:已连接", "Status: connected") if self.actionStop.isEnabled() else self.trText("当前状态:未连接", "Status: disconnected"))
        if self.currentLogMode == "file" and self.loadedLogPath:
            self.labLogStatus.setText(self.trText("当前日志：", "Current log: ") + os.path.basename(self.loadedLogPath))
        else:
            self.labLogStatus.setText(self.trText("当前日志：实时输出", "Current log: live output"))
        self.onDeviceChanged() if hasattr(self, "cmbDevices") else None
        self.onLogDockVisibilityChanged(self.logDock.isVisible()) if hasattr(self, "logDock") else None
        self.updateCurrentAppInfoTable()
        self.updateAttachedInfoTable()
        self.refreshAiState()
        self.refreshHookMetadataLanguage()
        self.updateTabHooks()
        self.refreshOverviewCards()
        self.refreshChildTranslations()

    def switchLanguage(self, language):
        if self.language == language:
            return
        self.language = language
        conf.write("kmain", "language", language)
        apply_app_language(QApplication.instance(), language)
        self.loadTypeData()
        self.retranslateUi(self)
        self.retranslateDynamicUi()

    def ChangeEnglish(self,checked):
        if checked==False:
            return
        self.switchLanguage("English")

    def ChangeChina(self,checked):
        if checked==False:
            return
        self.switchLanguage("China")

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
            name=self.fridaName+"32"
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
        self.refreshOverviewCards()
        # appinfo=self.th.default_api.loadappinfo()
        # self.loadAppInfo(appinfo)

    def getFridaDevice(self):
        if self.connType=="usb":
            if self.customPort != None and len(self.customPort) > 0:
                str_host = "127.0.0.1:%s" % (self.customPort)
                manager = frida.get_device_manager()
                device = manager.add_remote_device(str_host)
                return device
            selected_serial = self.selectedDeviceSerial()
            if len(selected_serial) > 0:
                manager = frida.get_device_manager()
                try:
                    return manager.get_device(selected_serial, timeout=5)
                except Exception:
                    pass
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
            self.th.usb_device_id = self.selectedDeviceSerial()
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
            self.th.usb_device_id = self.selectedDeviceSerial()
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
            self.attachedAppInfoSnapshot = {}
            self.updateAttachedInfoTable()
        self.refreshOverviewCards()

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
            self.th.customPort = self.customPort
            self.th.usb_device_id = self.selectedDeviceSerial()
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
        self.th.default_api.dumpptr(self.dumpForm.moduleName,self.dumpForm.address, self.dumpForm.dumpType,self.dumpForm.size)

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
        soName=self.dumpSoForm.moduleName
        module_info = self.th.default_api.findmodule(soName)
        print(module_info)
        base = module_info["base"]
        size = module_info["size"]
        module_buffer = self.th.default_api.dumpmodule(soName)
        if module_buffer != -1:
            dump_so_name = soName + ".dump.so"
            with open(dump_so_name, "wb") as f:
                f.write(module_buffer)
                f.close()
                arch = self.th.default_api.arch()
                fix_so_name = CmdUtil.fix_so(arch, soName, dump_so_name, base, size)
                self.outlog(fix_so_name)
                os.remove(dump_so_name)
                QMessageBox().information(self, "hint",self._translate("kmainForm", f"dump {soName} 成功"))

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

    def hookRootBypass(self, checked):
        self.chk_hook_insert(checked, "root_bypass", self._translate("kmainForm", "绕过常见 Root 检测"))

    def hookWebViewDebug(self, checked):
        self.chk_hook_insert(checked, "webview_debug", self._translate("kmainForm", "开启 WebView 调试与接口日志"))

    def hookOkHttpLogger(self, checked):
        self.chk_hook_insert(checked, "okhttp_logger", self._translate("kmainForm", "打印 OkHttp 请求与响应关键信息"))

    def hookSharedPrefsWatch(self, checked):
        self.chk_hook_insert(checked, "shared_prefs_watch", self._translate("kmainForm", "监控 SharedPreferences 读写"))

    def hookSQLiteLogger(self, checked):
        self.chk_hook_insert(checked, "sqlite_logger", self._translate("kmainForm", "监控 SQLite 查询与写入"))

    def hookClipboardMonitor(self, checked):
        self.chk_hook_insert(checked, "clipboard_monitor", self._translate("kmainForm", "监控剪贴板内容读写"))

    def hookIntentMonitor(self, checked):
        self.chk_hook_insert(checked, "intent_monitor", self._translate("kmainForm", "监控 Intent、Service 与 Broadcast 跳转"))

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
        self.customForm.refreshAiState()
        self.customForm.exec()
        self.syncCustomHooksToMain()
        self.refreshOverviewCards()

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

    def setCheckSilent(self, widget, checked):
        widget.blockSignals(True)
        widget.setChecked(checked)
        widget.blockSignals(False)

    # 加载hook列表后。这里刷新下checked
    def refreshChecks(self):
        self.setCheckSilent(self.chkNetwork, self.chkNetwork.tag in self.hooksData)
        self.setCheckSilent(self.chkJni, self.chkJni.tag in self.hooksData)
        self.setCheckSilent(self.chkJavaEnc, self.chkJavaEnc.tag in self.hooksData)
        self.setCheckSilent(self.chkSslPining, self.chkSslPining.tag in self.hooksData)
        self.setCheckSilent(self.chkRegisterNative, self.chkRegisterNative.tag in self.hooksData)
        self.setCheckSilent(self.chkArtMethod, self.chkArtMethod.tag in self.hooksData)
        self.setCheckSilent(self.chkLibArt, self.chkLibArt.tag in self.hooksData)
        self.setCheckSilent(self.chkHookEvent, self.chkHookEvent.tag in self.hooksData)
        self.setCheckSilent(self.chkAntiDebug, "anti_debug" in self.hooksData)
        self.setCheckSilent(self.chkNewJnitrace, "FCAnd_jnitrace" in self.hooksData)
        self.setCheckSilent(self.chkRootBypass, self.chkRootBypass.tag in self.hooksData)
        self.setCheckSilent(self.chkWebViewDebug, self.chkWebViewDebug.tag in self.hooksData)
        self.setCheckSilent(self.chkOkHttpLogger, self.chkOkHttpLogger.tag in self.hooksData)
        self.setCheckSilent(self.chkSharedPrefsWatch, self.chkSharedPrefsWatch.tag in self.hooksData)
        self.setCheckSilent(self.chkSQLiteLogger, self.chkSQLiteLogger.tag in self.hooksData)
        self.setCheckSilent(self.chkClipboardMonitor, self.chkClipboardMonitor.tag in self.hooksData)
        self.setCheckSilent(self.chkIntentMonitor, self.chkIntentMonitor.tag in self.hooksData)

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
                    line += 1
            else:
                self.tabHooks.insertRow(line)
                self.tabHooks.setItem(line, 0, QTableWidgetItem(item))
                self.tabHooks.setItem(line, 1, QTableWidgetItem(self.hooksData[item]["class"]))
                self.tabHooks.setItem(line, 2, QTableWidgetItem(self.hooksData[item]["method"]))
                self.tabHooks.setItem(line, 3, QTableWidgetItem(self.hooksData[item]["bak"]))
                line += 1
        self.refreshOverviewCards()

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

    def extractMatch(self, pattern, text, group=1):
        match = re.search(pattern, text, re.MULTILINE)
        if match is None:
            return ""
        return match.group(group).strip()

    def firstShellOutputLine(self, text):
        for line in (text or "").splitlines():
            line = line.strip()
            if len(line) > 0 and not line.startswith("cmd命令执行"):
                return line
        return ""

    def queryCurrentAppSnapshot(self, packageName, currentFocus, component, pid, baseDir):
        snapshot = {
            "packageName": packageName,
            "processName": packageName,
            "currentFocus": currentFocus,
            "component": component,
            "pid": pid,
            "baseDir": baseDir,
        }
        if len(packageName) <= 0:
            return snapshot
        packageDump = CmdUtil.exec("adb shell dumpsys package " + packageName)
        pathDump = CmdUtil.exec("adb shell pm path " + packageName)
        snapshot["apkPath"] = self.extractMatch(r"package:([^\n]+)", pathDump)
        snapshot["versionName"] = self.extractMatch(r"versionName=([^\s]+)", packageDump)
        snapshot["versionCode"] = self.extractMatch(r"versionCode=([^\s]+)", packageDump)
        snapshot["targetSdk"] = self.extractMatch(r"targetSdk=([^\s]+)", packageDump)
        snapshot["uid"] = self.extractMatch(r"userId=(\d+)", packageDump)
        snapshot["dataDir"] = self.extractMatch(r"dataDir=([^\s]+)", packageDump)
        snapshot["primaryCpuAbi"] = self.extractMatch(r"primaryCpuAbi=([^\s]+)", packageDump)
        snapshot["pkgFlags"] = self.extractMatch(r"pkgFlags=\[(.*?)\]", packageDump)
        snapshot["deviceAbiList"] = CmdUtil.exec("adb shell getprop ro.product.cpu.abilist").strip()
        flags = snapshot["pkgFlags"].upper()
        snapshot["debuggable"] = "DEBUGGABLE" in flags
        snapshot["allowBackup"] = "ALLOW_BACKUP" in flags
        return snapshot

    # 附加成功后取出app的信息展示
    def loadAppInfo(self, info):
        self.listModules.clear()
        self.listClasses.clear()

        if info==None:
            return
        if "modules" not in info or "classes" not in info:
            return
        self.modules = info["modules"]
        self.classes = info["classes"]

        for module in info["modules"]:
            self.listModules.addItem(module["name"] + "----" + module["base"])

        for item in info["classes"]:
            self.listClasses.addItem(item)

        try:
            self.listModules.itemClicked.disconnect(self.listModuleClick)
        except Exception:
            pass
        try:
            self.listClasses.itemClicked.disconnect(self.listClassClick)
        except Exception:
            pass
        self.listModules.itemClicked.connect(self.listModuleClick)
        self.listClasses.itemClicked.connect(self.listClassClick)
        packageName = self.labPackage.text()
        attach_type_map = {
            "attachCurrent": self.trText("附加当前前台进程", "Attach current foreground process"),
            "attach": self.trText("附加指定进程", "Attach selected process"),
            "spawn": self.trText("spawn 附加", "Spawn attach"),
        }
        snapshot = dict(info)
        snapshot["packageName"] = packageName
        snapshot["attachType"] = attach_type_map.get(self.th.attachType, self.th.attachType)
        snapshot["connectionType"] = "USB" if self.connType == "usb" else "WiFi"
        snapshot["fridaVersion"] = self.curFridaVer
        snapshot["hookCount"] = len(self.hooksData)
        self.attachedAppInfoSnapshot = snapshot
        self.updateAttachedInfoTable()
        self.refreshOverviewCards()

        with open("./tmp/" + packageName + ".classes.txt", "w+", encoding="utf-8") as packageTmpFile:
            for item in info["classes"]:
                packageTmpFile.write(item + "\n")
        spawnpath = ".spawn" if info["spawn"] == "1" else ""
        with open("./tmp/" + packageName + ".modules" + spawnpath + ".txt", "w+", encoding="utf-8") as packageTmpFile:
            for module in info["modules"]:
                packageTmpFile.write(module["name"] + "\n")

    def searchAppInfoRes(self, info):
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
        if len(self.selectedDeviceSerial()) <= 0:
            QMessageBox().information(self, "hint", self.trText("请先选择已连接的手机", "Please select a connected device first"))
            return
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
            self.log(m1.group(1))
            self.log(self._translate("kmainForm","焦点数据格式不正确"))
            QMessageBox().information(self, "hint", self._translate("kmainForm","焦点数据格式不正确"))
            return

        packageName = m1dataSp[0]
        currentFocus = m1dataSp[1]
        self.txtProcessName.setText(packageName)
        self.txtCurrentFocus.setText(currentFocus)
        activityDump = CmdUtil.exec("adb shell dumpsys activity -p " + packageName)
        pid = self.extractMatch(r" (\d+?):%s/" % re.escape(packageName), activityDump)
        component = self.extractMatch(r"android.intent.action.MAIN.+?cmp=(%s[^\s]+)" % re.escape(packageName), activityDump)
        if len(component) <= 0:
            component = packageName + "/" + currentFocus
        baseDir = self.extractMatch(r"baseDir=([^\s]+)", activityDump)
        if len(baseDir) <= 0:
            baseDir = self.extractMatch(r"package:([^\n]+)", CmdUtil.exec("adb shell pm path " + packageName))

        self.txtPid.setText(pid)
        self.txtComponent.setText(component)
        self.txtBaseDir.setText(baseDir)
        self.currentAppInfoSnapshot = self.queryCurrentAppSnapshot(packageName, currentFocus, component, pid, baseDir)
        self.updateCurrentAppInfoTable()
        self.refreshOverviewCards()

    def fartOpBin(self):
        self.fartBinForm.show()

    def stalkerOpLog(self):
        self.stalkerMatchForm.show()

    def resizeEvent(self, event):
        super(kmainForm, self).resizeEvent(event)
        self.rebuildResponsiveCards()
        self.rebuildAdvancedToolGrid()

    # 不关闭的话，mac下调试时退出会出现无法关闭进程
    def closeEvent(self, event):
        if platform.system() =='Darwin':
            CmdUtil.execCmd(CmdUtil.cmdhead + "\"pkill -9 frida\"")


def getTrans():
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


def apply_app_language(app, language):
    global ACTIVE_TRANSLATORS
    for trans in ACTIVE_TRANSLATORS:
        app.removeTranslator(trans)
    ACTIVE_TRANSLATORS = []
    if language == "English":
        ACTIVE_TRANSLATORS = getTrans()
        for trans in ACTIVE_TRANSLATORS:
            app.installTranslator(trans)


if __name__ == "__main__":
    current_exit_code = 1207
    app = QApplication(sys.argv)
    while current_exit_code == 1207:
        language=conf.read("kmain","language")
        apply_app_language(app, language)
        kmain = kmainForm()
        kmain.show()
        current_exit_code=app.exec_()
        kmain=None
    sys.exit(current_exit_code)



