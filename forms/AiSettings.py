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

    def loadConfig(self):
        data = self.aiService.get_config()
        self.txtHost.setText(data["host"])
        self.txtApiKey.setText(data["apikey"])
        self.txtModel.setText(data["model"])

    def refreshTranslations(self):
        self.retranslateUi(self)

    def clearUi(self):
        self.txtHost.clear()
        self.txtApiKey.clear()
        self.txtModel.clear()

    def submit(self):
        self.config.write("ai", "host", self.txtHost.text().strip())
        self.config.write("ai", "apikey", self.txtApiKey.text().strip())
        self.config.write("ai", "model", self.txtModel.text().strip())
        QMessageBox().information(self, "hint", self._translate("AiSettingsDialog", "AI 设置已保存"))
        self.accept()
