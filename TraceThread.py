# -*- coding: utf-8 -*-
import random
import re
import socket
import struct
import time
from copy import copy

from PyQt5.QtCore import *
import frida
import json
import hexdump
import hashlib
import os

from utils import CmdUtil

JAVA_PERFORM_PREFIX = re.compile(r'^\s*Java\.perform\(function\s*\(\)\s*\{', re.S)
JAVA_PERFORM_SUFFIX = re.compile(r'\}\s*\)\s*;?\s*$', re.S)

def wrap_java_perform_script(script_text, script_name):
    if not JAVA_PERFORM_PREFIX.match(script_text):
        return script_text
    stripped = JAVA_PERFORM_PREFIX.sub('', script_text, count=1)
    stripped = JAVA_PERFORM_SUFFIX.sub('', stripped, count=1)
    return f'''(function(){{
function __run_when_java_ready_{script_name.replace('.', '_').replace('-', '_')}() {{
{stripped}
}}
if (typeof Java !== "undefined" && Java.available) {{
    Java.perform(__run_when_java_ready_{script_name.replace('.', '_').replace('-', '_')});
}} else {{
    var __retry_count = 0;
    var __retry_timer = setInterval(function() {{
        __retry_count++;
        if (typeof Java !== "undefined" && Java.available) {{
            clearInterval(__retry_timer);
            Java.perform(__run_when_java_ready_{script_name.replace('.', '_').replace('-', '_')});
        }} else if (__retry_count >= 20) {{
            clearInterval(__retry_timer);
            send({{"jsname": "{script_name}", "data": "[java-wait] Java runtime not ready, skip delayed init"}});
        }}
    }}, 500);
}}
}})();'''

md5 = lambda bs: hashlib.md5(bs).hexdigest()
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
    loadAppInfoSignel=pyqtSignal(object)
    searchAppInfoSignel=pyqtSignal(object)
    classListSignel=pyqtSignal(list)
    searchMemorySignel=pyqtSignal(str,str)
    setBreakSignel=pyqtSignal(dict)
    #附加成功的信号
    attachOverSignel = pyqtSignal(str)


    def __init__(self,hooksData,attachName,isSpawn,connType):
        super(Runthread, self).__init__()
        self.hooksData = hooksData
        self.attachName=attachName
        self.scripts=[]
        self.sessions=[]
        self.default_script=None
        self.device=None
        self.isSpawn=isSpawn
        self.DEXDump=False
        self.enable_deep_search=False
        self.customCallFuns=[]
        self.connType=connType
        self.address=""
        self.port=""
        self.attachType=""
        self.customPort=None
        self.usb_device_id=""
        self.default_api=None

    def quit(self):
        if self.scripts:
            for s in copy(self.scripts):
                try:
                    s.unload()
                    self.log("trace script unload")
                    self.scripts.remove(s)
                except Exception as ex:
                    print(ex)
        if self.sessions:
            for session in copy(self.sessions):
                try:
                    session.detach()
                except Exception as ex:
                    print(ex)
                finally:
                    try:
                        self.sessions.remove(session)
                    except ValueError:
                        pass
        self.default_script = None
        self.default_api = None
        self.taskOverSignel.emit()

    def log(self,msg):
        self.loggerSignel.emit(msg)

    def outlog(self,msg):
        self.outloggerSignel.emit(msg)

    def _attach(self,pname):
        if not self.device:
            return
        self.log("attach '{}'".format(pname))
        try:
            if self.isSpawn:
                pid = self.device.spawn([pname])
                session =self.device.attach(pid)

            else:
                session = self.device.attach(pname)
            # session.enable_child_gating()
            source=""
        except Exception as ex:
            self.log("附加异常:"+str(ex))
            self.attachOverSignel.emit("ERROR."+str(ex))
            return

        for item in self.hooksData:
            if item=="r0capture":
                curtime=time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
                source+=open('./js/r0capture.js', 'r',encoding="utf8").read()
                self.ssl_sessions={}
                self.pcap_file = open(f"./pcap/r0capture_{curtime}.pcap", "wb", 0)
                for writes in (
                        ("=I", 0xa1b2c3d4),  # Magic number
                        ("=H", 2),  # Major version number
                        ("=H", 4),  # Minor version number
                        ("=i", time.timezone),  # GMT to local correction
                        ("=I", 0),  # Accuracy of timestamps
                        ("=I", 65535),  # Max length of captured packets
                        ("=I", 228)):  # Data link type (LINKTYPE_IPV4)
                    self.pcap_file.write(struct.pack(writes[0], writes[1]))
            elif item=="jnitrace":
                source+=open('./js/jni_trace_new.js', 'r',encoding="utf8").read()
                source=source.replace("%moduleName%",self.hooksData[item]["class"])
                source = source.replace("%methodName%", self.hooksData[item]["method"])
                source = source.replace("%offset%", self.hooksData[item]["offset"])
            elif item=="ZenTracer":
                source += open('./js/trace.js', 'r', encoding="utf8").read()
                match_s = str(self.hooksData[item]["traceClass"]).replace('u\'', '\'')
                black_s = str(self.hooksData[item]["traceBClass"]).replace('u\'', '\'')
                match_method=str(self.hooksData[item]["traceMethod"]).replace('u\'', '\'')
                match_bmethod=str(self.hooksData[item]["traceBMethod"]).replace('u\'', '\'')
                source=source.replace('{MATCHREGEX}', match_s).replace("{BLACKREGEX}", black_s)
                source=source.replace('{MATCHREGEXMETHOD}',match_method).replace("{BLACKREGEXMETHOD}",match_bmethod)
                source = source.replace('%stack%', self.hooksData[item]["stack"])
                source = source.replace('%hookInit%', self.hooksData[item]["hookInit"])
                source = source.replace('%isMatch%', self.hooksData[item]["isMatch"])
                source = source.replace('%isMatchMethod%', self.hooksData[item]["isMatchMethod"])
            elif item=="match_sub":
                source +=open('./js/traceNative.js', 'r', encoding="utf8").read()
                source = source.replace("%moduleName%", self.hooksData[item]["class"])
                methods=self.hooksData[item]["method"].split(",")
                methods_s=str(methods).replace('u\'', '\'')
                source = source.replace('{methodName}', methods_s)
            elif item=="sslpining":
                source += wrap_java_perform_script(open('./js/DroidSSLUnpinning.js', 'r', encoding="utf8").read(), 'DroidSSLUnpinning.js')
            elif item=="hookEvent":
                source += wrap_java_perform_script(open("./js/hookEvent.js", 'r', encoding="utf8").read(), 'hookEvent.js')
            elif item=="RegisterNative":
                source += open("./js/hook_RegisterNatives.js", 'r', encoding="utf8").read()
            elif item=="ArtMethod":
                source += open("./js/hook_artmethod.js", 'r', encoding="utf8").read()
            elif item=="libArm":
                source += open("./js/hook_art.js", 'r', encoding="utf8").read()
            elif item == "javaEnc":
                source += wrap_java_perform_script(open("./js/javaEnc.js", 'r', encoding="utf8").read(), 'javaEnc.js')
            elif item=="stakler":
                source += open("./js/sktrace.js", 'r', encoding="utf8").read()
                source = source.replace("%moduleName%", self.hooksData[item]["class"])
                source = source.replace("%symbol%", self.hooksData[item]["symbol"])
                source = source.replace("%offset%", self.hooksData[item]["offset"])
            elif item=="custom":
                for item in self.hooksData["custom"]:
                    if item.get("fileName") == "r0capture.js":
                        curtime = time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime(time.time()))
                        self.ssl_sessions = {}
                        self.pcap_file = open(f"./pcap/r0capture_{curtime}.pcap", "wb", 0)
                        for writes in (
                                ("=I", 0xa1b2c3d4),
                                ("=H", 2),
                                ("=H", 4),
                                ("=i", time.timezone),
                                ("=I", 0),
                                ("=I", 65535),
                                ("=I", 228)):
                            self.pcap_file.write(struct.pack(writes[0], writes[1]))
                    customJs= open("./custom/"+item["fileName"], 'r', encoding="utf8").read()
                    customJs = wrap_java_perform_script(customJs, item["fileName"])
                    customJs=customJs.replace("%customName%",item["class"])
                    customJs = customJs.replace("%customFileName%", item["fileName"])
                    #rpc.export.call_demo1= 匹配出主动调用要用的rpc函数
                    it = re.finditer(r"call_funs\.(.+?)=",customJs)
                    self.customCallFuns.clear()
                    for match in it:
                        self.customCallFuns.append(match.group(1))
                    # custom scripts in this repo are already self-contained IIFEs; append with separators
                    source += "\n;\n%s\n;\n" % customJs
            elif item=="tuoke":
                tuokeType=self.hooksData[item]["class"]
                if tuokeType=="dumpdex":
                    res = CmdUtil.dumpdexInit(self.attachName)
                    self.log(res)
                    source += open("./js/dump_dex.js", 'r', encoding="utf8").read()
                elif tuokeType=="dumpdexclass":
                    res=CmdUtil.dumpdexInit(self.attachName)
                    self.log(res)
                    source += open("./js/dump_dex_class.js", 'r', encoding="utf8").read()
                elif tuokeType=="FRIDA-DEXDump":
                    source += open("./js/FRIDA-DEXDump.js", 'r', encoding="utf8").read()
                    self.DEXDump=True
                elif tuokeType=="cookieDump":
                    source += open("./js/cookieDump.js", 'r', encoding="utf8").read()
                elif tuokeType=="fart":
                    # savepath="/data/local/tmp/fart/"+self.attachName
                    savepath="/data/data/"+self.attachName+"/fart/"
                    res = CmdUtil.fartInit(savepath)
                    self.log(res)
                    source += open("./js/frida_fart_hook.js", 'r', encoding="utf8").read()
                    source=source.replace("%savepath%",savepath)
            elif item=="patch":
                patchList = {}
                moduleName=""
                for patch in self.hooksData[item]:
                    patchList[patch["address"]]={
                        "moduleName":patch["class"],
                        "code": patch["code"],
                    }
                    moduleName=patch["class"]
                if len(patchList) > 0:
                    source += open("./js/patchCode.js", 'r', encoding="utf8").read()
                    print(json.dumps(patchList))
                    source = source.replace("{PATCHLIST}", json.dumps(patchList))
                    source = source.replace("%moduleName%",moduleName)
            elif item=="anti_debug":
                source += wrap_java_perform_script(open("./js/anti_debug.js", 'r', encoding="utf8").read(), 'anti_debug.js')
            elif item=="root_bypass":
                source += wrap_java_perform_script(open("./js/root_bypass.js", 'r', encoding="utf8").read(), 'root_bypass.js')
            elif item=="webview_debug":
                source += wrap_java_perform_script(open("./js/webview_debug.js", 'r', encoding="utf8").read(), 'webview_debug.js')
            elif item=="okhttp_logger":
                source += wrap_java_perform_script(open("./js/okhttp_logger.js", 'r', encoding="utf8").read(), 'okhttp_logger.js')
            elif item=="shared_prefs_watch":
                source += wrap_java_perform_script(open("./js/shared_prefs_watch.js", 'r', encoding="utf8").read(), 'shared_prefs_watch.js')
            elif item=="sqlite_logger":
                source += wrap_java_perform_script(open("./js/sqlite_logger.js", 'r', encoding="utf8").read(), 'sqlite_logger.js')
            elif item=="clipboard_monitor":
                source += wrap_java_perform_script(open("./js/clipboard_monitor.js", 'r', encoding="utf8").read(), 'clipboard_monitor.js')
            elif item=="intent_monitor":
                source += wrap_java_perform_script(open("./js/intent_monitor.js", 'r', encoding="utf8").read(), 'intent_monitor.js')
            elif item=="FCAnd_jnitrace":
                jsdata= open("./js/FCAnd_jnitrace.js", 'r', encoding="utf8").read()
                jsdata=jsdata.replace("%moduleName%",self.hooksData[item]["class"])
                jsdata =jsdata.replace("%methodName%", self.hooksData[item]["method"])
                jsdata = jsdata.replace("%offset%", self.hooksData[item]["offset"])
                source +=jsdata
            elif item=="antiFrida":
                jsdata = open("./js/anti_frida.js", 'r', encoding="utf8").read()
                jsdata = jsdata.replace("%antiType%", self.hooksData[item]["class"])
                jsdata = jsdata.replace("%Keyword%", self.hooksData[item]["method"])
                if self.hooksData[item]["isExitThread"]:
                    jsdata = jsdata.replace("%isExitThread%", "1")
                else:
                    jsdata = jsdata.replace("%isExitThread%", "")
                source += jsdata
        source += open("./js/default.js", 'r', encoding="utf8").read()
        source = source.replace("%spawn%", "1" if self.isSpawn else "")
        source += open("./js/Wallbreaker.js", 'r', encoding="utf8").read()
        script = session.create_script(source)
        script.on("message", self.on_message)
        script.load()
        if self.isSpawn:
            self.device.resume(pid)
            self.log("resume pid:%s" % pid)
        self.sessions.append(session)
        self.default_script=script
        self.default_api=script.exports
        self.scripts.append(script)
        if self.DEXDump:
            if self.enable_deep_search:
                script.exports.switchmode(True)
                self.outlog("[DEXDump]: deep search mode is enable, maybe wait long time.")
            mds = []
            self.dump(pname, script.exports, mds=mds)
        self.attachOverSignel.emit(pname)
        try:
            self.loadAppInfoSignel.emit(script.exports.loadappinfo())
        except Exception as ex:
            self.log("loadAppInfo rpc failed: " + str(ex))


    def log_pcap(self,pcap_file, ssl_session_id, function, src_addr, src_port,
                 dst_addr, dst_port, data):
        """Writes the captured data to a pcap file.
        Args:
          pcap_file: The opened pcap file.
          ssl_session_id: The SSL session ID for the communication.
          function: The function that was intercepted ("SSL_read" or "SSL_write").
          src_addr: The source address of the logged packet.
          src_port: The source port of the logged packet.
          dst_addr: The destination address of the logged packet.
          dst_port: The destination port of the logged packet.
          data: The decrypted packet data.
        """
        t = time.time()

        if ssl_session_id not in self.ssl_sessions:
            self.ssl_sessions[ssl_session_id] = (random.randint(0, 0xFFFFFFFF),
                                            random.randint(0, 0xFFFFFFFF))
        client_sent, server_sent = self.ssl_sessions[ssl_session_id]

        if function == "SSL_read":
            seq, ack = (server_sent, client_sent)
        else:
            seq, ack = (client_sent, server_sent)

        for writes in (
                # PCAP record (packet) header
                ("=I", int(t)),  # Timestamp seconds
                ("=I", int((t * 1000000) % 1000000)),  # Timestamp microseconds
                ("=I", 40 + len(data)),  # Number of octets saved
                ("=i", 40 + len(data)),  # Actual length of packet
                # IPv4 header
                (">B", 0x45),  # Version and Header Length
                (">B", 0),  # Type of Service
                (">H", 40 + len(data)),  # Total Length
                (">H", 0),  # Identification
                (">H", 0x4000),  # Flags and Fragment Offset
                (">B", 0xFF),  # Time to Live
                (">B", 6),  # Protocol
                (">H", 0),  # Header Checksum
                (">I", src_addr),  # Source Address
                (">I", dst_addr),  # Destination Address
                # TCP header
                (">H", src_port),  # Source Port
                (">H", dst_port),  # Destination Port
                (">I", seq),  # Sequence Number
                (">I", ack),  # Acknowledgment Number
                (">H", 0x5018),  # Header Length and Flags
                (">H", 0xFFFF),  # Window Size
                (">H", 0),  # Checksum
                (">H", 0)):  # Urgent Pointer
            pcap_file.write(struct.pack(writes[0], writes[1]))
        pcap_file.write(data)

        if function == "SSL_read":
            server_sent += len(data)
        else:
            client_sent += len(data)
        self.ssl_sessions[ssl_session_id] = (client_sent, server_sent)

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
        self.outlog("\n"+res)

        self.log_pcap(self.pcap_file, p["ssl_session_id"], p["function"], p["src_addr"],
                 p["src_port"], p["dst_addr"], p["dst_port"], data)


    def default_message(self,p):
        if "appinfo" in p:
            self.loadAppInfoSignel.emit(p["appinfo"])
        elif "appinfo_search" in p:
            self.searchAppInfoSignel.emit(p["appinfo_search"])
        elif "class_list" in p:
            self.classListSignel.emit(p["class_list"])
        elif "scanInfoList" in p:
            self.searchMemorySignel.emit("searchMem",p["scanInfoList"])
        elif "scanlog" in p:
            self.searchMemorySignel.emit("outlog", p["scanlog"])
        elif "breakout" in p:
            self.setBreakSignel.emit(p["breakout"])
        self.outlog(str(p["data"]))


    def sktrace_message(self,p):
        if "data" in p:
            self.outlog(p["data"])
            return
        optype=p["type"]
        if optype=="inst":
            # print(p)
            inst=json.loads(p["val"])
            address=int(p["address"],16)
            oplist=[]
            for opdata in inst["operands"]:
                if opdata["type"]=="reg":
                    if opdata["value"] not in oplist:
                        oplist.append(opdata["value"])
                elif opdata["type"]=="mem":
                    memdata=opdata["value"]
                    if memdata["base"] not in oplist:
                        oplist.append(memdata["base"])
            enddata = ""
            for item in oplist:
                enddata+="%s={%s} "%(item,item)
            outdata="tid:%s address:%s %s %s\t\t//%s"%(str(p["tid"]),str(hex(address)),inst["mnemonic"],inst["opStr"],enddata)
            self.outlog(outdata)
        elif optype=="ctx":
            context=json.loads(p["val"])
            address=int(p["address"],16)
            self.outlog("tid:" +str(p["tid"])+" address:"+str(hex(address))+" context:"+ p["val"])
        else:
            self.outlog(json.dumps(p))

    def fcand_jnitrace_message(self,p):
        data=p["data"]
        try:
            dataJson=eval(data)
            msg=json.dumps(dataJson,indent=2)
            self.outlog(msg)
        except:
            self.outlog(data)

    def other_message(self,p):
        self.outlog(str(p["data"]))

    # def showMethods(self,postdata):
    #     postdata["func"]="showMethod"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post showMethods:"+postdata["className"]+","+postdata["methodName"])
    # 
    # def showExport(self,moduleName,methodName):
    #     self.default_script.showexport(moduleName,methodName)
    #     self.log("post showExport:"+postdata["moduleName"]+","+postdata["methodName"])
    # 
    # def dumpPtr(self,postdata):
    #     postdata["func"] = "dumpPtr"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post dumpPtr:" + postdata["moduleName"] + "," + str(hex(postdata["address"])))
    # 
    # def dumpSoPtr(self,postdata):
    #     postdata["func"] = "dumpSoPtr"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post dumpSoPtr:" + postdata["moduleName"])
    # 
    # def searchInfo(self,postdata):
    #     postdata["func"] = "searchInfo"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post searchInfo")
    # 
    # def newScanProtect(self,postdata):
    #     postdata["func"] = "newScanProtect"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post newScanProtect")
    # 
    # def newScanByAddress(self,postdata):
    #     postdata["func"] = "newScanByAddress"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post newScanByAddress")
    # 
    # def getInfo(self,postdata):
    #     postdata["func"] = "getInfo"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post getInfo")
    # 
    # def setBreak(self,postdata):
    #     postdata["func"] = "setBreak"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post setBreak")
    # 
    # def nextScan(self,postdata):
    #     postdata["func"] = "nextScan"
    #     self.default_script.post({'type': 'input', 'payload': postdata})
    #     self.log("post nextScan")

    def newScanProtect(self,postdata):
        postdata["func"] = "newScanProtect"
        self.default_script.post({'type': 'input', 'payload': postdata})
        self.log("post newScanProtect")

    def newScanByAddress(self,postdata):
        postdata["func"] = "newScanByAddress"
        self.default_script.post({'type': 'input', 'payload': postdata})
        self.log("post newScanByAddress")

    def fart(self,fartType,classes):
        # postdata["func"] = "fart"
        # self.default_script.post({'type': 'input', 'payload': postdata})
        # self.log("post fart")
        api=self.default_script.exports
        if fartType==1:                 #使用frida的fart处理部分类
            api.fartclass(classes)
        elif fartType==2:               #使用frida的fart
            api.fart()
        elif fartType==3:               #使用rom的fart处理部分类
            api.romfartclass(classes)
        elif fartType==4:               #使用rom的fart完整处理
            api.romfart()

    def dumpdex(self):
        api = self.default_script.exports
        api.dumpdex()

    def on_message(self,message, data):
        if message["type"] == "error":
            print("[DEBUG] on_message ERROR: %s" % json.dumps(message)[:300])
            self.outlog(json.dumps(message))
            return
        payload = message.get("payload", {})
        # 调试：打印所有非 error 消息的 key
        if isinstance(payload, dict):
            print("[DEBUG] on_message: keys=%s" % list(payload.keys()))
        else:
            print("[DEBUG] on_message: payload type=%s, val=%s" % (type(payload), str(payload)[:200]))
        if "init" in payload:
            self.outlog(payload["init"])
            self.log(payload["init"])
            return
        if "jsname" not in payload:
            print("[DEBUG] on_message: no jsname, payload=%s" % str(payload)[:200])
            return

        # 调试：检查 class_list 消息
        if "class_list" in payload:
            print("[DEBUG] on_message: class_list found, count=%d" % len(payload["class_list"]))

        if payload["jsname"]=="default":
            self.default_message(payload)
            return
        elif message["payload"]["jsname"]=="r0capture":
            self.r0capture_message(message["payload"],data)
        elif message["payload"]["jsname"]=="sktrace":
            self.sktrace_message(message["payload"])
        elif message["payload"]["jsname"] == "FCAnd_Jnitrace":
            self.fcand_jnitrace_message(message["payload"])
        else:
            self.other_message(message["payload"])

    def _on_child_added(self,child):
        print("_on_child_added")
        for item in self.hooksData:
            self._attach(child.pid,item)
        self._attach(child.pid, "default")

    def run(self):
        if self.connType=="usb":
            # self.device.on("child-added", self._on_child_added)
            custom_port = (self.customPort or "").strip()
            if len(custom_port)>0:
                str_host = "%s:%s" % ("127.0.0.1", custom_port)
                manager = frida.get_device_manager()
                self.device = manager.add_remote_device(str_host)
            else:
                if self.usb_device_id:
                    manager = frida.get_device_manager()
                    try:
                        self.device = manager.get_device(self.usb_device_id, timeout=5)
                    except Exception:
                        self.device = frida.get_usb_device()
                else:
                    self.device = frida.get_usb_device()
        elif self.connType=="wifi":
            str_host = "%s:%s"%(self.address,self.port)
            manager = frida.get_device_manager()
            self.device = manager.add_remote_device(str_host)

        if self.attachType=="attachCurrent":
            try:
                application = self.device.get_frontmost_application()
            except Exception as err:
                self.log("附加异常,application is None err:%s"%err)
                self.attachOverSignel.emit("ERROR.无法获取到进程列表")
                return
            if application == None:
                self.log("附加异常,application is None")
                self.attachOverSignel.emit("ERROR.无法获取到进程列表")
                return

            target = 'Gadget' if application.identifier == 're.frida.Gadget' else application.name
            packageName=application.identifier
            if len(self.attachName) <= 0:
                for process in self.device.enumerate_processes():
                    if target == process.name:
                        self.attachName = process.name
                        break
                    if packageName== process.name:
                        self.attachName = packageName
                        break

        self._attach(self.attachName)
        print("thread over")
        # self.taskOverSignel.emit()


    #DEXDump相关的
    def dex_fix(self,dex_bytes):
        import struct
        dex_size = len(dex_bytes)

        if dex_bytes[:4] != b"dex\n":
            dex_bytes = b"dex\n035\x00" + dex_bytes[8:]

        if dex_size >= 0x24:
            dex_bytes = dex_bytes[:0x20] + struct.Struct("<I").pack(dex_size) + dex_bytes[0x24:]

        if dex_size >= 0x28:
            dex_bytes = dex_bytes[:0x24] + struct.Struct("<I").pack(0x70) + dex_bytes[0x28:]

        if dex_size >= 0x2C and dex_bytes[0x28:0x2C] not in [b'\x78\x56\x34\x12', b'\x12\x34\x56\x78']:
            dex_bytes = dex_bytes[:0x28] + b'\x78\x56\x34\x12' + dex_bytes[0x2C:]

        return dex_bytes

    def dump(self,pkg_name, api, mds=None):
        """
        """
        if mds is None:
            mds = []
        matches = api.scandex()
        for info in matches:
            try:
                bs = api.memorydump(info['addr'], info['size'])
                md = md5(bs)
                if md in mds:
                    self.outlog("[DEXDump]: Skip duplicate dex {}<{}>".format(info['addr'], md))
                    continue
                mds.append(md)
                savePath="./FRIDA_DEXDump/" + pkg_name + "/"
                if not os.path.exists(savePath):
                    os.makedirs(savePath)
                bs = self.dex_fix(bs)
                with open(savePath + info['addr'] + ".dex", 'wb') as out:
                    out.write(bs)
                self.outlog("[DEXDump]: DexSize={}, DexMd5={}, SavePath={}/{}.dex"
                            .format(hex(info['size']), md, savePath, info['addr']))
            except Exception as e:
                self.outlog("[Except] - {}: {}".format(e, info))
