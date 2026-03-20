import json
import os

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QAction, QDialog, QHeaderView, QMenu, QMessageBox, QTableWidgetItem

from ui.custom import Ui_CustomDialog
from utils.AiUtil import AiService, AiWorker


class customForm(QDialog, Ui_CustomDialog):
    def __init__(self, parent=None):
        super(customForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.95)
        self._translate = QtCore.QCoreApplication.translate
        self.header = [self._translate("customForm", "别名"), self._translate("customForm", "文件名"), self._translate("customForm", "备注")]
        self.aiService = AiService()
        self.aiWorker = None
        self.customs = []
        self.customHooks = []

        self.btnSubmit.clicked.connect(self.submit)
        self.btnClear.clicked.connect(self.UiClear)
        self.btnAiPromptTemplate.clicked.connect(self.fillPromptTemplate)
        self.btnAiGenerate.clicked.connect(self.generateAiScript)
        self.txtJsName.textChanged.connect(self.jsNameChanged)

        self.tabCustomList.setColumnCount(3)
        self.tabCustomList.setHorizontalHeaderLabels(self.header)
        self.tabCustomList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabCustomList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabCustomList.customContextMenuRequested[QPoint].connect(self.cusTomRightMenuShow)
        self.tabCustomList.itemDoubleClicked.connect(self.cusTomDoubleClicked)

        self.tabCustomHookList.setColumnCount(3)
        self.tabCustomHookList.setHorizontalHeaderLabels(self.header)
        self.tabCustomHookList.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabCustomHookList.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabCustomHookList.customContextMenuRequested[QPoint].connect(self.cusTomHookRightMenuShow)

        self.initData()
        self.refreshAiState()

    def refreshAiState(self):
        available = self.aiService.is_available()
        self.btnAiGenerate.setEnabled(available)
        if available:
            self.labAiStatus.setText(self._translate("customForm", "AI 状态：已配置，可生成 Hook 脚本"))
        else:
            self.labAiStatus.setText(self._translate("customForm", "AI 状态：") + self.aiService.missing_message())

    def fillPromptTemplate(self):
        template = (
            "目标应用/场景：\n"
            "要 hook 的类 / 方法 / so：\n"
            "预期行为：\n"
            "需要打印的内容：参数 / 返回值 / 堆栈 / URL / Header / Body\n"
            "是否需要 call_funs 主动调用函数：\n"
            "兼容性要求或注意事项：\n"
        )
        self.txtAiPrompt.setPlainText(template)

    def generateAiScript(self):
        prompt = self.txtAiPrompt.toPlainText().strip()
        if not self.aiService.is_available():
            self.refreshAiState()
            QMessageBox().information(self, "hint", self.aiService.missing_message())
            return
        if not prompt:
            QMessageBox().information(self, "hint", self._translate("customForm", "请先填写 AI 需求说明"))
            return
        self.btnAiGenerate.setEnabled(False)
        self.btnAiGenerate.setText(self._translate("customForm", "生成中..."))
        self.aiWorker = AiWorker(
            self.aiService.generate_hook_script,
            prompt,
            self.txtJsName.text().strip(),
            self.txtBak.text().strip(),
        )
        self.aiWorker.success.connect(self.onAiScriptGenerated)
        self.aiWorker.error.connect(self.onAiScriptFailed)
        self.aiWorker.start()

    def onAiScriptGenerated(self, script):
        self.txtJsData.setPlainText(script)
        self.btnAiGenerate.setEnabled(True)
        self.btnAiGenerate.setText(self._translate("customForm", "AI 生成 Hook"))
        if not self.txtBak.text().strip():
            self.txtBak.setText(self._translate("customForm", "AI 生成脚本"))
        QMessageBox().information(self, "hint", self._translate("customForm", "AI 脚本生成完成，已回填到编辑器"))

    def onAiScriptFailed(self, message):
        self.btnAiGenerate.setEnabled(self.aiService.is_available())
        self.btnAiGenerate.setText(self._translate("customForm", "AI 生成 Hook"))
        QMessageBox().information(self, "hint", message)

    def cusTomDoubleClicked(self, item):
        data = self.customs[item.row()]
        path = "./custom/" + data["fileName"]
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as jsfile:
                jsdata = jsfile.read()
                self.txtJsData.setPlainText(jsdata)
                self.txtJsName.setText(data["name"])
                self.txtJsFileName.setText(data["fileName"])
                self.txtBak.setText(data["bak"])
        else:
            QMessageBox().information(self, "hint", self._translate("customForm", "文件 ") + data["fileName"] + self._translate("customForm", " 不存在"))

    def UiClear(self):
        self.txtBak.clear()
        self.txtJsName.clear()
        self.txtJsFileName.clear()
        self.txtJsData.setPlainText("")
        self.txtAiPrompt.setPlainText("")

    def cusTomRightMenuShow(self):
        rightMenu = QMenu(self.tabCustomList)
        removeAction = QAction(self._translate("customForm", "删除"), self, triggered=self.customRemove)
        addAction = QAction(self._translate("customForm", "添加到hook"), self, triggered=self.customAdd)
        rightMenu.addAction(removeAction)
        rightMenu.addAction(addAction)
        rightMenu.exec_(QCursor.pos())

    def cusTomHookRightMenuShow(self):
        rightMenu = QMenu(self.tabCustomHookList)
        removeAction = QAction(self._translate("customForm", "删除"), self, triggered=self.hooksRemove)
        rightMenu.addAction(removeAction)
        rightMenu.exec_(QCursor.pos())

    def jsNameChanged(self):
        name = self.txtJsName.text().strip()
        if name:
            self.txtJsFileName.setText(name + ".js")

    def customAdd(self):
        for item in self.tabCustomList.selectedItems():
            if item.row() < len(self.customs):
                exists = False
                for cdata in self.customHooks:
                    if cdata["fileName"] == self.customs[item.row()]["fileName"]:
                        exists = True
                        break
                if exists:
                    QMessageBox().information(self, "hint", self._translate("customForm", "文件") + self.customs[item.row()]["fileName"] + self._translate("customForm", ",已添加到hook,不能重复添加"))
                    continue
                self.customHooks.append(self.customs[item.row()])
                break
        self.updateTabCustomHook()

    def customRemove(self):
        removed_file = ""
        for item in self.tabCustomList.selectedItems():
            if item.row() < len(self.customs):
                removed_file = self.customs[item.row()]["fileName"]
                path = "./custom/" + removed_file
                if os.path.exists(path):
                    os.remove(path)
                self.customs.remove(self.customs[item.row()])
                break
        if removed_file:
            self.customHooks = [hook for hook in self.customHooks if hook["fileName"] != removed_file]
        self.save()
        self.updateTabCustom()
        self.updateTabCustomHook()

    def hooksRemove(self):
        for item in self.tabCustomHookList.selectedItems():
            if item.row() < len(self.customHooks):
                self.customHooks.remove(self.customHooks[item.row()])
                break
        self.updateTabCustomHook()

    def initData(self):
        self.customs.clear()
        customPath = "./custom/customs.txt"
        customs = []
        if os.path.exists(customPath) is False:
            self.updateTabCustom()
            self.updateTabCustomHook()
            return
        with open(customPath, "r", encoding="utf-8") as costomFile:
            customData = costomFile.read()
            try:
                if len(customData) > 0:
                    customs = json.loads(customData)
            except Exception:
                customs = []
        for item in customs:
            if os.path.exists("./custom/" + item["fileName"]):
                self.customs.append(item)
        valid_files = {item["fileName"] for item in self.customs}
        self.customHooks = [hook for hook in self.customHooks if hook["fileName"] in valid_files]
        self.updateTabCustom()
        self.updateTabCustomHook()

    def updateTabCustom(self):
        self.tabCustomList.clear()
        self.tabCustomList.setColumnCount(3)
        self.tabCustomList.setHorizontalHeaderLabels(self.header)
        self.tabCustomList.setRowCount(len(self.customs))
        for line, item in enumerate(self.customs):
            self.tabCustomList.setItem(line, 0, QTableWidgetItem(item["name"]))
            self.tabCustomList.setItem(line, 1, QTableWidgetItem(item["fileName"]))
            self.tabCustomList.setItem(line, 2, QTableWidgetItem(item["bak"]))

    def updateTabCustomHook(self):
        self.tabCustomHookList.clear()
        self.tabCustomHookList.setColumnCount(3)
        self.tabCustomHookList.setHorizontalHeaderLabels(self.header)
        self.tabCustomHookList.setRowCount(len(self.customHooks))
        for line, item in enumerate(self.customHooks):
            self.tabCustomHookList.setItem(line, 0, QTableWidgetItem(item["name"]))
            self.tabCustomHookList.setItem(line, 1, QTableWidgetItem(item["fileName"]))
            self.tabCustomHookList.setItem(line, 2, QTableWidgetItem(item["bak"]))

    def save(self):
        with open("./custom/customs.txt", "w", encoding="utf-8") as customFile:
            customFile.write(json.dumps(self.customs, ensure_ascii=False))

    def submit(self):
        if len(self.txtJsName.text().strip()) <= 0:
            QMessageBox().information(self, "hint", self._translate("customForm", "别名不能为空"))
            return
        if len(self.txtJsData.toPlainText().strip()) <= 0:
            QMessageBox().information(self, "hint", self._translate("customForm", "脚本不能为空"))
            return
        data = {
            "name": self.txtJsName.text().strip(),
            "fileName": self.txtJsFileName.text().strip(),
            "bak": self.txtBak.text().strip(),
        }
        if len(data["fileName"]) <= 0:
            data["fileName"] = data["name"] + ".js"
            self.txtJsFileName.setText(data["fileName"])
        savepath = "./custom/" + data["fileName"]
        with open(savepath, "w", encoding="utf-8") as saveFile:
            saveFile.write(self.txtJsData.toPlainText())
        updated = False
        for idx in range(len(self.customs)):
            if self.customs[idx]["fileName"] == data["fileName"]:
                self.customs[idx] = data
                updated = True
                break
        if updated is False:
            self.customs.append(data)
        self.save()
        self.updateTabCustom()