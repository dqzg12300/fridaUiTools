import json
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor, QColor, QFont
from PyQt5.QtWidgets import QAction, QDialog, QHeaderView, QMenu, QMessageBox, QTableWidgetItem

try:
    from PyQt5.Qsci import QsciScintilla, QsciLexerJavaScript
except ImportError:
    QsciScintilla = None
    QsciLexerJavaScript = None

from ui.custom import Ui_CustomDialog
from utils.AiUtil import AiService, AiWorker
from utils.IniUtil import IniConfig


class customForm(QDialog, Ui_CustomDialog):
    def __init__(self, parent=None):
        super(customForm, self).__init__(parent)
        self.setupUi(self)
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

    def bundledTemplateRenameMap(self):
        return {
            "样例模板1.js": {"legacy": {"样例模板1"}, "name": "Sample Template 1"},
            "样例模板2.js": {"legacy": {"样例模板2"}, "name": "Sample Template 2"},
            "函数重放样例模板1.js": {"legacy": {"函数重放样例模板1"}, "name": "Function Replay Sample 1"},
            "类型转json打印模版.js": {"legacy": {"类型转json打印模版"}, "name": "Type To JSON Printer"},
            "GumTrace_trace_sample.js": {"legacy": {"GumTrace trace 样例"}, "name": "GumTrace Trace Sample"},
            "GumTrace_offset_auto_trace.js": {"legacy": {"GumTrace 偏移自动追踪"}, "name": "GumTrace Offset Auto Trace"},
            "GumTrace_export_trigger_trace.js": {"legacy": {"GumTrace 导出符号追踪"}, "name": "GumTrace Export Trigger Trace"},
            "javaEnc.js": {"legacy": {"Java 加解密(全函数)"}, "name": "Java Crypto Hooks"},
            "DroidSSLUnpinning.js": {"legacy": {"SSL Pinning 旁路"}, "name": "SSL Pinning Bypass"},
            "hookEvent.js": {"legacy": {"控件点击事件"}, "name": "UI Click Events"},
            "hook_RegisterNatives.js": {"legacy": {"RegisterNatives 监控"}, "name": "RegisterNatives Monitor"},
            "hook_artmethod.js": {"legacy": {"ArtMethod 监控"}, "name": "ArtMethod Monitor"},
            "hook_art.js": {"legacy": {"libart 关键函数"}, "name": "libart Key Functions"},
            "anti_debug.js": {"legacy": {"一键反调试"}, "name": "One-Click Anti-Debug"},
            "root_bypass.js": {"legacy": {"Root 检测绕过"}, "name": "Root Detection Bypass"},
            "shared_prefs_watch.js": {"legacy": {"SharedPrefs 监控"}, "name": "SharedPrefs Monitor"},
        }

    def normalizeBundledTemplateNames(self):
        rename_map = self.bundledTemplateRenameMap()
        changed = False
        for item in self.customs:
            file_name = item.get("fileName", "")
            rename_rule = rename_map.get(file_name)
            if rename_rule is None:
                continue
            current_name = item.get("name", "")
            if current_name in rename_rule["legacy"]:
                item["name"] = rename_rule["name"]
                changed = True
        return changed

    def pinnedTemplateSortKey(self, item):
        try:
            return (0, self.pinnedTemplateOrderValue(item), item.get("name", "").lower(), item.get("fileName", "").lower())
        except Exception:
            return (1, item.get("name", "").lower(), item.get("fileName", "").lower())

    def pinnedTemplateOrderValue(self, item, default=-1):
        try:
            return int(item.get("pinOrder", default))
        except Exception:
            return default

    def normalizePinnedTemplateOrders(self):
        changed = False
        pinned = [item for item in self.customs if item.get("pinToMain")]
        pinned.sort(key=self.pinnedTemplateSortKey)
        for index, item in enumerate(pinned):
            if item.get("pinOrder") != index:
                item["pinOrder"] = index
                changed = True
        for item in self.customs:
            if not item.get("pinToMain") and item.get("pinOrder", -1) != -1:
                item["pinOrder"] = -1
                changed = True
        return changed

    def nextPinnedTemplateOrder(self):
        orders = []
        for item in self.customs:
            if not item.get("pinToMain"):
                continue
            orders.append(self.pinnedTemplateOrderValue(item))
        return (max(orders) + 1) if orders else 0

    def setPinnedTemplateOrder(self, ordered_file_names):
        if not isinstance(ordered_file_names, list):
            return
        order_map = {}
        for file_name in ordered_file_names:
            if file_name and file_name not in order_map:
                order_map[file_name] = len(order_map)
        next_order = len(order_map)
        remaining = [item for item in self.customs if item.get("pinToMain") and item.get("fileName") not in order_map]
        remaining.sort(key=self.pinnedTemplateSortKey)
        for item in remaining:
            file_name = item.get("fileName", "")
            if file_name:
                order_map[file_name] = next_order
                next_order += 1
        changed = False
        for item in self.customs:
            file_name = item.get("fileName", "")
            if item.get("pinToMain"):
                new_order = order_map.get(file_name, next_order)
                if item.get("pinOrder") != new_order:
                    item["pinOrder"] = new_order
                    changed = True
            elif item.get("pinOrder", -1) != -1:
                item["pinOrder"] = -1
                changed = True
        if changed:
            self.save()
            self.updateTabCustom()

    def initSmartUi(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.resize(1320, 820)
        self.setMinimumSize(1160, 720)
        self.mainSplitter.setChildrenCollapsible(False)
        self.mainSplitter.setStretchFactor(0, 7)
        self.mainSplitter.setStretchFactor(1, 4)
        self.mainSplitter.setSizes([860, 440])
        self.topSplitter.setChildrenCollapsible(False)
        self.topSplitter.setStretchFactor(0, 5)
        self.topSplitter.setStretchFactor(1, 4)
        self.topSplitter.setSizes([320, 240])
        self.groupBox_2.setMinimumWidth(720)
        self.sidebarWidget.setMinimumWidth(360)
        self.groupBox.setMinimumHeight(260)
        self.groupBox_3.setMinimumHeight(220)
        self.groupBox_4.setMaximumHeight(150)
        self.txtAiPrompt.setMinimumHeight(110)
        self.groupBox_2.setObjectName("editorPanel")
        self.groupBox_2.setTitle("")
        self.editorLayout.setContentsMargins(14, 14, 14, 14)
        self.editorLayout.setSpacing(10)
        self.labEditorSectionTitle = QtWidgets.QLabel(self.groupBox_2)
        self.labEditorSectionTitle.setObjectName("editorSectionTitle")
        self.editorLayout.insertWidget(0, self.labEditorSectionTitle)
        self.aiGroup.setObjectName("aiAssistantPanel")
        self.aiGroup.setTitle("")
        self.aiGroup.setFlat(True)
        self.aiLayout.setContentsMargins(0, 0, 0, 0)
        self.aiLayout.setSpacing(8)
        self.labAiSectionTitle = QtWidgets.QLabel(self.aiGroup)
        self.labAiSectionTitle.setObjectName("assistantSectionTitle")
        self.aiLayout.insertWidget(0, self.labAiSectionTitle)
        self.labAiStatus.setObjectName("sectionCaption")
        self.setupScriptEditor()
        self.tabCustomList.setAlternatingRowColors(True)
        self.tabCustomHookList.setAlternatingRowColors(True)
        self.tabCustomList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabCustomHookList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tabCustomList.setMinimumHeight(220)
        self.tabCustomHookList.setMinimumHeight(180)
        self.tabCustomList.verticalHeader().setVisible(False)
        self.tabCustomHookList.verticalHeader().setVisible(False)
        self.tabCustomList.verticalHeader().setDefaultSectionSize(28)
        self.tabCustomHookList.verticalHeader().setDefaultSectionSize(28)
        self.aiButtonLayout.setSpacing(10)
        self.actionLayout.setSpacing(10)
        for button in [self.btnAiPromptTemplate, self.btnAiGenerate]:
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(36)
        for button in [self.btnAiPromptTemplate, self.btnAiGenerate]:
            button.setMinimumHeight(40)
            button.setMinimumWidth(150)
        self.txtAiPrompt.setMinimumHeight(170)

        self.editorHeaderLayout = QtWidgets.QHBoxLayout()
        self.editorHeaderLayout.setContentsMargins(0, 0, 0, 0)
        self.editorHeaderLayout.setSpacing(10)
        self.editorLayout.removeWidget(self.label_2)
        self.label_2.hide()

        self.editorHeaderForm = QtWidgets.QGridLayout()
        self.editorHeaderForm.setContentsMargins(0, 0, 0, 0)
        self.editorHeaderForm.setHorizontalSpacing(8)
        self.editorHeaderForm.setVerticalSpacing(4)
        self.formLayout.removeWidget(self.label)
        self.formLayout.removeWidget(self.txtJsName)
        self.formLayout.removeWidget(self.label_6)
        self.formLayout.removeWidget(self.txtJsFileName)
        self.formLayout.removeWidget(self.label_5)
        self.formLayout.removeWidget(self.txtBak)
        self.editorHeaderForm.addWidget(self.label, 0, 0, 1, 1)
        self.editorHeaderForm.addWidget(self.txtJsName, 0, 1, 1, 1)
        self.editorHeaderForm.addWidget(self.label_6, 0, 2, 1, 1)
        self.editorHeaderForm.addWidget(self.txtJsFileName, 0, 3, 1, 1)
        self.editorHeaderForm.addWidget(self.label_5, 0, 4, 1, 1)
        self.editorHeaderForm.addWidget(self.txtBak, 0, 5, 1, 1)
        self.editorHeaderForm.setColumnStretch(1, 3)
        self.editorHeaderForm.setColumnStretch(3, 3)
        self.editorHeaderForm.setColumnStretch(5, 4)
        self.editorHeaderLayout.addLayout(self.editorHeaderForm, 1)

        self.editorLayout.removeItem(self.actionLayout)
        self.editorHeaderLayout.addWidget(self.btnClear)
        self.editorHeaderLayout.addWidget(self.btnSubmit)
        self.editorLayout.insertLayout(self.editorLayout.indexOf(self.txtJsData), self.editorHeaderLayout)

        for button in [self.btnClear, self.btnSubmit]:
            button.setCursor(Qt.PointingHandCursor)
            button.setMinimumHeight(32)
            button.setMinimumWidth(120)
        self._applyFallbackTheme()
        self.applyEditorPanelStyles()

    def _applyFallbackTheme(self):
        import sys
        if 'qt_material' in sys.modules:
            return
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
        QLabel#editorSectionTitle {
            color: #16324a;
            font-size: 16px;
            font-weight: 700;
            padding-bottom: 2px;
        }
        QLabel#assistantSectionTitle {
            color: #16324a;
            font-size: 13px;
            font-weight: 700;
            padding-bottom: 2px;
        }
        QLabel#sectionCaption {
            color: #60738a;
        }
        """)

    def applyEditorPanelStyles(self):
        self.groupBox_2.setStyleSheet("""
        QGroupBox#editorPanel {
            margin-top: 0px;
            padding-top: 0px;
        }
        QGroupBox#editorPanel::title {
            subcontrol-origin: margin;
            width: 0px;
            height: 0px;
            padding: 0px;
        }
        QGroupBox#aiAssistantPanel {
            border: none;
            margin-top: 0px;
            padding-top: 0px;
            background: transparent;
        }
        QGroupBox#aiAssistantPanel::title {
            subcontrol-origin: margin;
            width: 0px;
            height: 0px;
            padding: 0px;
        }
        QLabel#editorSectionTitle {
            font-weight: 700;
        }
        QLabel#assistantSectionTitle {
            font-weight: 700;
        }
        """)

    def setupScriptEditor(self):
        placeholder = self._translate("customForm", "在这里编辑或让 AI 生成符合 custom 模块格式的 Frida Hook 脚本...")
        if QsciScintilla is None:
            self.txtJsData.setMinimumHeight(360)
            self.txtJsData.setPlaceholderText(placeholder)
            self.scriptEditorUsesQsci = False
            return

        old_editor = self.txtJsData
        editor = QsciScintilla(self.groupBox_2)
        editor.setObjectName("txtJsData")
        editor.setMinimumHeight(360)
        editor.setUtf8(True)
        editor.setWrapMode(QsciScintilla.WrapNone)
        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(4)
        editor.setIndentationWidth(4)
        editor.setAutoIndent(True)
        editor.setBackspaceUnindents(True)
        editor.setTabIndents(True)
        editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        editor.setFolding(QsciScintilla.BoxedTreeFoldStyle)
        editor.setMarginsForegroundColor(QColor("#7a8a9a"))
        editor.setMarginsBackgroundColor(QColor("#263238"))
        editor.setMarginType(0, QsciScintilla.NumberMargin)
        editor.setMarginLineNumbers(0, True)
        editor.setMarginWidth(0, "0000")
        editor.setCaretLineVisible(True)
        editor.setCaretLineBackgroundColor(QColor("#2c3b41"))
        editor.setMatchedBraceBackgroundColor(QColor("#3d5266"))
        editor.setMatchedBraceForegroundColor(QColor("#80cbc4"))
        editor.setUnmatchedBraceBackgroundColor(QColor("#5c3030"))
        editor.setUnmatchedBraceForegroundColor(QColor("#ff6b6b"))
        editor.setPaper(QColor("#263238"))
        editor.setColor(QColor("#cfd8dc"))
        editor.setSelectionBackgroundColor(QColor("#546e7a"))
        editor.setSelectionForegroundColor(QColor("#ffffff"))
        font = QFont("DejaVu Sans Mono")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(10)
        editor.setFont(font)
        editor.setMarginsFont(font)
        lexer = QsciLexerJavaScript(editor)
        lexer.setDefaultFont(font)
        # 设置深色主题的语法高亮颜色
        lexer.setDefaultPaper(QColor("#263238"))
        lexer.setDefaultColor(QColor("#cfd8dc"))
        lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.Keyword)  # 关键字 - 绿色
        lexer.setColor(QColor("#f07178"), QsciLexerJavaScript.KeywordSet2)  # 次要关键字 - 红色
        lexer.setColor(QColor("#c792ea"), QsciLexerJavaScript.Number)  # 数字 - 紫色
        lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.DoubleQuotedString)  # 双引号字符串 - 绿色
        lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.SingleQuotedString)  # 单引号字符串 - 绿色
        lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.Comment)  # 注释 - 灰色
        lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.CommentLine)  # 单行注释 - 灰色
        lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.CommentDoc)  # 文档注释 - 灰色
        lexer.setColor(QColor("#82aaff"), QsciLexerJavaScript.Identifier)  # 标识符 - 蓝色
        lexer.setColor(QColor("#89ddff"), QsciLexerJavaScript.Operator)  # 操作符 - 青色
        lexer.setColor(QColor("#ffcb6b"), QsciLexerJavaScript.UnclosedString)  # 未闭合字符串 - 黄色
        editor.setLexer(lexer)
        editor.setText(old_editor.toPlainText())
        old_editor.hide()
        self.editorLayout.replaceWidget(old_editor, editor)
        old_editor.deleteLater()
        self.txtJsData = editor
        self.scriptEditorUsesQsci = True
        self.txtJsData.setToolTip(placeholder)

    def editorSetText(self, text):
        if getattr(self, "scriptEditorUsesQsci", False):
            self.txtJsData.setText(text)
        else:
            self.txtJsData.setPlainText(text)

    def editorGetText(self):
        if getattr(self, "scriptEditorUsesQsci", False):
            return self.txtJsData.text()
        return self.txtJsData.toPlainText()

    def editorAppendText(self, text):
        if getattr(self, "scriptEditorUsesQsci", False):
            self.txtJsData.append(text)
            self.txtJsData.ensureLineVisible(self.txtJsData.lines() - 1)
            return
        cursor = self.txtJsData.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.txtJsData.setTextCursor(cursor)
        self.txtJsData.ensureCursorVisible()

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
        self.groupBox_2.setTitle("")
        self.groupBox_4.setTitle(self.trText("操作提示", "Usage tips"))
        self.aiGroup.setTitle("")
        self.labEditorSectionTitle.setText(self.trText("脚本编辑器", "Script editor"))
        self.labAiSectionTitle.setText(self.trText("AI 助手", "AI Assistant"))
        self.label.setText(self.trText("脚本别名：", "Alias:"))
        self.label_6.setText(self.trText("脚本名：", "Filename:"))
        self.label_5.setText(self.trText("备注：", "Remark:"))
        self.label_2.setText(self.trText("Hook 脚本：", "Hook script:"))
        self.btnAiPromptTemplate.setText(self.trText("填充提示词模板", "Fill prompt template"))
        self.btnAiGenerate.setText(self.trText("AI 生成 Hook", "AI Generate Hook"))
        self.btnClear.setText(self.trText("清空", "Clear"))
        self.btnSubmit.setText(self.trText("保存脚本", "Save script"))
        self.label_3.setText(self.trText("双击脚本仓库中的脚本可进入编辑；右键可删除或加入当前 Hook 列表。关闭窗口后，当前使用脚本会同步到主界面的 Hook 列表。", "Double-click a script in the library to edit it. Right-click to delete it or add it to the current hook list. After closing the dialog, active hook scripts sync back to the main window."))
        self.label_4.setText(self.trText("AI 功能会按照 fridaUiTools custom 模块格式生成脚本；未配置 API Key / Host / 模型时，将自动禁用 AI 按钮。", "AI features generate scripts in the fridaUiTools custom-module format. If API Key / Host / Model is missing, AI buttons stay disabled automatically."))
        self.header = [self.trText("别名", "Alias"), self.trText("文件名", "Filename"), self.trText("备注", "Remark")]
        self.txtAiPrompt.setPlaceholderText(self.trText("例如：帮我 hook okhttp3 请求和响应，打印 URL、Header、Body，并保留 call_funs.demo 作为主动调用样例。", "Example: hook okhttp3 requests and responses, print URL, headers and body, and keep call_funs.demo as an active invocation example."))
        if getattr(self, "scriptEditorUsesQsci", False):
            self.txtJsData.setToolTip(self.trText("在这里编辑或让 AI 生成符合 custom 模块格式的 Frida Hook 脚本...", "Edit here or let AI generate a Frida hook script that matches the custom-module format..."))
        else:
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
        self.editorSetText("")
        self.aiWorker = AiWorker(
            self.aiService.generate_hook_script,
            prompt,
            self.txtJsName.text().strip(),
            self.txtBak.text().strip(),
            stream_handler=self.aiService.generate_hook_script_stream,
        )
        self.aiWorker.chunk.connect(self.onAiScriptChunk)
        self.aiWorker.success.connect(self.onAiScriptGenerated)
        self.aiWorker.error.connect(self.onAiScriptFailed)
        self.aiWorker.start()

    def onAiScriptChunk(self, chunk):
        self.editorAppendText(chunk)

    def onAiScriptGenerated(self, script):
        self.editorSetText(script)
        self.btnAiGenerate.setEnabled(True)
        self.btnAiGenerate.setText(self.trText("AI 生成 Hook", "AI Generate Hook"))
        if not self.txtBak.text().strip():
            self.txtBak.setText(self.trText("AI 生成脚本", "AI generated script"))
        QMessageBox().information(self, "hint", self.trText("AI 脚本生成完成，已回填到编辑器", "AI hook script generated and inserted into the editor"))

    def onAiScriptFailed(self, message):
        self.btnAiGenerate.setEnabled(self.aiService.is_available())
        self.btnAiGenerate.setText(self.trText("AI 生成 Hook", "AI Generate Hook"))
        QMessageBox().information(self, "hint", message)

    def refreshPinnedTemplatesOnParent(self):
        if self.parent() is not None and hasattr(self.parent(), "refreshPinnedCustomTemplates"):
            self.parent().refreshPinnedCustomTemplates()

    def cusTomDoubleClicked(self, item):
        data = self.customs[item.row()]
        path = "./custom/" + data["fileName"]
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as jsfile:
                jsdata = jsfile.read()
                self.editorSetText(jsdata)
                self.txtJsName.setText(data["name"])
                self.txtJsFileName.setText(data["fileName"])
                self.txtBak.setText(data["bak"])
        else:
            QMessageBox().information(self, "hint", self._translate("customForm", "文件 ") + data["fileName"] + self._translate("customForm", " 不存在"))

    def UiClear(self):
        self.txtBak.clear()
        self.txtJsName.clear()
        self.txtJsFileName.clear()
        self.editorSetText("")
        self.txtAiPrompt.setPlainText("")

    def cusTomRightMenuShow(self):
        rightMenu = QMenu(self.tabCustomList)
        removeAction = QAction(self._translate("customForm", "删除"), self, triggered=self.customRemove)
        addAction = QAction(self._translate("customForm", "添加到hook"), self, triggered=self.customAdd)
        pinAction = QAction(self._translate("customForm", "添加到主界面"), self, triggered=self.customPinToMain)
        unpinAction = QAction(self._translate("customForm", "从主界面移除"), self, triggered=self.customUnpinFromMain)

        rightMenu.addAction(removeAction)
        rightMenu.addAction(addAction)
        rightMenu.addSeparator()
        index = self._selectedCustomIndex()
        selected = self.customs[index] if 0 <= index < len(self.customs) else {}
        pinAction.setEnabled(not bool(selected.get("pinToMain")))
        unpinAction.setEnabled(bool(selected.get("pinToMain")))
        if selected.get("builtin"):
            removeAction.setEnabled(False)

        rightMenu.addAction(pinAction)
        rightMenu.addAction(unpinAction)
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

    def _selectedCustomIndex(self):
        for item in self.tabCustomList.selectedItems():
            if 0 <= item.row() < len(self.customs):
                return item.row()
        return -1

    def _setCustomPinToMain(self, index, pinned):
        if index < 0 or index >= len(self.customs):
            return
        self.customs[index]["pinToMain"] = bool(pinned)
        self.customs[index]["pinOrder"] = self.nextPinnedTemplateOrder() if pinned else -1
        self.normalizePinnedTemplateOrders()
        self.save()
        self.updateTabCustom()
        self.refreshPinnedTemplatesOnParent()
        QMessageBox().information(
            self,
            "hint",
            self.trText("已更新主界面固定状态", "Pinned state updated on main")
        )

    def customPinToMain(self):
        index = self._selectedCustomIndex()
        self._setCustomPinToMain(index, True)

    def customUnpinFromMain(self):
        index = self._selectedCustomIndex()
        self._setCustomPinToMain(index, False)

    def customRemove(self):
        removed_file = ""
        for item in self.tabCustomList.selectedItems():
            if item.row() < len(self.customs):
                target = self.customs[item.row()]
                if target.get("builtin"):
                    QMessageBox().information(self, "hint", self.trText("内置模板不支持删除", "Built-in templates cannot be deleted"))
                    return
                removed_file = target["fileName"]
                path = "./custom/" + removed_file
                if os.path.exists(path):
                    os.remove(path)
                self.customs.remove(target)
                break
        if removed_file:
            self.customHooks = [hook for hook in self.customHooks if hook["fileName"] != removed_file]
        self.normalizePinnedTemplateOrders()
        self.save()
        self.updateTabCustom()
        self.updateTabCustomHook()
        self.refreshPinnedTemplatesOnParent()

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
        changed = False
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
                if "pinToMain" not in item:
                    item["pinToMain"] = False
                self.customs.append(item)
        changed = self.normalizeBundledTemplateNames()
        changed = self.normalizePinnedTemplateOrders() or changed
        valid_files = {item["fileName"] for item in self.customs}
        self.customHooks = [hook for hook in self.customHooks if hook["fileName"] in valid_files]
        if changed:
            self.save()
        self.updateTabCustom()
        self.updateTabCustomHook()

    def updateTabCustom(self):
        self.tabCustomList.clear()
        self.tabCustomList.setColumnCount(3)
        self.tabCustomList.setHorizontalHeaderLabels(self.header)
        self.tabCustomList.setRowCount(len(self.customs))
        for line, item in enumerate(self.customs):
            name = item.get("name", "")
            if item.get("builtin"):
                name = "[内置] " + name if not self.isEnglish() else "[Builtin] " + name
            if item.get("pinToMain"):
                name = "[主界面] " + name if not self.isEnglish() else "[Pinned] " + name

            name_item = QTableWidgetItem(name)
            file_item = QTableWidgetItem(item.get("fileName", ""))
            bak_item = QTableWidgetItem(item.get("bak", ""))

            if item.get("pinToMain"):
                accent = QColor("#2563eb")
                name_item.setForeground(accent)
                file_item.setForeground(accent)
                bak_item.setForeground(accent)
                name_item.setData(Qt.UserRole, "pinned")

            self.tabCustomList.setItem(line, 0, name_item)
            self.tabCustomList.setItem(line, 1, file_item)
            self.tabCustomList.setItem(line, 2, bak_item)

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

    def scriptDataByFileName(self, file_name):
        for item in self.customs:
            if item.get("fileName") == file_name:
                return item
        return None

    def refreshCustomHookReferences(self):
        by_file = {item.get("fileName"): item for item in self.customs}
        refreshed = []
        for hook in self.customHooks:
            file_name = hook.get("fileName")
            if file_name in by_file:
                refreshed.append(by_file[file_name])
        self.customHooks = refreshed
        self.updateTabCustomHook()

    def ensureCustomHook(self, file_name):
        for hook in self.customHooks:
            if hook["fileName"] == file_name:
                return
        for item in self.customs:
            if item["fileName"] == file_name:
                self.customHooks.append(item)
                break
        self.updateTabCustomHook()

    def openCustomScript(self, file_name):
        for item in self.customs:
            if item["fileName"] == file_name:
                path = "./custom/" + file_name
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as jsfile:
                        self.editorSetText(jsfile.read())
                    self.txtJsName.setText(item["name"])
                    self.txtJsFileName.setText(item["fileName"])
                    self.txtBak.setText(item["bak"])
                return

    def upsertCustomScript(self, data, script_text, add_to_hook=False, show_message=True):
        if len(data.get("fileName", "").strip()) <= 0:
            data["fileName"] = data["name"] + ".js"
        existing = None
        for item in self.customs:
            if item.get("fileName") == data["fileName"]:
                existing = item
                break
        data.setdefault("pinToMain", bool(existing.get("pinToMain", False)) if existing else False)
        data.setdefault("pinOrder", self.pinnedTemplateOrderValue(existing) if existing else -1)
        data.setdefault("builtin", bool(existing.get("builtin", False)) if existing else False)
        data.setdefault("sourceHookKey", existing.get("sourceHookKey", "") if existing else "")
        save_path = "./custom/" + data["fileName"]
        with open(save_path, "w", encoding="utf-8") as save_file:
            save_file.write(script_text)
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
        self.refreshCustomHookReferences()
        if add_to_hook:
            self.ensureCustomHook(data["fileName"])
        self.refreshPinnedTemplatesOnParent()
        if show_message:
            QMessageBox().information(self, "hint", self.trText("保存成功", "Saved"))
        return save_path

    def submit(self):
        if len(self.txtJsName.text().strip()) <= 0:
            QMessageBox().information(self, "hint", self._translate("customForm", "别名不能为空"))
            return
        if len(self.editorGetText().strip()) <= 0:
            QMessageBox().information(self, "hint", self._translate("customForm", "脚本不能为空"))
            return
        existing_pin = False
        existing_pin_order = -1
        existing_builtin = False
        existing_source_key = ""
        for item in self.customs:
            if item.get("fileName") == self.txtJsFileName.text().strip():
                existing_pin = bool(item.get("pinToMain", False))
                existing_pin_order = self.pinnedTemplateOrderValue(item)
                existing_builtin = bool(item.get("builtin", False))
                existing_source_key = item.get("sourceHookKey", "")
                break

        data = {
            "name": self.txtJsName.text().strip(),
            "fileName": self.txtJsFileName.text().strip(),
            "bak": self.txtBak.text().strip(),
            "pinToMain": existing_pin,
            "pinOrder": existing_pin_order,
            "builtin": existing_builtin,
            "sourceHookKey": existing_source_key,
        }
        if len(data["fileName"]) <= 0:
            data["fileName"] = data["name"] + ".js"
            self.txtJsFileName.setText(data["fileName"])
        savepath = "./custom/" + data["fileName"]
        with open(savepath, "w", encoding="utf-8") as saveFile:
            saveFile.write(self.editorGetText())
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
        self.refreshCustomHookReferences()
