from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.aiSettings import Ui_AiSettingsDialog
from utils.AiUtil import AiService
from utils.IniUtil import IniConfig


class aiSettingsForm(QDialog, Ui_AiSettingsDialog):
    def __init__(self, parent=None):
        super(aiSettingsForm, self).__init__(parent)
        self.setupUi(self)
        self.config = IniConfig()
        self.aiService = AiService(self.config)
        self._translate = QtCore.QCoreApplication.translate
        self.btnSubmit.clicked.connect(self.submit)
        self.btnClear.clicked.connect(self.clearUi)
        self.initSmartUi()
        self.loadConfig()
        self.refreshTranslations()

    def initSmartUi(self):
        self.resize(640, 320)
        self.setMinimumSize(560, 280)
        for button in [self.btnClear, self.btnSubmit]:
            button.setMinimumHeight(40)
        self._applyFallbackTheme()

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
        QLineEdit {
            background: #fbfcff;
            border: 1px solid #cfd8e5;
            border-radius: 8px;
            padding: 6px;
        }
        QLabel {
            color: #60738a;
        }
        """)

    def isEnglish(self):
        return (self.config.read("kmain", "language") or "China") == "English"

    def trText(self, zh_text, en_text):
        return en_text if self.isEnglish() else zh_text


    def loadConfig(self):
        data = self.aiService.get_config()
        self.txtHost.setText(data["host"])
        self.txtApiKey.setText(data["apikey"])
        self.txtModel.setText(data["model"])

    def refreshTranslations(self):
        self.retranslateUi(self)
        self.setWindowTitle(self.trText("AI 设置", "AI Settings"))
        self.groupBox.setTitle(self.trText("OpenAI 兼容接口配置", "OpenAI-compatible endpoint settings"))
        self.formLayout.labelForField(self.txtHost).setText(self.trText("Host：", "Host:"))
        self.formLayout.labelForField(self.txtApiKey).setText(self.trText("API Key：", "API Key:"))
        self.formLayout.labelForField(self.txtModel).setText(self.trText("模型：", "Model:"))
        self.txtHost.setPlaceholderText(self.trText("例如：https://api.openai.com/v1 或你的兼容服务地址", "Example: https://api.openai.com/v1 or your compatible API host"))
        self.txtApiKey.setPlaceholderText(self.trText("请输入 API Key", "Enter API Key"))
        self.txtModel.setPlaceholderText(self.trText("例如：gpt-4o-mini / deepseek-chat / qwen-max", "Example: gpt-4o-mini / deepseek-chat / qwen-max"))
        self.labHint.setText(self.trText("未配置 API Key / Host / 模型 时，AI 写脚本和 AI 分析日志功能会自动禁用。AI 配置将单独保存在本地文件，不再写入项目内的 config/conf.ini。", "If API Key / Host / Model is not configured, AI hook generation and AI log analysis stay disabled automatically. AI settings are stored in a separate local file instead of the project's config/conf.ini."))
        self.labHint.setToolTip(self.trText("本地配置文件：", "Local config file: ") + self.config.aiConfigPath)
        self.btnClear.setText(self.trText("清空", "Clear"))
        self.btnSubmit.setText(self.trText("保存", "Save"))

    def clearUi(self):
        self.txtHost.clear()
        self.txtApiKey.clear()
        self.txtModel.clear()

    def submit(self):
        self.config.write("ai", "host", self.txtHost.text().strip())
        self.config.write("ai", "apikey", self.txtApiKey.text().strip())
        self.config.write("ai", "model", self.txtModel.text().strip())
        QMessageBox().information(
            self,
            "hint",
            self.trText("AI 设置已保存到本地文件：", "AI settings saved to local file: ") + self.config.aiConfigPath
        )
        self.accept()
