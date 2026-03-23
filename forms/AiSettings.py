from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.aiSettings import Ui_AiSettingsDialog
from utils.AiUtil import AiService
from utils.IniUtil import IniConfig


class aiSettingsForm(QDialog, Ui_AiSettingsDialog):
    def __init__(self, parent=None):
        super(aiSettingsForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.96)
        self.config = IniConfig()
        self.aiService = AiService(self.config)
        self._translate = QtCore.QCoreApplication.translate
        self.btnSubmit.clicked.connect(self.submit)
        self.btnClear.clicked.connect(self.clearUi)
        self.loadConfig()
        self.refreshTranslations()

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
        self.labHint.setText(self.trText("未配置 API Key / Host / 模型 时，AI 写脚本和 AI 分析日志功能会自动禁用。", "If API Key / Host / Model is not configured, AI hook generation and AI log analysis will stay disabled automatically."))
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
        QMessageBox().information(self, "hint", self.trText("AI 设置已保存", "AI settings saved"))
        self.accept()
