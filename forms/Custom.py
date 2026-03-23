import json
import os

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QAction, QDialog, QHeaderView, QMenu, QMessageBox, QTableWidgetItem

from ui.custom import Ui_CustomDialog
from utils.AiUtil import AiService, AiWorker
from utils.IniUtil import IniConfig


class customForm(QDialog, Ui_CustomDialog):
    def __init__(self, parent=None):
        super(customForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.95)
        self.config = IniConfig()
        self._translate = QtCore.QCoreApplication.translate
        self.header = [self._translate("customForm", "别名"), self._translate("customForm", "文件名"), self._translate("customForm", "备注")]
        self.aiService = AiService()
        self.aiWorker = None
        self.customs = []
        self.customHooks = []

        self.initSmartUi()

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
        self.refreshTranslations()

    def isEnglish(self):
        return (self.config.read("kmain", "language") or "China") == "English"

    def trText(self, zh_text, en_text):
        return en_text if self.isEnglish() else zh_text

    def initSmartUi(self):
        self.resize(1360, 940)
        self.setMinimumSize(1160, 780)
        self.topSplitter.setChildrenCollapsible(False)
        self.topSplitter.setStretchFactor(0, 5)
        self.topSplitter.setStretchFactor(1, 4)
        self.topSplitter.setSizes([720, 560])
        self.txtAiPrompt.setMinimumHeight(110)
        self.txtJsData.setMinimumHeight(280)
        self.txtJsData.setPlaceholderText(self._translate("customForm", "在这里编辑或让 AI 生成符合 custom 模块格式的 Frida Hook 脚本..."))
        self.tabCustomList.setAlternatingRowColors(True)
        self.tabCustomHookList.setAlternatingRowColors(True)
        self.tabCustomList.verticalHeader().setVisible(False)
        self.tabCustomHookList.verticalHeader().setVisible(False)
        self.aiButtonLayout.setSpacing(10)
        self.actionLayout.setSpacing(10)
        for button in [self.btnAiPromptTemplate, self.btnAiGenerate, self.btnClear, self.btnSubmit]:
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(40)
            button.setMinimumWidth(160)
        self.setStyleSheet("""
        QDialog {
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
        QPushButton:disabled {
            background: #eef1f4;
            color: #93a0b0;
            border-color: #d6dce5;
        }
        QLineEdit, QPlainTextEdit, QTableWidget {
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
        QLabel {
            color: #30485f;
        }
        """)

    def refreshAiState(self):
        available = self.aiService.is_available()
        self.btnAiGenerate.setEnabled(available)
        if available:
            self.labAiStatus.setText(self.trText("AI 状态：已配置，可生成 Hook 脚本", "AI status: configured and ready to generate hook scripts"))
        else:
            self.labAiStatus.setText(self.trText("AI 状态：", "AI status: ") + self.aiService.missing_message("English" if self.isEnglish() else "China"))

    def refreshTranslations(self):
        self.retranslateUi(self)
        self.setWindowTitle(self.trText("自定义", "Custom"))
        self.groupBox.setTitle(self.trText("脚本仓库", "Script library"))
        self.groupBox_3.setTitle(self.trText("当前使用脚本", "Active hook scripts"))
        self.groupBox_2.setTitle(self.trText("脚本编辑器", "Script editor"))
        self.groupBox_4.setTitle(self.trText("操作提示", "Usage tips"))
        self.aiGroup.setTitle(self.trText("AI 助手", "AI Assistant"))
        self.label.setText(self.trText("脚本别名：", "Alias:"))
        self.label_6.setText(self.trText("脚本名：", "Filename:"))
        self.label_5.setText(self.trText("备注：", "Remark:"))
        self.label_2.setText(self.trText("Hook 脚本：", "Hook script:"))
        self.btnAiPromptTemplate.setText(self.trText("填充提示词模板", "Fill prompt template"))
        self.btnAiGenerate.setText(self.trText("AI 生成 Hook", "AI Generate Hook"))
        self.btnClear.setText(self.trText("清空", "Clear"))
        self.btnSubmit.setText(self.trText("保存脚本", "Save script"))
        self.label_3.setText(self.trText("双击左侧脚本可进入编辑；右键可删除或加入当前 Hook 列表。关闭窗口后，右侧列表会同步到主界面的 Hook 列表。", "Double-click a script on the left to edit it. Right-click to delete it or add it to the current hook list. After closing the dialog, the right-side list syncs back to the main window."))
        self.label_4.setText(self.trText("AI 功能会按照 fridaUiTools custom 模块格式生成脚本；未配置 API Key / Host / 模型时，将自动禁用 AI 按钮。", "AI features generate scripts in the fridaUiTools custom-module format. If API Key / Host / Model is missing, AI buttons stay disabled automatically."))
        self.header = [self.trText("别名", "Alias"), self.trText("文件名", "Filename"), self.trText("备注", "Remark")]
        self.txtAiPrompt.setPlaceholderText(self.trText("例如：帮我 hook okhttp3 请求和响应，打印 URL、Header、Body，并保留 call_funs.demo 作为主动调用样例。", "Example: hook okhttp3 requests and responses, print URL, headers and body, and keep call_funs.demo as an active invocation example."))
        self.txtJsData.setPlaceholderText(self.trText("在这里编辑或让 AI 生成符合 custom 模块格式的 Frida Hook 脚本...", "Edit here or let AI generate a Frida hook script that matches the custom-module format..."))
        self.updateTabCustom()
        self.updateTabCustomHook()
        self.refreshAiState()

    def fillPromptTemplate(self):
        template = self.trText(
            "目标应用/场景：\n要 hook 的类 / 方法 / so：\n预期行为：\n需要打印的内容：参数 / 返回值 / 堆栈 / URL / Header / Body\n是否需要 call_funs 主动调用函数：\n兼容性要求或注意事项：\n",
            "Target app / scenario:\nClass / method / so to hook:\nExpected behavior:\nData to print: args / return value / stack / URL / headers / body\nNeed active invocation through call_funs?:\nCompatibility requirements or cautions:\n"
        )
        self.txtAiPrompt.setPlainText(template)

    def generateAiScript(self):
        prompt = self.txtAiPrompt.toPlainText().strip()
        if not self.aiService.is_available():
            self.refreshAiState()
            QMessageBox().information(self, "hint", self.aiService.missing_message("English" if self.isEnglish() else "China"))
            return
        if not prompt:
            QMessageBox().information(self, "hint", self.trText("请先填写 AI 需求说明", "Please describe your AI hook requirement first"))
            return
        self.btnAiGenerate.setEnabled(False)
        self.btnAiGenerate.setText(self.trText("生成中...", "Generating..."))
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
        self.btnAiGenerate.setText(self.trText("AI 生成 Hook", "AI Generate Hook"))
        if not self.txtBak.text().strip():
            self.txtBak.setText(self.trText("AI 生成脚本", "AI generated script"))
        QMessageBox().information(self, "hint", self.trText("AI 脚本生成完成，已回填到编辑器", "AI hook script generated and inserted into the editor"))

    def onAiScriptFailed(self, message):
        self.btnAiGenerate.setEnabled(self.aiService.is_available())
        self.btnAiGenerate.setText(self.trText("AI 生成 Hook", "AI Generate Hook"))
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