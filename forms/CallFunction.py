from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.callFunction import Ui_CallFunctionDialog


class callFunctionForm(QDialog,Ui_CallFunctionDialog):
    def __init__(self, parent=None):
        super(callFunctionForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.method = ""
        self.btnClear.clicked.connect(self.clearUi)
        self.clearUi()
        self.listMethods.itemClicked.connect(self.MethodItemClick)
        self.callMethods=[]
        self.api = None

    def initData(self):
        self.listMethods.clear()
        for item in self.callMethods:
            self.listMethods.addItem(item)

    def MethodItemClick(self,item):
        self.txtMethod.setText(item.text())


    def clearUi(self):
        self.txtMethod.setText("")
        self.txtArgs.setText("")

    def submit(self):
        if len(self.txtMethod.text())<=0:
            QMessageBox().information(self, "提示", "函数不能为空")
            return
        methodName = self.txtMethod.text()
        args=self.txtArgs.text()
        self.api.callnormal(methodName,args)
        QMessageBox().information(self, "提示", "调用完成")
