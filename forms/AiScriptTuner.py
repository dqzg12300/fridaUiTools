import json
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDialog, QMessageBox

try:
    from PyQt5.Qsci import QsciScintilla, QsciLexerJavaScript
except ImportError:
    QsciScintilla = None
    QsciLexerJavaScript = None

from utils.AiUtil import AiService, AiWorker
from utils.IniUtil import IniConfig


class aiScriptTunerForm(QDialog):
    SETTINGS_SECTION = "ai_script_tuner"
    SETTINGS_KEY_LAST_SCRIPT = "last_script_file"
    SETTINGS_KEY_GEOMETRY = "window_geometry"
    SETTINGS_KEY_SPLITTER = "content_splitter"

    def __init__(self, parent=None):
        super(aiScriptTunerForm, self).__init__(parent)
        self.mainWindow = parent
        self.config = IniConfig()
        self.aiService = AiService()
        self.aiWorker = None
        self.currentFileName = ""
        self.currentScriptMeta = None
        self.lastSavedScriptText = ""
        self.pendingUpdatedScriptText = ""
        self.lastAppliedScriptText = ""
        self.windowStateRestored = False
        self._buildUi()
        self.setupScriptEditor()
        self._connectSignals()
        self.refreshTranslations()

    def _buildUi(self):
        self.setObjectName("aiScriptTunerWindow")
        self.setModal(False)
        self.setWindowModality(Qt.NonModal)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(1080, 820)
        self.setMinimumSize(920, 700)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.mainLayout.setSpacing(10)

        self.toolbarLayout = QtWidgets.QHBoxLayout()
        self.toolbarLayout.setContentsMargins(0, 0, 0, 0)
        self.toolbarLayout.setSpacing(6)
        self.labScript = QtWidgets.QLabel(self)
        self.cmbScript = QtWidgets.QComboBox(self)
        self.cmbScript.setMinimumWidth(220)
        self.btnReloadScript = QtWidgets.QPushButton(self)
        self.toolbarLayout.addWidget(self.labScript)
        self.toolbarLayout.addWidget(self.cmbScript, 1)
        self.toolbarLayout.addWidget(self.btnReloadScript)
        self.mainLayout.addLayout(self.toolbarLayout)

        self.labAiState = QtWidgets.QLabel(self)
        self.labAiState.setObjectName("aiStateLabel")
        self.labAiState.setWordWrap(True)
        self.mainLayout.addWidget(self.labAiState)

        self.topActionLayout = QtWidgets.QHBoxLayout()
        self.topActionLayout.setContentsMargins(0, 0, 0, 0)
        self.topActionLayout.setSpacing(6)
        self.btnLoadCurrentLog = QtWidgets.QPushButton(self)
        self.btnClearLog = QtWidgets.QPushButton(self)
        self.topActionLayout.addWidget(self.btnLoadCurrentLog)
        self.topActionLayout.addWidget(self.btnClearLog)
        self.topActionLayout.addStretch(1)
        self.mainLayout.addLayout(self.topActionLayout)

        self.contentSplitter = QtWidgets.QSplitter(Qt.Horizontal, self)
        self.contentSplitter.setChildrenCollapsible(False)
        self.mainLayout.addWidget(self.contentSplitter, 1)

        self.scriptPanel = QtWidgets.QFrame(self.contentSplitter)
        self.scriptPanel.setObjectName("aiScriptPreviewSection")
        self.scriptPanelLayout = QtWidgets.QVBoxLayout(self.scriptPanel)
        self.scriptPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.scriptPanelLayout.setSpacing(6)
        self.scriptHeaderLayout = QtWidgets.QHBoxLayout()
        self.scriptHeaderLayout.setContentsMargins(0, 0, 0, 0)
        self.scriptHeaderLayout.setSpacing(6)
        self.labScriptEditor = QtWidgets.QLabel(self.scriptPanel)
        self.scriptHeaderLayout.addWidget(self.labScriptEditor)
        self.scriptHeaderLayout.addStretch(1)
        self.scriptPanelLayout.addLayout(self.scriptHeaderLayout)
        self.txtScript = QtWidgets.QPlainTextEdit(self.scriptPanel)
        self.txtScript.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.scriptPanelLayout.addWidget(self.txtScript, 1)

        self.rightPanel = QtWidgets.QWidget(self.contentSplitter)
        self.rightPanelLayout = QtWidgets.QVBoxLayout(self.rightPanel)
        self.rightPanelLayout.setContentsMargins(0, 0, 0, 0)
        self.rightPanelLayout.setSpacing(10)

        self.labIssue = QtWidgets.QLabel(self.rightPanel)
        self.txtIssue = QtWidgets.QPlainTextEdit(self.rightPanel)
        self.txtIssue.setMinimumHeight(110)
        self.rightPanelLayout.addWidget(self.labIssue)
        self.rightPanelLayout.addWidget(self.txtIssue)

        self.labLog = QtWidgets.QLabel(self.rightPanel)
        self.txtLog = QtWidgets.QPlainTextEdit(self.rightPanel)
        self.txtLog.setMinimumHeight(150)
        self.rightPanelLayout.addWidget(self.labLog)
        self.rightPanelLayout.addWidget(self.txtLog, 1)

        self.labResult = QtWidgets.QLabel(self.rightPanel)
        self.txtResult = QtWidgets.QPlainTextEdit(self.rightPanel)
        self.txtResult.setReadOnly(True)
        self.txtResult.setMinimumHeight(170)
        self.rightPanelLayout.addWidget(self.labResult)
        self.rightPanelLayout.addWidget(self.txtResult, 1)

        self.contentSplitter.setStretchFactor(0, 6)
        self.contentSplitter.setStretchFactor(1, 5)
        self.contentSplitter.setSizes([620, 460])

        self.actionLayout = QtWidgets.QHBoxLayout()
        self.actionLayout.setContentsMargins(0, 0, 0, 0)
        self.actionLayout.setSpacing(6)
        self.btnAiTune = QtWidgets.QPushButton(self)
        self.btnApplyChanges = QtWidgets.QPushButton(self)
        self.btnUndoChanges = QtWidgets.QPushButton(self)
        self.btnSaveScript = QtWidgets.QPushButton(self)
        self.actionLayout.addWidget(self.btnAiTune)
        self.actionLayout.addWidget(self.btnApplyChanges)
        self.actionLayout.addWidget(self.btnUndoChanges)
        self.actionLayout.addWidget(self.btnSaveScript)
        self.mainLayout.addLayout(self.actionLayout)

    def _connectSignals(self):
        self.cmbScript.currentIndexChanged.connect(self.onScriptSelectionChanged)
        self.btnReloadScript.clicked.connect(self.reloadCurrentScript)
        self.btnLoadCurrentLog.clicked.connect(self.loadCurrentLog)
        self.btnClearLog.clicked.connect(self.txtLog.clear)
        self.btnAiTune.clicked.connect(self.requestAiTune)
        self.btnApplyChanges.clicked.connect(self.applyPendingChanges)
        self.btnUndoChanges.clicked.connect(self.undoLastAppliedChanges)
        self.btnSaveScript.clicked.connect(self.saveCurrentScript)

    def isEnglish(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "isEnglish"):
            return parent.isEnglish()
        return (self.config.read("kmain", "language") or "China") == "English"

    def trText(self, zh_text, en_text):
        return en_text if self.isEnglish() else zh_text

    def currentMainWindow(self):
        return self.mainWindow

    def lastSelectedScriptFile(self):
        return (self.config.read(self.SETTINGS_SECTION, self.SETTINGS_KEY_LAST_SCRIPT) or "").strip()

    def saveLastSelectedScriptFile(self, file_name):
        file_name = (file_name or "").strip()
        self.config.write(self.SETTINGS_SECTION, self.SETTINGS_KEY_LAST_SCRIPT, file_name)

    def savedWindowGeometry(self):
        return (self.config.read(self.SETTINGS_SECTION, self.SETTINGS_KEY_GEOMETRY) or "").strip()

    def saveWindowGeometryState(self):
        try:
            geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
            self.config.write(self.SETTINGS_SECTION, self.SETTINGS_KEY_GEOMETRY, geometry)
            self.config.write(self.SETTINGS_SECTION, self.SETTINGS_KEY_SPLITTER, json.dumps(self.contentSplitter.sizes()))
        except Exception:
            pass

    def restoreWindowGeometryState(self):
        if self.windowStateRestored:
            return
        geometry_text = self.savedWindowGeometry()
        restored = False
        if geometry_text:
            try:
                geometry_bytes = QtCore.QByteArray.fromBase64(geometry_text.encode("ascii"))
                restored = bool(self.restoreGeometry(geometry_bytes))
            except Exception:
                restored = False
        if restored and self.isWindowGeometryVisible():
            self.windowStateRestored = True
        else:
            self.windowStateRestored = True
            self.moveToDefaultPosition()
        splitter_text = (self.config.read(self.SETTINGS_SECTION, self.SETTINGS_KEY_SPLITTER) or "").strip()
        if splitter_text:
            try:
                sizes = json.loads(splitter_text)
                if isinstance(sizes, list) and len(sizes) == 2:
                    self.contentSplitter.setSizes([max(220, int(sizes[0])), max(220, int(sizes[1]))])
            except Exception:
                pass

    def isWindowGeometryVisible(self):
        frame = self.frameGeometry()
        if frame.width() <= 0 or frame.height() <= 0:
            return False
        for screen in QApplication.screens():
            if screen.availableGeometry().intersects(frame):
                return True
        return False

    def moveToDefaultPosition(self):
        main = self.currentMainWindow()
        if main is not None and main.isVisible():
            target = main.frameGeometry().topRight() + QtCore.QPoint(24, 40)
            self.move(target)
            return
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(available.center() - self.rect().center())

    def setupScriptEditor(self):
        placeholder = self.trText(
            "这里展示目标脚本内容。AI 返回局部修改后，会直接替换这里的对应片段。",
            "The target script is shown here. When AI returns partial edits, the matching fragments are replaced here directly.",
        )
        if QsciScintilla is None:
            self.txtScript.setPlaceholderText(placeholder)
            self.scriptEditorUsesQsci = False
            return

        old_editor = self.txtScript
        editor = QsciScintilla(self.scriptPanel)
        editor.setObjectName("txtScript")
        editor.setMinimumHeight(280)
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
        lexer.setDefaultPaper(QColor("#263238"))
        lexer.setDefaultColor(QColor("#cfd8dc"))
        lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.Keyword)
        lexer.setColor(QColor("#f07178"), QsciLexerJavaScript.KeywordSet2)
        lexer.setColor(QColor("#c792ea"), QsciLexerJavaScript.Number)
        lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.DoubleQuotedString)
        lexer.setColor(QColor("#c3e88d"), QsciLexerJavaScript.SingleQuotedString)
        lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.Comment)
        lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.CommentLine)
        lexer.setColor(QColor("#546e7a"), QsciLexerJavaScript.CommentDoc)
        lexer.setColor(QColor("#82aaff"), QsciLexerJavaScript.Identifier)
        lexer.setColor(QColor("#89ddff"), QsciLexerJavaScript.Operator)
        lexer.setColor(QColor("#ffcb6b"), QsciLexerJavaScript.UnclosedString)
        editor.setLexer(lexer)
        editor.setText(old_editor.toPlainText())
        old_editor.hide()
        self.scriptPanelLayout.replaceWidget(old_editor, editor)
        old_editor.deleteLater()
        self.txtScript = editor
        self.scriptEditorUsesQsci = True
        self.txtScript.setToolTip(placeholder)

    def scriptEditorSetText(self, text):
        if getattr(self, "scriptEditorUsesQsci", False):
            self.txtScript.setText(text)
        else:
            self.txtScript.setPlainText(text)

    def scriptEditorGetText(self):
        if getattr(self, "scriptEditorUsesQsci", False):
            return self.txtScript.text()
        return self.txtScript.toPlainText()

    def refreshTranslations(self):
        self.labScript.setText(self.trText("目标脚本：", "Target script:"))
        self.labScriptEditor.setText(self.trText("脚本内容", "Script content"))
        self.labIssue.setText(self.trText("问题描述 / 调整要求", "Issue description / tuning request"))
        self.labLog.setText(self.trText("相关日志", "Relevant log"))
        self.labResult.setText(self.trText("AI 处理结果", "AI result"))
        self.btnReloadScript.setText(self.trText("重载", "Reload"))
        self.btnLoadCurrentLog.setText(self.trText("加载当前日志", "Load current log"))
        self.btnClearLog.setText(self.trText("清空日志", "Clear log"))
        self.btnAiTune.setText(self.trText("AI 微调", "AI Tune"))
        self.btnApplyChanges.setText(self.trText("应用修改", "Apply"))
        self.btnUndoChanges.setText(self.trText("撤销本次", "Undo"))
        self.btnSaveScript.setText(self.trText("保存脚本", "Save"))
        if getattr(self, "scriptEditorUsesQsci", False):
            self.txtScript.setToolTip(self.trText("这里展示目标脚本内容。AI 返回局部修改后，会直接替换这里的对应片段。", "The target script is shown here. When AI returns partial edits, the matching fragments are replaced here directly."))
        else:
            self.txtScript.setPlaceholderText(self.trText("这里展示目标脚本内容。AI 返回局部修改后，会直接替换这里的对应片段。", "The target script is shown here. When AI returns partial edits, the matching fragments are replaced here directly."))
        self.txtIssue.setPlaceholderText(self.trText("例如：附加后报错 undefined、某个 overload 写错、日志太少需要补打印。", "Example: the script fails after attach with undefined, an overload is wrong, or more logging is needed."))
        self.txtLog.setPlaceholderText(self.trText("可粘贴报错日志，也可点“加载当前日志”直接带入主界面的日志内容。", "Paste error logs here, or click 'Load current log' to import the current log content from the main window."))
        self.txtResult.setPlaceholderText(self.trText("这里会显示 AI 给出的局部修改摘要。确认后再应用到脚本。", "AI partial edit summaries will appear here. Review them before applying changes to the script."))
        self.refreshAiState()

    def refreshAiState(self):
        available = self.aiService.is_available()
        self.btnAiTune.setEnabled(available)
        self.labAiState.setText(
            self.trText("AI 状态：已配置，可进行局部脚本微调", "AI status: configured and ready for partial script tuning")
            if available else
            (self.trText("AI 状态：", "AI status: ") + self.aiService.missing_message("English" if self.isEnglish() else "China"))
        )
        self.updateActionStates()

    def activeCustomFileNames(self):
        main = self.currentMainWindow()
        if main is None or not hasattr(main, "customForm"):
            return set()
        return {item.get("fileName") for item in main.customForm.customHooks if item.get("fileName")}

    def _scriptDisplayText(self, item):
        name = item.get("name", "")
        file_name = item.get("fileName", "")
        prefix = self.trText("[使用中] ", "[Active] ") if file_name in self.activeCustomFileNames() else ""
        return "%s%s (%s)" % (prefix, name or file_name, file_name)

    def refreshScriptList(self, preferred_file_name=""):
        main = self.currentMainWindow()
        if main is None or not hasattr(main, "customForm"):
            return
        main.customForm.initData()
        scripts = list(main.customForm.customs)
        active_files = self.activeCustomFileNames()
        scripts.sort(key=lambda item: (0 if item.get("fileName") in active_files else 1, item.get("name", "").lower(), item.get("fileName", "").lower()))
        current_target = preferred_file_name or self.lastSelectedScriptFile() or self.currentFileName
        blocker = QtCore.QSignalBlocker(self.cmbScript)
        self.cmbScript.clear()
        for item in scripts:
            self.cmbScript.addItem(self._scriptDisplayText(item), item.get("fileName", ""))
        self._refreshScriptControls()
        if self.cmbScript.count() <= 0:
            self.currentFileName = ""
            self.currentScriptMeta = None
            self.lastSavedScriptText = ""
            self.pendingUpdatedScriptText = ""
            self.lastAppliedScriptText = ""
            self.scriptEditorSetText("")
            self.txtResult.clear()
            del blocker
            return
        index = self.cmbScript.findData(current_target)
        if index < 0:
            index = 0
        self.cmbScript.setCurrentIndex(index)
        del blocker
        self.loadScriptByFile(str(self.cmbScript.itemData(index) or ""), force=True)

    def _refreshScriptControls(self):
        has_scripts = self.cmbScript.count() > 0
        self.cmbScript.setEnabled(has_scripts)
        self.btnReloadScript.setEnabled(has_scripts)
        self.updateActionStates()

    def updateActionStates(self):
        has_script = bool(self.currentFileName)
        self.btnApplyChanges.setEnabled(bool(self.pendingUpdatedScriptText))
        self.btnUndoChanges.setEnabled(bool(self.lastAppliedScriptText))
        self.btnSaveScript.setEnabled(has_script)

    def currentScriptText(self):
        return self.scriptEditorGetText()

    def hasUnsavedChanges(self):
        return self.currentScriptText() != self.lastSavedScriptText

    def confirmDiscardChanges(self):
        if not self.hasUnsavedChanges():
            return True
        result = QMessageBox.question(
            self,
            "hint",
            self.trText("当前脚本有未保存修改，是否放弃这些修改？", "The current script has unsaved changes. Discard them?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    def scriptMetaByFile(self, file_name):
        main = self.currentMainWindow()
        if main is None or not hasattr(main, "customForm"):
            return None
        return main.customForm.scriptDataByFileName(file_name)

    def loadScriptByFile(self, file_name, force=False):
        file_name = (file_name or "").strip()
        if not file_name:
            return False
        if not force and self.currentFileName and self.currentFileName != file_name and not self.confirmDiscardChanges():
            blocker = QtCore.QSignalBlocker(self.cmbScript)
            restore_index = self.cmbScript.findData(self.currentFileName)
            if restore_index >= 0:
                self.cmbScript.setCurrentIndex(restore_index)
            del blocker
            return False
        meta = self.scriptMetaByFile(file_name)
        if meta is None:
            QMessageBox().information(self, "hint", self.trText("未找到目标脚本元数据", "Target script metadata was not found"))
            return False
        path = os.path.join("./custom", file_name)
        if os.path.exists(path) is False:
            QMessageBox().information(self, "hint", self.trText("脚本文件不存在：", "Script file does not exist: ") + path)
            return False
        with open(path, "r", encoding="utf-8") as script_file:
            content = script_file.read()
        self.currentFileName = file_name
        self.currentScriptMeta = dict(meta)
        self.lastSavedScriptText = content
        self.pendingUpdatedScriptText = ""
        self.lastAppliedScriptText = ""
        self.scriptEditorSetText(content)
        self.txtResult.clear()
        self.saveLastSelectedScriptFile(file_name)
        self.updateActionStates()
        return True

    def onScriptSelectionChanged(self, index):
        if index < 0:
            return
        file_name = str(self.cmbScript.itemData(index) or "")
        self.loadScriptByFile(file_name, force=False)

    def reloadCurrentScript(self):
        if not self.currentFileName:
            return
        if self.confirmDiscardChanges() is False:
            return
        self.loadScriptByFile(self.currentFileName, force=True)

    def currentVisibleLogText(self):
        main = self.currentMainWindow()
        if main is None or hasattr(main, "currentLogTextForAiTuner") is False:
            return ""
        return main.currentLogTextForAiTuner()

    def loadCurrentLog(self):
        content = self.currentVisibleLogText()
        if not content.strip():
            QMessageBox().information(self, "hint", self.trText("当前没有可加载的日志内容", "There is no log content available to load"))
            return
        self.txtLog.setPlainText(content)

    def requestAiTune(self):
        script_text = self.currentScriptText().strip()
        issue = self.txtIssue.toPlainText().strip()
        log_text = self.txtLog.toPlainText().strip()
        if not self.aiService.is_available():
            self.refreshAiState()
            QMessageBox().information(self, "hint", self.aiService.missing_message("English" if self.isEnglish() else "China"))
            return
        if not script_text:
            QMessageBox().information(self, "hint", self.trText("请先选择并加载要微调的脚本", "Please choose and load the script to tune first"))
            return
        if not issue and not log_text:
            QMessageBox().information(self, "hint", self.trText("请先填写问题描述，或加载相关日志", "Please describe the issue first, or load relevant logs"))
            return
        self.btnAiTune.setEnabled(False)
        self.btnAiTune.setText(self.trText("处理中...", "Processing..."))
        self.pendingUpdatedScriptText = ""
        self.txtResult.setPlainText(self.trText("AI 正在分析脚本并生成局部修改指令...", "AI is analyzing the script and generating partial edit instructions..."))
        self.aiWorker = AiWorker(
            self.aiService.tune_hook_script,
            script_text,
            issue,
            log_text,
            self.currentScriptMeta.get("name", "") if self.currentScriptMeta else "",
            self.currentScriptMeta.get("bak", "") if self.currentScriptMeta else "",
        )
        self.aiWorker.success.connect(self.onAiTuneSuccess)
        self.aiWorker.error.connect(self.onAiTuneFailed)
        self.aiWorker.start()

    def onAiTuneSuccess(self, payload_text):
        try:
            payload = self.aiService.parse_script_tune_payload(payload_text)
            updated_script, applied = self.aiService.apply_script_tune_operations(self.currentScriptText(), payload.get("operations", []))
            self.pendingUpdatedScriptText = updated_script
            lines = []
            summary = (payload.get("summary", "") or "").strip()
            if summary:
                lines.append(self.trText("修改摘要：", "Summary: ") + summary)
                lines.append("")
            lines.append(self.trText("待应用的局部修改：", "Pending partial edits: "))
            for index, item in enumerate(applied, start=1):
                action_text = {
                    "replace": self.trText("替换", "replace"),
                    "insert_before": self.trText("前插入", "insert_before"),
                    "insert_after": self.trText("后插入", "insert_after"),
                }.get(item.get("action", ""), item.get("action", ""))
                reason = (item.get("reason", "") or "").strip()
                target_preview = (item.get("target", "") or "").strip().replace("\n", "\\n")
                if len(target_preview) > 120:
                    target_preview = target_preview[:120] + "..."
                lines.append("%d. %s | %s" % (index, action_text, target_preview))
                if reason:
                    lines.append("   " + self.trText("原因：", "Reason: ") + reason)
            lines.append("")
            lines.append(self.trText("确认后点击“应用修改”，再保存脚本并回主界面测试。", "Click 'Apply' to update the script, then save it and return to the main window for testing."))
            self.txtResult.setPlainText("\n".join(lines))
        except Exception as error:
            self.pendingUpdatedScriptText = ""
            self.txtResult.setPlainText(self.trText("AI 返回结果解析失败：", "Failed to parse AI result: ") + str(error) + "\n\n" + payload_text)
            QMessageBox().information(self, "hint", str(error))
        finally:
            self.btnAiTune.setEnabled(self.aiService.is_available())
            self.btnAiTune.setText(self.trText("AI 微调", "AI Tune"))
            self.aiWorker = None
            self.updateActionStates()

    def onAiTuneFailed(self, message):
        self.btnAiTune.setEnabled(self.aiService.is_available())
        self.btnAiTune.setText(self.trText("AI 微调", "AI Tune"))
        self.pendingUpdatedScriptText = ""
        self.txtResult.setPlainText(message)
        self.aiWorker = None
        self.updateActionStates()
        QMessageBox().information(self, "hint", message)

    def applyPendingChanges(self):
        if not self.pendingUpdatedScriptText:
            return
        self.lastAppliedScriptText = self.currentScriptText()
        self.scriptEditorSetText(self.pendingUpdatedScriptText)
        self.pendingUpdatedScriptText = ""
        self.updateActionStates()

    def undoLastAppliedChanges(self):
        if not self.lastAppliedScriptText:
            return
        self.scriptEditorSetText(self.lastAppliedScriptText)
        self.lastAppliedScriptText = ""
        self.pendingUpdatedScriptText = ""
        self.updateActionStates()

    def saveCurrentScript(self):
        if not self.currentFileName or self.currentScriptMeta is None:
            QMessageBox().information(self, "hint", self.trText("请先选择脚本", "Please choose a script first"))
            return
        script_text = self.currentScriptText().strip()
        if not script_text:
            QMessageBox().information(self, "hint", self.trText("脚本内容不能为空", "Script content cannot be empty"))
            return
        main = self.currentMainWindow()
        if main is None or hasattr(main, "saveAiTunedScript") is False:
            QMessageBox().information(self, "hint", self.trText("主窗口未提供保存入口", "The main window does not provide a save entry"))
            return
        save_path = main.saveAiTunedScript(self.currentFileName, script_text)
        self.lastSavedScriptText = self.currentScriptText()
        self.lastAppliedScriptText = ""
        self.pendingUpdatedScriptText = ""
        self.refreshScriptList(preferred_file_name=self.currentFileName)
        QMessageBox().information(self, "hint", self.trText("脚本已保存：", "Script saved: ") + save_path)

    def openWithScript(self, file_name=""):
        self.restoreWindowGeometryState()
        self.refreshAiState()
        self.refreshScriptList(preferred_file_name=file_name)
        if not self.txtLog.toPlainText().strip():
            log_text = self.currentVisibleLogText()
            if log_text.strip():
                self.txtLog.setPlainText(log_text)
        self.show()
        if self.isMinimized():
            self.showNormal()

    def moveEvent(self, event):
        super(aiScriptTunerForm, self).moveEvent(event)
        if self.isVisible():
            self.saveWindowGeometryState()

    def resizeEvent(self, event):
        super(aiScriptTunerForm, self).resizeEvent(event)
        if self.isVisible():
            self.saveWindowGeometryState()

    def closeEvent(self, event):
        if self.confirmDiscardChanges():
            self.saveWindowGeometryState()
            event.accept()
        else:
            event.ignore()
