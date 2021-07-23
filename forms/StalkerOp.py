import json
import os
import re

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from ui.stalkerMatch import Ui_StalkerMatchDialog


class stalkerMatchForm(QDialog,Ui_StalkerMatchDialog):
    def __init__(self, parent=None):
        super(stalkerMatchForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSubmit.clicked.connect(self.submit)
        self.btnSelectLogPath.clicked.connect(self.selectLogPath)
        self.btnSelectSavePath.clicked.connect(self.selectSavePath)
        self.cwd = os.getcwd()+"/example/"

    def selectLogPath(self):
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                "选取文件",
                                                                self.cwd,
                                                                "Text Files (*.txt);;Log Files(*.log);;All Files (*)")
        if fileName_choose == "":
            return
        self.txtLogPath.setText(fileName_choose)
        self.txtSavePath.setText(fileName_choose+"_match.txt")

    def selectSavePath(self):
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                "文件保存",
                                                                self.cwd,  # 起始路径
                                                                "All Files (*);;Text Files (*.txt)")  # 设置文件扩展名过滤,用双分号间隔
        if fileName_choose == "":
            return
        self.txtSavePath.setText(fileName_choose)

    def appendResult(self,data):
        self.txtResult.appendPlainText(data)

    def submit(self):
        if len(self.txtLogPath.text())<=0 or os.path.exists(self.txtLogPath.text())==False:
            QMessageBox().information(self, "提示", "log路径为空或文件不存在")
            return
        if len(self.txtSavePath.text())<=0:
            QMessageBox().information(self, "提示", "save路径为空")
            return
        logfile=open(self.txtLogPath.text(),"r",encoding="utf-8")
        logdata=logfile.read()
        logfile.close()

        #
        lines= re.findall(r"DEBUG: (tid:.+?address:.+)",logdata)
        contexts=[]
        insts=[]
        for line in lines:
            if "context:" in line:
                contexts.append(line)
            else:
                insts.append(line)
        for line in insts:
            # print(line)
            ops= re.findall(r"=\{(.+?)\}",line)
            m1=re.search(r"address:(.+?) ",line)
            if m1==None:
                continue
            address=m1.group(0)
            curcontext=""
            for context in contexts:
                if address in context:
                    curcontext=context
                    contexts.remove(context)
                    break
            m2 = re.search("context:(.+)", curcontext)
            if m2==None:
                continue
            condata=json.loads(m2.group(1))
            #如果是arm64的情况。会有x0寄存器，然后把w相关的寄存器值手动加进去
            if "x0" in condata:
                for i in range(28):
                    extReg="w%d"%i
                    xdata="x%d"%i
                    wdata=int(condata[xdata],16)&0xffffffff
                    condata[extReg]="%x"%wdata
            newline =line
            for op in ops:
                if op=="wzr":
                    opdata="0"
                else:
                    opdata=condata[op]
                newline=str.replace(newline,"{%s}"%op,opdata)
            self.appendResult(newline)
