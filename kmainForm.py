# coding=utf-8
import datetime
import re
import shlex
import sys
import time
from time import sleep

from PyQt5 import uic, QtWidgets,QtCore
from PyQt5.QtCore import Qt, QPoint, QTranslator, QUrl
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor, QDesktopServices, QIcon, QPixmap, QPainter, QColor, QPen, QPolygon, QDrag
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStatusBar, QLabel, QMessageBox, QHeaderView, \
    QTableWidgetItem, QMenu, QAction, QActionGroup, qApp, QLineEdit, QProgressDialog, QDialog, QVBoxLayout, QPlainTextEdit, QPushButton
from urllib.parse import urlparse
import urllib.error
import urllib.request

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
from utils.AiUtil import AiService, AiWorker, FileDownloadWorker, AdbPushWorker, CommandWorker
import json, os, threading, frida
import platform
import shutil
import subprocess
import tempfile

import TraceThread
from utils.IniUtil import IniConfig


def resolve_app_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resolve_bundle_root():
    if getattr(sys, "frozen", False):
        meipass_root = getattr(sys, "_MEIPASS", "")
        if meipass_root:
            return os.path.abspath(meipass_root)
        return os.path.join(resolve_app_root(), "_internal")
    return resolve_app_root()


def sync_runtime_resource_dir(directory_name):
    source_dir = os.path.join(BUNDLE_ROOT, directory_name)
    target_dir = os.path.join(APP_ROOT, directory_name)
    if os.path.isdir(source_dir) is False:
        return
    if os.path.exists(target_dir) is False:
        shutil.copytree(source_dir, target_dir)
        return
    for current_root, _, file_names in os.walk(source_dir):
        relative_root = os.path.relpath(current_root, source_dir)
        target_root = target_dir if relative_root == "." else os.path.join(target_dir, relative_root)
        os.makedirs(target_root, exist_ok=True)
        for file_name in file_names:
            source_file = os.path.join(current_root, file_name)
            target_file = os.path.join(target_root, file_name)
            if os.path.exists(target_file) is False:
                shutil.copy2(source_file, target_file)


def bootstrap_runtime_resources():
    for directory_name in ("config", "custom", "exec", "js", "lib", "sh"):
        sync_runtime_resource_dir(directory_name)


APP_ROOT = resolve_app_root()
BUNDLE_ROOT = resolve_bundle_root()
bootstrap_runtime_resources()
os.chdir(APP_ROOT)

FRIDA_ARCH_FAMILIES = {
    "arm64": ["arm", "arm64"],
    "x64": ["x86", "x86_64"],
}
FRIDA_MENU_FAMILIES = ("arm64", "x64")
FRIDA_LOCAL_ARCH_TO_FAMILY = {
    "arm": "arm64",
    "arm64": "arm64",
    "x86": "x64",
    "x86_64": "x64",
}
FRIDA_SUPPORTED_MAJORS = [14, 15, 16]
FRIDA_MENU_VERSION_LIMIT = 3
FRIDA_RELEASE_CACHE_PATH = os.path.join(APP_ROOT, "config", "frida_versions.json")
FRIDA_RELEASE_TAGS_API_URL = "https://api.github.com/repos/frida/frida/tags?per_page=100&page={page}"
FRIDA_RELEASE_TAGS_PAGES = 4
FRIDA_EMPTY_RELEASE_CATALOG = {major: [] for major in FRIDA_SUPPORTED_MAJORS}
FRIDA_FALLBACK_VERSION_CATALOG = {
    14: ["14.2.18", "14.2.17", "14.2.16"],
    15: ["15.2.2", "15.2.1", "15.2.0"],
    16: ["16.7.19", "16.7.18", "16.7.17"],
}

conf=IniConfig()
ACTIVE_TRANSLATORS = []


class PinnedTemplateCheckBox(QtWidgets.QCheckBox):
    reorderRequested = QtCore.pyqtSignal(str, str, bool)
    MIME_TYPE = "application/x-fridaui-pinned-template"

    def __init__(self, text, file_name, parent=None):
        super(PinnedTemplateCheckBox, self).__init__(text, parent)
        self.fileName = file_name
        self._dragStartPos = QPoint()
        self._dragActive = False
        self.setAcceptDrops(True)

    def _draggedFileName(self, event):
        mime = event.mimeData()
        if mime is None or not mime.hasFormat(self.MIME_TYPE):
            return ""
        try:
            return bytes(mime.data(self.MIME_TYPE)).decode("utf-8")
        except Exception:
            return ""

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragStartPos = event.pos()
            self._dragActive = False
        super(PinnedTemplateCheckBox, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            super(PinnedTemplateCheckBox, self).mouseMoveEvent(event)
            return
        if (event.pos() - self._dragStartPos).manhattanLength() < QApplication.startDragDistance():
            super(PinnedTemplateCheckBox, self).mouseMoveEvent(event)
            return
        if not self.fileName:
            return
        self._dragActive = True
        self.setDown(False)
        drag = QDrag(self)
        mime = QtCore.QMimeData()
        mime.setData(self.MIME_TYPE, self.fileName.encode("utf-8"))
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        if self._dragActive:
            self._dragActive = False
            self.setDown(False)
            event.accept()
            return
        super(PinnedTemplateCheckBox, self).mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        dragged_file_name = self._draggedFileName(event)
        if dragged_file_name and dragged_file_name != self.fileName:
            event.acceptProposedAction()
            return
        event.ignore()

    def dragMoveEvent(self, event):
        dragged_file_name = self._draggedFileName(event)
        if dragged_file_name and dragged_file_name != self.fileName:
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event):
        dragged_file_name = self._draggedFileName(event)
        if not dragged_file_name or dragged_file_name == self.fileName:
            event.ignore()
            return
        insert_after = event.pos().x() >= (self.width() / 2)
        self.reorderRequested.emit(dragged_file_name, self.fileName, insert_after)
        event.acceptProposedAction()

def restart_real_live():
    qApp.exit(1207)

class kmainForm(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(kmainForm, self).__init__(parent)
        self.setupUi(self)
        self.aiService = AiService(conf)
        self.aiWorker = None
        self.fridaDownloadWorker = None
        self.fridaDownloadDialog = None
        self.fridaUploadWorker = None
        self.fridaUploadDialog = None
        self.fridaVersionWorker = None
        self.fridaVersionDialog = None
        self.fridaVersionOutput = None
        self.fridaVersionCloseButton = None
        self.fridaUploadMenu = None
        self.fridaArm64Menu = None
        self.fridaX64Menu = None
        self.fridaReleaseCatalog = self.loadCachedFridaReleaseCatalog()
        self.fridaReleaseCatalogError = ""
        self.fridaVersionMenuActions = []
        self.fridaDownloadCancelled = False
        self.curFridaVer = "14.2.18"
        self.liveOutputLogBuffer = []
        self.currentLogMode = "live"
        self.loadedLogPath = ""
        self.loadedLogContent = ""
        self.language = conf.read("kmain", "language") or "China"
        self.currentAppInfoSnapshot = {}
        self.mainContextForegroundPackage = ""
        self.attachedAppInfoSnapshot = {}
        self.hooksData = {}
        self.initUi()
        self.th = TraceThread.Runthread(self.hooksData, "", False, self.connType)
        self.th.usb_device_id = self.selectedDeviceSerial()
        self.updateCmbHooks()
        self.outlogger = LogUtil.Logger('all.txt', level='debug')

    def createColoredPlayIcon(self, color, size=20):
        """创建彩色播放图标"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置颜色
        painter.setBrush(QColor(color))
        painter.setPen(QPen(QColor(color), 2))
        
        # 绘制播放三角形
        triangle = QPolygon([
            QPoint(int(size * 0.25), int(size * 0.15)),
            QPoint(int(size * 0.25), int(size * 0.85)),
            QPoint(int(size * 0.80), int(size * 0.50))
        ])
        painter.drawPolygon(triangle)
        
        painter.end()
        return QIcon(pixmap)

    def createColoredStopIcon(self, color, size=20):
        """创建彩色停止图标"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color))
        painter.setPen(QPen(QColor(color), 1))
        margin = int(size * 0.2)
        side = size - (margin * 2)
        painter.drawRoundedRect(margin, margin, side, side, 3, 3)
        painter.end()
        return QIcon(pixmap)

    def initUi(self):
        self.resize(980, 720)
        self.setMinimumSize(920, 660)
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
        self.languageGroup.setExclusive(True)
        self.languageGroup.addAction(self.actionChina)
        self.languageGroup.addAction(self.actionEnglish)

        self.fridaName = conf.read("kmain", "frida_name")
        self.customPort = conf.read("kmain", "usb_port")
        self.address=conf.read("kmain", "wifi_addr")
        self.wifi_port = conf.read("kmain", "wifi_port")
        self.updateLanguageSelectionUi()
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
        self.actionFrida32Start.triggered.connect(self.StartFridaServer)
        self.actionFrida64Start.setVisible(False)
        self.actionFridax86Start.setVisible(False)
        self.actionFridax64Start.setVisible(False)
        self.actionPullApk.triggered.connect(self.PullApk)
        self.actionPushGumTrace = QAction(self)
        self.actionPushGumTrace.setObjectName("actionPushGumTrace")
        self.actionPushGumTrace.triggered.connect(self.PushGumTraceLib)
        self.menu.insertAction(self.actionPullDumpDexRes, self.actionPushGumTrace)
        self.actionPullGumTraceLog = QtWidgets.QAction(self)
        self.actionPullGumTraceLog.setObjectName("actionPullGumTraceLog")
        self.actionPullGumTraceLog.triggered.connect(self.pullGumTraceLog)
        self.menu.insertAction(self.actionPullDumpDexRes, self.actionPullGumTraceLog)
        self.initFridaUploadMenu()

        self.menufrida.aboutToShow.connect(self.ensureFridaVersionMenuReady)
        self.rebuildFridaVersionMenu()

        self.connectHeadGroup = QActionGroup(self)
        self.connectHeadGroup.setExclusive(True)
        self.connectHeadGroup.addAction(self.actionWifi)
        self.connectHeadGroup.addAction(self.actionUsb)
        self.actionWifi.triggered.connect(self.WifiConn)
        self.actionUsb.triggered.connect(self.UsbConn)
        self.actionEnglish.triggered.connect(self.ChangeEnglish)
        self.actionChina.triggered.connect(self.ChangeChina)

        self.actionChangePort.triggered.connect(self.ChangePort)
        self.verGroup = QActionGroup(self)
        self.verGroup.setExclusive(True)
        self.verGroup.addAction(self.actionVer14)
        self.verGroup.addAction(self.actionVer15)
        self.verGroup.addAction(self.actionVer16)

        self.btnDumpPtr.clicked.connect(self.dumpPtr)
        self.btnDumpSo.clicked.connect(self.dumpSo)
        self.btnFart.clicked.connect(self.dumpFart)
        self.btnDumpDex.clicked.connect(self.dumpDex)
        self.btnWallbreaker.clicked.connect(self.wallBreaker)
        self.btnCallFunction.clicked.connect(self.callFunction)

        # r0capture moved to Custom Templates
        # plain jnitrace moved out of main pre-attach UI
        # FCAnd_jnitrace moved to lower tool button

        # simple presets moved to Custom Templates

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
        self.dexes = []
        self.filteredModules = []
        self.currentSelectedModule = None
        self.currentSelectedDex = None
        self.currentAttachResourceType = "module"
        self.moduleExportCache = {}
        self.moduleSymbolCache = {}
        self.lastSearchModuleKey = None

        # legacy pre-attach checkbox tags removed; r0capture/plain jnitrace now handled elsewhere
        self.connType = "usb"
        self.updateConnectionSelectionUi()
        self.selectedDeviceId = ""
        self.lastMainSplitterSizes = [760, 420]

        self.actionattach = QtWidgets.QAction(self)
        self.actionattach.setText("attach")
        self.actionattach.setToolTip("attach by packageName")
        self.actionattach.setIcon(self.createColoredPlayIcon("#FF6B6B"))  # 红色
        self.actionattach.triggered.connect(self.actionAttachNameStart)
        self.toolBar.addAction(self.actionattach)

        self.actionattachF = QtWidgets.QAction(self)
        self.actionattachF.setText("attachF")
        self.actionattachF.setToolTip("attach current top app")
        self.actionattachF.setIcon(self.createColoredPlayIcon("#4ECDC4"))  # 青色
        self.actionattachF.triggered.connect(self.actionAttachStart)
        self.toolBar.addAction(self.actionattachF)

        self.actionspawn = QtWidgets.QAction(self)
        self.actionspawn.setText("spawn")
        self.actionspawn.setIcon(self.createColoredPlayIcon("#95E1D3"))  # 浅绿色
        self.actionspawn.triggered.connect(self.actionSpawnStart)
        self.toolBar.addAction(self.actionspawn)

        self.actionstop = QtWidgets.QAction(self)
        self.actionstop.setText("stop")
        self.actionstop.setIcon(self.createColoredStopIcon("#94a3b8"))
        self.actionstop.triggered.connect(self.StopAttach)
        self.toolBar.addAction(self.actionstop)
        self.updateAttachActionStates(False)

        self.toolBar.addSeparator()

        self.actionCustomModule = QtWidgets.QAction(self)
        self.actionCustomModule.setText(self.trText("自定义", "Custom"))
        self.actionCustomModule.setToolTip(self.trText("打开自定义模块", "Open Custom module"))
        self.actionCustomModule.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        self.actionCustomModule.triggered.connect(self.custom)
        self.toolBar.addAction(self.actionCustomModule)

        self.actionGumTracePanel = QtWidgets.QAction(self)
        self.actionGumTracePanel.setText("GumTrace")
        self.actionGumTracePanel.setToolTip(self.trText("打开 GumTrace 工作台", "Open GumTrace workbench"))
        self.actionGumTracePanel.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogListView))
        self.actionGumTracePanel.triggered.connect(self.openGumTraceWorkspace)
        self.toolBar.addAction(self.actionGumTracePanel)

        # 设置工具栏按钮样式：图标在上，文字在下
        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolBar.setIconSize(QtCore.QSize(20, 20))  # 设置图标大小
        self.toolBar.setMinimumHeight(52)  # 工具栏高度
        self.toolBar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
            }
            QToolBar QToolButton {
                padding: 4px 8px 6px 8px;
                min-width: 65px;
                min-height: 46px;
            }
        """)

        self.actionVer14.setChecked(True)
        self.menu_frida_server.menuAction().setVisible(False)
        self.setCmdMenuVisible(False)
        self.actionFrida32Start.setText(self.trText("启动 frida-server", "Start frida-server"))
        self.menuedit.insertAction(self.actionChangePort, self.actionFrida32Start)
        self.actionChangePort.setVisible(True)
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
        self.migrateLegacySimpleHooksToCustom()
        self.syncCustomHooksFromHooksData()
        self.refreshPinnedCustomTemplates()
        self.initLogTools()
        self.initSettingsMenu()
        self.initGumTraceWorkspace()
        self.loadGumTraceConfig()
        self.applyWorkbenchTheme()
        if self.styleSheet():
            self.customForm.setStyleSheet(self.styleSheet())
        self.customForm.setWindowFlags(self.customForm.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.retranslateDynamicUi()
        self.refreshDeviceList()
        self.refreshOverviewCards()

    def isEnglish(self):
        return self.language == "English"

    def trText(self, zh_text, en_text):
        return en_text if self.isEnglish() else zh_text

    def languageDisplayName(self, language):
        return self.trText("中文", "Chinese") if language == "China" else "English"

    def updateLanguageSelectionUi(self):
        current_language = self.language if self.language in ("China", "English") else "China"
        current_label = self.languageDisplayName(current_language)
        self.menu_3.setTitle("{} [{}]".format(self.trText("语言", "language"), current_label))

        selected_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
        for action, language in ((self.actionChina, "China"), (self.actionEnglish, "English")):
            is_current = language == current_language
            label = self.languageDisplayName(language)
            if is_current:
                label += self.trText("（当前）", " (Current)")
            action.setText(label)
            action.setChecked(is_current)
            action.setIcon(selected_icon if is_current else QIcon())
            action.setIconVisibleInMenu(True)

    def connectionDisplayName(self, conn_type):
        return "WiFi" if conn_type == "wifi" else "USB"

    def currentConnectionPortDisplay(self):
        current_conn_type = getattr(self, "connType", "usb")
        if current_conn_type == "wifi":
            address = (self.address or "").strip()
            port = (self.wifi_port or "").strip()
            if len(address) > 0 and len(port) > 0:
                return "%s:%s" % (address, port)
            if len(port) > 0:
                return port
            return self.trText("未设置", "Not set")
        custom_port = (self.customPort or "").strip()
        if len(custom_port) > 0:
            return custom_port
        return "27042 / 27043"

    def currentConnectionSettingsActionText(self):
        current_conn_type = getattr(self, "connType", "usb")
        return self.trText("连接设置", "Connection settings") if current_conn_type == "wifi" else self.trText("修改端口", "Change port")

    def openCurrentConnectionSettings(self):
        if getattr(self, "connType", "usb") == "wifi":
            self.WifiConn()
            return
        self.ChangePort()

    def updateToolbarContextPanel(self):
        current_serial = self.selectedDeviceSerial()
        port_text = self.currentConnectionPortDisplay()
        if hasattr(self, "labMainContextDeviceTitle"):
            self.labMainContextDeviceTitle.setText(self.trText("设备", "Device"))
        if hasattr(self, "labMainContextPortTitle"):
            self.labMainContextPortTitle.setText(self.trText("端口", "Port"))
        if hasattr(self, "cmbMainContextDevices"):
            self.cmbMainContextDevices.setToolTip(current_serial if len(current_serial) > 0 else self.trText("当前没有已选设备", "No device selected"))
        if hasattr(self, "txtMainContextPortValue"):
            self.txtMainContextPortValue.setText(port_text)
            self.txtMainContextPortValue.setToolTip(port_text)
            self.txtMainContextPortValue.setCursorPosition(0)
        if hasattr(self, "btnMainContextRefreshDevices"):
            self.btnMainContextRefreshDevices.setText(self.trText("刷新设备", "Refresh devices"))
            self.fitButtonTextWidth(self.btnMainContextRefreshDevices)
        if hasattr(self, "btnMainContextPortSettings"):
            self.btnMainContextPortSettings.setText(self.currentConnectionSettingsActionText())
            self.fitButtonTextWidth(self.btnMainContextPortSettings)
        if hasattr(self, "txtMainContextForegroundPackage"):
            attached_package = (self.labPackage.text().strip() if hasattr(self, "labPackage") else "")
            if len(attached_package) > 0:
                display_text = attached_package
                placeholder = self.trText("当前已附加包名", "Attached package")
            else:
                display_text = self.trText("未附加进程", "No process attached")
                placeholder = display_text
            self.txtMainContextForegroundPackage.setPlaceholderText(placeholder)
            self.txtMainContextForegroundPackage.setText(display_text)
            self.txtMainContextForegroundPackage.setToolTip(display_text if len(display_text) > 0 else placeholder)
            self.txtMainContextForegroundPackage.setCursorPosition(0)

    def updateConnectionSelectionUi(self):
        current_conn_type = getattr(self, "connType", "usb")
        if current_conn_type not in ("usb", "wifi"):
            current_conn_type = "usb"
        current_label = self.connectionDisplayName(current_conn_type)
        self.menu_2.setTitle("{} [{}]".format(self.trText("连接方式", "connect type"), current_label))

        selected_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
        for action, conn_type, label in (
            (self.actionUsb, "usb", self.trText("usb连接", "USB")),
            (self.actionWifi, "wifi", self.trText("wifi连接", "WiFi")),
        ):
            is_current = conn_type == current_conn_type
            action_label = label
            if is_current:
                action_label += self.trText("（当前）", " (Current)")
            action.setText(action_label)
            action.setChecked(is_current)
            action.setIcon(selected_icon if is_current else QIcon())
            action.setIconVisibleInMenu(True)
        self.updateToolbarContextPanel()

    def currentFridaVersionDisplay(self):
        for action in getattr(self, "fridaVersionMenuActions", []):
            version = str(action.data() or "").strip()
            if action.isChecked() and version:
                return version
        current_version = str(getattr(self, "curFridaVer", "") or "").strip()
        if current_version:
            return current_version
        return self.getInstalledPythonFridaVersion().strip()

    def updateFridaVersionSelectionUi(self, current_version=""):
        current_version = (current_version or self.currentFridaVersionDisplay()).strip()
        if current_version:
            self.menufrida.setTitle("{} [{}]".format(self.trText("frida切换", "frida ver"), current_version))
        else:
            self.menufrida.setTitle(self.trText("frida切换", "frida ver"))

        selected_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
        for action in getattr(self, "fridaVersionMenuActions", []):
            version = str(action.data() or "").strip()
            if not version:
                continue
            is_current = version == current_version
            label = version
            if is_current:
                label += self.trText("（当前）", " (Current)")
            action.setText(label)
            action.setChecked(is_current)
            action.setIcon(selected_icon if is_current else QIcon())
            action.setIconVisibleInMenu(True)
        self.updateToolbarContextPanel()

    def currentPythonVersionDisplay(self):
        return "{}.{}".format(sys.version_info.major, sys.version_info.minor)

    def isFridaVersionSupportedOnCurrentPython(self, version):
        return True, ""

    def setCmdMenuVisible(self, visible):
        self.menucmd.menuAction().setVisible(visible)

    def getFridaReleaseCatalogOrEmpty(self):
        return self.fridaReleaseCatalog or self.loadCachedFridaReleaseCatalog() or FRIDA_EMPTY_RELEASE_CATALOG

    def initFridaUploadMenu(self):
        self.actionPushFridaServer.setVisible(False)
        self.actionPushFridaServerX86.setVisible(False)
        self.fridaUploadMenu = QMenu(self.menu)
        self.fridaUploadMenu.setObjectName("fridaUploadMenu")
        self.fridaUploadMenu.aboutToShow.connect(self.refreshFridaUploadMenu)
        self.fridaArm64Menu = QMenu(self.fridaUploadMenu)
        self.fridaX64Menu = QMenu(self.fridaUploadMenu)
        self.menu.insertMenu(self.actionPushFartSo, self.fridaUploadMenu)

    def clearFridaUploadMenuActions(self):
        if self.fridaUploadMenu is None:
            return
        self.fridaUploadMenu.clear()
        self.fridaArm64Menu = QMenu(self.fridaUploadMenu)
        self.fridaX64Menu = QMenu(self.fridaUploadMenu)

    def fridaFamilyText(self, family_key):
        return self.trText("arm64", "arm64") if family_key == "arm64" else self.trText("x64", "x64")

    def createDisabledMenuAction(self, text):
        action = QAction(text, self)
        action.setEnabled(False)
        return action

    def sortVersionsDescending(self, versions):
        return sorted(versions, key=lambda item: tuple(int(part) for part in item.split(".")), reverse=True)

    def listLocalFridaInventory(self):
        inventory = {}
        exec_dir = os.path.abspath("./exec")
        if os.path.exists(exec_dir) is False:
            return inventory

        pattern = re.compile(r"^frida-server-(\d+\.\d+\.\d+)-android-(arm|arm64|x86|x86_64)$")
        preferred_arch_by_family = {
            "arm64": "arm64",
            "x64": "x86_64",
        }
        for file_name in os.listdir(exec_dir):
            match = pattern.match(file_name)
            if match is None:
                continue

            version, arch = match.groups()
            family_key = FRIDA_LOCAL_ARCH_TO_FAMILY.get(arch)
            if family_key is None:
                continue

            local_path = os.path.join(exec_dir, file_name)
            if os.path.isfile(local_path) is False or os.path.getsize(local_path) <= 0:
                continue

            version_inventory = inventory.setdefault(version, {})
            current_entry = version_inventory.get(family_key)
            should_replace = current_entry is None or arch == preferred_arch_by_family.get(family_key)
            if should_replace:
                version_inventory[family_key] = {arch: local_path}
        return inventory

    def buildLatestPatchVersionMap(self, versions):
        catalog = {major: [] for major in FRIDA_SUPPORTED_MAJORS}
        grouped = {major: [] for major in FRIDA_SUPPORTED_MAJORS}
        for version in versions:
            try:
                major = int(version.split(".", 1)[0])
            except Exception:
                continue
            if major not in grouped:
                continue
            grouped[major].append(version)
        for major in FRIDA_SUPPORTED_MAJORS:
            catalog[major] = self.sortVersionsDescending(list(set(grouped[major])))[:FRIDA_MENU_VERSION_LIMIT]
        return catalog

    def loadCachedFridaReleaseCatalog(self):
        if os.path.exists(FRIDA_RELEASE_CACHE_PATH) is False:
            return None
        try:
            with open(FRIDA_RELEASE_CACHE_PATH, "r", encoding="utf-8") as cache_file:
                data = json.loads(cache_file.read())
            if not isinstance(data, dict):
                return None
            catalog = {major: list(data.get(str(major), data.get(major, []))) for major in FRIDA_SUPPORTED_MAJORS}
            if not any(catalog.values()):
                return None
            return catalog
        except Exception:
            return None

    def saveFridaReleaseCatalogCache(self, catalog):
        with open(FRIDA_RELEASE_CACHE_PATH, "w", encoding="utf-8") as cache_file:
            json.dump({str(key): value for key, value in catalog.items()}, cache_file, ensure_ascii=False, indent=2)

    def rebuildFridaVersionMenu(self):
        self.menufrida.clear()
        self.fridaVersionMenuActions = []
        installed_version = self.getInstalledPythonFridaVersion()
        if installed_version:
            self.curFridaVer = installed_version
        inventory = self.listLocalFridaInventory()
        local_versions = self.sortVersionsDescending(list(inventory.keys()))
        if not local_versions:
            placeholder = QAction(self.trText("请先下载并上传 frida", "Download and upload frida first"), self)
            placeholder.setEnabled(False)
            self.menufrida.addAction(placeholder)
            self.updateFridaVersionSelectionUi(installed_version)
            return
        self.verGroup = QActionGroup(self)
        self.verGroup.setExclusive(True)
        for version in local_versions:
            action = QAction(version, self)
            action.setCheckable(True)
            action.setData(version)
            supported, unsupported_reason = self.isFridaVersionSupportedOnCurrentPython(version)
            action.setChecked(bool(installed_version) and version == installed_version)
            action.setEnabled(supported)
            if not supported:
                action.setToolTip(unsupported_reason)
                action.setStatusTip(unsupported_reason)
            action.triggered.connect(lambda checked, current_version=version: self.changeFridaClientVersion(current_version, checked))
            self.verGroup.addAction(action)
            self.menufrida.addAction(action)
            self.fridaVersionMenuActions.append(action)
        self.updateFridaVersionSelectionUi(installed_version or self.curFridaVer)

    def fetchFridaReleaseCatalog(self):
        versions = []
        version_re = re.compile(r"^\d+\.\d+\.\d+$")
        for page in range(1, FRIDA_RELEASE_TAGS_PAGES + 1):
            request = urllib.request.Request(
                FRIDA_RELEASE_TAGS_API_URL.format(page=page),
                headers={"User-Agent": "fridaUiTools/1.0"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                tag_data = json.loads(response.read().decode("utf-8"))
            if not isinstance(tag_data, list) or len(tag_data) <= 0:
                break
            page_versions = []
            for item in tag_data:
                tag_name = str(item.get("name", "")).strip()
                if version_re.match(tag_name):
                    page_versions.append(tag_name)
            versions.extend(page_versions)
            if len(page_versions) <= 0:
                break
        if len(versions) <= 0:
            raise RuntimeError("empty tag list")
        return self.buildLatestPatchVersionMap(versions)

    def ensureFridaReleaseCatalog(self):
        if self.fridaReleaseCatalog is not None:
            return self.fridaReleaseCatalog
        cached_catalog = self.loadCachedFridaReleaseCatalog()
        if cached_catalog is not None:
            self.fridaReleaseCatalog = cached_catalog
            self.fridaReleaseCatalogError = ""
            return self.fridaReleaseCatalog
        try:
            self.fridaReleaseCatalog = self.fetchFridaReleaseCatalog()
            self.saveFridaReleaseCatalogCache(self.fridaReleaseCatalog)
            self.fridaReleaseCatalogError = ""
            return self.fridaReleaseCatalog
        except Exception as error:
            self.fridaReleaseCatalogError = str(error)
            fallback_catalog = {major: list(FRIDA_FALLBACK_VERSION_CATALOG.get(major, [])) for major in FRIDA_SUPPORTED_MAJORS}
            self.fridaReleaseCatalog = fallback_catalog
            try:
                self.saveFridaReleaseCatalogCache(fallback_catalog)
            except Exception:
                pass
            return fallback_catalog

    def ensureFridaVersionMenuReady(self):
        if self.fridaReleaseCatalog is None:
            self.ensureFridaReleaseCatalog()
        self.rebuildFridaVersionMenu()

    def addFridaMenuAction(self, menu, text, version, family_key, source, arch, checked=False):
        action = QAction(text, self)
        action.setCheckable(checked)
        action.setChecked(checked)
        action.setData({"version": version, "family": family_key, "source": source, "arch": arch})
        action.triggered.connect(self.handleFridaMenuAction)
        menu.addAction(action)
        return action

    def populateFridaFamilyMenu(self, menu, family_key, catalog, inventory):
        menu.setTitle(self.fridaFamilyText(family_key))
        has_item = False
        target_arch = "arm64" if family_key == "arm64" else "x86_64"
        for major in FRIDA_SUPPORTED_MAJORS:
            versions = catalog.get(major, [])
            if not versions:
                continue
            if has_item:
                menu.addSeparator()
            for version in versions:
                checked = family_key in inventory.get(version, {})
                self.addFridaMenuAction(menu, version, version, family_key, "remote", target_arch, checked=checked)
                has_item = True
        if has_item is False:
            menu.addAction(self.createDisabledMenuAction(self.trText("版本列表加载失败", "Failed to load versions")))

    def refreshFridaUploadMenu(self):
        self.clearFridaUploadMenuActions()
        self.fridaUploadMenu.setTitle(self.trText("上传 frida", "Upload frida"))
        if self.fridaReleaseCatalog is None:
            self.ensureFridaReleaseCatalog()
        inventory = self.listLocalFridaInventory()
        has_local = False
        for version in self.sortVersionsDescending(list(inventory.keys())):
            version_inventory = inventory.get(version, {})
            for family_key in FRIDA_MENU_FAMILIES:
                entry = version_inventory.get(family_key)
                if entry:
                    local_arch = next(iter(entry.keys()))
                    text = f"{version} [{self.fridaFamilyText(family_key)}]"
                    self.addFridaMenuAction(self.fridaUploadMenu, text, version, family_key, "local", local_arch)
                    has_local = True
        if has_local is False:
            self.fridaUploadMenu.addAction(self.createDisabledMenuAction(self.trText("没有已下载的 frida 版本", "No downloaded frida versions")))
        self.fridaUploadMenu.addSeparator()
        catalog = self.fridaReleaseCatalog or FRIDA_EMPTY_RELEASE_CATALOG
        self.populateFridaFamilyMenu(self.fridaArm64Menu, "arm64", catalog, inventory)
        self.populateFridaFamilyMenu(self.fridaX64Menu, "x64", catalog, inventory)
        self.fridaUploadMenu.addMenu(self.fridaArm64Menu)
        self.fridaUploadMenu.addMenu(self.fridaX64Menu)

    def handleFridaMenuAction(self):
        action = self.sender()
        if action is None:
            return
        data = action.data() or {}
        version = data.get("version", "")
        family_key = data.get("family", "")
        source = data.get("source", "")
        arch = data.get("arch", "")
        if not version or not family_key:
            return
        upload_only = source == "local"
        self.handleFridaVersionUpload(version, family_key, arch=arch, upload_only=upload_only)

    def handleFridaVersionUpload(self, version, family_key, arch="", upload_only=False):
        try:
            self.setFridaUploadActionsEnabled(False)
            self.uploadFridaFamily(version, family_key, preferred_arch=arch, upload_only=upload_only)
            self.curFridaVer = version
            QMessageBox().information(self, "hint", self.trText("上传完成.", "Upload completed."))
        except Exception as error:
            message = f"{self.trText('上传异常：', 'Upload failed: ')}{error}\nVersion: {version}\nFamily: {family_key}"
            if arch:
                message += f"\nArch: {arch}"
            if self.fridaReleaseCatalogError:
                message += f"\nCatalog error: {self.fridaReleaseCatalogError}"
            QMessageBox.critical(self, "error", message)
        finally:
            self.setFridaUploadActionsEnabled(True)


    def selectedDeviceSerial(self):
        if hasattr(self, "cmbDevices"):
            current_serial = (self.cmbDevices.currentData() or self.cmbDevices.currentText() or "").strip()
            if len(current_serial) > 0:
                return current_serial
        if hasattr(self, "cmbMainContextDevices"):
            current_serial = (self.cmbMainContextDevices.currentData() or self.cmbMainContextDevices.currentText() or "").strip()
            if len(current_serial) > 0:
                return current_serial
        return (getattr(self, "selectedDeviceId", "") or "").strip()

    def selectedDeviceLabel(self):
        if hasattr(self, "cmbDevices") and self.cmbDevices.currentIndex() >= 0:
            return self.cmbDevices.currentText().strip()
        return self.selectedDeviceSerial()

    def currentAppSnapshotForSelectedDevice(self):
        snapshot = self.currentAppInfoSnapshot or {}
        if len(snapshot) <= 0:
            return {}
        snapshot_serial = (snapshot.get("deviceSerial") or "").strip()
        current_serial = self.selectedDeviceSerial()
        if snapshot_serial and current_serial and snapshot_serial != current_serial:
            return {}
        return snapshot

    def setMainContextForegroundPackage(self, package_name):
        self.mainContextForegroundPackage = (package_name or "").strip()

    def readForegroundPackageNameSilently(self):
        if len(self.selectedDeviceSerial()) <= 0:
            return ""
        try:
            res = CmdUtil.exec("adb shell dumpsys window")
        except Exception:
            return ""
        m1 = re.search("mCurrentFocus=Window\\{(.+?)\\}", res)
        if m1 is None:
            return ""
        m1sp = m1.group(1).split(" ")
        if len(m1sp) < 3:
            return ""
        focus_entry = m1sp[2].strip()
        if focus_entry == "StatusBar":
            return ""
        focus_parts = focus_entry.split("/")
        if len(focus_parts) < 2:
            return ""
        return focus_parts[0].strip()

    def refreshMainContextForegroundPackage(self):
        snapshot = self.currentAppSnapshotForSelectedDevice()
        if snapshot:
            self.setMainContextForegroundPackage(snapshot.get("packageName"))
            return
        self.setMainContextForegroundPackage(self.readForegroundPackageNameSilently())

    def updateSelectedDevice(self, serial):
        self.selectedDeviceId = (serial or "").strip()
        if self.selectedDeviceId:
            os.environ["ANDROID_SERIAL"] = self.selectedDeviceId
        elif "ANDROID_SERIAL" in os.environ:
            os.environ.pop("ANDROID_SERIAL")

    def populateDeviceCombo(self, combo, devices, target):
        if combo is None:
            return
        combo.blockSignals(True)
        combo.clear()
        for serial in devices:
            combo.addItem(serial, serial)
        combo.setEnabled(len(devices) > 0)
        if target:
            index = combo.findData(target)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

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
        target = previous if previous in devices else (devices[0] if devices else "")
        self.populateDeviceCombo(self.cmbDevices, devices, target)
        if hasattr(self, "cmbMainContextDevices"):
            self.populateDeviceCombo(self.cmbMainContextDevices, devices, target)
        self.updateSelectedDevice(target)
        snapshot_serial = ((self.currentAppInfoSnapshot or {}).get("deviceSerial") or "").strip()
        if len(target) <= 0 or (snapshot_serial and snapshot_serial != target):
            self.currentAppInfoSnapshot = {}
        self.refreshMainContextForegroundPackage()
        if hasattr(self, "labDeviceStatus"):
            if target:
                self.labDeviceStatus.setText(self.trText("当前设备：", "Current device: ") + target)
            else:
                self.labDeviceStatus.setText(self.trText("当前设备：未检测到已连接设备", "Current device: no connected device detected"))
        self.updateToolbarContextPanel()
        self.updateCurrentAppInfoTable()
        self.refreshOverviewCards()

    def onDeviceChanged(self):
        sender = self.sender()
        current = ""
        if isinstance(sender, QtWidgets.QComboBox):
            current = (sender.currentData() or sender.currentText() or "").strip()
        else:
            current = self.selectedDeviceSerial()
        for combo_name in ("cmbDevices", "cmbMainContextDevices"):
            combo = getattr(self, combo_name, None)
            if combo is None or combo is sender:
                continue
            index = combo.findData(current)
            combo.blockSignals(True)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)
        self.updateSelectedDevice(current)
        snapshot_serial = ((self.currentAppInfoSnapshot or {}).get("deviceSerial") or "").strip()
        if len(current) <= 0 or (snapshot_serial and snapshot_serial != current):
            self.currentAppInfoSnapshot = {}
        self.refreshMainContextForegroundPackage()
        if hasattr(self, "labDeviceStatus"):
            self.labDeviceStatus.setText((self.trText("当前设备：", "Current device: ") + current) if current else self.trText("当前设备：未检测到已连接设备", "Current device: no connected device detected"))
        self.updateToolbarContextPanel()
        self.updateCurrentAppInfoTable()
        self.refreshOverviewCards()

    def toggleLogDock(self):
        self.showLogDock(self.tab_3)

    def showLogDock(self, target_tab=None):
        if target_tab is not None and self.tabWidget.indexOf(target_tab) >= 0:
            self.tabWidget.setCurrentWidget(target_tab)
        self.raise_()
        self.activateWindow()

    def loadTypeData(self):
        typePath = os.path.join(APP_ROOT, "config", "type_en.json" if self.isEnglish() else "type.json")
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
        data = self.currentAppSnapshotForSelectedDevice()
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
        dex_count = runtime.get("dexCount") or len(data.get("dexes", []))
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
            (self.trText("DEX 数量", "DEX count"), dex_count),
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
            (self.trText("DEX 信息异常", "DEX info error"), data.get("dexError")),
            (self.trText("附加信息异常", "Attach info error"), data.get("packageError")),
        ]

    def updateAttachedInfoTable(self):
        if hasattr(self, "attachInfoTable"):
            self.setupInfoTable(self.attachInfoTable)
            self.setInfoTableRows(self.attachInfoTable, self.buildAttachedInfoRows())

    def initSmartLayout(self):
        self.resize(980, 720)
        self.setMinimumSize(920, 660)
        self.tabWidget.setDocumentMode(False)
        self.groupLogs.setDocumentMode(False)
        self.groupLogs.setTabPosition(QtWidgets.QTabWidget.North)
        self.groupLogs.setUsesScrollButtons(True)

        self.groupBox.setMinimumWidth(0)
        self.groupBox_2.setMinimumWidth(0)
        self.groupBox.setMinimumHeight(0)
        self.groupBox_2.setMinimumHeight(0)

        main_buttons = [
            self.btnDumpSo,
            self.btnDumpPtr,
            self.btnDumpDex,
            self.btnFart,
            self.btnWallbreaker,
            self.btnCallFunction,
            self.btnMemSearch,
            self.btnMatchMethod,
            self.btnNatives,
            self.btnStalker,
            self.btnTuoke,
            self.btnCustom,
            self.btnPatch,
            self.btnAntiFrida,
        ]
        for button in main_buttons:
            button.setMinimumHeight(40)
            button.setCursor(Qt.PointingHandCursor)

        self.gridLayout_6.removeWidget(self.groupBox)
        self.gridLayout_6.removeWidget(self.groupBox_2)
        self.gridLayout_6.removeWidget(self.groupLogs)
        self.groupLogs.setVisible(False)

        self.mainLeftWidget = QtWidgets.QWidget(self.tab_2)
        self.mainLeftWidget.setMaximumWidth(16777215)
        self.mainLeftWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.mainLeftLayout = QtWidgets.QVBoxLayout(self.mainLeftWidget)
        self.mainLeftLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLeftLayout.setSpacing(4)
        self.initMainContextPanel()
        self.groupBox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.groupBox_2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.mainLeftLayout.addWidget(self.mainContextGroup)
        self.mainLeftLayout.addWidget(self.groupBox)
        self.mainLeftLayout.addWidget(self.groupBox_2)

        self.customTemplateGroup = QtWidgets.QGroupBox(self.trText("自定义模板", "Custom Templates"), self.tab_2)
        self.customTemplateGroup.setObjectName("panelCard")
        self.customTemplateGroup.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.customTemplateLayout = QtWidgets.QVBoxLayout(self.customTemplateGroup)
        self.customTemplateLayout.setContentsMargins(10, 12, 10, 8)
        self.customTemplateLayout.setSpacing(6)
        self.labCustomTemplateHint = QLabel(
            self.trText("将常用脚本固定到主界面，一键启用/禁用；管理与编辑请进入“自定义”。", "Pin frequently used scripts here for one-click enable/disable. Use 'Custom' to manage and edit templates."),
            self.customTemplateGroup,
        )
        self.labCustomTemplateHint.setWordWrap(True)
        self.labCustomTemplateHint.setObjectName("panelHint")
        self.customTemplateLayout.addWidget(self.labCustomTemplateHint)
        self.customTemplateScroll = QtWidgets.QScrollArea(self.customTemplateGroup)
        self.customTemplateScroll.setObjectName("customTemplateScroll")
        self.customTemplateScroll.setWidgetResizable(True)
        self.customTemplateScroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.customTemplateScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.customTemplateScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.customTemplateScroll.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.customTemplateContainer = QtWidgets.QWidget(self.customTemplateScroll)
        self.customTemplateContainer.setObjectName("customTemplateContainer")
        self.customTemplateGrid = QtWidgets.QGridLayout(self.customTemplateContainer)
        self.customTemplateGrid.setContentsMargins(0, 0, 0, 0)
        self.customTemplateGrid.setHorizontalSpacing(4)
        self.customTemplateGrid.setVerticalSpacing(4)
        self.customTemplateScroll.setWidget(self.customTemplateContainer)
        self.customTemplateLayout.addWidget(self.customTemplateScroll, 1)
        self.customTemplateTiles = []
        QtCore.QTimer.singleShot(0, self.rebuildPinnedCustomTemplateGrid)
        self.mainLeftLayout.addWidget(self.customTemplateGroup, 1)

        self.mainLeftLayout.setAlignment(Qt.AlignTop)
        self.mainLeftLayout.setStretch(0, 0)
        self.mainLeftLayout.setStretch(1, 0)
        self.mainLeftLayout.setStretch(2, 0)
        self.mainLeftLayout.setStretch(3, 1)
        self.gridLayout_6.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_6.setHorizontalSpacing(4)
        self.gridLayout_6.setVerticalSpacing(4)
        self.gridLayout_6.setRowStretch(0, 0)
        self.gridLayout_6.setRowStretch(1, 1)
        self.gridLayout_6.setColumnStretch(0, 1)
        self.gridLayout_6.setColumnMinimumWidth(0, 0)
        self.gridLayout_6.addWidget(self.mainLeftWidget, 0, 0, 1, 1, Qt.AlignTop)

        self.configureClassicMainPanels()
        self.ensureBuiltinCustomTemplates()
        self.refreshPinnedCustomTemplates()
        self.configureInfoTabs()
        self.configureAttachExplorerTab()
        self.removeAssistTab()
        self.registerLogTabs()
        self.configureLogWidgets()

    def registerLogTabs(self):
        log_tabs = [self.tab_4, self.tab_3, self.tab_5]
        while self.groupLogs.count() > 0:
            self.groupLogs.removeTab(0)
        for tab in log_tabs:
            if self.tabWidget.indexOf(tab) < 0:
                self.tabWidget.addTab(tab, "")

    def configureClassicMainPanels(self):
        self.gridLayout_4.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_7.setContentsMargins(4, 4, 4, 4)
        self.gridLayout_4.setHorizontalSpacing(4)
        self.gridLayout_4.setVerticalSpacing(4)
        self.gridLayout_7.setHorizontalSpacing(4)
        self.gridLayout_7.setVerticalSpacing(2)

        for widget in [
            self.chkNetwork,
            self.chkJni,
            self.chkNewJnitrace,
            self.chkHookEvent,
            self.chkAntiDebug,
            self.chkRegisterNative,
            self.chkJavaEnc,
            self.chkArtMethod,
            self.chkSslPining,
            self.chkLibArt,
        ]:
            self.gridLayout_5.removeWidget(widget)
            widget.deleteLater()

        common_buttons = [
            self.btnDumpSo,
            self.btnWallbreaker,
            self.btnCallFunction,
            self.btnMemSearch,
            self.btnDumpPtr,
            self.btnFart,
            self.btnDumpDex,
        ]
        for button in common_buttons:
            self.gridLayout_4.removeWidget(button)
            button.setMinimumHeight(32)
            button.setMaximumHeight(32)
            button.setCursor(Qt.PointingHandCursor)
        self.gridLayout_4.addWidget(self.btnDumpSo, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.btnWallbreaker, 0, 1, 1, 1)
        self.gridLayout_4.addWidget(self.btnCallFunction, 0, 2, 1, 1)
        self.gridLayout_4.addWidget(self.btnMemSearch, 0, 3, 1, 1)
        self.gridLayout_4.addWidget(self.btnDumpPtr, 1, 0, 1, 1)
        self.gridLayout_4.addWidget(self.btnFart, 1, 1, 1, 1)
        self.gridLayout_4.addWidget(self.btnDumpDex, 1, 2, 1, 1)
        for col in range(4):
            self.gridLayout_4.setColumnStretch(col, 1)

        if hasattr(self, "labAiFeatureStatusMain"):
            self.gridLayout_7.removeWidget(self.labAiFeatureStatusMain)
            self.labAiFeatureStatusMain.deleteLater()
            del self.labAiFeatureStatusMain

        if hasattr(self, "mainFeatureButtonGrid"):
            self.gridLayout_7.removeItem(self.mainFeatureButtonGrid)
        self.mainFeatureButtonGrid = QtWidgets.QGridLayout()
        self.mainFeatureButtonGrid.setContentsMargins(0, 0, 0, 0)
        self.mainFeatureButtonGrid.setHorizontalSpacing(4)
        self.mainFeatureButtonGrid.setVerticalSpacing(4)
        self.gridLayout_7.removeItem(self.gridLayout_5)
        self.gridLayout_7.removeItem(self.horizontalLayout)

        self.btnFCAndJnitracePanel = QtWidgets.QPushButton(self.groupBox_2)
        self.btnFCAndJnitracePanel.setObjectName("btnFCAndJnitracePanel")
        self.btnFCAndJnitracePanel.setMinimumHeight(32)
        self.btnFCAndJnitracePanel.setMaximumHeight(32)
        self.btnFCAndJnitracePanel.setCursor(Qt.PointingHandCursor)
        self.btnFCAndJnitracePanel.clicked.connect(self.openFCAndJnitrace)

        feature_buttons = [
            self.btnMatchMethod,
            self.btnNatives,
            self.btnStalker,
            self.btnTuoke,
            self.btnPatch,
            self.btnAntiFrida,
            self.btnFCAndJnitracePanel,
        ]
        # 隐藏已移到工具栏的按钮
        self.btnCustom.hide()
        for index, button in enumerate(feature_buttons):
            self.horizontalLayout.removeWidget(button)
            button.setMinimumHeight(32)
            button.setMaximumHeight(32)
            button.setCursor(Qt.PointingHandCursor)
            self.mainFeatureButtonGrid.addWidget(button, index // 4, index % 4, 1, 1)
        for col in range(4):
            self.mainFeatureButtonGrid.setColumnStretch(col, 1)
        self.gridLayout_7.addLayout(self.mainFeatureButtonGrid, 1, 0, 1, 1)
        self.gridLayout_7.setRowMinimumHeight(0, 0)
        self.gridLayout_7.setRowMinimumHeight(1, 0)
        self.gridLayout_7.setRowMinimumHeight(2, 0)
        self.gridLayout_7.setRowStretch(0, 0)
        self.gridLayout_7.setRowStretch(1, 0)
        self.gridLayout_7.setRowStretch(2, 0)
        self.gridLayout_7.setRowStretch(3, 0)

    def createSummaryCard(self, title, value, accent_color):
        card = QtWidgets.QFrame(self.tab)
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

        self.attachSummaryWidget = QtWidgets.QWidget(self.tab)
        self.attachSummaryLayout = QtWidgets.QHBoxLayout(self.attachSummaryWidget)
        self.attachSummaryLayout.setContentsMargins(0, 0, 0, 0)
        self.attachSummaryLayout.setSpacing(10)
        self.attachPackageCard = self.createSummaryCard(self.trText("附加目标", "Attached target"), "-", "#1b5fd1")
        self.attachProcessCard = self.createSummaryCard(self.trText("进程环境", "Process runtime"), "-", "#0f766e")
        self.attachModuleCard = self.createSummaryCard(self.trText("SO 模块", "SO modules"), "-", "#7c3aed")
        self.attachDexCard = self.createSummaryCard(self.trText("DEX", "DEX"), "-", "#b45309")
        self.attachDebugCard = self.createSummaryCard(self.trText("调试状态", "Debug state"), "-", "#dc2626")
        for card in [self.attachPackageCard, self.attachProcessCard, self.attachModuleCard, self.attachDexCard, self.attachDebugCard]:
            self.attachSummaryLayout.addWidget(card, 1)

        self.groupBox_4.hide()
        self.groupBox_6.hide()
        self.btnMethod.hide()
        self.btnMethodClear.hide()

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

        self.attachDexGroup = QtWidgets.QGroupBox(self.tab)
        self.attachDexGroup.setObjectName("panelCard")
        self.attachDexLayout = QtWidgets.QVBoxLayout(self.attachDexGroup)
        self.attachDexLayout.setContentsMargins(10, 12, 10, 10)
        self.attachDexLayout.setSpacing(8)
        self.labAttachDexHint = QLabel(self.attachDexGroup)
        self.labAttachDexHint.setObjectName("panelHint")
        self.labAttachDexHint.setWordWrap(True)
        self.attachDexLayout.addWidget(self.labAttachDexHint)
        self.txtDex = QLineEdit(self.attachDexGroup)
        self.attachDexLayout.addWidget(self.txtDex)
        self.listDex = QtWidgets.QListWidget(self.attachDexGroup)
        self.attachDexLayout.addWidget(self.listDex, 1)

        self.attachResourceDetailGroup = QtWidgets.QGroupBox(self.tab)
        self.attachResourceDetailGroup.setObjectName("panelCard")
        self.attachResourceDetailLayout = QtWidgets.QVBoxLayout(self.attachResourceDetailGroup)
        self.attachResourceDetailLayout.setContentsMargins(10, 12, 10, 10)
        self.attachResourceDetailLayout.setSpacing(8)
        self.labAttachResourceHint = QLabel(self.attachResourceDetailGroup)
        self.labAttachResourceHint.setWordWrap(True)
        self.labAttachResourceHint.setObjectName("panelHint")
        self.attachResourceDetailLayout.addWidget(self.labAttachResourceHint)
        self.attachResourceTable = QtWidgets.QTableWidget(self.attachResourceDetailGroup)
        self.attachResourceTable.setObjectName("attachResourceTable")
        self.attachResourceDetailLayout.addWidget(self.attachResourceTable, 1)
        self.setupInfoTable(self.attachResourceTable)

        self.nativeResultWidget = QtWidgets.QWidget(self.tab)
        self.nativeResultLayout = QtWidgets.QHBoxLayout(self.nativeResultWidget)
        self.nativeResultLayout.setContentsMargins(0, 0, 0, 0)
        self.nativeResultLayout.setSpacing(12)
        self.nativeResultLayout.addWidget(self.nativeActionGroup, 2)
        self.nativeResultLayout.addWidget(self.groupBox_5, 7)

        self.javaResultWidget = QtWidgets.QWidget(self.tab)
        self.javaResultLayout = QtWidgets.QHBoxLayout(self.javaResultWidget)
        self.javaResultLayout.setContentsMargins(0, 0, 0, 0)
        self.javaResultLayout.setSpacing(12)
        self.javaResultLayout.addWidget(self.javaActionGroup, 2)
        self.javaResultLayout.addWidget(self.groupBox_6, 7)

        self.attachResourceTabs = QtWidgets.QTabWidget(self.tab)
        self.attachResourceTabs.addTab(self.groupBox_3, "")
        self.attachResourceTabs.addTab(self.attachDexGroup, "")

        self.attachResultTabs = QtWidgets.QTabWidget(self.tab)
        self.attachResultTabs.addTab(self.nativeResultWidget, "")
        self.attachResultTabs.addTab(self.groupBox_7, "")

        self.attachRightPane = QtWidgets.QWidget(self.tab)
        self.attachRightLayout = QtWidgets.QVBoxLayout(self.attachRightPane)
        self.attachRightLayout.setContentsMargins(0, 0, 0, 0)
        self.attachRightLayout.setSpacing(12)
        self.attachRightLayout.addWidget(self.attachResourceDetailGroup, 3)
        self.attachRightLayout.addWidget(self.attachResultTabs, 7)

        self.attachExplorerSplitter = QtWidgets.QSplitter(Qt.Horizontal, self.tab)
        self.attachExplorerSplitter.setChildrenCollapsible(False)
        self.attachExplorerSplitter.addWidget(self.attachResourceTabs)
        self.attachExplorerSplitter.addWidget(self.attachRightPane)
        self.attachExplorerSplitter.setStretchFactor(0, 4)
        self.attachExplorerSplitter.setStretchFactor(1, 7)
        self.attachExplorerSplitter.setSizes([420, 860])

        self.attachRootWidget = QtWidgets.QWidget(self.tab)
        self.attachRootLayout = QtWidgets.QVBoxLayout(self.attachRootWidget)
        self.attachRootLayout.setContentsMargins(0, 0, 0, 0)
        self.attachRootLayout.setSpacing(12)
        self.attachRootLayout.addWidget(self.attachSummaryWidget)
        self.attachRootLayout.addWidget(self.attachExplorerSplitter, 1)
        self.gridLayout_14.addWidget(self.attachRootWidget, 0, 0, 1, 1)

        self.txtDex.textChanged.connect(self.changeDex)
        self.listDex.itemClicked.connect(self.listDexClick)
        self.listSymbol.itemClicked.connect(self.listSymbolClick)
        self.attachResultTabs.currentChanged.connect(self.onAttachResultTabChanged)
        self.setupInfoTable(self.attachResourceTable)

    def removeAssistTab(self):
        if hasattr(self, "tab_7"):
            tab_index = self.tabWidget.indexOf(self.tab_7)
            if tab_index >= 0:
                self.tabWidget.removeTab(tab_index)

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

        if hasattr(self, "labAiFeatureStatusMain"):
            self.gridLayout_7.removeWidget(self.labAiFeatureStatusMain)
            self.labAiFeatureStatusMain.deleteLater()
            del self.labAiFeatureStatusMain

        self.quickScriptGroup = QtWidgets.QGroupBox(self._translate("kmainForm", "常用 Hook 预设"), self.groupBox_2)
        self.quickScriptGroup.setObjectName("panelCard")
        self.quickScriptLayout = QtWidgets.QVBoxLayout(self.quickScriptGroup)
        self.quickScriptLayout.setContentsMargins(12, 14, 12, 12)
        self.quickScriptLayout.setSpacing(10)
        self.labQuickScriptHint = QLabel(
            self._translate("kmainForm", "主页只保留需要额外参数或特殊处理的 Hook；普通脚本预设统一迁到“自定义模板”。"),
            self.quickScriptGroup,
        )
        self.labQuickScriptHint.setWordWrap(True)
        self.labQuickScriptHint.setObjectName("panelHint")
        self.quickScriptLayout.addWidget(self.labQuickScriptHint)
        for widget in [
            self.chkJavaEnc,
            self.chkSslPining,
            self.chkHookEvent,
            self.chkRegisterNative,
            self.chkArtMethod,
            self.chkLibArt,
            self.chkAntiDebug,
        ]:
            self.gridLayout_5.removeWidget(widget)
            widget.hide()

        for widget in [
            self.chkJavaEnc,
            self.chkSslPining,
            self.chkHookEvent,
            self.chkRegisterNative,
            self.chkArtMethod,
            self.chkLibArt,
            self.chkAntiDebug,
        ]:
            self.gridLayout_5.removeWidget(widget)
            widget.hide()

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
        self.cmdPatch = self.buildToolLauncher(self.advancedToolGroup, self.patch)
        self.cmdStalker = self.buildToolLauncher(self.advancedToolGroup, self.stalker)
        self.cmdTuoke = self.buildToolLauncher(self.advancedToolGroup, self.tuoke)
        self.cmdAiSettings = self.buildToolLauncher(self.advancedToolGroup, self.openAiSettings)
        self.advancedButtons = [
            self.cmdOpenCustom,
            self.cmdOpenGumTrace,
            self.cmdOpenInspector,
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
        self.gridLayout_7.addWidget(self.hookPanelWidget, 1, 0, 1, 1)
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
        return


    def configureLogWidgets(self):
        for editor in [self.txtLogs, self.txtoutLogs]:
            editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            editor.setPlaceholderText(self._translate("kmainForm", "日志将在这里滚动显示..."))
        self.tabHooks.setAlternatingRowColors(True)
        self.tabHooks.verticalHeader().setVisible(False)
        if hasattr(self, "txtAiLogInput"):
            self.txtAiLogInput.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
            self.txtAiLogInput.setPlaceholderText(self._translate("kmainForm", "打开日志文件，或直接粘贴 / 输入待分析日志..."))
        self.txtAiAnalysis.setPlaceholderText(self._translate("kmainForm", "AI 分析结果会显示在这里")) if hasattr(self, "txtAiAnalysis") else None

    def applyWorkbenchTheme(self):
        # 如果已经应用了 qt-material 主题，跳过自定义 stylesheet
        try:
            import sys
            if 'qt_material' in sys.modules:
                return
        except Exception:
            pass
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
            background: #d6e7ff;
            border-color: #6b9ef5;
            border-width: 2px;
        }
        QPushButton:pressed {
            background: #c5d9ff;
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
            background: #e3f0ff;
            border-color: #7aa5f0;
            border-width: 2px;
        }
        QCommandLinkButton::description {
            color: #60738a;
        }
        QCheckBox {
            spacing: 8px;
            padding: 4px 0;
        }
        QCheckBox:hover {
            background: #f0f7ff;
            border-radius: 4px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 2px solid #c8d7ee;
            border-radius: 4px;
            background: #ffffff;
        }
        QCheckBox::indicator:hover {
            border-color: #6b9ef5;
            border-width: 2px;
            background: #f0f7ff;
        }
        QCheckBox::indicator:checked {
            background: #4f8cff;
            border-color: #4f8cff;
        }
        QCheckBox::indicator:checked:hover {
            background: #3d7ae8;
            border-color: #3d7ae8;
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

        self.aiAnalysisSplitter = QtWidgets.QSplitter(Qt.Vertical, self.aiAnalysisTab)
        self.aiAnalysisSplitter.setChildrenCollapsible(False)

        self.txtAiLogInput = QtWidgets.QPlainTextEdit(self.aiAnalysisSplitter)
        self.txtAiLogInput.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        self.txtAiAnalysis = QtWidgets.QPlainTextEdit(self.aiAnalysisSplitter)
        self.txtAiAnalysis.setReadOnly(True)

        self.aiAnalysisLayout.addWidget(self.aiAnalysisSplitter, 1)
        self.aiAnalysisSplitter.setStretchFactor(0, 1)
        self.aiAnalysisSplitter.setStretchFactor(1, 1)
        self.aiAnalysisSplitter.setSizes([360, 320])
        if self.tabWidget.indexOf(self.aiAnalysisTab) < 0:
            self.tabWidget.addTab(self.aiAnalysisTab, "")

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
        self.txtAiLogInput.setPlaceholderText(self._translate("kmainForm", "打开日志文件，或直接粘贴 / 输入待分析日志..."))
        self.txtAiAnalysis.setPlaceholderText(self._translate("kmainForm", "AI 分析结果会显示在这里"))
        self.btnOpenLogFile.clicked.connect(self.openLogFile)
        self.btnRestoreLiveLog.clicked.connect(self.restoreLiveLog)
        self.btnAnalyzeLog.clicked.connect(self.analyzeLogWithAi)

    def initSettingsMenu(self):
        self.actionAiSettings = QAction(self._translate("kmainForm", "AI 设置"), self)
        self.actionAiSettings.triggered.connect(self.openAiSettings)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionAiSettings)

    def initMainContextPanel(self):
        control_height = 46
        self.mainContextGroup = QtWidgets.QFrame(self.mainLeftWidget)
        self.mainContextGroup.setObjectName("summaryCard")
        self.mainContextGroup.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.mainContextGroup.setMinimumHeight(58)
        self.mainContextGroup.setMaximumHeight(58)
        self.mainContextLayout = QtWidgets.QHBoxLayout(self.mainContextGroup)
        self.mainContextLayout.setContentsMargins(12, 6, 12, 6)
        self.mainContextLayout.setSpacing(8)

        self.labMainContextDeviceTitle = QLabel(self.mainContextGroup)
        self.labMainContextDeviceTitle.setObjectName("summaryTitle")
        self.cmbMainContextDevices = QtWidgets.QComboBox(self.mainContextGroup)
        self.cmbMainContextDevices.setMinimumWidth(240)
        self.cmbMainContextDevices.setMaximumWidth(360)
        self.cmbMainContextDevices.setFixedHeight(control_height)
        self.cmbMainContextDevices.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContentsOnFirstShow)
        self.cmbMainContextDevices.currentIndexChanged.connect(self.onDeviceChanged)

        self.labMainContextPortTitle = QLabel(self.mainContextGroup)
        self.labMainContextPortTitle.setObjectName("summaryTitle")
        self.txtMainContextPortValue = QLineEdit(self.mainContextGroup)
        self.txtMainContextPortValue.setReadOnly(True)
        self.txtMainContextPortValue.setMinimumWidth(110)
        self.txtMainContextPortValue.setMaximumWidth(160)
        self.txtMainContextPortValue.setFixedHeight(control_height)

        self.btnMainContextRefreshDevices = QtWidgets.QPushButton(self.mainContextGroup)
        self.btnMainContextRefreshDevices.clicked.connect(self.refreshDeviceList)
        self.btnMainContextRefreshDevices.setFixedHeight(control_height)
        self.btnMainContextRefreshDevices.setMinimumWidth(132)
        self.btnMainContextRefreshDevices.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.btnMainContextRefreshDevices.setStyleSheet("padding: 3px 16px 6px 16px;")
        self.btnMainContextRefreshDevices.setCursor(Qt.PointingHandCursor)

        self.btnMainContextPortSettings = QtWidgets.QPushButton(self.mainContextGroup)
        self.btnMainContextPortSettings.clicked.connect(self.openCurrentConnectionSettings)
        self.btnMainContextPortSettings.setFixedHeight(control_height)
        self.btnMainContextPortSettings.setMinimumWidth(118)
        self.btnMainContextPortSettings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.btnMainContextPortSettings.setStyleSheet("padding: 3px 16px 6px 16px;")
        self.btnMainContextPortSettings.setCursor(Qt.PointingHandCursor)

        self.txtMainContextForegroundPackage = QLineEdit(self.mainContextGroup)
        self.txtMainContextForegroundPackage.setReadOnly(True)
        self.txtMainContextForegroundPackage.setMinimumWidth(220)
        self.txtMainContextForegroundPackage.setFixedHeight(control_height)
        self.txtMainContextForegroundPackage.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        for widget in [
            self.labMainContextDeviceTitle,
            self.cmbMainContextDevices,
            self.labMainContextPortTitle,
            self.txtMainContextPortValue,
            self.btnMainContextRefreshDevices,
            self.btnMainContextPortSettings,
            self.txtMainContextForegroundPackage,
        ]:
            stretch = 1 if widget is self.txtMainContextForegroundPackage else 0
            self.mainContextLayout.addWidget(widget, stretch)
        self.updateToolbarContextPanel()

    def fitButtonTextWidth(self, button, padding=16):
        if button is None:
            return
        width = button.sizeHint().width() + padding
        button.setMinimumWidth(max(button.minimumWidth(), width))


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
        action_buttons = [self.btnGumTraceSaveConfig, self.btnGumTracePreview, self.btnGumTraceSaveCustom, self.btnGumTraceActivate]
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
        self.gumTraceWindow = QtWidgets.QMainWindow(self)
        self.gumTraceWindow.setObjectName("gumTraceWindow")
        self.gumTraceWindow.setCentralWidget(self.gumTraceTab)
        self.gumTraceWindow.resize(1180, 780)
        self.gumTraceWindow.setMinimumSize(980, 680)

        self.txtGumTraceName.textChanged.connect(self.syncGumTraceFileName)
        self.cmbGumTraceMode.currentIndexChanged.connect(self.updateGumTraceModeFields)
        self.btnGumTraceSaveConfig.clicked.connect(self.saveGumTraceConfig)
        self.btnGumTracePreview.clicked.connect(self.renderGumTracePreview)
        self.btnGumTraceSaveCustom.clicked.connect(self.applyGumTraceScript)
        self.btnGumTraceActivate.clicked.connect(self.applyGumTraceScriptAndActivate)
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

    def syncCustomHooksToMain(self, refresh_pinned=True):
        if len(self.customForm.customHooks) > 0:
            self.hooksData["custom"] = []
            for item in self.customForm.customHooks:
                self.hooksData["custom"].append({"class": item["name"], "method": item["fileName"], "bak": item["bak"], "fileName": item["fileName"]})
        elif "custom" in self.hooksData:
            self.hooksData.pop("custom")
        self.updateTabHooks()
        if refresh_pinned:
            self.refreshPinnedCustomTemplates()

    def cleanCustomTemplateRemark(self, remark):
        cleaned = (remark or "").strip()
        for prefix in ("内置：", "内置:", "Built-in: ", "Built-in:", "Builtin: ", "Builtin:"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        return cleaned

    def pinnedCustomTemplateSortKey(self, item):
        raw_order = item.get("pinOrder", None)
        try:
            return (0, int(raw_order), item.get("name", "").lower(), item.get("fileName", "").lower())
        except Exception:
            return (1, item.get("name", "").lower(), item.get("fileName", "").lower())

    def builtinCustomTemplateDefs(self):
        return [
            {
                "sourceHookKey": "r0capture",
                "fileName": "r0capture.js",
                "name": "r0capture",
                "bak": "内置：r0capture.js",
                "scriptPath": "./js/r0capture.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "javaEnc",
                "fileName": "javaEnc.js",
                "name": "Java Crypto Hooks",
                "bak": "内置：javaEnc.js",
                "scriptPath": "./js/javaEnc.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "sslpining",
                "fileName": "DroidSSLUnpinning.js",
                "name": "SSL Pinning Bypass",
                "bak": "内置：DroidSSLUnpinning.js",
                "scriptPath": "./js/DroidSSLUnpinning.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "hookEvent",
                "fileName": "hookEvent.js",
                "name": "UI Click Events",
                "bak": "内置：hookEvent.js",
                "scriptPath": "./js/hookEvent.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "RegisterNative",
                "fileName": "hook_RegisterNatives.js",
                "name": "RegisterNatives Monitor",
                "bak": "内置：hook_RegisterNatives.js",
                "scriptPath": "./js/hook_RegisterNatives.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "ArtMethod",
                "fileName": "hook_artmethod.js",
                "name": "ArtMethod Monitor",
                "bak": "内置：hook_artmethod.js",
                "scriptPath": "./js/hook_artmethod.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "libArm",
                "fileName": "hook_art.js",
                "name": "libart Key Functions",
                "bak": "内置：hook_art.js",
                "scriptPath": "./js/hook_art.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "anti_debug",
                "fileName": "anti_debug.js",
                "name": "One-Click Anti-Debug",
                "bak": "内置：anti_debug.js",
                "scriptPath": "./js/anti_debug.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "root_bypass",
                "fileName": "root_bypass.js",
                "name": "Root Detection Bypass",
                "bak": "内置：root_bypass.js",
                "scriptPath": "./js/root_bypass.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "webview_debug",
                "fileName": "webview_debug.js",
                "name": "WebView Debug",
                "bak": "内置：webview_debug.js",
                "scriptPath": "./js/webview_debug.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "okhttp_logger",
                "fileName": "okhttp_logger.js",
                "name": "OkHttp Logger",
                "bak": "内置：okhttp_logger.js",
                "scriptPath": "./js/okhttp_logger.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "shared_prefs_watch",
                "fileName": "shared_prefs_watch.js",
                "name": "SharedPrefs Monitor",
                "bak": "内置：shared_prefs_watch.js",
                "scriptPath": "./js/shared_prefs_watch.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "sqlite_logger",
                "fileName": "sqlite_logger.js",
                "name": "SQLite Logger",
                "bak": "内置：sqlite_logger.js",
                "scriptPath": "./js/sqlite_logger.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "clipboard_monitor",
                "fileName": "clipboard_monitor.js",
                "name": "Clipboard Monitor",
                "bak": "内置：clipboard_monitor.js",
                "scriptPath": "./js/clipboard_monitor.js",
                "pinToMain": True,
            },
            {
                "sourceHookKey": "intent_monitor",
                "fileName": "intent_monitor.js",
                "name": "Intent Monitor",
                "bak": "内置：intent_monitor.js",
                "scriptPath": "./js/intent_monitor.js",
                "pinToMain": True,
            },
        ]

    def ensureBuiltinCustomTemplates(self):
        if not hasattr(self, "customForm"):
            return
        self.customForm.initData()
        defs = self.builtinCustomTemplateDefs()
        by_file = {item.get("fileName"): item for item in self.customForm.customs}
        changed = False

        for definition in defs:
            file_name = definition["fileName"]
            existing = by_file.get(file_name)

            if existing is None:
                existing = {
                    "name": definition["name"],
                    "fileName": file_name,
                    "bak": definition["bak"],
                    "pinToMain": bool(definition.get("pinToMain", False)),
                    "pinOrder": self.customForm.nextPinnedTemplateOrder() if definition.get("pinToMain", False) else -1,
                    "builtin": True,
                    "sourceHookKey": definition.get("sourceHookKey", ""),
                }
                self.customForm.customs.append(existing)
                by_file[file_name] = existing
                changed = True
            else:
                if "pinToMain" not in existing:
                    existing["pinToMain"] = bool(definition.get("pinToMain", False))
                    if existing["pinToMain"] and "pinOrder" not in existing:
                        existing["pinOrder"] = self.customForm.nextPinnedTemplateOrder()
                    changed = True
                elif existing.get("pinToMain") and "pinOrder" not in existing:
                    existing["pinOrder"] = self.customForm.nextPinnedTemplateOrder()
                    changed = True
                if "builtin" not in existing and file_name in [d["fileName"] for d in defs]:
                    existing["builtin"] = True
                    changed = True
                if "sourceHookKey" not in existing and definition.get("sourceHookKey"):
                    existing["sourceHookKey"] = definition["sourceHookKey"]
                    changed = True

            target_path = os.path.join("./custom", file_name)
            if os.path.exists(target_path) is False and os.path.exists(definition["scriptPath"]):
                try:
                    with open(definition["scriptPath"], "r", encoding="utf-8") as source_file:
                        script_text = source_file.read()
                    with open(target_path, "w", encoding="utf-8") as dest_file:
                        dest_file.write(script_text)
                    changed = True
                except Exception as ex:
                    self.log("ensure builtin custom failed: " + str(ex))

        if changed:
            self.customForm.save()
            self.customForm.updateTabCustom()

    def syncCustomHooksFromHooksData(self):
        if not hasattr(self, "customForm"):
            return
        hooks = self.hooksData.get("custom")
        if not isinstance(hooks, list):
            return
        by_file = {item.get("fileName"): item for item in self.customForm.customs}
        resolved = []
        for hook in hooks:
            if not isinstance(hook, dict):
                continue
            file_name = hook.get("fileName") or hook.get("method")
            if not file_name:
                continue
            item = by_file.get(file_name)
            if item is None:
                item = {
                    "name": hook.get("class") or file_name,
                    "fileName": file_name,
                    "bak": hook.get("bak", ""),
                    "pinToMain": False,
                    "builtin": False,
                    "sourceHookKey": "",
                }
                self.customForm.customs.append(item)
            resolved.append(item)
        self.customForm.customHooks = resolved
        self.customForm.updateTabCustomHook()

    def migrateLegacySimpleHooksToCustom(self):
        legacy_keys = {definition["sourceHookKey"]: definition for definition in self.builtinCustomTemplateDefs()}
        mutated = False
        for key in list(self.hooksData.keys()):
            if key not in legacy_keys:
                continue
            definition = legacy_keys[key]
            file_name = definition["fileName"]
            self.customForm.ensureCustomHook(file_name)
            self.hooksData.pop(key, None)
            mutated = True
        if mutated:
            self.syncCustomHooksToMain()

    def refreshPinnedCustomTemplates(self):
        if not hasattr(self, "customTemplateGrid") or not hasattr(self, "customForm"):
            return
        pinned = [item for item in self.customForm.customs if item.get("pinToMain")]
        pinned.sort(key=self.pinnedCustomTemplateSortKey)
        active_files = {item.get("fileName") for item in self.customForm.customHooks}

        self._clearCustomTemplateGrid(delete_widgets=True)
        self.customTemplateTiles = []

        if not pinned:
            empty = QLabel(
                self.trText("暂无固定模板，可在“自定义”里右键模板→添加到主界面", "No pinned templates yet. Right-click a template in Custom and pin it to main."),
                self.customTemplateContainer,
            )
            empty.setWordWrap(True)
            empty.setObjectName("panelHint")
            self.customTemplateGrid.addWidget(empty, 0, 0, 1, 1)
            self.customTemplateGrid.setColumnStretch(0, 1)
            return

        for item in pinned:
            file_name = item.get("fileName")
            if not file_name:
                continue
            display_name = item.get("name", file_name)
            tile = PinnedTemplateCheckBox(display_name, file_name, self.customTemplateContainer)
            tile.setObjectName("customTemplateTile")
            tile.setCursor(Qt.PointingHandCursor)
            tile.setChecked(file_name in active_files)
            tooltip_lines = [self.trText("文件：", "File: ") + file_name]
            remark = self.cleanCustomTemplateRemark(item.get("bak", ""))
            if remark:
                tooltip_lines.append(self.trText("备注：", "Remark: ") + remark)
            tile.setToolTip("\n".join(tooltip_lines))
            tile.setContextMenuPolicy(Qt.CustomContextMenu)
            tile.customContextMenuRequested.connect(lambda _pos, current=file_name: self.showPinnedCustomTemplateMenu(current))
            tile.stateChanged.connect(lambda state, current=file_name: self.onPinnedCustomTemplateClicked(current, state == Qt.Checked))
            tile.reorderRequested.connect(self.onPinnedCustomTemplateReordered)
            self.customTemplateTiles.append(tile)

        self.rebuildPinnedCustomTemplateGrid()

    def _clearCustomTemplateGrid(self, delete_widgets=False):
        while self.customTemplateGrid.count():
            item = self.customTemplateGrid.takeAt(0)
            widget = item.widget()
            if widget is None:
                continue
            if delete_widgets:
                widget.deleteLater()
            else:
                widget.hide()

    def rebuildPinnedCustomTemplateGrid(self):
        if not hasattr(self, "customTemplateGrid"):
            return
        self._clearCustomTemplateGrid(delete_widgets=False)
        tiles = list(getattr(self, "customTemplateTiles", []))
        if not tiles:
            self.customTemplateGrid.setColumnStretch(0, 1)
            return
        viewport_width = self.customTemplateScroll.viewport().width() if hasattr(self, "customTemplateScroll") else 0
        tile_width = 175
        columns = max(1, viewport_width // tile_width) if viewport_width > 0 else 1
        for index, tile in enumerate(tiles):
            tile.show()
            tile.setMinimumHeight(24)
            tile.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            self.customTemplateGrid.addWidget(tile, index // columns, index % columns)
        for col in range(columns):
            self.customTemplateGrid.setColumnStretch(col, 1)

    def onPinnedCustomTemplateReordered(self, dragged_file_name, target_file_name, insert_after):
        if not hasattr(self, "customTemplateTiles") or not hasattr(self, "customForm"):
            return
        current_order = [getattr(tile, "fileName", "") for tile in self.customTemplateTiles if getattr(tile, "fileName", "")]
        if dragged_file_name not in current_order or target_file_name not in current_order:
            return
        if dragged_file_name == target_file_name:
            return

        current_order.remove(dragged_file_name)
        target_index = current_order.index(target_file_name)
        insert_index = target_index + (1 if insert_after else 0)
        current_order.insert(insert_index, dragged_file_name)

        tile_by_file = {getattr(tile, "fileName", ""): tile for tile in self.customTemplateTiles}
        self.customTemplateTiles = [tile_by_file[file_name] for file_name in current_order if file_name in tile_by_file]
        self.customForm.setPinnedTemplateOrder(current_order)
        self.rebuildPinnedCustomTemplateGrid()

    def onPinnedCustomTemplateClicked(self, file_name, checked):
        if not hasattr(self, "customForm") or not file_name:
            return
        if checked:
            self.customForm.ensureCustomHook(file_name)
        else:
            self.customForm.customHooks = [item for item in self.customForm.customHooks if item.get("fileName") != file_name]
            self.customForm.updateTabCustomHook()
        self.syncCustomHooksToMain(refresh_pinned=False)

    def showPinnedCustomTemplateMenu(self, file_name):
        if not file_name:
            return
        menu = QMenu(self)
        remove_action = QAction(self.trText("从主界面移除", "Remove from main"), self)
        remove_action.triggered.connect(lambda: self.removePinnedCustomTemplate(file_name))
        menu.addAction(remove_action)
        menu.exec_(QCursor.pos())

    def removePinnedCustomTemplate(self, file_name):
        if not hasattr(self, "customForm") or not file_name:
            return
        mutated = False
        for item in self.customForm.customs:
            if item.get("fileName") == file_name and item.get("pinToMain"):
                item["pinToMain"] = False
                item["pinOrder"] = -1
                mutated = True
                break
        if not mutated:
            return
        self.customForm.customHooks = [item for item in self.customForm.customHooks if item.get("fileName") != file_name]
        self.customForm.normalizePinnedTemplateOrders()
        self.customForm.save()
        self.customForm.updateTabCustom()
        self.customForm.updateTabCustomHook()
        self.syncCustomHooksToMain()

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
        gumtrace_window = getattr(self, "gumTraceWindow", None)
        if gumtrace_window is None:
            return
        try:
            if gumtrace_window.isMinimized():
                gumtrace_window.showNormal()
            else:
                gumtrace_window.show()
            # Some Linux window managers/plugins may hang or ignore raise_()/activateWindow().
            # Showing the top-level window is enough here; avoid forcing foreground activation.
        except RuntimeError as ex:
            self.log("openGumTraceWorkspace runtime error: %s" % str(ex))
            QMessageBox().information(self, "hint", self.trText("打开 GumTrace 工作台失败：", "Failed to open GumTrace workbench: ") + str(ex))

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
        self.refreshAttachSummaryCards()

    def formatModuleDisplay(self, module):
        return module["name"] + "----" + module["base"]

    def classifyModuleOwnership(self, module):
        package = (self.attachedAppInfoSnapshot or {}).get("package", {})
        module_path = self.valueText(module.get("path"), "")
        native_dir = self.valueText(package.get("nativeLibraryDir"), "")
        package_name = self.valueText(package.get("packageName"), "")
        if native_dir and native_dir in module_path:
            return "app"
        if package_name and package_name.replace('.', '/') in module_path:
            return "app"
        if module_path.startswith("/data/app") or module_path.startswith("/data/data"):
            return "app"
        if module_path.startswith("/system") or module_path.startswith("/apex") or module_path.startswith("/vendor"):
            return "system"
        return "other"

    def moduleDisplayText(self, module):
        display = self.formatModuleDisplay(module)
        ownership = self.classifyModuleOwnership(module)
        if ownership == "app":
            return "[APP] " + display
        if ownership == "system":
            return "[SYS] " + display
        return display

    def moduleByDisplayText(self, text):
        if not self.modules:
            return None
        normalized = text.replace("[APP] ", "").replace("[SYS] ", "")
        for module in self.modules:
            if self.formatModuleDisplay(module) == normalized:
                return module
        fallback_name = normalized.split("----")[0].strip()
        fallback_lower = fallback_name.lower()
        for module in self.modules:
            module_name = self.valueText(module.get("name"), "")
            module_path = self.valueText(module.get("path"), "")
            if module_name == fallback_name or module_name.lower() == fallback_lower:
                return module
            if module_path == fallback_name or module_path.lower() == fallback_lower:
                return module
        return None

    def isNativeModuleInput(self, text):
        normalized = (text or "").replace("[APP] ", "").replace("[SYS] ", "").split("----")[0].strip().lower()
        return normalized.endswith(".so")

    def adbCommandArgs(self):
        args = ["adb"]
        serial = self.selectedDeviceSerial()
        if len(serial) > 0:
            args.extend(["-s", serial])
        return args

    def adbScriptPrefix(self):
        serial = self.selectedDeviceSerial()
        if platform.system() == "Windows":
            return 'adb -s "%s"' % serial if len(serial) > 0 else "adb"

        adb_path = "adb"
        if platform.system() == "Darwin":
            adb_path = CmdUtil.execCmdData("which adb").strip() or "adb"
        adb_path = shlex.quote(adb_path)
        if len(serial) > 0:
            return "%s -s %s" % (adb_path, shlex.quote(serial))
        return adb_path

    def parseElfSymbolOutput(self, output, search_type):
        results = []
        for line in (output or "").splitlines():
            line = line.strip()
            if len(line) <= 0 or ":" not in line:
                continue
            match = re.match(r"^\s*\d+:\s+([0-9A-Fa-f]+)\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$", line)
            if match is None:
                continue
            address, symbol_type, bind_type, visibility, ndx, name = match.groups()
            name = name.strip()
            if len(name) <= 0 or name == "0":
                continue
            if search_type == "export" and ndx == "UND":
                continue
            results.append({
                "name": name,
                "address": "0x" + address.lower(),
                "type": symbol_type.lower(),
                "bind": bind_type.lower(),
                "visibility": visibility.lower(),
                "index": ndx,
            })
        return results

    def loadModuleSymbolsLocal(self, module, search_type):
        result_key = "export" if search_type == "export" else "symbol"
        result = {"type": search_type, result_key: []}
        if not module:
            result["error"] = self.trText("未找到模块信息", "Module information not found")
            return result
        module_path = self.valueText(module.get("path"), "")
        if module_path in ["", "-"]:
            result["error"] = self.trText("模块路径为空，无法离线解析", "Module path is empty, cannot analyze offline")
            return result
        tmp_root = os.path.abspath("./tmp")
        os.makedirs(tmp_root, exist_ok=True)
        work_dir = tempfile.mkdtemp(prefix="elf_", dir=tmp_root)
        local_path = os.path.join(work_dir, os.path.basename(module_path) or "module.so")
        try:
            pull_cmd = self.adbCommandArgs() + ["pull", module_path, local_path]
            pull_proc = subprocess.run(pull_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if pull_proc.returncode != 0 or not os.path.exists(local_path):
                result["error"] = self.trText("拉取模块失败：", "Failed to pull module: ") + pull_proc.stdout.strip()
                return result
            readelf_args = ["readelf", "--dyn-syms", "-W", local_path] if search_type == "export" else ["readelf", "--symbols", "-W", local_path]
            readelf_proc = subprocess.run(readelf_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if readelf_proc.returncode != 0:
                result["error"] = self.trText("解析模块失败：", "Failed to parse module: ") + readelf_proc.stdout.strip()
                return result
            result[result_key] = self.parseElfSymbolOutput(readelf_proc.stdout, search_type)
            if len(result[result_key]) <= 0:
                result["error"] = self.trText("本地 ELF 解析完成，但未找到结果", "Local ELF parsing finished but no results were found")
            return result
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def preferredModule(self):
        if not self.modules:
            return None
        native_app_modules = [module for module in self.modules if self.classifyModuleOwnership(module) == "app" and self.isNativeSharedObject(module)]
        if native_app_modules:
            return sorted(native_app_modules, key=lambda item: (0 if self.valueText(item.get("path"), "").endswith(item["name"]) else 1, item["name"].lower()))[0]
        app_modules = [module for module in self.modules if self.classifyModuleOwnership(module) == "app"]
        if app_modules:
            return sorted(app_modules, key=lambda item: (0 if self.valueText(item.get("path"), "").endswith(item["name"]) else 1, item["name"].lower()))[0]
        native_modules = [module for module in self.modules if self.isNativeSharedObject(module)]
        if native_modules:
            return sorted(native_modules, key=lambda item: item["name"].lower())[0]
        return sorted(self.modules, key=lambda item: item["name"].lower())[0]

    def refreshModuleList(self, keyword=""):
        self.listModules.clear()
        if self.modules is None:
            return
        normalized = (keyword or "").split("----")[0].strip().upper()
        visible_modules = []
        for module in self.modules:
            haystacks = [module.get("name", ""), self.valueText(module.get("path"), "")]
            if normalized and not any(normalized in item.upper() for item in haystacks if item):
                continue
            visible_modules.append(module)
            self.listModules.addItem(self.moduleDisplayText(module))
        self.filteredModules = visible_modules

    def dexListKey(self, dex):
        if not dex:
            return ""
        return self.valueText(dex.get("location"), "") + "::" + self.valueText(dex.get("classLoader"), "")

    def changeDex(self, data):
        self.listDex.clear()
        keyword = (data or "").strip().upper()
        for dex in self.dexes:
            location = self.valueText(dex.get("location"), "")
            loader = self.valueText(dex.get("classLoader"), "")
            if keyword and keyword not in location.upper() and keyword not in loader.upper():
                continue
            item = QtWidgets.QListWidgetItem(location)
            item.setData(Qt.UserRole, self.dexListKey(dex))
            self.listDex.addItem(item)

    def listDexClick(self, item):
        self.currentAttachResourceType = "dex"
        self.currentSelectedModule = None
        selected_key = item.data(Qt.UserRole)
        self.currentSelectedDex = None
        for dex in self.dexes:
            if self.dexListKey(dex) == selected_key:
                self.currentSelectedDex = dex
                break
        self.renderCurrentDex()

    def moduleCacheKey(self, module):
        if not module:
            return ""
        return self.valueText(module.get("name"), "") + "::" + self.valueText(module.get("base"), "")

    def isNativeSharedObject(self, module):
        if not module:
            return False
        module_name = self.valueText(module.get("name"), "").lower()
        module_path = self.valueText(module.get("path"), "").lower()
        return module_name.endswith(".so") or module_path.endswith(".so")

    def moduleInfoRows(self, module):
        if not module:
            return []
        cache_key = self.moduleCacheKey(module)
        export_cache = self.moduleExportCache.get(cache_key, [])
        symbol_cache = self.moduleSymbolCache.get(cache_key, [])
        return [
            (self.trText("模块名", "Module name"), module.get("name")),
            (self.trText("基址", "Base"), module.get("base")),
            (self.trText("大小", "Size"), module.get("size")),
            (self.trText("路径", "Path"), module.get("path")),
            (self.trText("来源", "Ownership"), self.classifyModuleOwnership(module)),
            (self.trText("导出数量", "Export count"), len(export_cache)),
            (self.trText("符号数量", "Symbol count"), len(symbol_cache)),
        ]

    def dexInfoRows(self, dex):
        if not dex:
            return []
        return [
            (self.trText("位置", "Location"), dex.get("location")),
            (self.trText("类型", "Type"), dex.get("type")),
            (self.trText("ClassLoader", "ClassLoader"), dex.get("classLoader")),
            (self.trText("来源", "Source"), dex.get("source")),
            (self.trText("内存 DEX", "Memory DEX"), self.boolText(dex.get("isMemoryDex"))),
        ]

    def renderAttachResourceRows(self, rows):
        if hasattr(self, "attachResourceTable"):
            self.setupInfoTable(self.attachResourceTable)
            self.setInfoTableRows(self.attachResourceTable, rows)

    def renderCurrentModule(self):
        if not self.currentSelectedModule:
            self.renderAttachResourceRows([])
            return
        self.currentAttachResourceType = "module"
        self.renderAttachResourceRows(self.moduleInfoRows(self.currentSelectedModule))
        self.attachResultTabs.blockSignals(True)
        self.attachResultTabs.setCurrentWidget(self.groupBox_7)
        self.attachResultTabs.blockSignals(False)
        self.log(self.trText("已禁用模块导出/符号自动查询，以避免目标进程崩溃。", "Automatic export/symbol queries are disabled to avoid target process crashes."))

    def renderCurrentDex(self):
        if not self.currentSelectedDex:
            self.renderAttachResourceRows([])
            return
        self.currentAttachResourceType = "dex"
        self.attachResourceTabs.setCurrentWidget(self.attachDexGroup)
        self.renderAttachResourceRows(self.dexInfoRows(self.currentSelectedDex))
        self.attachResultTabs.blockSignals(True)
        self.attachResultTabs.setCurrentWidget(self.groupBox_7)
        self.attachResultTabs.blockSignals(False)

    def renderAttachRuntimeInfo(self):
        self.currentAttachResourceType = "runtime"
        self.attachResourceTabs.setCurrentWidget(self.groupBox_4)
        self.attachResultTabs.setCurrentWidget(self.groupBox_7)
        self.renderAttachResourceRows(self.buildAttachedInfoRows())

    def refreshAttachSummaryCards(self):
        if not hasattr(self, "attachPackageCard"):
            return
        data = self.attachedAppInfoSnapshot or {}
        runtime = data.get("runtime", {})
        package = data.get("package", {})
        module_count = runtime.get("moduleCount") or len(data.get("modules", []))
        dex_count = runtime.get("dexCount") or len(data.get("dexes", []))
        self.attachPackageCard.valueLabel.setText(self.valueText(data.get("packageName") or package.get("packageName") or self.labPackage.text()))
        self.attachProcessCard.valueLabel.setText("PID %s / %s" % (self.valueText(runtime.get("processId")), self.valueText(runtime.get("arch"))))
        self.attachModuleCard.valueLabel.setText(str(module_count))
        self.attachDexCard.valueLabel.setText(str(dex_count))
        debug_state = []
        if package:
            debug_state.append(self.trText("可调试", "Debuggable") + ": " + self.boolText(package.get("debuggable")))
            debug_state.append("targetSdk: " + self.valueText(package.get("targetSdk")))
        else:
            debug_state.append(self.valueText(runtime.get("platform")))
        self.attachDebugCard.valueLabel.setText("\n".join(debug_state))

    def populateSymbolList(self, items):
        self.listSymbol.clear()
        for item in items:
            self.listSymbol.addItem(item["name"])

    def ensureModuleSearchLoaded(self, module, search_type):
        if not module:
            return
        cache_map = self.moduleExportCache if search_type == "export" else self.moduleSymbolCache
        cache_key = self.moduleCacheKey(module)
        self.lastSearchModuleKey = cache_key
        if cache_key in cache_map:
            self.searchType = search_type
            self.symbols = cache_map[cache_key]
            self.populateSymbolList(self.symbols)
            self.renderAttachResourceRows(self.moduleInfoRows(module))
            return
        try:
            appinfo = self.loadModuleSymbolsLocal(module, search_type)
            self.searchAppInfoRes(appinfo)
        except Exception as ex:
            error_text = self.trText("加载模块导出失败: ", "Failed to load exports: ") if search_type == "export" else self.trText("加载模块符号失败: ", "Failed to load symbols: ")
            self.log(error_text + str(ex))

    def ensureModuleExportLoaded(self, module):
        self.ensureModuleSearchLoaded(module, "export")

    def ensureModuleSymbolLoaded(self, module):
        self.ensureModuleSearchLoaded(module, "symbol")

    def onAttachResultTabChanged(self, index):
        if not hasattr(self, "attachResultTabs"):
            return
        widget = self.attachResultTabs.widget(index)
        if widget == self.groupBox_7:
            if self.currentAttachResourceType == "dex" and self.currentSelectedDex:
                self.renderAttachResourceRows(self.dexInfoRows(self.currentSelectedDex))
            elif self.currentAttachResourceType == "module" and self.currentSelectedModule:
                self.renderAttachResourceRows(self.moduleInfoRows(self.currentSelectedModule))
            else:
                self.renderAttachRuntimeInfo()


    def refreshAiState(self):
        available = self.aiService.is_available()
        missing_message = self.aiService.missing_message("English" if self.isEnglish() else "China")
        self.btnAnalyzeLog.setEnabled(available)
        self.customForm.refreshAiState()
        if hasattr(self, "aiSummaryCard"):
            self.aiSummaryCard.valueLabel.setText(self.trText("已配置，可写 Hook 与分析日志", "Configured for hook generation and log analysis") if available else missing_message)
        if hasattr(self, "txtAiAnalysis"):
            self.txtAiAnalysis.setPlaceholderText(
                self.trText("AI 分析结果会显示在这里", "AI analysis output will appear here") if available else missing_message
            )
            if available and self.txtAiAnalysis.toPlainText().strip() == missing_message:
                self.txtAiAnalysis.setPlainText("")
        self.refreshOverviewCards()

    def openAiSettings(self):
        self.aiSettingsForm.loadConfig()
        res = self.aiSettingsForm.exec()
        if res == 0:
            return
        self.refreshAiState()

    def currentLogText(self):
        if hasattr(self, "txtAiLogInput"):
            return self.txtAiLogInput.toPlainText()
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
        self.txtAiLogInput.setPlainText(self.loadedLogContent)
        self.txtoutLogs.setPlainText(self.loadedLogContent)
        self.showLogDock(self.aiAnalysisTab)
        self.labLogStatus.setText(self.trText("当前日志：", "Current log: ") + os.path.basename(filepath[0]))
        self.log(self.trText("已加载日志文件：", "Loaded log file: ") + filepath[0])
        self.refreshOverviewCards()

    def restoreLiveLog(self):
        self.currentLogMode = "live"
        self.loadedLogPath = ""
        self.loadedLogContent = ""
        live_content = "\n".join(self.liveOutputLogBuffer)
        self.txtAiLogInput.setPlainText(live_content)
        self.txtoutLogs.setPlainText(live_content)
        self.labLogStatus.setText(self.trText("当前日志：实时输出", "Current log: live output"))
        self.showLogDock(self.aiAnalysisTab)
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
        self.txtAiAnalysis.setPlainText("")
        self.showLogDock(self.aiAnalysisTab)
        self.aiWorker = AiWorker(self.aiService.analyze_log, content, stream_handler=self.aiService.analyze_log_stream)
        self.aiWorker.chunk.connect(self.onAiAnalysisChunk)
        self.aiWorker.success.connect(self.onAiAnalysisSuccess)
        self.aiWorker.error.connect(self.onAiAnalysisFailed)
        self.aiWorker.start()

    def onAiAnalysisChunk(self, chunk):
        cursor = self.txtAiAnalysis.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        self.txtAiAnalysis.setTextCursor(cursor)
        self.txtAiAnalysis.ensureCursorVisible()

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
        module = self.moduleByDisplayText(self.txtModule.text())
        if module:
            if not self.isNativeSharedObject(module):
                QMessageBox().information(self, "hint", self.trText("当前模块不是 .so，无法查询导出。", "The selected module is not a .so, so exports cannot be queried."))
                return
        elif not self.isNativeModuleInput(self.txtModule.text()):
            QMessageBox().information(self, "hint", self.trText("当前模块不是 .so，无法查询导出。", "The selected module is not a .so, so exports cannot be queried."))
            return
        self.lastSearchModuleKey = self.moduleCacheKey(module) if module else None
        appinfo = self.loadModuleSymbolsLocal(module, "export") if module else {"type": "export", "export": [], "error": self.trText("请从模块列表中选择一个有效 .so", "Please select a valid .so from the module list")}
        self.searchAppInfoRes(appinfo)

    def searchSymbol(self):
        if len(self.txtModule.text()) <= 0:
            QMessageBox().information(self, "hint", self._translate("kmainForm","未填写模块名称"))
            return
        module = self.moduleByDisplayText(self.txtModule.text())
        if module:
            if not self.isNativeSharedObject(module):
                QMessageBox().information(self, "hint", self.trText("当前模块不是 .so，无法查询符号。", "The selected module is not a .so, so symbols cannot be queried."))
                return
        elif not self.isNativeModuleInput(self.txtModule.text()):
            QMessageBox().information(self, "hint", self.trText("当前模块不是 .so，无法查询符号。", "The selected module is not a .so, so symbols cannot be queried."))
            return
        self.lastSearchModuleKey = self.moduleCacheKey(module) if module else None
        appinfo = self.loadModuleSymbolsLocal(module, "symbol") if module else {"type": "symbol", "symbol": [], "error": self.trText("请从模块列表中选择一个有效 .so", "Please select a valid .so from the module list")}
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
        if self.currentLogMode == "live" and hasattr(self, "txtAiLogInput"):
            self.txtAiLogInput.appendPlainText(line)
        self.outlogger.logger.debug(logstr)
        if "default.js init hook success" in logstr:
            QMessageBox().information(self, "hint", self._translate("kmainForm", "附加进程成功"))

    # 线程调用脚本结束，并且触发结束信号
    def StopAttach(self):
        if not hasattr(self, "th") or self.th is None:
            return
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
        if hasattr(self, "txtAiLogInput"):
            self.txtAiLogInput.setPlainText("")
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
            QMessageBox().information(self, "hint",self._translate("kmainForm",  "设置权限失败。请确认设备权限状态"))
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
        family_key = "arm64" if arch in ["arm", "arm64"] else "x64"
        self.handleFridaVersionUpload(self.curFridaVer, family_key)

    def getFridaArchPair(self, arch):
        arch_map = {
            "arm": ["arm", "arm64"],
            "x86": ["x86", "x86_64"],
        }
        if arch not in arch_map:
            raise ValueError(self.trText("不支持的架构：", "Unsupported architecture: ") + str(arch))
        return arch_map[arch]

    def getFridaFamilyArches(self, family_key):
        if family_key not in FRIDA_ARCH_FAMILIES:
            raise ValueError(self.trText("不支持的 frida 架构类型：", "Unsupported Frida family: ") + str(family_key))
        return FRIDA_ARCH_FAMILIES[family_key]

    def getFridaServerFilename(self, version, arch):
        return f"frida-server-{version}-android-{arch}"

    def getFridaServerLocalPath(self, version, arch):
        return os.path.join(".", "exec", self.getFridaServerFilename(version, arch))

    def getFridaServerDownloadUrl(self, version, arch):
        file_name = self.getFridaServerFilename(version, arch)
        return f"https://github.com/frida/frida/releases/download/{version}/{file_name}.xz"

    def getFridaRemoteName(self, arch, version=None):
        if self.fridaName != "":
            return self.fridaName + ("32" if arch in ["arm", "x86"] else "64")
        return self.getFridaServerFilename(version or self.curFridaVer, arch)

    def setFridaUploadActionsEnabled(self, enabled):
        self.actionPushFridaServer.setEnabled(enabled)
        self.actionPushFridaServerX86.setEnabled(enabled)
        if self.fridaUploadMenu is not None:
            self.fridaUploadMenu.menuAction().setEnabled(enabled)

    def updateFridaDownloadProgress(self, downloaded, total):
        if self.fridaDownloadDialog is None:
            return
        if total > 0:
            if self.fridaDownloadDialog.maximum() != total:
                self.fridaDownloadDialog.setRange(0, total)
            self.fridaDownloadDialog.setValue(min(downloaded, total))
        else:
            self.fridaDownloadDialog.setRange(0, 0)
        QApplication.processEvents()

    def updateFridaDownloadStatus(self, status, version, arch):
        if self.fridaDownloadDialog is None:
            return
        if status == "extracting":
            label = self.trText("正在解压 frida-server {version} {arch}...", "Extracting frida-server {version} {arch}...")
            self.fridaDownloadDialog.setRange(0, 0)
        else:
            label = self.trText("正在下载 frida-server {version} {arch}...", "Downloading frida-server {version} {arch}...")
        self.fridaDownloadDialog.setLabelText(label.format(version=version, arch=arch))
        QApplication.processEvents()

    def cleanupFridaDownloadWorker(self):
        if self.fridaDownloadDialog is not None:
            self.fridaDownloadDialog.close()
            self.fridaDownloadDialog.deleteLater()
            self.fridaDownloadDialog = None
        if self.fridaDownloadWorker is not None:
            self.fridaDownloadWorker.wait()
            self.fridaDownloadWorker.deleteLater()
            self.fridaDownloadWorker = None

    def cancelFridaDownload(self, loop, result):
        if result.get("path"):
            return
        self.fridaDownloadCancelled = True
        result["error"] = "cancelled"
        if self.fridaDownloadWorker is not None:
            self.fridaDownloadWorker.cancel()
        loop.quit()

    def disconnectFridaDownloadCancel(self, cancel_handler):
        if self.fridaDownloadDialog is None:
            return
        try:
            self.fridaDownloadDialog.canceled.disconnect(cancel_handler)
        except TypeError:
            pass

    def downloadFridaServer(self, version, arch, local_path):
        download_url = self.getFridaServerDownloadUrl(version, arch)
        self.fridaDownloadCancelled = False
        self.fridaDownloadDialog = QProgressDialog(self)
        self.fridaDownloadDialog.setWindowTitle(self.trText("下载 frida-server", "Download frida-server"))
        self.fridaDownloadDialog.setLabelText("")
        self.fridaDownloadDialog.setCancelButtonText(self.trText("取消", "Cancel"))
        self.fridaDownloadDialog.setMinimumDuration(0)
        self.fridaDownloadDialog.setAutoClose(False)
        self.fridaDownloadDialog.setAutoReset(False)
        self.fridaDownloadDialog.setWindowModality(Qt.WindowModal)
        self.updateFridaDownloadStatus("connecting", version, arch)
        self.fridaDownloadDialog.show()

        loop = QtCore.QEventLoop(self)
        result = {"path": None, "error": None}
        self.fridaDownloadWorker = FileDownloadWorker(download_url, local_path, self)
        cancel_handler = lambda: self.cancelFridaDownload(loop, result)
        self.fridaDownloadDialog.canceled.connect(cancel_handler)
        self.fridaDownloadWorker.progress.connect(self.updateFridaDownloadProgress)
        self.fridaDownloadWorker.status.connect(lambda status: self.updateFridaDownloadStatus(status, version, arch))
        self.fridaDownloadWorker.success.connect(lambda path: result.update({"path": path}))
        self.fridaDownloadWorker.success.connect(lambda: self.disconnectFridaDownloadCancel(cancel_handler))
        self.fridaDownloadWorker.success.connect(loop.quit)
        self.fridaDownloadWorker.error.connect(lambda message: result.update({"error": message}))
        self.fridaDownloadWorker.error.connect(loop.quit)
        self.fridaDownloadWorker.start()
        loop.exec_()
        self.cleanupFridaDownloadWorker()
        if result["error"]:
            if result["error"] == "cancelled":
                raise RuntimeError(self.trText("已取消下载 frida-server", "Frida-server download cancelled"))
            raise RuntimeError(self.trText("下载 frida-server 失败：", "Failed to download frida-server: ") + f"{result['error']}\nURL: {download_url}\nLocal: {local_path}")
        if not result["path"] or os.path.exists(result["path"]) is False:
            raise RuntimeError(self.trText("下载 frida-server 失败，未生成本地文件", "Failed to download frida-server: local file was not created") + f"\nURL: {download_url}\nLocal: {local_path}")
        return result["path"]

    def ensureFridaServerLocal(self, version, arch):
        local_path = self.getFridaServerLocalPath(version, arch)
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return local_path
        return self.downloadFridaServer(version, arch, local_path)

    def ensureFridaFamilyLocal(self, version, family_key, preferred_arch="", upload_only=False):
        if preferred_arch:
            local_path = self.getFridaServerLocalPath(version, preferred_arch)
            if upload_only:
                if os.path.exists(local_path) is False or os.path.getsize(local_path) <= 0:
                    raise RuntimeError(self.trText("本地未找到已下载的 frida-server：", "Downloaded frida-server not found locally: ") + local_path)
                return [(preferred_arch, local_path)]
            return [(preferred_arch, self.ensureFridaServerLocal(version, preferred_arch))]
        local_files = []
        for arch in self.getFridaFamilyArches(family_key):
            local_files.append((arch, self.ensureFridaServerLocal(version, arch)))
        return local_files

    def updateFridaUploadProgress(self, value, total):
        if self.fridaUploadDialog is None:
            return
        if total > 0:
            if self.fridaUploadDialog.maximum() != total:
                self.fridaUploadDialog.setRange(0, total)
            self.fridaUploadDialog.setValue(min(value, total))
        else:
            self.fridaUploadDialog.setRange(0, 0)
        QApplication.processEvents()

    def updateFridaUploadStatus(self, text):
        if self.fridaUploadDialog is None or not text:
            return
        if self.fridaUploadDialog.maximum() != 0:
            self.fridaUploadDialog.setRange(0, 0)
        self.fridaUploadDialog.setLabelText(text)
        QApplication.processEvents()

    def cleanupFridaUploadWorker(self):
        if self.fridaUploadDialog is not None:
            self.fridaUploadDialog.close()
            self.fridaUploadDialog.deleteLater()
            self.fridaUploadDialog = None
        if self.fridaUploadWorker is not None:
            self.fridaUploadWorker.wait()
            self.fridaUploadWorker.deleteLater()
            self.fridaUploadWorker = None

    def pushSingleFridaServer(self, local_path, remote_name, version, arch):
        remote_path = "/data/local/tmp/" + remote_name
        command_args = self.adbCommandArgs() + ["push", local_path, remote_path]
        self.fridaUploadDialog = QProgressDialog(self)
        self.fridaUploadDialog.setWindowTitle(self.trText("上传 frida-server", "Upload frida-server"))
        self.fridaUploadDialog.setLabelText(self.trText("正在上传 frida-server {version} {arch}...", "Uploading frida-server {version} {arch}...").format(version=version, arch=arch))
        self.fridaUploadDialog.setCancelButton(None)
        self.fridaUploadDialog.setMinimumDuration(0)
        self.fridaUploadDialog.setAutoClose(False)
        self.fridaUploadDialog.setAutoReset(False)
        self.fridaUploadDialog.setWindowModality(Qt.WindowModal)
        self.fridaUploadDialog.setRange(0, 0)
        self.fridaUploadDialog.setValue(0)
        self.fridaUploadDialog.show()
        QApplication.processEvents()

        loop = QtCore.QEventLoop(self)
        result = {"remote_path": None, "error": None}
        self.fridaUploadWorker = AdbPushWorker(command_args, remote_path, self)
        self.fridaUploadWorker.progress.connect(self.updateFridaUploadProgress)
        self.fridaUploadWorker.status.connect(self.updateFridaUploadStatus)
        self.fridaUploadWorker.success.connect(lambda path: result.update({"remote_path": path}))
        self.fridaUploadWorker.success.connect(loop.quit)
        self.fridaUploadWorker.error.connect(lambda message: result.update({"error": message}))
        self.fridaUploadWorker.error.connect(loop.quit)
        self.fridaUploadWorker.start()
        loop.exec_()
        self.cleanupFridaUploadWorker()
        if result["error"]:
            raise RuntimeError(self.trText("上传 frida-server 失败：", "Failed to upload frida-server: ") + f"{result['error']}\nLocal: {local_path}\nRemote: {remote_path}")
        return result["remote_path"]

    def chmodFridaServerRemote(self, remote_paths):
        return CmdUtil.adbshellCmd("chmod 0777 " + " ".join(remote_paths))

    def uploadFridaFamily(self, version, family_key, preferred_arch="", upload_only=False):
        local_files = self.ensureFridaFamilyLocal(version, family_key, preferred_arch=preferred_arch, upload_only=upload_only)
        remote_paths = []
        for arch, local_path in local_files:
            remote_paths.append(self.pushSingleFridaServer(local_path, self.getFridaRemoteName(arch, version), version, arch))
        chmod_res = self.chmodFridaServerRemote(remote_paths)
        self.log(chmod_res)
        if "invalid" in chmod_res:
            QMessageBox().information(self, "hint", self._translate("kmainForm", "上传完成，但是设置权限失败。请确认设备权限状态."))


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
                QMessageBox().information(self, "hint", self.trText("GumTrace 上传完成，但设置权限失败。请确认设备权限状态。", "GumTrace upload finished, but chmod failed. Check device permissions."))
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

    def prepareGumTraceLogFile(self):
        """hook 启动前，如果有 GumTrace 相关 hook，预创建日志文件并给权限"""
        custom_hooks = self.hooksData.get("custom", [])
        if not isinstance(custom_hooks, list):
            return
        has_gumtrace = any(
            "gumtrace" in (item.get("fileName") or "").lower() or "gumtrace" in (item.get("class") or "").lower()
            for item in custom_hooks if isinstance(item, dict)
        )
        if not has_gumtrace:
            return
        log_path = "/data/local/tmp/gumtrace.log"
        if hasattr(self, "txtGumTraceOutput"):
            custom_path = self.txtGumTraceOutput.text().strip()
            if custom_path:
                log_path = custom_path
        res = CmdUtil.adbshellCmd("touch %s && chmod 0666 %s" % (log_path, log_path))
        self.log("prepareGumTraceLogFile: %s -> %s" % (log_path, res.strip()))

    def pullGumTraceLog(self):
        from PyQt5.QtWidgets import QApplication
        active_window = QApplication.activeWindow() or self
        package_candidates = []
        for package_name in [self.labPackage.text().strip(), self.txtProcessName.text().strip()]:
            if len(package_name) > 0 and package_name not in package_candidates:
                package_candidates.append(package_name)
        search_dirs = ["/data/local/tmp", "/sdcard"]
        if hasattr(self, "txtGumTraceOutput"):
            custom_output = self.txtGumTraceOutput.text().strip()
            if len(custom_output) > 0:
                custom_dir = os.path.dirname(custom_output) if not custom_output.endswith("/") else custom_output
                if custom_dir and custom_dir not in search_dirs:
                    search_dirs.insert(0, custom_dir)
        for package_name in package_candidates:
            search_dirs.append(f"/data/data/{package_name}/files")
            search_dirs.append(f"/data/user/0/{package_name}/files")

        remote_path = ""
        for search_dir in search_dirs:
            # 直接用 adb shell 执行，避免 su 包装导致通配符失效
            cmd = "adb shell ls -t %s/gumtrace*.log 2>/dev/null | head -n 1" % search_dir
            search_res = CmdUtil.exec(cmd).strip()
            self.log("[DEBUG pullGumTrace] dir=%s res='%s'" % (search_dir, search_res.replace('\n', '\\n')[:200]))
            if not search_res or "No such file" in search_res or "not found" in search_res.lower():
                continue
            line = search_res.splitlines()[0].strip()
            if not line:
                continue
            if not line.startswith("/"):
                line = search_dir.rstrip("/") + "/" + line
            remote_path = line
            self.log("[DEBUG pullGumTrace] found: %s" % remote_path)
            break
        if len(remote_path) <= 0:
            QMessageBox().information(active_window, "hint", self.trText("未找到 GumTrace 日志。默认会搜索 /data/local/tmp、/sdcard 以及当前包名的 files 目录。", "No GumTrace log was found. Searched /data/local/tmp, /sdcard and the current package files directories."))
            return

        export_path = remote_path
        if not (remote_path.startswith("/sdcard/") or remote_path.startswith("/data/local/tmp/")):
            export_dir = "/sdcard/gumtrace_export"
            export_path = export_dir + "/" + os.path.basename(remote_path)
            export_res = CmdUtil.adbshellCmd("mkdir -p %s && cp '%s' '%s' && chmod 0666 '%s'" % (export_dir, remote_path, export_path, export_path))
            self.log(export_res)
            if "No such file" in export_res or "not found" in export_res:
                QMessageBox().information(active_window, "hint", self.trText("复制 GumTrace 日志到 /sdcard 失败：", "Failed to copy GumTrace log to /sdcard: ") + export_res)
                return

        local_dir = "./logs/gumtrace"
        if os.path.exists(local_dir) is False:
            os.makedirs(local_dir)
        base_name = os.path.basename(export_path)
        name_root, name_ext = os.path.splitext(base_name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        local_path = os.path.join(local_dir, "%s_%s%s" % (name_root, timestamp, name_ext or ".log"))
        pull_res = CmdUtil.exec("adb pull '%s' '%s'" % (export_path, local_path)).strip()
        self.log("adb pull result: " + pull_res)
        if "does not exist" in pull_res or ("error" in pull_res.lower() and "0 files pulled" not in pull_res.lower()) or "failed to access" in pull_res.lower():
            QMessageBox().information(active_window, "hint", self.trText("下载 GumTrace 日志失败：", "Failed to download GumTrace log: ") + pull_res)
            return
        self.refreshOverviewCards()
        QMessageBox().information(active_window, "hint", self.trText("GumTrace 日志下载完成：", "GumTrace log downloaded: ") + local_path)
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
        adb_prefix = self.adbScriptPrefix()
        line_sep = "\n"
        if platform.system() == "Darwin":
            line_sep = "; "
        binary_name = name
        launch_name = binary_name
        custom_port = (self.customPort or "").strip()
        wifi_port = (self.wifi_port or "").strip()
        if self.connType == "wifi":
            if len(wifi_port) > 0:
                launch_name += " -l 0.0.0.0:" + wifi_port
            data = data.replace("%removeForwards%", "")
            data = data.replace("%defaultForwards%", "")
            data = data.replace("%customPort%", "")
        elif self.connType == "usb":
            if len(custom_port) > 0:
                launch_name += " -l 0.0.0.0:" + custom_port
                data = data.replace("%removeForwards%", line_sep.join([
                    f"{adb_prefix} forward --remove tcp:27042 2>/dev/null",
                    f"{adb_prefix} forward --remove tcp:27043 2>/dev/null",
                    f"{adb_prefix} forward --remove tcp:{custom_port} 2>/dev/null",
                ]))
                data = data.replace("%defaultForwards%", "")
                data = data.replace("%customPort%", f"{adb_prefix} forward tcp:{custom_port} tcp:{custom_port}")
            else:
                data = data.replace("%removeForwards%", line_sep.join([
                    f"{adb_prefix} forward --remove tcp:27042 2>/dev/null",
                    f"{adb_prefix} forward --remove tcp:27043 2>/dev/null",
                ]))
                data = data.replace("%defaultForwards%", line_sep.join([
                    f"{adb_prefix} forward tcp:27042 tcp:27042",
                    f"{adb_prefix} forward tcp:27043 tcp:27043",
                ]))
                data = data.replace("%customPort%","")
        else:
            data = data.replace("%removeForwards%", "")
            data = data.replace("%defaultForwards%", "")
            data = data.replace("%customPort%", "")
        data = data.replace("%adbPrefix%", adb_prefix)
        data = data.replace("%fridaName%", binary_name)
        data = data.replace("%fridaLaunch%", launch_name)
        if self.fridaName != None and len(self.fridaName) > 0:
            data = data.replace("%fName%", self.fridaName)
        else:
            data = data.replace("%fName%", "frida-server")
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

    def runAdbCommand(self, extra_args, timeout=20, log_command=True, log_output=True):
        command_args = self.adbCommandArgs() + list(extra_args)
        if log_command:
            self.log(self.trText("执行命令：", "Run command: ") + " ".join(shlex.quote(part) for part in command_args))
        proc = subprocess.run(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        output = (proc.stdout or "").strip()
        if log_output and output:
            self.log(output)
        return proc.returncode, output

    def runAdbShellScript(self, script_text, timeout=20, log_command=True, log_output=True):
        return self.runAdbCommand(
            ["shell", "sh", "-c", shlex.quote(script_text)],
            timeout=timeout,
            log_command=log_command,
            log_output=log_output,
        )

    def fridaLaunchParts(self, name):
        launch_parts = ["/data/local/tmp/" + name]
        custom_port = (self.customPort or "").strip()
        wifi_port = (self.wifi_port or "").strip()
        if self.connType == "wifi" and len(wifi_port) > 0:
            launch_parts.extend(["-l", "0.0.0.0:" + wifi_port])
        elif self.connType == "usb" and len(custom_port) > 0:
            launch_parts.extend(["-l", "0.0.0.0:" + custom_port])
        return launch_parts

    def expectedFridaPort(self):
        if self.connType == "wifi":
            return (self.wifi_port or "").strip()
        if self.connType == "usb":
            return (self.customPort or "").strip()
        return ""

    def isRemotePortListening(self, port):
        if len(port) <= 0:
            return False
        try:
            port_hex = format(int(port), "04X")
        except ValueError:
            return False
        _, output = self.runAdbShellScript(
            "cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | grep -i ':%s '" % port_hex,
            timeout=8,
            log_command=False,
            log_output=False,
        )
        return len(output.strip()) > 0

    def readRemoteFridaStartLog(self):
        _, output = self.runAdbShellScript(
            "cat /data/local/tmp/frida_start.log 2>/dev/null || true",
            timeout=8,
            log_command=False,
            log_output=False,
        )
        return output.strip()

    def prepareFridaForward(self):
        if self.connType != "usb":
            return
        custom_port = (self.customPort or "").strip()
        ports_to_remove = ["27042", "27043"]
        if len(custom_port) > 0:
            ports_to_remove.append(custom_port)
        for port in ports_to_remove:
            self.runAdbCommand(["forward", "--remove", "tcp:" + port], timeout=8, log_command=False, log_output=False)
        if len(custom_port) > 0:
            rc, output = self.runAdbCommand(["forward", "tcp:" + custom_port, "tcp:" + custom_port], timeout=8)
            if rc != 0:
                raise RuntimeError(self.trText("创建自定义端口转发失败：", "Failed to create custom port forward: ") + output)
        else:
            for port in ("27042", "27043"):
                rc, output = self.runAdbCommand(["forward", "tcp:" + port, "tcp:" + port], timeout=8)
                if rc != 0:
                    raise RuntimeError(self.trText("创建端口转发失败：", "Failed to create port forward: ") + output)

    def ensureFridaServerReady(self):
        last_error = ""
        for _ in range(12):
            try:
                device = self.getFridaDevice()
                device.enumerate_processes()
                return
            except Exception as ex:
                last_error = str(ex)
                time.sleep(0.5)
        remote_log = self.readRemoteFridaStartLog()
        details = self.trText("连接 frida-server 失败：", "Failed to connect to frida-server: ") + last_error
        if remote_log:
            details += "\nfrida_start.log:\n" + remote_log
        raise RuntimeError(details)

    def startFridaServerDirect(self, name):
        launch_parts = self.fridaLaunchParts(name)
        expected_port = self.expectedFridaPort()
        self.log(self.trText("准备启动 frida-server...", "Preparing to start frida-server..."))

        kill_cmd = "killall %s %s frida-server 2>/dev/null || true" % (self.fridaName or "frida-server", name)
        self.runAdbShellScript(kill_cmd, timeout=8, log_command=False, log_output=False)

        chmod_targets = ["/data/local/tmp/" + name]
        if self.fridaName:
            chmod_targets.insert(0, "/data/local/tmp/" + self.fridaName)
        chmod_cmd = "; ".join("chmod 0777 %s 2>/dev/null" % target for target in chmod_targets)
        self.runAdbShellScript(chmod_cmd, timeout=8, log_command=False, log_output=False)

        self.prepareFridaForward()

        remote_launch = "nohup %s >/data/local/tmp/frida_start.log 2>&1 &" % " ".join(shlex.quote(part) for part in launch_parts)
        rc, output = self.runAdbShellScript(remote_launch, timeout=8)
        if rc != 0:
            raise RuntimeError(self.trText("启动 frida-server 失败：", "Failed to start frida-server: ") + output)

        if len(expected_port) > 0:
            for _ in range(12):
                if self.isRemotePortListening(expected_port):
                    break
                time.sleep(0.5)
            else:
                remote_log = self.readRemoteFridaStartLog()
                details = self.trText("目标端口未监听：", "Target port is not listening: ") + expected_port
                if remote_log:
                    details += "\nfrida_start.log:\n" + remote_log
                raise RuntimeError(details)

        self.ensureFridaServerReady()
        self.log(self.trText("frida-server 已启动并通过连通性检测。", "frida-server is running and passed connectivity checks."))

    def fridaWheelCacheDir(self):
        return os.path.abspath(os.path.join(".", "tmp", "frida_wheels"))

    def ensureFridaWheelCacheDir(self):
        cache_dir = self.fridaWheelCacheDir()
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def currentPythonExecutable(self):
        if getattr(sys, "frozen", False):
            return "python3"
        return sys.executable or "python3"

    def bundledPythonSiteTarget(self):
        if getattr(sys, "frozen", False):
            return BUNDLE_ROOT
        return ""

    def getInstalledPythonFridaVersion(self):
        try:
            if getattr(sys, "frozen", False):
                preferred_version = conf.read("kmain", "python_frida_version").strip()
                if preferred_version:
                    return preferred_version
                return getattr(frida, "__version__", "") or ""
            command_args = [self.currentPythonExecutable(), "-c", "import frida; print(getattr(frida, '__version__', ''))"]
            output = subprocess.check_output(command_args, stderr=subprocess.STDOUT, text=True).strip()
            return output
        except Exception:
            return ""

    def buildFridaInstallCommand(self, version):
        cache_dir = self.ensureFridaWheelCacheDir()
        package_spec = f"frida=={version}"
        python_cmd = self.currentPythonExecutable()
        target_dir = self.bundledPythonSiteTarget()
        # 仅切换 frida Python 包版本；保留现有 frida-tools。
        # 本地有 wheel 时走纯离线安装；否则允许 pip 访问索引并在需要时从源码构建。
        if self.hasCachedFridaWheel(cache_dir, version):
            command = [
                python_cmd, "-m", "pip", "install", "-U",
                "--no-index",
                "--find-links", cache_dir,
                package_spec,
            ]
        else:
            command = [
                python_cmd, "-m", "pip", "install", "-U",
                "--cache-dir", cache_dir,
                "--find-links", cache_dir,
                package_spec,
            ]
        if target_dir:
            command[4:4] = ["--target", target_dir]
        return command

    def buildFridaWheelDownloadCommand(self, version):
        cache_dir = self.ensureFridaWheelCacheDir()
        return [
            self.currentPythonExecutable(),
            "-m",
            "pip",
            "download",
            "--dest",
            cache_dir,
            f"frida=={version}",
        ]

    def installPythonFridaVersion(self, version):
        installed = self.getInstalledPythonFridaVersion()
        if installed == version:
            return []
        return self.buildFridaInstallCommand(version)

    def hasCachedFridaWheel(self, cache_dir, version):
        """检查缓存目录中是否存在指定版本可直接安装的 frida wheel"""
        if not os.path.isdir(cache_dir):
            return False
        prefix = f"frida-{version}-"
        for f in os.listdir(cache_dir):
            if f.startswith(prefix) and f.endswith(".whl"):
                return True
        return False

    def hasCachedFridaPackage(self, cache_dir, version):
        if not os.path.isdir(cache_dir):
            return False
        wheel_prefix = f"frida-{version}-"
        source_prefix = f"frida-{version}."
        for f in os.listdir(cache_dir):
            if f.startswith(wheel_prefix) and f.endswith(".whl"):
                return True
            if f.startswith(source_prefix) and (f.endswith(".tar.gz") or f.endswith(".zip")):
                return True
        return False

    def appendFridaVersionOutput(self, text):
        if self.fridaVersionOutput is None or not text:
            return
        self.fridaVersionOutput.appendPlainText(text)
        cursor = self.fridaVersionOutput.textCursor()
        cursor.movePosition(cursor.End)
        self.fridaVersionOutput.setTextCursor(cursor)
        self.fridaVersionOutput.ensureCursorVisible()
        QApplication.processEvents()

    def cleanupFridaVersionWorker(self):
        if self.fridaVersionWorker is not None:
            self.fridaVersionWorker.wait()
            self.fridaVersionWorker.deleteLater()
            self.fridaVersionWorker = None

    def closeFridaVersionDialog(self):
        if self.fridaVersionDialog is not None:
            self.fridaVersionDialog.close()
            self.fridaVersionDialog.deleteLater()
            self.fridaVersionDialog = None
            self.fridaVersionOutput = None
            self.fridaVersionCloseButton = None

    def setFridaVersionDialogClosable(self, enabled):
        if self.fridaVersionCloseButton is not None:
            self.fridaVersionCloseButton.setEnabled(enabled)

    def setFridaVersionDialogTitle(self, zh_text, en_text):
        if self.fridaVersionDialog is not None:
            self.fridaVersionDialog.setWindowTitle(self.trText(zh_text, en_text))

    def createFridaVersionDialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.trText("切换 frida 版本", "Switch frida version"))
        dialog.setWindowModality(Qt.WindowModal)
        dialog.resize(760, 420)
        layout = QVBoxLayout(dialog)

        output_view = QPlainTextEdit(dialog)
        output_view.setReadOnly(True)
        layout.addWidget(output_view)

        close_button = QPushButton(self.trText("关闭", "Close"), dialog)
        close_button.setEnabled(False)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        self.fridaVersionDialog = dialog
        self.fridaVersionOutput = output_view
        self.fridaVersionCloseButton = close_button
        return dialog

    def finishFridaVersionChange(self, version, output, warm_cache=True):
        self.cleanupFridaVersionWorker()
        self.curFridaVer = version
        conf.write("kmain", "python_frida_version", version)
        for action in self.fridaVersionMenuActions:
            action.setChecked(str(action.data() or "").strip() == version)
        self.updateFridaVersionSelectionUi(version)
        self.appendFridaVersionOutput(self.trText("\n切换完成。", "\nSwitch completed."))
        self.setFridaVersionDialogClosable(True)
        self.setFridaVersionDialogTitle("切换完成", "Switch completed")
        if warm_cache:
            cache_dir = self.ensureFridaWheelCacheDir()
            if not self.hasCachedFridaPackage(cache_dir, version):
                try:
                    download_command = self.buildFridaWheelDownloadCommand(version)
                    self.appendFridaVersionOutput(self.trText("缓存 frida 安装包以加速下次切换：", "Caching the frida package for faster switching: ") + " ".join(shlex.quote(arg) for arg in download_command))
                    subprocess.Popen(
                        download_command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
            else:
                self.appendFridaVersionOutput(self.trText("本地 frida 安装包缓存已存在，跳过下载。", "Local frida package cache exists, skipping download."))
        QMessageBox().information(self, "hint", self.trText("已切换本地 frida 版本：", "Switched local frida version: ") + version)

    def failFridaVersionChange(self, message):
        self.cleanupFridaVersionWorker()
        self.appendFridaVersionOutput("\n" + self.trText("执行失败：", "Command failed: ") + message)
        self.setFridaVersionDialogClosable(True)
        self.setFridaVersionDialogTitle("切换失败", "Switch failed")
        QMessageBox.critical(self, "error", message)
        self.rebuildFridaVersionMenu()

    def changeFridaClientVersion(self, version, checked):
        if checked is False:
            return
        supported, unsupported_reason = self.isFridaVersionSupportedOnCurrentPython(version)
        if not supported:
            self.rebuildFridaVersionMenu()
            QMessageBox().information(self, "hint", unsupported_reason)
            return
        self.cleanupFridaVersionWorker()
        self.closeFridaVersionDialog()
        command_args = self.installPythonFridaVersion(version)
        dialog = self.createFridaVersionDialog()

        installed = self.getInstalledPythonFridaVersion()
        if installed == version or not command_args:
            self.appendFridaVersionOutput(self.trText("当前 frida 版本已是目标版本，无需重复安装。", "The current frida version already matches the target version. Skipping reinstall."))
            self.finishFridaVersionChange(version, "", warm_cache=False)
            dialog.show()
            return

        command_text = " ".join(shlex.quote(arg) for arg in command_args)
        self.appendFridaVersionOutput(self.trText("准备切换本地 frida 版本...", "Preparing to switch local frida version..."))
        self.appendFridaVersionOutput(self.trText("仅切换 Python frida 包版本，保留现有 frida-tools。", "Only the Python frida package will be switched. Existing frida-tools will be kept."))
        self.appendFridaVersionOutput(self.trText("执行命令：", "Command: ") + command_text)

        self.fridaVersionWorker = CommandWorker(command_args, self)
        self.fridaVersionWorker.started.connect(lambda started_command: self.appendFridaVersionOutput(self.trText("开始执行：", "Started: ") + started_command))
        self.fridaVersionWorker.output.connect(self.appendFridaVersionOutput)
        self.fridaVersionWorker.success.connect(lambda output: self.setFridaVersionDialogClosable(True))
        self.fridaVersionWorker.success.connect(lambda output, current_version=version: self.finishFridaVersionChange(current_version, output, warm_cache=True))
        self.fridaVersionWorker.error.connect(lambda message: self.setFridaVersionDialogClosable(True))
        self.fridaVersionWorker.error.connect(self.failFridaVersionChange)
        self.fridaVersionWorker.start()
        dialog.show()


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
        self.groupBox_2.setTitle(self.trText("附加前使用", "Pre-attach"))
        if hasattr(self, "customTemplateGroup"):
            self.customTemplateGroup.setTitle(self.trText("自定义模板", "Custom Templates"))
        if hasattr(self, "labCustomTemplateHint"):
            self.labCustomTemplateHint.setText(self.trText("将常用脚本固定到主界面，一键启用/禁用；管理与编辑请进入“自定义”。", "Pin frequently used scripts here for one-click enable/disable. Use 'Custom' to manage and edit templates."))
        if hasattr(self, "btnGumTracePanel"):
            self.btnGumTracePanel.setText(self.trText("GumTrace", "GumTrace"))
        if hasattr(self, "btnFCAndJnitracePanel"):
            self.btnFCAndJnitracePanel.setText(self.trText("jnitrace", "jnitrace"))
        self.groupBox_7.setTitle(self.trText("附加进程逆向信息", "Attached process RE info"))
        self.labAttachedInfoHint.setText(self.trText("这里汇总 Frida 运行时、应用包信息、模块/DEX/类数量和调试属性，便于附加后快速判断分析切入点。", "This panel summarizes Frida runtime data, package metadata, module/DEX/class counts and debug-related flags to help pick an analysis entry point quickly."))
        if hasattr(self, "attachDexGroup"):
            self.attachDexGroup.setTitle(self.trText("已加载 DEX", "Loaded DEX"))
        if hasattr(self, "labAttachDexHint"):
            self.labAttachDexHint.setText(self.trText("这里展示附加后识别到的 dex / apk / jar 入口，便于判断 Java 代码来源。", "This panel lists dex / apk / jar entries discovered after attach so you can quickly spot Java code origins."))
        if hasattr(self, "txtDex"):
            self.txtDex.setPlaceholderText(self.trText("按 dex 路径或 ClassLoader 过滤", "Filter by dex path or ClassLoader"))
        if hasattr(self, "attachResourceDetailGroup"):
            self.attachResourceDetailGroup.setTitle(self.trText("当前选中资源详情", "Selected resource details"))
        if hasattr(self, "labAttachResourceHint"):
            self.labAttachResourceHint.setText(self.trText("点击左侧模块或 DEX 后，这里展示路径、大小、来源、导出/符号数量等关键属性。", "Click a module or DEX entry on the left to inspect key attributes here, including path, size, ownership and export/symbol counts."))
        if hasattr(self, "attachResourceTabs"):
            self.attachResourceTabs.setTabText(self.attachResourceTabs.indexOf(self.groupBox_3), self.trText("SO 模块", "SO modules"))
            self.attachResourceTabs.setTabText(self.attachResourceTabs.indexOf(self.attachDexGroup), self.trText("DEX", "DEX"))
        if hasattr(self, "attachResultTabs"):
            self.attachResultTabs.setTabText(self.attachResultTabs.indexOf(self.nativeResultWidget), self.trText("导出/符号", "Exports / Symbols"))
            self.attachResultTabs.setTabText(self.attachResultTabs.indexOf(self.groupBox_7), self.trText("运行时详情", "Runtime details"))
        self.labAppWorkbenchHint.setText(self.trText("支持先选择目标手机，再刷新前台应用与扩展元数据。默认会选中第一个已连接设备。", "Choose the target device first, then refresh the foreground app and extended metadata. The first connected device is selected by default."))
        self.currentAppExtraGroup.setTitle(self.trText("当前前台应用补充信息", "Foreground app extra info"))
        self.labCurrentAppInfoHint.setText(self.trText("这里基于 dumpsys / pm 输出补充显示版本、ABI、调试标记、数据目录等信息。", "This panel augments dumpsys / pm results with version, ABI, debug flags and data-path details."))
        self.labDeviceSelector.setText(self.trText("连接手机：", "Device:")) if hasattr(self, "labDeviceSelector") else None
        self.btnRefreshDevices.setText(self.trText("刷新设备", "Refresh devices")) if hasattr(self, "btnRefreshDevices") else None
        self.labOutputLogView.setText(self.trText("输出日志视图", "Output log view"))
        self.txtLogs.setPlaceholderText(self.trText("日志将在这里滚动显示...", "Logs will stream here..."))
        self.txtoutLogs.setPlaceholderText(self.trText("日志将在这里滚动显示...", "Logs will stream here..."))
        self.txtAiLogInput.setPlaceholderText(self.trText("打开日志文件，或直接粘贴 / 输入待分析日志...", "Open a log file, or paste / type the log content to analyze..."))
        if self.aiService.is_available():
            self.txtAiAnalysis.setPlaceholderText(self.trText("AI 分析结果会显示在这里", "AI analysis output will appear here"))
        else:
            self.txtAiAnalysis.setPlaceholderText(self.aiService.missing_message("English" if self.isEnglish() else "China"))
        self.btnOpenLogFile.setText(self.trText("打开日志文件", "Open log file"))
        self.btnRestoreLiveLog.setText(self.trText("恢复实时日志", "Restore live log"))
        self.btnAnalyzeLog.setText(self.trText("AI 分析日志", "AI analyze log"))
        self.actionAiSettings.setText(self.trText("AI 设置", "AI Settings"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), self.trText("主界面", "Main"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), self.trText("附加进程信息", "Attach process info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), self.trText("应用信息", "App info"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), self.trText("hook列表", "Hook list"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), self.trText("操作日志", "Operation log"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), self.trText("输出日志", "Output log"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.aiAnalysisTab), self.trText("AI 分析", "AI Analysis"))
        self.gumTraceWindow.setWindowTitle(self.trText("GumTrace 工作台", "GumTrace workbench")) if hasattr(self, "gumTraceWindow") else None
        self.btnDumpPtr.setText(self.trText("dump指定地址", "dump address"))
        self.btnDumpDex.setText(self.trText("dump_dex加载class后调用", "dump dex after class load"))
        self.btnCallFunction.setText(self.trText("函数重放", "function replay"))
        self.btnMemSearch.setText(self.trText("内存搜索", "memory search"))
        self.btnNatives.setText(self.trText("批量native", "multiple native"))
        self.btnTuoke.setText(self.trText("脱壳", "unpack"))
        self.btnCustom.setText(self.trText("自定义", "custom"))
        self.btnAntiFrida.setText(self.trText("frida检测", "frida check"))
        # 安全检查：只在控件存在、未被删除且可见时设置文本
        if hasattr(self, 'chkJavaEnc') and self.chkJavaEnc is not None:
            try:
                if not self.chkJavaEnc.isHidden():
                    self.chkJavaEnc.setText(self.trText("java加解密", "java encrypt"))
            except RuntimeError:
                pass
        self.label.setText(self.trText("别名：", "Alias:"))
        self.label_2.setText(self.trText("别名：", "Alias:"))
        self.btnSaveHooks.setText(self.trText("保存列表", "Save list"))
        self.btnImportHooks.setText(self.trText("导入JSON", "Import JSON"))
        self.btnLoadHooks.setText(self.trText("加载记录", "Load record"))
        self.btnClearHooks.setText(self.trText("清空列表", "Clear list"))
        self.groupBox_3.setTitle(self.trText("module列表", "Module list"))
        self.groupBox_5.setTitle(self.trText("符号", "Symbols"))
        self.nativeActionGroup.setTitle(self.trText("Native 查询动作", "Native query actions"))
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
        self.menufile.setTitle(self.trText("文件", "file"))
        self.menuedit.setTitle(self.trText("执行", "run"))
        self.menuAttach.setTitle(self.trText("附加进程", "attach"))
        self.setCmdMenuVisible(False)
        self.actionFrida32Start.setText(self.trText("启动 frida-server", "Start frida-server"))
        self.menu_frida_server.setTitle(self.trText("启动frida-server", "start frida-server"))
        self.menuhelp.setTitle(self.trText("帮助", "help"))
        self.menu.setTitle(self.trText("上传与下载", "upload and download"))
        self.menu_2.setTitle(self.trText("连接方式", "connect type"))
        self.menufrida.setTitle(self.trText("frida切换", "frida ver"))
        self.menufrida.menuAction().setVisible(True)
        if self.fridaUploadMenu is not None:
            self.fridaUploadMenu.setTitle(self.trText("上传 frida", "Upload frida"))
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
        if hasattr(self, "actionPullGumTraceLog"):
            self.actionPullGumTraceLog.setText(self.trText("下载GumTrace日志", "Download GumTrace log"))
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
        self.actionattach.setText("attach")
        self.actionattach.setToolTip("attach by packageName")
        self.actionattachF.setText("attachF")
        self.actionattachF.setToolTip("attach current top app")
        self.actionspawn.setText("spawn")
        self.actionstop.setText("stop")
        if hasattr(self, "actionCustomModule"):
            self.actionCustomModule.setText(self.trText("自定义", "Custom"))
            self.actionCustomModule.setToolTip(self.trText("打开自定义模块", "Open Custom module"))
        if hasattr(self, "actionGumTracePanel"):
            self.actionGumTracePanel.setText("GumTrace")
            self.actionGumTracePanel.setToolTip(self.trText("打开 GumTrace 工作台", "Open GumTrace workbench"))
        self.updateToolbarContextPanel()
        self.cmbGumTraceMode.setItemText(0, self.trText("手动启动", "Manual"))
        self.cmbGumTraceMode.setItemText(1, self.trText("偏移触发", "Offset trigger"))
        self.cmbGumTraceMode.setItemText(2, self.trText("导出触发", "Export trigger"))
        self.labStatus.setText(self.trText("当前状态:已连接", "Status: connected") if self.actionStop.isEnabled() else self.trText("当前状态:未连接", "Status: disconnected"))
        if self.currentLogMode == "file" and self.loadedLogPath:
            self.labLogStatus.setText(self.trText("当前日志：", "Current log: ") + os.path.basename(self.loadedLogPath))
        else:
            self.labLogStatus.setText(self.trText("当前日志：实时输出", "Current log: live output"))
        self.onDeviceChanged() if hasattr(self, "cmbDevices") else None
        self.updateCurrentAppInfoTable()
        self.updateAttachedInfoTable()
        self.refreshAiState()
        self.refreshHookMetadataLanguage()
        self.updateTabHooks()
        self.refreshOverviewCards()
        self.refreshChildTranslations()
        self.rebuildFridaVersionMenu()
        self.updateConnectionSelectionUi()
        self.updateFridaVersionSelectionUi()
        self.updateLanguageSelectionUi()

    def switchLanguage(self, language):
        if self.language == language:
            self.updateLanguageSelectionUi()
            return
        self.language = language
        conf.write("kmain", "language", language)
        apply_app_language(QApplication.instance(), language)
        self.loadTypeData()
        self.retranslateUi(self)
        self.retranslateDynamicUi()
        self.updateLanguageSelectionUi()

    def ChangeEnglish(self,checked):
        if checked==False:
            return
        self.switchLanguage("English")

    def ChangeChina(self,checked):
        if checked==False:
            return
        self.switchLanguage("China")

    def StartFridaServer(self):
        binary_name = "frida-server"
        if self.fridaName != None and len(self.fridaName) > 0:
            binary_name = self.fridaName + "64"
        try:
            self.startFridaServerDirect(binary_name)
            QMessageBox().information(self, "hint", self.trText("frida-server 启动成功。", "frida-server started successfully."))
        except Exception as ex:
            self.log(self.trText("启动 frida-server 异常：", "Failed to start frida-server: ") + str(ex))
            QMessageBox().information(self, "hint", self.trText("启动 frida-server 异常：", "Failed to start frida-server: ") + str(ex))

    def Frida32Start(self):
        self.StartFridaServer()

    def Frida64Start(self):
        self.StartFridaServer()

    def FridaX86Start(self):
        self.StartFridaServer()

    def FridaX64Start(self):
        self.StartFridaServer()

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
        self.updateToolbarContextPanel()
        self.refreshOverviewCards()

    def getFridaDevice(self):
        if self.connType=="usb":
            custom_port = (self.customPort or "").strip()
            if len(custom_port) > 0:
                str_host = "127.0.0.1:%s" % custom_port
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

    def normalizeWifiSettings(self):
        self.address = (self.address or "").strip()
        self.wifi_port = (self.wifi_port or "").strip()
        return self.address, self.wifi_port

    def ensureWifiConnectionReady(self):
        if self.connType != "wifi":
            return True
        address, port = self.normalizeWifiSettings()
        if len(address) <= 0 or len(port) <= 0:
            QMessageBox().information(self, "hint", self._translate("kmainForm","当前为wifi连接,但是未设置地址或端口"))
            return False
        return True

    # 启动附加
    def actionAttachStart(self):
        self.log("actionAttach")
        try:
            if self.ensureWifiConnectionReady() is False:
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
            self.th.classListSignel.connect(self.onClassListReceived)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.searchAppInfoSignel.connect(self.searchAppInfoRes)
            self.th.searchMemorySignel.connect(self.searchMemResp)
            self.th.setBreakSignel.connect(self.setBreakResp)
            self.th.attachType="attachCurrent"
            self.prepareGumTraceLogFile()
            self.th.start()
            if len(self.hooksData) <= 0:
                # QMessageBox().information(self, "提示", "未设置hook选项")
                self.log(self._translate("kmainForm","未设置hook选项"))
        except Exception as ex:
            self.changeAttachStatus(False)
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
            if self.ensureWifiConnectionReady() is False:
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
            self.th.classListSignel.connect(self.onClassListReceived)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.searchAppInfoSignel.connect(self.searchAppInfoRes)
            self.th.searchMemorySignel.connect(self.searchMemResp)
            self.th.attachType="spawn"

            self.prepareGumTraceLogFile()
            self.th.start()
            if len(self.hooksData) <= 0:
                # QMessageBox().information(self, "提示", "未设置hook选项")
                self.log(self._translate("kmainForm","未设置hook选项"))
        except Exception as ex:
            self.changeAttachStatus(False)
            self.log(self._translate("kmainForm","附加异常")+".err:" + str(ex))
            QMessageBox().information(self, "hint", self._translate("kmainForm","附加异常.") + str(ex))

    def updateAttachActionStates(self, attached):
        attach_enabled = not attached
        for action_name in [
            "actionAttach",
            "actionAttachName",
            "actionSpawn",
            "actionattach",
            "actionattachF",
            "actionspawn",
            "action",
            "action_2",
            "actionspwan",
        ]:
            action = getattr(self, action_name, None)
            if action is not None:
                action.setEnabled(attach_enabled)
        for action_name in ["actionStop", "actionstop"]:
            action = getattr(self, action_name, None)
            if action is not None:
                action.setEnabled(attached)
                if action_name == "actionstop":
                    action.setIcon(self.createColoredStopIcon("#ef4444" if attached else "#94a3b8"))
        if hasattr(self, "menuAttach"):
            self.menuAttach.setEnabled(attach_enabled)

    # 修改ui的状态表现
    def changeAttachStatus(self, isattach):
        self.updateAttachActionStates(isattach)
        if isattach:
            self.labStatus.setText( self._translate("kmainForm","当前状态:已连接") )
        else:
            self.labStatus.setText(self._translate("kmainForm","当前状态:未连接") )
            self.labPackage.setText("")
            self.attachedAppInfoSnapshot = {}
            self.modules = None
            self.classes = None
            self.dexes = []
            self.filteredModules = []
            self.currentSelectedModule = None
            self.currentSelectedDex = None
            self.moduleExportCache = {}
            self.moduleSymbolCache = {}
            self.lastSearchModuleKey = None
            if hasattr(self, "listModules"):
                self.listModules.clear()
            if hasattr(self, "listClasses"):
                self.listClasses.clear()
            if hasattr(self, "listDex"):
                self.listDex.clear()
            if hasattr(self, "listSymbol"):
                self.listSymbol.clear()
            if hasattr(self, "listMethod"):
                self.listMethod.clear()
            if hasattr(self, "attachResourceTable"):
                self.renderAttachResourceRows([])
            self.updateAttachedInfoTable()
        self.updateToolbarContextPanel()
        self.refreshOverviewCards()

    # 根据进程名进行附加进程
    def actionAttachNameStart(self):
        self.log("actionAttachName")
        try:
            if self.ensureWifiConnectionReady() is False:
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
            self.th.classListSignel.connect(self.onClassListReceived)
            self.th.attachOverSignel.connect(self.attachOver)
            self.th.searchAppInfoSignel.connect(self.searchAppInfoRes)
            self.th.searchMemorySignel.connect(self.searchMemResp)
            self.th.attachType = "attach"
            self.prepareGumTraceLogFile()
            self.th.start()
        except Exception as ex:
            self.changeAttachStatus(False)
            self.log(self._translate("kmainForm","附加异常")+".err:" + str(ex))
            QMessageBox().information(self, "hint", self._translate("kmainForm","附加异常.") + str(ex))

    def ChangePort(self):
        self.portForm.txtFridaName.setText(self.fridaName)
        self.portForm.txtPort.setText(self.customPort)
        res=self.portForm.exec()
        if res==0:
            return
        self.fridaName = (self.portForm.fridaName or "").strip()
        self.customPort = (self.portForm.port or "").strip()
        conf.write("kmain", "frida_name", self.fridaName)
        conf.write("kmain", "usb_port", self.customPort)
        self.updateConnectionSelectionUi()

    def WifiConn(self):
        self.wifiForm.txtAddress.setText(self.address)
        self.wifiForm.txtPort.setText(self.wifi_port)
        res=self.wifiForm.exec()
        if res==0 :
            self.updateConnectionSelectionUi()
            return
        self.connType="wifi"
        self.address=self.wifiForm.address
        self.wifi_port=self.wifiForm.port
        conf.write("kmain", "wifi_addr", self.address)
        conf.write("kmain", "wifi_port", self.wifi_port)
        self.updateConnectionSelectionUi()
    def UsbConn(self):
        self.connType="usb"
        self.updateConnectionSelectionUi()

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
        print("[DEBUG] wallBreaker: self.classes=%d" % len(self.classes or []))
        api = getattr(self.th.default_script, 'exports_sync', None) or self.th.default_script.exports
        self.wallBreakerForm.api = api
        self.wallBreakerForm._mainForm = self
        self.wallBreakerForm.classes = self.classes or []
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

    def hookJNI(self, checked=None):
        typeStr = "jnitrace"
        self.log("hook jni")
        self.jniform.flushCmb()
        res = self.jniform.exec()
        if res == 0:
            return
        jniHook = {"class": self.jniform.moduleName, "method": self.jniform.methodName,
                   "offset":self.jniform.offset,
                   "bak": self._translate("kmainForm","jni trace(不打印详细参数和返回值结果)")}
        self.hooksData[typeStr] = jniHook
        self.updateTabHooks()

    def hookNetwork(self, checked=None):
        self.chk_hook_insert(True,"r0capture",self._translate("kmainForm","网络相关"))

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

    def hookNewJnitrace(self, checked=None):
        typeStr = "FCAnd_jnitrace"
        self.log("hook jni")
        self.newJniform.checkData=False
        self.newJniform.flushCmb()
        res = self.newJniform.exec()
        if res == 0:
            return
        jniHook = {"class": self.newJniform.moduleName, "method": self.newJniform.methodName,
                   "offset":self.newJniform.offset,
                   "bak": self._translate("kmainForm","FCAnd_jnitrace有详细的打印细节")}
        self.hooksData[typeStr] = jniHook
        self.updateTabHooks()
        # self.chk_hook_insert(checked, "FCAnd_jnitrace", "新的jnitrace")

    def openFCAndJnitrace(self):
        self.hookNewJnitrace()

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
        """hook 列表变动后，同步 customForm 并刷新主界面的 pinned checkbox 状态"""
        if hasattr(self, "customForm"):
            # 从 hooksData 反向同步 customForm.customHooks
            custom_hooks = self.hooksData.get("custom", [])
            if isinstance(custom_hooks, list):
                active_files = {item.get("fileName") or item.get("method") for item in custom_hooks if isinstance(item, dict)}
                self.customForm.customHooks = [
                    item for item in self.customForm.customHooks
                    if item.get("fileName") in active_files
                ]
                self.customForm.updateTabCustomHook()
            else:
                self.customForm.customHooks = []
                self.customForm.updateTabCustomHook()
        # 刷新主界面 pinned checkbox
        if hasattr(self, "customTemplateTiles"):
            active_files = set()
            if hasattr(self, "customForm"):
                active_files = {item.get("fileName") for item in self.customForm.customHooks}
            for tile in self.customTemplateTiles:
                file_name = getattr(tile, "fileName", None)
                if file_name is not None:
                    tile.blockSignals(True)
                    tile.setChecked(file_name in active_files)
                    tile.blockSignals(False)

    def loadJson(self, filepath):
        if os.path.exists(filepath)==False:
            return
        with open(filepath, "r", encoding="utf8") as hooksFile:
            data = hooksFile.read()
            self.hooksData = json.loads(data)
            self.syncCustomHooksFromHooksData()
            self.migrateLegacySimpleHooksToCustom()
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
        self.refreshModuleList(data)

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
        self.log(self.trText("已禁用模块点击联动，仅同步模块名称。", "Module click linkage is disabled; only the module name is synchronized."))

    def listClassClick(self, item):
        self.txtClass.setText(item.text())

    def listSymbolClick(self, item):
        self.txtSymbol.setText(item.text())

    def listMethodClick(self, item):
        self.txtMethod.setText(item.text())

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
            "deviceSerial": self.selectedDeviceSerial(),
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

    def onClassListReceived(self, classes):
        """通过 send 消息从 default.js 异步接收 Java 类列表"""
        self.classes = classes or []
        print("[DEBUG] onClassListReceived: %d classes" % len(self.classes))
        self.log("onClassListReceived: %d classes" % len(self.classes))
        if hasattr(self, 'changeClass') and hasattr(self, 'txtClass'):
            self.changeClass(self.txtClass.text() if self.txtClass.text() else "")

    # 附加成功后取出app的信息展示
    def loadAppInfo(self, info):
        print("[DEBUG] loadAppInfo called, info is None: %s" % (info is None))
        if info==None:
            return

        print("[DEBUG] loadAppInfo: keys=%s" % list(info.keys()))
        print("[DEBUG] loadAppInfo: classes in info=%s, len=%d" % ("classes" in info, len(info.get("classes", []))))
        print("[DEBUG] loadAppInfo: javaUnavailable=%s" % info.get("javaUnavailable", False))

        self.listModules.clear()
        if hasattr(self, "listDex"):
            self.listDex.clear()

        if "modules" not in info:
            return
        self.modules = info["modules"]
        self.classes = info.get("classes", []) or []
        self.methods = []
        self.dexes = info.get("dexes", []) or []
        self.filteredModules = []
        self.currentSelectedModule = None
        self.currentSelectedDex = None
        self.moduleExportCache = {}
        self.moduleSymbolCache = {}
        self.lastSearchModuleKey = None

        self.refreshModuleList(self.txtModule.text() if hasattr(self, "txtModule") else "")

        if hasattr(self, "listDex"):
            self.changeDex(self.txtDex.text() if hasattr(self, "txtDex") else "")

        try:
            self.listModules.itemClicked.disconnect(self.listModuleClick)
        except Exception:
            pass
        self.listModules.itemClicked.connect(self.listModuleClick)
        packageName = self.labPackage.text().strip()
        if len(packageName) <= 0:
            packageName = ((info.get("package") or {}).get("packageName") or "").strip()
            if len(packageName) > 0:
                self.labPackage.setText(packageName)
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
        self.renderAttachRuntimeInfo()

        preferred_module = self.preferredModule()
        if preferred_module is not None:
            normalized_display = self.moduleDisplayText(preferred_module)
            matches = self.listModules.findItems(normalized_display, Qt.MatchExactly)
            if matches:
                self.listModules.setCurrentItem(matches[0])
            if hasattr(self, "txtModule"):
                self.txtModule.clear()

        with open("./tmp/" + packageName + ".modules" + (".spawn" if info.get("spawn") == "1" else "") + ".txt", "w+", encoding="utf-8") as packageTmpFile:
            for module in info["modules"]:
                packageTmpFile.write(module["name"] + "\n")

    def searchAppInfoRes(self, info):
        searchTyep = info["type"]
        self.searchType = searchTyep
        if searchTyep == "export" or searchTyep == "symbol":
            error_message = info.get("error")
            self.symbols = info[searchTyep]
            cache_key = self.lastSearchModuleKey
            if cache_key and not error_message:
                if searchTyep == "export":
                    self.moduleExportCache[cache_key] = info[searchTyep]
                else:
                    self.moduleSymbolCache[cache_key] = info[searchTyep]
            self.lastSearchModuleKey = None
            self.populateSymbolList(self.symbols)
            if error_message:
                self.log(self.trText("模块查询已跳过：", "Module query skipped: ") + error_message)
            if self.currentSelectedModule is not None and self.moduleCacheKey(self.currentSelectedModule) == cache_key:
                self.renderAttachResourceRows(self.moduleInfoRows(self.currentSelectedModule))
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
        self.setMainContextForegroundPackage(packageName)
        self.updateCurrentAppInfoTable()
        self.updateToolbarContextPanel()
        self.refreshOverviewCards()

    def fartOpBin(self):
        self.fartBinForm.show()

    def stalkerOpLog(self):
        self.stalkerMatchForm.show()

    def resizeEvent(self, event):
        super(kmainForm, self).resizeEvent(event)
        self.rebuildResponsiveCards()
        self.rebuildAdvancedToolGrid()
        self.rebuildPinnedCustomTemplateGrid()

    # 不关闭的话，mac下调试时退出会出现无法关闭进程
    def closeEvent(self, event):
        if hasattr(self, "gumTraceWindow"):
            self.gumTraceWindow.close()
        if platform.system() =='Darwin':
            CmdUtil.adbshellCmd("pkill -9 frida")


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
    import os
    # 抑制 Qt 的 SVG 和样式警告 - 必须在 QApplication 创建之前设置
    os.environ['QT_LOGGING_RULES'] = 'qt.svg=false;*.warning=false'
    
    current_exit_code = 1207
    app = QApplication(sys.argv)
    try:
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        # 抑制 Qt 内部警告
        import warnings
        warnings.filterwarnings('ignore')
        
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='dark_teal.xml', extra={
            'density_scale': '0',
        })
        # qt-material 不覆盖 checkbox/radio，手动补充，并添加悬浮效果
        app.setStyleSheet(app.styleSheet() + """
        QPushButton {
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #00897b;
            border: 2px solid #4db6ac;
        }
        QPushButton:pressed {
            background-color: #00695c;
        }
        QCheckBox::indicator {
            width: 18px; height: 18px;
            border: 2px solid #80cbc4;
            border-radius: 3px;
            background: transparent;
        }
        QCheckBox::indicator:checked {
            background: #009688;
            border-color: #009688;
            image: url(none);
        }
        QCheckBox::indicator:hover {
            border-color: #26a69a;
            border-width: 3px;
            background: rgba(77, 182, 172, 0.1);
        }
        QCheckBox::indicator:checked:hover {
            background: #00897b;
            border-color: #00897b;
        }
        QCheckBox {
            spacing: 8px;
            color: #ffffff;
        }
        QCheckBox:hover {
            color: #4db6ac;
            background: rgba(77, 182, 172, 0.05);
            border-radius: 4px;
            padding: 2px;
        }
        QRadioButton::indicator {
            width: 18px; height: 18px;
            border: 2px solid #80cbc4;
            border-radius: 10px;
            background: transparent;
        }
        QRadioButton::indicator:checked {
            background: #009688;
            border-color: #009688;
        }
        QRadioButton::indicator:hover {
            border-color: #26a69a;
            border-width: 3px;
        }
        """)
    except ImportError:
        pass
    while current_exit_code == 1207:
        language=conf.read("kmain","language")
        apply_app_language(app, language)
        kmain = kmainForm()
        kmain.show()
        current_exit_code=app.exec_()
        kmain=None
    sys.exit(current_exit_code)
