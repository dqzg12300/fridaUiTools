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

    def FridaReceive(self,message, data):
        pass

    def __del__(self):
        self.wait()

    def log(self,msg):
        self.loggerSignel.emit(msg)

    def outlog(self,msg):
        self.outloggerSignel.emit("start trace")

    def run(self):

        self.taskOverSignel.emit()

