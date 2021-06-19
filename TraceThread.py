import socket
import struct
from copy import copy

from PyQt5.QtCore import *
import frida
import json
import hexdump


# 继承QThread
class Runthread(QThread):
    #  通过类成员对象定义信号对象
    #功能日志信号
    loggerSignel=pyqtSignal(str)
    #输出日志
    outloggerSignel = pyqtSignal(str)
    #线程退出信号
    taskOverSignel=pyqtSignal()
    #获取一些附加成功就可以取的通用信息。这里暂时还不知道初始化一些啥信息比较好。先打通流程
    loadAppInfoSignel=pyqtSignal(str)
    #附加成功的信号
    attachOverSignel = pyqtSignal(str)
    def __init__(self,hooksData,attachName):
        super(Runthread, self).__init__()
        self.hooksData = hooksData
        self.attachName=attachName
        self.script=None
        self.device=None

    def quit(self):
        if self.script:
                self.script.unload()
                self.taskOverSignel.emit()

    def log(self,msg):
        self.loggerSignel.emit(msg)

    def outlog(self,msg):
        self.outloggerSignel.emit(msg)

    def _attach(self,pid):
        if not self.device: return
        self.log("attach '{}'".format(pid))
        session = self.device.attach(pid)
        session.enable_child_gating()
        source=""
        for item in self.hooksData:
            # 使用r0capture.js
            if item=="r0capture":
                source+=open('./js/r0capture.js', 'r',encoding="utf8").read()
            elif item=="jnitrace":
                source+=open('./js/jni_trace_new.js', 'r',encoding="utf8").read()
                source=source.replace("%moduleName%",self.hooksData[item]["class"])
                source = source.replace("%methodName%", self.hooksData[item]["method"])
                source = source.replace("%spawn%", "")
            elif item=="ZenTracer":
                source += open('./js/trace.js', 'r', encoding="utf8").read()
                match_s = str(self.hooksData[item]["traceClass"]).replace('u\'', '\'')
                black_s = str(self.hooksData[item]["traceBClass"]).replace('u\'', '\'')
                source=source.replace('{MATCHREGEX}', match_s).replace("{BLACKREGEX}", black_s)

        # if len(source) <= 0 :
        source+=open("./js/default.js",'r',encoding="utf8").read()

        script = session.create_script(source)
        script.on("message", self.on_message)
        self.script = script
        self.attachOverSignel.emit(pid)
        script.load()


    def r0capture_message(self,p,data):
        if data==None or len(data) == 1:
            self.outlog(p["function"])
            if len(p["stack"])>0:
                self.outlog(p["stack"])
            return

        src_addr = socket.inet_ntop(socket.AF_INET,
                                    struct.pack(">I", p["src_addr"]))
        dst_addr = socket.inet_ntop(socket.AF_INET,
                                    struct.pack(">I", p["dst_addr"]))
        self.outlog("SSL Session: " + p["ssl_session_id"])
        self.outlog("[%s] %s:%d --> %s:%d" % (
            p["function"],
            src_addr,
            p["src_port"],
            dst_addr,
            p["dst_port"]))

        self.outlog(p["stack"])
        res= hexdump.hexdump(data,"return")
        self.outlog(res)

    def default_message(self,p):
        if "appinfo" in p:
            self.loadAppInfoSignel.emit(p["appinfo"])
        self.outlog(p["data"])

    def jnitrace_message(self,p):
        self.outlog(p["data"])

    def ZenTracer_message(self,p):
        self.outlog(p["data"])

    def showMethods(self,postdata):
        postdata["func"]="showMethod"
        self.script.post({'type': 'input', 'payload': postdata})
        self.log("post showMethods:"+postdata["className"]+","+postdata["methodName"])

    def showExport(self,postdata):
        postdata["func"] = "showExport"
        self.script.post({'type': 'input', 'payload': postdata})
        self.log("post showExport:"+postdata["moduleName"]+","+postdata["methodName"])

    def dumpPtr(self,postdata):
        postdata["func"] = "dumpPtr"
        self.script.post({'type': 'input', 'payload': postdata})
        self.log("post dumpPtr:" + postdata["moduleName"] + "," + str(hex(postdata["address"])))

    def on_message(self,message, data):
        if message["type"] == "error":
            self.outlog(json.dumps(message))
            return
        if "init" in message["payload"]:
            self.outlog(message["payload"]["init"])
            self.log(message["payload"]["init"])
            return
        if message["payload"]["jsname"]=="default":
            self.default_message(message["payload"])
            return
        elif message["payload"]["jsname"]=="r0capture":
            self.r0capture_message(message["payload"],data)
        elif message["payload"]["jsname"]=="jni_trace_new":
            self.jnitrace_message(message["payload"])
        elif message["payload"]["jsname"]=="ZenTracer":
            self.ZenTracer_message(message["payload"])

    def _on_child_added(self,child):
        self._attach(child.pid)

    def run(self):
        self.device = frida.get_usb_device()
        self.device.on("child-added", self._on_child_added)
        application = self.device.get_frontmost_application()
        target = 'Gadget' if application.identifier == 're.frida.Gadget' else application.identifier
        if len(self.attachName)<=0:
            for process in self.device.enumerate_processes():
                if target == process.name:
                    self._attach(process.name)
        else:
            self._attach(self.attachName)
        print("thread over")
        # self.taskOverSignel.emit()

