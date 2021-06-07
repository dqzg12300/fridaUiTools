from PyQt5.QtCore import *
import frida
import json



# 继承QThread
class Runthread(QThread):
    #  通过类成员对象定义信号对象
    #功能日志信号
    loggerSignel=pyqtSignal(str)
    #输出日志
    outloggerSignel = pyqtSignal(str)
    #线程退出信号
    taskOverSignel=pyqtSignal()

    def __init__(self,hooksData):
        super(Runthread, self).__init__()
        self.hooksData = hooksData
        self.scripts=""
        self.device=None

    def FridaReceive(self,message, data):
        pass

    def __del__(self):
        self.wait()

    def log(self,msg):
        self.loggerSignel.emit(msg)

    def outlog(self,msg):
        self.outloggerSignel.emit("start trace")

    def _attach(self,pid):
        if not self.device: return
        self.log("attach '{}'".format(pid))
        session = self.device.attach(pid)
        session.enable_child_gating()
        # source = open('trace.js', 'r').read().replace('{MATCHREGEX}', match_s).replace("{BLACKREGEX}", black_s)

    def _on_child_added(self,child):
        self._attach(child.pid)

    def run(self):
        device = frida.get_usb_device()
        device.on("child-added", self._on_child_added)
        # self.taskOverSignel.emit()

