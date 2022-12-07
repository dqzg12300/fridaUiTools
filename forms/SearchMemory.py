from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QMessageBox, QHeaderView, QTableWidgetItem, QMenu, QAction

from forms.fbreak import handle_exception, data_info
from forms.fbreak.handle_excepetion_info import exception_info
from forms.fbreak.rpcFunc import rpcFunc
from ui.searchMemory import Ui_searchMemory


class searchMemoryForm(QDialog,Ui_searchMemory):
    def __init__(self, parent=None):
        super(searchMemoryForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnSearch.clicked.connect(self.search)
        self.btnHexDump.clicked.connect(self.hexDump)
        self.btnCString.clicked.connect(self.cstring)
        self.btnBreak.clicked.connect(self.setBreak)
        self.btnModules.clicked.connect(self.showModules)

        self.searchHistory= []
        self.searchResult=""

        self.header = ["序号","值", "地址","备注"]

        self.tabHistory.clear()
        self.tabHistory.setColumnCount(4)
        self.tabHistory.setRowCount(0)
        self.tabHistory.setHorizontalHeaderLabels(self.header)
        self.tabHistory.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabHistory.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabHistory.customContextMenuRequested[QPoint].connect(self.rightMenuShow)

        self.txtResult.setContextMenuPolicy(Qt.CustomContextMenu)
        self.txtResult.customContextMenuRequested[QPoint].connect(self.logRightMenuShow)

        self.th = None
    def init(self):
        data_info.rpc = rpcFunc(self.th.default_script.exports)
        data_info.proc_info['arch'] = data_info.rpc.get_device_arch()
        data_info.proc_info['platform'] = data_info.rpc.get_platform()
        data_info.proc_info['pointersize'] = data_info.rpc.get_pointer_size()
        data_info.proc_info['pagesize'] = data_info.rpc.get_page_size()
        data_info.proc_info['mem_protect'] = data_info.rpc.get_protect_ranges()

    def remake_memprotect_info(self):
        for item in data_info.proc_info['mem_protect']:
            item['base'] = int(item['base'], 16)

    def pointersize_pagesize_to_maskcode(self,pointer_size, page_size):
        pointer_mask = 'ff' * pointer_size
        page_size_len = 0
        while page_size != 1:
            page_size = page_size / 0x10
            page_size_len = page_size_len + 1
        pointer_mask_list = list(pointer_mask)
        pointer_mask_list[2 * pointer_size - page_size_len:] = '0' * page_size_len
        pointer_mask = ''.join(pointer_mask_list)
        return int(pointer_mask, 16)
    def get_breakinfo(self):
        ret_list = []
        for item in data_info.proc_info['mem_protect']:
            if data_info.break_point_info['break_addr'] + data_info.break_point_info['break_len'] in range(item['base'],
                                                                                                 item['base'] + item[
                                                                                                     'size']):
                ret_list = [data_info.break_point_info['break_addr'] & self.pointersize_pagesize_to_maskcode(
                    data_info.proc_info['pointersize'], data_info.proc_info['pagesize']), item['protection']]
                data_info.break_point_info['break_page_info'] = ret_list
                break

        if [] == ret_list:
            raise Exception('get_break_info the break pointer must be in a segement')

    def set_breakpoint(self):
        point = data_info.break_point_info['break_page_info']
        data_info.rpc.set_page_protect(point[0], '---')
        data_info.rpc.set_exception_handler()

    def wrapper_to_post(self,_type, content):
        return {'type': _type, 'payload': content}

    def find_soft_breakpoint_from_list(self,addr: int):
        with data_info.soft_breakpoint_runtime_lock:
            breakpoint_list_len = len(data_info.soft_breakpoint_runtime)
            if 0 != breakpoint_list_len:
                for index in range(0, breakpoint_list_len):
                    if data_info.soft_breakpoint_runtime[index]['break_addr'] == addr:
                        return index
            return -1
    def my_message_handler(self,messgae_data):
        try:
            if 'exception' == messgae_data['__tag']:
                handle_exception.handle(messgae_data)
            # 从js脚本那收到的设置软断点的信息，并把此保存到soft_breakpoint_runtime
            elif 'set_soft_breakpoint' == messgae_data['__tag']:
                addr = int(messgae_data['break_addr'], 16)
                index = self.find_soft_breakpoint_from_list(addr)
                # 多线程访问
                if -1 != index:
                    data_info.rpc.api._script.post(self.wrapper_to_post('set_soft_breakpoint_ret', 0))
                    return
                else:
                    save_soft_breakpoint = data_info.soft_breakpoint_struct.copy()
                    save_soft_breakpoint['break_addr'] = int(messgae_data['break_addr'], 16)
                    save_soft_breakpoint['break_len'] = messgae_data['break_len']
                    save_soft_breakpoint['ins_content'] = messgae_data['ins_content']
                with data_info.soft_breakpoint_runtime_lock:
                    pass
                    # TODO
                    data_info.soft_breakpoint_runtime.append(save_soft_breakpoint)
                data_info.rpc.api._script.post(self.wrapper_to_post('set_soft_breakpoint_ret', 0))
            elif 'resume_soft_breakpoint' == messgae_data['__tag']:
                addr = int(messgae_data['addr'], 16)

                # 删除指定断点
                index = self.find_soft_breakpoint_from_list(addr)
                if -1 != index:
                    with data_info.soft_breakpoint_runtime_lock:
                        pass
                else:
                    raise Exception('soft_breakpoint no found')

                send_dict = {}
                send_dict['msg'] = 1
                data_info.rpc.api._script.post(self.wrapper_to_post('resume_soft_breakpoint_ret', send_dict))
            elif 'show_details' == messgae_data['__tag']:
                # exception_info(messgae_data, data_info.proc_info['arch']).print_info()
                info= exception_info(messgae_data, data_info.proc_info['arch']).get_info()
                self.appendResult(info)
        except :
            pass

    def showModules(self):
        modules=data_info.rpc.get_modules()
        if self.txtModule.text() == '':
            self.appendResult(str(modules))
        else:
            flag=False
            for module in modules:
                if self.txtModule.text() in module['name']:
                    self.appendResult(str(module))
                    flag=True
            if flag==False:
                self.appendResult("没有找到指定模块")
            

    def setBreak(self):
        module = self.txtModule.text()
        symbol = self.txtSymbol.text()
        offset = self.txtOffset.text()
        abaddress= self.txtAbAddress.text()
        breakSize=self.txtBreakSize.text()
        if len(breakSize)<=0:
            QMessageBox.warning(self, "提示", "请输入断点大小")
            return

        if breakSize.startswith("0x"):
            size = int(breakSize, 16)
        else:
            size = int(breakSize)

        data_info.break_point_info['break_len'] =size
        if len(module) > 0:
            moduleBase=data_info.rpc.get_module(module)
            baseAddr= int(moduleBase["base"], 16)
            self.appendResult("模块%s基址为：0x%x" % (module,baseAddr))

        if len(abaddress)>0:
            data_info.break_point_info['break_addr'] = int(abaddress, 16)
            flag=True
        elif len(module)>0 and len(symbol)>0:
            data_info.break_point_info['break_addr'] = int(data_info.rpc.get_export_by_name(module, symbol), 16)
            flag = True
        elif len(module)>0 and len(offset)>0:
            data_info.break_point_info['break_addr'] = baseAddr + int(offset, 16)
            flag=True
        if flag:
            self.remake_memprotect_info()
            self.get_breakinfo()
            self.set_breakpoint()
            self.appendResult(str(data_info.break_point_info))


        # postdata = {"start": base, "size": size, "protect": protect}
        # self.th.setBreak(postdata)



    def logRightMenuShow(self):
        rightMenu = QMenu(self.txtResult)
        clearAction = QAction(u"清空", self, triggered=self.clearResultLog)
        rightMenu.addAction(clearAction)
        rightMenu.exec_(QCursor.pos())

    def clearResultLog(self):
        self.txtResult.clear()

    def selectModule(self):
        protect_modules = data_info.rpc.get_protect_ranges()
        modules=data_info.rpc.get_modules()
        for item in self.tabHistory.selectedItems():
            # 因为patch是多个的。所以移除的时候要注意。不然会全部移掉的。
            addr=int(self.tabHistory.item(item.row(), 2).text(),16)
            for module in protect_modules:
                moduleBase=int(module["base"],16)
                moduleSize=int(module["size"])
                if addr>moduleBase and addr<(moduleBase+moduleSize):
                    self.appendResult(str(module))
                    break
            for module in modules:
                moduleBase=int(module["base"],16)
                moduleSize=int(module["size"])
                if addr>moduleBase and addr<(moduleBase+moduleSize):
                    self.appendResult(str(module))
                    break
                    
            

    def rightMenuShow(self):
        rightMenu = QMenu(self.tabHistory)
        clearAction = QAction(u"清空", self, triggered=self.clearHistory)
        rightMenu.addAction(clearAction)
        selectModuleAction = QAction(u"查询所属module", self, triggered=self.selectModule)
        rightMenu.addAction(selectModuleAction)

        rightMenu.exec_(QCursor.pos())

    def clearHistory(self):
        self.tabHistory.clearContents()
        self.tabHistory.setRowCount(0)
        self.tabHistory.setHorizontalHeaderLabels(self.header)

    def cstring(self):
        base = self.txtBase.text()
        if len(base) <= 0:
            QMessageBox.warning(self, "提示", "请输入起始地址")
            return
        try:
            if "+" in base:
                base = base.split("+")[0]
                offset=base.split("+")[1]
                if "0x" in base:
                    base = int(base, 16)
                if "0x" in offset:
                    offset = int(offset, 16)
                base=base+offset
            else:
                if "0x" in base:
                    base = int(base, 16)
                else:
                    base = int(base)
        except:
            QMessageBox.warning(self, "提示", "请输入正确的地址")
            return
        res = data_info.rpc.cstring(base)
        self.appendResult(res)

    def hexDump(self):
        base = self.txtBase.text()
        baseSize = self.txtSize.text()
        if len(base) <= 0:
            QMessageBox.warning(self, "提示", "请输入起始地址")
            return
        if len(baseSize) <= 0:
            QMessageBox.warning(self, "提示", "请输入范围大小")
            return
        try:
            if "+" in base:
                baseSp=base.split("+")
                base = baseSp[0]
                offset=baseSp[1]
                if "0x" in base:
                    base = int(base, 16)
                if "0x" in offset:
                    offset = int(offset, 16)
                base=base+offset
            else:
                if "0x" in base:
                    base = int(base, 16)
                else:
                    base = int(base)
        except:
            QMessageBox.warning(self, "提示", "请输入正确的地址")
            return
        
        if baseSize.startswith("0x"):
            size = int(baseSize, 16)
        else:
            size=int(baseSize)
        res= data_info.rpc.hexdump(base, size)
        self.appendResult(res)

    def appendHistory(self,data):
        historyData=eval(data)
        idx=1
        for line in historyData:
            self.tabHistory.insertRow(0)
            self.tabHistory.setItem(0, 0, QTableWidgetItem("%s"%idx))
            self.tabHistory.setItem(0, 1, QTableWidgetItem(f"{line['value']}"))
            self.tabHistory.setItem(0, 2, QTableWidgetItem(line["key"]))
            self.tabHistory.setItem(0, 3, QTableWidgetItem(line["bak"]))
            idx+=1
        # self.appendResult(str(data))
        QMessageBox.information(self, "提示", f"搜索完成,检索到{len(historyData)}条结果")

    def appendResult(self, result):
        self.txtResult.appendPlainText(result)

    def search(self):
        input=self.txtInput.text()
        if len(input) == 0:
            QMessageBox.warning(self, "提示", "请输入搜索内容")
            return

        base=self.txtBase.text()
        baseSize=self.txtSize.text()
        value=input
        size=0
        if self.rdoInt.isChecked():
            try:
                if "0x" in input:
                    value=int(input,16)
                else:
                    value=int(input)
            except:
                QMessageBox.warning(self, "提示", "请输入正确的整数")
                return
            size = 1
            if value<=0xff:
                size=1
            elif value<=0xffff:
                size=2
            elif value <= 0xffffffff:
                size = 4
            elif value <= 0xffffffffffffffff:
                size = 8
        elif self.rdoStr.isChecked():
            size=""
        protect="rw"
        if self.txtProtect.text()!="":
            protect=self.txtProtect.text()

        if len(base) <= 0:
            postdata = {"protect":protect, "value": value, "size": size,"bak":self.txtBak.text()}
            self.th.newScanProtect(postdata)
        else:
            if len(baseSize) <= 0:
                QMessageBox.warning(self, "提示", "请输入范围大小")
                return
            postdata={"start":base,"end":base+baseSize,"value":value,"size":size,"bak":self.txtBak.text()}
            self.th.newScanByAddress(postdata)

