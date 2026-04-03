import concurrent.futures
import json
import math
import os
import re
import struct
import threading
import time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor, QFont
from PyQt5.QtWidgets import (
    QAction,
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QMenu,
    QMessageBox,
    QTableWidgetItem,
)

from forms.fbreak import data_info, handle_exception
from forms.fbreak.handle_excepetion_info import exception_info
from forms.fbreak.rpcFunc import rpcFunc
from ui.searchMemory import Ui_searchMemory


class MemorySearchWorker(QtCore.QThread):
    progress = QtCore.pyqtSignal(str)
    resultBatch = QtCore.pyqtSignal(list)
    finishedSummary = QtCore.pyqtSignal(dict)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, rpc, ranges, pattern, worker_count, result_limit, display_value, note):
        super(MemorySearchWorker, self).__init__()
        self.rpc = rpc
        self.ranges = ranges or []
        self.pattern = pattern
        self.worker_count = max(1, int(worker_count or 1))
        self.result_limit = max(1, int(result_limit or 1))
        self.display_value = display_value
        self.note = note or ""
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def _per_range_limit(self):
        if len(self.ranges) <= 0:
            return self.result_limit
        estimate = int(math.ceil(float(self.result_limit) / float(len(self.ranges))))
        return max(32, min(self.result_limit, estimate * 4))

    def _scan_one_range(self, range_info, per_range_limit):
        if self._cancel_event.is_set():
            return []
        addresses = self.rpc.scan_range(range_info["base"], range_info["size"], self.pattern, per_range_limit)
        results = []
        for address in addresses:
            if self._cancel_event.is_set():
                break
            address_text = str(address)
            results.append({
                "address": address_text,
                "value": self.display_value,
                "note": self.note,
                "module": range_info.get("moduleName", ""),
                "protection": range_info.get("protection", ""),
                "regionBase": range_info.get("base", ""),
                "regionSize": range_info.get("size", 0),
                "filePath": range_info.get("filePath", ""),
            })
        return results

    def _submit_next_range(self, executor, future_map, range_iter, per_range_limit):
        if self._cancel_event.is_set():
            return False
        try:
            range_info = next(range_iter)
        except StopIteration:
            return False
        future = executor.submit(self._scan_one_range, range_info, per_range_limit)
        future_map[future] = range_info
        return True

    def run(self):
        if len(self.ranges) <= 0:
            self.failed.emit("没有可扫描的内存范围")
            return
        start_time = time.time()
        per_range_limit = self._per_range_limit()
        total_ranges = len(self.ranges)
        completed = 0
        collected = []
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                future_map = {}
                range_iter = iter(self.ranges)
                while len(future_map) < self.worker_count and self._submit_next_range(executor, future_map, range_iter, per_range_limit):
                    pass
                while len(future_map) > 0:
                    done, _ = concurrent.futures.wait(
                        tuple(future_map.keys()),
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                    for future in done:
                        range_info = future_map.pop(future, {})
                        completed += 1
                        try:
                            batch = future.result()
                        except Exception as ex:
                            self.progress.emit("扫描范围失败: %s (%s)" % (range_info.get("base", ""), str(ex)))
                            batch = []
                        if batch:
                            remaining = self.result_limit - len(collected)
                            if remaining <= 0:
                                self._cancel_event.set()
                                batch = []
                            elif len(batch) > remaining:
                                batch = batch[:remaining]
                            if batch:
                                collected.extend(batch)
                                self.resultBatch.emit(batch)
                                self.progress.emit("命中 %d 条，最近范围 %s" % (len(collected), range_info.get("base", "")))
                                if len(collected) >= self.result_limit:
                                    self._cancel_event.set()
                        elif completed % 16 == 0:
                            self.progress.emit("已扫描 %d / %d 个内存范围" % (completed, total_ranges))
                        if not self._cancel_event.is_set():
                            self._submit_next_range(executor, future_map, range_iter, per_range_limit)
            elapsed = time.time() - start_time
            self.finishedSummary.emit({
                "count": len(collected),
                "scannedRanges": completed,
                "totalRanges": total_ranges,
                "elapsed": elapsed,
                "cancelled": self._cancel_event.is_set(),
                "limitReached": len(collected) >= self.result_limit,
            })
        except Exception as ex:
            self.failed.emit(str(ex))


class searchMemoryForm(QDialog, Ui_searchMemory):
    def __init__(self, parent=None):
        super(searchMemoryForm, self).__init__(parent)
        self.setupUi(self)
        self._translate = QtCore.QCoreApplication.translate
        self.th = None
        self.searchWorker = None
        self.rangeCache = []
        self.moduleCache = []
        self.searchResults = []
        self.breakpointEvents = []
        self._setupUiState()
        self._bindSignals()

    def _setupUiState(self):
        fixed_font = QFont("Monospace")
        fixed_font.setStyleHint(QFont.TypeWriter)
        self.txtHexDump.setFont(fixed_font)
        self.txtBreakpointDetails.setFont(fixed_font)
        self.txtConsole.setFont(fixed_font)

        self.cmbValueType.clear()
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "UTF-8 字符串"), "utf8")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "十六进制字节"), "bytes")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "Int32"), "i32")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "UInt32"), "u32")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "Int64"), "i64")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "UInt64"), "u64")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "Float"), "f32")
        self.cmbValueType.addItem(self._translate("searchMemoryForm", "Double"), "f64")

        self.cmbProtect.clear()
        for item in ["all", "rw-", "r--", "r-x", "rwx", "---"]:
            self.cmbProtect.addItem(item)
        self.cmbProtect.setCurrentText("rw-")

        cpu_count = os.cpu_count() or 4
        self.spinWorkers.setValue(max(1, min(cpu_count, 4)))
        self.spinResultLimit.setValue(500)
        self.spinInspectBytes.setValue(128)
        self.spinDisasmCount.setValue(24)
        self.spinBreakSize.setValue(4)

        self.txtSearchValue.setPlaceholderText(self._translate("searchMemoryForm", "输入字符串、数字或十六进制字节"))
        self.txtSearchBase.setPlaceholderText("0x0")
        self.txtSearchSize.setPlaceholderText("0x1000")
        self.txtModuleFilter.setPlaceholderText(self._translate("searchMemoryForm", "可选，按模块名或路径过滤"))
        self.txtSearchNote.setPlaceholderText(self._translate("searchMemoryForm", "给本次搜索加备注，便于区分"))
        self.txtInspectAddress.setPlaceholderText("0x0")
        self.txtBreakModule.setPlaceholderText("libtarget.so")
        self.txtBreakOffset.setPlaceholderText("0x1234")
        self.txtBreakSymbol.setPlaceholderText("symbol_name")
        self.txtBreakAddress.setPlaceholderText("0x0")

        self.btnSearchStop.setEnabled(False)

        self.resultHeaders = [
            self._translate("searchMemoryForm", "地址"),
            self._translate("searchMemoryForm", "模块"),
            self._translate("searchMemoryForm", "保护"),
            self._translate("searchMemoryForm", "范围"),
            self._translate("searchMemoryForm", "匹配值"),
            self._translate("searchMemoryForm", "备注"),
        ]
        self.tabResults.setColumnCount(len(self.resultHeaders))
        self.tabResults.setHorizontalHeaderLabels(self.resultHeaders)
        self.tabResults.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabResults.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabResults.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabResults.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabResults.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabResults.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabResults.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabResults.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabResults.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabResults.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabResults.verticalHeader().setVisible(False)
        self.tabResults.verticalHeader().setDefaultSectionSize(28)

        self.disasmHeaders = [
            self._translate("searchMemoryForm", "地址"),
            self._translate("searchMemoryForm", "模块"),
            self._translate("searchMemoryForm", "符号"),
            self._translate("searchMemoryForm", "指令"),
        ]
        self.tabDisasm.setColumnCount(len(self.disasmHeaders))
        self.tabDisasm.setHorizontalHeaderLabels(self.disasmHeaders)
        self.tabDisasm.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabDisasm.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabDisasm.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabDisasm.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabDisasm.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabDisasm.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabDisasm.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabDisasm.verticalHeader().setVisible(False)
        self.tabDisasm.verticalHeader().setDefaultSectionSize(26)

        self.breakpointEventHeaders = [
            self._translate("searchMemoryForm", "时间"),
            self._translate("searchMemoryForm", "类型"),
            self._translate("searchMemoryForm", "PC"),
            self._translate("searchMemoryForm", "目标地址"),
            self._translate("searchMemoryForm", "符号"),
            self._translate("searchMemoryForm", "指令"),
        ]
        self.tabBreakpointEvents.setColumnCount(len(self.breakpointEventHeaders))
        self.tabBreakpointEvents.setHorizontalHeaderLabels(self.breakpointEventHeaders)
        self.tabBreakpointEvents.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabBreakpointEvents.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabBreakpointEvents.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabBreakpointEvents.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabBreakpointEvents.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.tabBreakpointEvents.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabBreakpointEvents.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabBreakpointEvents.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabBreakpointEvents.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabBreakpointEvents.verticalHeader().setVisible(False)
        self.tabBreakpointEvents.verticalHeader().setDefaultSectionSize(28)

        self.registerHeaders = [
            self._translate("searchMemoryForm", "寄存器"),
            self._translate("searchMemoryForm", "值"),
        ]
        self.tabRegisters.setColumnCount(len(self.registerHeaders))
        self.tabRegisters.setHorizontalHeaderLabels(self.registerHeaders)
        self.tabRegisters.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabRegisters.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabRegisters.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabRegisters.verticalHeader().setVisible(False)
        self.tabRegisters.verticalHeader().setDefaultSectionSize(24)

        self.labSearchStatus.setText(self._translate("searchMemoryForm", "等待开始搜索"))
        self.labInspectSummary.setText(self._translate("searchMemoryForm", "尚未选择地址"))
        self.labBreakpointEventSummary.setText(self._translate("searchMemoryForm", "尚未命中断点"))

    def _bindSignals(self):
        self.btnSearchAll.clicked.connect(self.searchAll)
        self.btnSearchRange.clicked.connect(self.searchInRange)
        self.btnSearchStop.clicked.connect(self.stopSearch)
        self.btnRefreshRanges.clicked.connect(self.refreshRuntimeSnapshot)
        self.btnClearResults.clicked.connect(self.clearResults)
        self.btnInspect.clicked.connect(self.inspectAddress)
        self.btnUseSelectedForInspect.clicked.connect(self.useSelectedAddressForInspect)
        self.btnUseSelectedForBreak.clicked.connect(self.useSelectedAddressForBreakpoint)
        self.btnResolveBreakAddress.clicked.connect(self.resolveBreakpointAddress)
        self.btnSetBreakpoint.clicked.connect(self.setBreak)
        self.btnShowModules.clicked.connect(self.showModules)
        self.tabResults.itemSelectionChanged.connect(self.onResultSelectionChanged)
        self.tabResults.itemDoubleClicked.connect(lambda _: self.inspectSelectedResult())
        self.tabResults.customContextMenuRequested[QPoint].connect(self.resultMenuShow)
        self.txtConsole.setContextMenuPolicy(Qt.CustomContextMenu)
        self.txtConsole.customContextMenuRequested[QPoint].connect(self.consoleMenuShow)
        self.tabBreakpointEvents.itemSelectionChanged.connect(self.onBreakpointEventSelectionChanged)

    def init(self):
        if not self.ensureRuntime(show_message=False):
            return
        self.refreshRuntimeSnapshot(show_message=False, ensure_runtime=False)

    def ensureRuntime(self, show_message=True):
        if self.th is None or not hasattr(self.th, "default_script") or self.th.default_script is None:
            data_info.rpc = None
            self.labSearchStatus.setText(self._translate("searchMemoryForm", "未附加进程"))
            if show_message:
                QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "请先附加进程后再使用内存工作台"))
            return False
        try:
            data_info.rpc = rpcFunc(self.th.default_script.exports)
            data_info.proc_info["arch"] = data_info.rpc.get_device_arch()
            data_info.proc_info["platform"] = data_info.rpc.get_platform()
            data_info.proc_info["pointersize"] = data_info.rpc.get_pointer_size()
            data_info.proc_info["pagesize"] = data_info.rpc.get_page_size()
            return True
        except Exception as ex:
            data_info.rpc = None
            self.labSearchStatus.setText(self._translate("searchMemoryForm", "运行时不可用"))
            self.appendResult(self._translate("searchMemoryForm", "初始化内存工作台失败: ") + str(ex))
            if show_message:
                QMessageBox.warning(self, "hint", str(ex))
            return False

    def collectAllRuntimeRanges(self):
        if data_info.rpc is None:
            return []
        protections = ["---", "r--", "rw-", "r-x", "rwx", "--x", "-w-", "-wx"]
        merged = {}
        for protection in protections:
            try:
                ranges = data_info.rpc.enumerate_ranges(protection, False)
            except Exception:
                continue
            for range_info in ranges:
                normalized = self.normalizeRange(range_info)
                key = (normalized["base"], normalized["size"], normalized["protection"])
                merged[key] = normalized
        return sorted(merged.values(), key=lambda item: item["base_int"])

    def readRangesByProtection(self, protection_text):
        if data_info.rpc is None:
            return []
        normalized = (protection_text or "").strip().lower()
        if normalized in ("all", "*", "any"):
            return list(self.collectAllRuntimeRanges())
        return [self.normalizeRange(rng) for rng in data_info.rpc.enumerate_ranges(protection_text, False)]

    def refreshRuntimeSnapshot(self, show_message=True, ensure_runtime=True):
        if ensure_runtime and not self.ensureRuntime(show_message=show_message):
            return False
        if data_info.rpc is None:
            return False
        try:
            self.moduleCache = [self.normalizeModule(module) for module in data_info.rpc.get_modules()]
            data_info.proc_info["mem_protect"] = self.collectAllRuntimeRanges()
            self.rangeCache = self.readRangesByProtection(self.currentProtectFilter())
            self.appendResult(self._translate("searchMemoryForm", "已刷新模块与内存范围，共 %d 个范围") % len(self.rangeCache))
            if show_message:
                self.labSearchStatus.setText(self._translate("searchMemoryForm", "内存图已刷新，共 %d 个范围") % len(self.rangeCache))
            return True
        except Exception as ex:
            self.appendResult(self._translate("searchMemoryForm", "刷新内存图失败: ") + str(ex))
            if show_message:
                QMessageBox.warning(self, "hint", str(ex))
            return False

    def normalizeModule(self, module):
        base_value = module.get("base", 0)
        if isinstance(base_value, str):
            base_int = int(base_value, 16)
            base_text = base_value
        else:
            base_int = int(base_value)
            base_text = hex(base_int)
        size_value = int(module.get("size", 0))
        return {
            "name": module.get("name", ""),
            "path": module.get("path", ""),
            "base": base_text,
            "base_int": base_int,
            "size": size_value,
        }

    def normalizeRange(self, range_info):
        base_value = range_info.get("base", 0)
        if isinstance(base_value, str):
            base_int = int(base_value, 16)
            base_text = base_value
        else:
            base_int = int(base_value)
            base_text = hex(base_int)
        size_value = int(range_info.get("size", 0))
        module_name = range_info.get("moduleName", "")
        if len(module_name) <= 0:
            module_info = self.findModuleByAddressInt(base_int)
            module_name = module_info.get("name", "") if module_info else ""
        return {
            "base": base_text,
            "base_int": base_int,
            "size": size_value,
            "protection": range_info.get("protection", ""),
            "filePath": range_info.get("filePath", ""),
            "moduleName": module_name,
        }

    def currentProtectFilter(self):
        protect = (self.cmbProtect.currentText() or "").strip()
        return protect if len(protect) > 0 else "rw-"

    def parseNumber(self, value_text):
        value_text = (value_text or "").strip().replace("_", "")
        if len(value_text) <= 0:
            raise ValueError(self._translate("searchMemoryForm", "请输入数值"))
        return int(value_text, 16) if value_text.lower().startswith("0x") else int(value_text, 10)

    def parseFloat(self, value_text):
        value_text = (value_text or "").strip()
        if len(value_text) <= 0:
            raise ValueError(self._translate("searchMemoryForm", "请输入浮点数"))
        return float(value_text)

    def parseAddress(self, address_text):
        address_text = (address_text or "").strip()
        if len(address_text) <= 0:
            raise ValueError(self._translate("searchMemoryForm", "请输入起始地址"))
        if "+" in address_text:
            base_text, offset_text = address_text.split("+", 1)
            return self.parseNumber(base_text) + self.parseNumber(offset_text)
        return self.parseNumber(address_text)

    def parseRange(self, base_text, size_text):
        start = self.parseAddress(base_text)
        size = self.parseNumber(size_text)
        if size <= 0:
            raise ValueError(self._translate("searchMemoryForm", "范围大小必须大于0"))
        return start, size

    def encodeBytesToPattern(self, raw_bytes):
        return " ".join(["%02X" % byte for byte in raw_bytes])

    def encodeBytesToCompactPattern(self, raw_bytes):
        return raw_bytes.hex().upper()

    def parseHexPattern(self, input_text):
        tokens = [token for token in re.split(r"[\s,]+", input_text.strip()) if len(token) > 0]
        if len(tokens) <= 0:
            raise ValueError(self._translate("searchMemoryForm", "请输入十六进制字节"))
        parts = []
        for token in tokens:
            upper = token.upper()
            if upper in ("??", "?"):
                parts.append("??")
                continue
            if len(upper) == 1:
                upper = "0" + upper
            int(upper, 16)
            parts.append(upper)
        return " ".join(parts)

    def buildSearchPattern(self):
        value_type = self.cmbValueType.currentData()
        value_text = self.txtSearchValue.text().strip()
        if len(value_text) <= 0:
            raise ValueError(self._translate("searchMemoryForm", "请输入搜索内容"))
        if value_type == "utf8":
            return self.encodeBytesToCompactPattern(value_text.encode("utf-8")), value_text
        if value_type == "bytes":
            pattern = self.parseHexPattern(value_text)
            return pattern, pattern
        if value_type in ("i32", "u32", "i64", "u64"):
            number = self.parseNumber(value_text)
            if value_type == "i32":
                if number < -(2 ** 31) or number > (2 ** 31 - 1):
                    raise ValueError(self._translate("searchMemoryForm", "Int32 超出范围"))
                packed = struct.pack("<i", number)
            elif value_type == "u32":
                if number < 0 or number > (2 ** 32 - 1):
                    raise ValueError(self._translate("searchMemoryForm", "UInt32 超出范围"))
                packed = struct.pack("<I", number)
            elif value_type == "i64":
                if number < -(2 ** 63) or number > (2 ** 63 - 1):
                    raise ValueError(self._translate("searchMemoryForm", "Int64 超出范围"))
                packed = struct.pack("<q", number)
            else:
                if number < 0 or number > (2 ** 64 - 1):
                    raise ValueError(self._translate("searchMemoryForm", "UInt64 超出范围"))
                packed = struct.pack("<Q", number)
            return self.encodeBytesToPattern(packed), str(number)
        number = self.parseFloat(value_text)
        if value_type == "f32":
            packed = struct.pack("<f", number)
        elif value_type == "f64":
            packed = struct.pack("<d", number)
        else:
            raise ValueError(self._translate("searchMemoryForm", "不支持的搜索类型"))
        return self.encodeBytesToPattern(packed), str(number)

    def findModuleByAddressInt(self, address_int):
        for module in self.moduleCache:
            start = module["base_int"]
            end = start + module["size"]
            if start <= address_int < end:
                return module
        return None

    def findRangeByAddressInt(self, address_int):
        for range_info in data_info.proc_info.get("mem_protect", []):
            start = range_info["base_int"]
            end = start + range_info["size"]
            if start <= address_int < end:
                return range_info
        return None

    def formatRangeText(self, region_base, region_size):
        region_base = str(region_base or "").strip()
        size_value = int(region_size or 0)
        if len(region_base) <= 0 and size_value <= 0:
            return ""
        if len(region_base) <= 0:
            return "0x%x" % size_value
        if size_value <= 0:
            return region_base
        try:
            base_int = self.parseAddress(region_base)
            return "%s - 0x%x" % (region_base, base_int + size_value)
        except Exception:
            return "%s + 0x%x" % (region_base, size_value)

    def disconnectSearchWorker(self, worker):
        if worker is None:
            return
        signal_pairs = [
            (worker.progress, self.appendResult),
            (worker.resultBatch, self.addResultBatch),
            (worker.finishedSummary, self.onSearchFinished),
            (worker.failed, self.onSearchFailed),
        ]
        for signal, slot in signal_pairs:
            try:
                signal.disconnect(slot)
            except TypeError:
                pass

    def releaseSearchWorker(self, worker=None):
        target = worker or self.searchWorker
        if target is None:
            return
        if target is self.searchWorker:
            self.searchWorker = None
        self.disconnectSearchWorker(target)
        if not target.isRunning():
            target.deleteLater()

    def isStaleSearchSignal(self):
        sender = self.sender()
        return sender is not None and sender is not self.searchWorker

    def collectSearchRanges(self, use_explicit_range):
        module_filter = (self.txtModuleFilter.text() or "").strip().lower()
        if use_explicit_range:
            base_text = self.txtSearchBase.text().strip()
            size_text = self.txtSearchSize.text().strip()
            start, size = self.parseRange(base_text, size_text)
            module_info = self.findModuleByAddressInt(start)
            range_info = self.findRangeByAddressInt(start)
            return [{
                "base": hex(start),
                "base_int": start,
                "size": size,
                "protection": range_info.get("protection", self.currentProtectFilter()) if range_info else self.currentProtectFilter(),
                "filePath": range_info.get("filePath", module_info.get("path", "") if module_info else "") if range_info else (module_info.get("path", "") if module_info else ""),
                "moduleName": range_info.get("moduleName", module_info.get("name", "") if module_info else "") if range_info else (module_info.get("name", "") if module_info else ""),
            }]

        ranges = self.readRangesByProtection(self.currentProtectFilter())
        if len(module_filter) <= 0:
            return ranges
        filtered = []
        for range_info in ranges:
            module_name = (range_info.get("moduleName", "") or "").lower()
            file_path = (range_info.get("filePath", "") or "").lower()
            if module_filter in module_name or module_filter in file_path:
                filtered.append(range_info)
        return filtered

    def startSearch(self, use_explicit_range):
        if not self.ensureRuntime(show_message=True):
            return
        if len(self.moduleCache) <= 0 or len(data_info.proc_info.get("mem_protect", [])) <= 0:
            self.refreshRuntimeSnapshot(show_message=False, ensure_runtime=False)
        try:
            pattern, display_value = self.buildSearchPattern()
            ranges = self.collectSearchRanges(use_explicit_range)
        except Exception as error:
            QMessageBox.warning(self, "hint", str(error))
            return
        if len(ranges) <= 0:
            QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "没有找到可扫描的内存范围"))
            return

        if self.searchWorker is not None:
            if self.searchWorker.isRunning():
                if not self.stopSearch(wait_timeout=1500, quiet=True):
                    QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "上一次搜索仍在停止，请稍后再试"))
                    return
            else:
                self.releaseSearchWorker(self.searchWorker)
        self.clearResults()
        self.searchResults = []
        self.labSearchStatus.setText(self._translate("searchMemoryForm", "准备扫描 %d 个范围...") % len(ranges))
        self.appendResult(self._translate("searchMemoryForm", "搜索模式: ") + ("range" if use_explicit_range else "global"))
        self.appendResult(self._translate("searchMemoryForm", "搜索 pattern: ") + pattern)

        self.searchWorker = MemorySearchWorker(
            data_info.rpc,
            ranges,
            pattern,
            self.spinWorkers.value(),
            self.spinResultLimit.value(),
            display_value,
            self.txtSearchNote.text().strip(),
        )
        self.searchWorker.progress.connect(self.appendResult)
        self.searchWorker.resultBatch.connect(self.addResultBatch)
        self.searchWorker.finishedSummary.connect(self.onSearchFinished)
        self.searchWorker.failed.connect(self.onSearchFailed)
        self.searchWorker.finished.connect(self.searchWorker.deleteLater)
        self.btnSearchStop.setEnabled(True)
        self.searchWorker.start()

    def searchAll(self):
        self.startSearch(False)

    def searchInRange(self):
        self.startSearch(True)

    def stopSearch(self, wait_timeout=1500, quiet=False):
        worker = self.searchWorker
        if worker is None:
            self.btnSearchStop.setEnabled(False)
            return True
        worker.cancel()
        self.btnSearchStop.setEnabled(False)
        self.labSearchStatus.setText(self._translate("searchMemoryForm", "正在停止搜索..."))
        if worker.isRunning() and wait_timeout > 0:
            worker.wait(wait_timeout)
        if worker.isRunning():
            if not quiet:
                self.appendResult(self._translate("searchMemoryForm", "停止请求已发送，等待当前扫描任务收尾"))
            return False
        self.releaseSearchWorker(worker)
        return True

    def onSearchFinished(self, summary):
        if self.isStaleSearchSignal():
            return
        cancelled = summary.get("cancelled", False)
        count = summary.get("count", 0)
        elapsed = summary.get("elapsed", 0.0)
        scanned = summary.get("scannedRanges", 0)
        total = summary.get("totalRanges", 0)
        suffix = self._translate("searchMemoryForm", "已停止") if cancelled else self._translate("searchMemoryForm", "已完成")
        if summary.get("limitReached"):
            suffix += self._translate("searchMemoryForm", "（达到结果上限）")
        self.labSearchStatus.setText(self._translate("searchMemoryForm", "搜索%s：%d 条结果，扫描 %d / %d 个范围，耗时 %.2fs") % (suffix, count, scanned, total, elapsed))
        self.appendResult(self.labSearchStatus.text())
        self.btnSearchStop.setEnabled(False)
        self.releaseSearchWorker(self.sender())

    def onSearchFailed(self, message):
        if self.isStaleSearchSignal():
            return
        self.labSearchStatus.setText(self._translate("searchMemoryForm", "搜索失败"))
        self.appendResult(self._translate("searchMemoryForm", "搜索失败: ") + message)
        self.btnSearchStop.setEnabled(False)
        self.releaseSearchWorker(self.sender())
        QMessageBox.warning(self, "hint", message)

    def clearResults(self):
        self.tabResults.clearContents()
        self.tabResults.setRowCount(0)
        self.tabResults.setHorizontalHeaderLabels(self.resultHeaders)
        self.searchResults = []

    def resultRowPayload(self, row):
        item = self.tabResults.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.UserRole)

    def addResultBatch(self, batch):
        if self.isStaleSearchSignal():
            return
        for result in batch:
            row = self.tabResults.rowCount()
            self.tabResults.insertRow(row)
            self.searchResults.append(result)
            range_text = self.formatRangeText(result.get("regionBase", ""), result.get("regionSize", 0))
            row_values = [
                result.get("address", ""),
                result.get("module", ""),
                result.get("protection", ""),
                range_text,
                result.get("value", ""),
                result.get("note", ""),
            ]
            for column, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.UserRole, result)
                self.tabResults.setItem(row, column, item)

    def appendHistory(self, data):
        history_data = data
        if isinstance(data, str):
            try:
                history_data = json.loads(data)
            except Exception:
                self.appendResult(self._translate("searchMemoryForm", "旧搜索结果格式异常"))
                return
        if not isinstance(history_data, list):
            self.appendResult(self._translate("searchMemoryForm", "旧搜索结果格式异常"))
            return
        batch = []
        for line in history_data:
            batch.append({
                "address": line.get("key", ""),
                "value": line.get("value", ""),
                "note": line.get("bak", ""),
                "module": "",
                "protection": "",
                "regionBase": "",
                "regionSize": 0,
                "filePath": "",
            })
        self.addResultBatch(batch)

    def appendResult(self, result):
        if result is None:
            return
        self.txtConsole.appendPlainText(str(result))

    def currentSelectedAddress(self):
        row = self.tabResults.currentRow()
        if row < 0:
            return ""
        payload = self.resultRowPayload(row)
        if payload is None:
            return ""
        return str(payload.get("address", ""))

    def onResultSelectionChanged(self):
        address = self.currentSelectedAddress()
        if len(address) <= 0:
            return
        self.txtInspectAddress.setText(address)
        self.txtBreakAddress.setText(address)

    def useSelectedAddressForInspect(self):
        address = self.currentSelectedAddress()
        if len(address) <= 0:
            QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "请先在搜索结果中选择地址"))
            return
        self.txtInspectAddress.setText(address)
        self.inspectAddress()

    def useSelectedAddressForBreakpoint(self):
        address = self.currentSelectedAddress()
        if len(address) <= 0:
            QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "请先在搜索结果中选择地址"))
            return
        self.txtBreakAddress.setText(address)
        self.txtBreakModule.clear()
        self.txtBreakOffset.clear()
        self.txtBreakSymbol.clear()
        self.resolveBreakpointAddress(show_message=False)

    def inspectSelectedResult(self):
        address = self.currentSelectedAddress()
        if len(address) <= 0:
            return
        self.txtInspectAddress.setText(address)
        self.inspectAddress()

    def inspectAddress(self):
        if not self.ensureRuntime(show_message=True):
            return
        try:
            address = self.parseAddress(self.txtInspectAddress.text())
        except Exception as error:
            QMessageBox.warning(self, "hint", str(error))
            return
        try:
            info = data_info.rpc.inspect_address(hex(address), self.spinInspectBytes.value(), self.spinDisasmCount.value())
        except Exception as ex:
            QMessageBox.warning(self, "hint", str(ex))
            return
        self.renderInspectInfo(info)
        self.detailTabs.setCurrentWidget(self.inspectTab)

    def renderInspectInfo(self, info):
        summary_lines = [self._translate("searchMemoryForm", "地址: ") + str(info.get("address", ""))]
        module_info = info.get("module") or {}
        range_info = info.get("range") or {}
        symbol_info = info.get("symbol") or {}
        if module_info:
            summary_lines.append(self._translate("searchMemoryForm", "模块: ") + "%s @ %s" % (module_info.get("name", ""), module_info.get("base", "")))
        if range_info:
            summary_lines.append(self._translate("searchMemoryForm", "范围: ") + "%s [%s]" % (
                self.formatRangeText(range_info.get("base", ""), range_info.get("size", 0)),
                range_info.get("protection", ""),
            ))
        if symbol_info and symbol_info.get("name"):
            summary_lines.append(self._translate("searchMemoryForm", "符号: ") + "%s!%s" % (
                symbol_info.get("moduleName", ""),
                symbol_info.get("name", ""),
            ))
        cstring = info.get("cstring", "") or info.get("utf8", "")
        if cstring:
            summary_lines.append(self._translate("searchMemoryForm", "字符串: ") + cstring)
        self.labInspectSummary.setText("\n".join(summary_lines))
        self.txtHexDump.setPlainText(info.get("hexdump", ""))
        self.renderDisassembly(info.get("disassembly", []))

    def renderDisassembly(self, instructions):
        self.tabDisasm.clearContents()
        self.tabDisasm.setRowCount(0)
        self.tabDisasm.setHorizontalHeaderLabels(self.disasmHeaders)
        for row, instruction in enumerate(instructions or []):
            self.tabDisasm.insertRow(row)
            values = [
                instruction.get("address", ""),
                instruction.get("moduleName", ""),
                instruction.get("symbolName", ""),
                instruction.get("text", ""),
            ]
            for column, value in enumerate(values):
                self.tabDisasm.setItem(row, column, QTableWidgetItem(str(value)))

    def resolveBreakpointAddress(self, show_message=True):
        if not self.ensureRuntime(show_message=show_message):
            return None
        module = self.txtBreakModule.text().strip()
        offset = self.txtBreakOffset.text().strip()
        symbol = self.txtBreakSymbol.text().strip()
        absolute_text = self.txtBreakAddress.text().strip()
        resolved = None
        try:
            if len(absolute_text) > 0:
                resolved = self.parseAddress(absolute_text)
            elif len(module) > 0 and len(symbol) > 0:
                resolved = int(data_info.rpc.get_export_by_name(module, symbol), 16)
            elif len(module) > 0 and len(offset) > 0:
                module_info = data_info.rpc.get_module(module)
                if not module_info:
                    raise ValueError(self._translate("searchMemoryForm", "没有找到指定模块"))
                module_base = int(module_info["base"], 16)
                resolved = module_base + self.parseNumber(offset)
            else:
                raise ValueError(self._translate("searchMemoryForm", "请填写绝对地址，或 module+symbol，或 module+offset"))
        except Exception as error:
            if show_message:
                QMessageBox.warning(self, "hint", str(error))
            return None

        self.txtBreakAddress.setText(hex(resolved))
        module_info = self.findModuleByAddressInt(resolved)
        if module_info is not None and len(module) <= 0:
            self.txtBreakModule.setText(module_info.get("name", ""))
            self.txtBreakOffset.setText(hex(resolved - module_info["base_int"]))
        status_text = self._translate("searchMemoryForm", "断点地址: ") + hex(resolved)
        if module_info is not None:
            status_text += " (%s+%s)" % (module_info.get("name", ""), hex(resolved - module_info["base_int"]))
        self.labBreakpointStatus.setText(status_text)
        self.appendResult(status_text)
        return resolved

    def remake_memprotect_info(self):
        for item in data_info.proc_info["mem_protect"]:
            if isinstance(item["base"], str):
                item["base"] = int(item["base"], 16)

    def pointersize_pagesize_to_maskcode(self, pointer_size, page_size):
        pointer_mask = "ff" * pointer_size
        page_size_len = 0
        while page_size != 1:
            page_size = page_size / 0x10
            page_size_len = page_size_len + 1
        pointer_mask_list = list(pointer_mask)
        pointer_mask_list[2 * pointer_size - page_size_len:] = "0" * page_size_len
        pointer_mask = "".join(pointer_mask_list)
        return int(pointer_mask, 16)

    def get_breakinfo(self):
        ret_list = []
        for item in data_info.proc_info["mem_protect"]:
            if data_info.break_point_info["break_addr"] + data_info.break_point_info["break_len"] in range(item["base"], item["base"] + item["size"]):
                ret_list = [
                    data_info.break_point_info["break_addr"] & self.pointersize_pagesize_to_maskcode(
                        data_info.proc_info["pointersize"],
                        data_info.proc_info["pagesize"],
                    ),
                    item["protection"],
                ]
                data_info.break_point_info["break_page_info"] = ret_list
                break
        if ret_list == []:
            raise Exception("get_break_info the break pointer must be in a segement")

    def set_breakpoint(self):
        point = data_info.break_point_info["break_page_info"]
        data_info.rpc.set_page_protect(point[0], "---")
        data_info.rpc.set_exception_handler()

    def wrapper_to_post(self, _type, content):
        return {"type": _type, "payload": content}

    def find_soft_breakpoint_from_list(self, addr):
        with data_info.soft_breakpoint_runtime_lock:
            breakpoint_list_len = len(data_info.soft_breakpoint_runtime)
            if breakpoint_list_len != 0:
                for index in range(0, breakpoint_list_len):
                    if data_info.soft_breakpoint_runtime[index]["break_addr"] == addr:
                        return index
            return -1

    def setBreak(self):
        if not self.ensureRuntime(show_message=True):
            return
        break_size = self.spinBreakSize.value()
        if break_size <= 0:
            QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "请输入正确的断点大小"))
            return

        resolved = self.resolveBreakpointAddress(show_message=False)
        if resolved is None:
            QMessageBox.warning(self, "hint", self._translate("searchMemoryForm", "请填写绝对地址，或 module+symbol，或 module+offset"))
            return

        data_info.break_point_info["break_addr"] = resolved
        data_info.break_point_info["break_len"] = break_size
        try:
            self.remake_memprotect_info()
            self.get_breakinfo()
            self.set_breakpoint()
        except Exception as ex:
            QMessageBox.warning(self, "hint", str(ex))
            return

        status_text = self._translate("searchMemoryForm", "已设置内存断点: %s (%d bytes)") % (hex(resolved), break_size)
        self.labBreakpointStatus.setText(status_text)
        self.appendResult(status_text)

    def showModules(self):
        if not self.ensureRuntime(show_message=True):
            return
        module_filter = self.txtBreakModule.text().strip().lower()
        try:
            modules = [self.normalizeModule(module) for module in data_info.rpc.get_modules()]
        except Exception as ex:
            QMessageBox.warning(self, "hint", str(ex))
            return
        found = False
        for module in modules:
            name = (module.get("name", "") or "").lower()
            path = (module.get("path", "") or "").lower()
            if len(module_filter) > 0 and module_filter not in name and module_filter not in path:
                continue
            found = True
            self.appendResult("%s @ %s size=0x%x %s" % (
                module.get("name", ""),
                module.get("base", ""),
                int(module.get("size", 0)),
                module.get("path", ""),
            ))
        if not found:
            self.appendResult(self._translate("searchMemoryForm", "没有找到指定模块"))

    def registerOrder(self, context):
        keys = list(context.keys())
        preferred = ["pc", "sp", "fp", "lr", "x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "x9",
                     "x10", "x11", "x12", "x13", "x14", "x15", "x16", "x17", "x18", "x19", "x20",
                     "x21", "x22", "x23", "x24", "x25", "x26", "x27", "x28",
                     "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11", "r12"]
        ordered = [key for key in preferred if key in context]
        ordered.extend(sorted([key for key in keys if key not in ordered]))
        return ordered

    def renderRegisters(self, context):
        self.tabRegisters.clearContents()
        self.tabRegisters.setRowCount(0)
        self.tabRegisters.setHorizontalHeaderLabels(self.registerHeaders)
        if not isinstance(context, dict):
            return
        for row, key in enumerate(self.registerOrder(context)):
            self.tabRegisters.insertRow(row)
            self.tabRegisters.setItem(row, 0, QTableWidgetItem(key))
            self.tabRegisters.setItem(row, 1, QTableWidgetItem(str(context.get(key, ""))))

    def renderBreakpointDetail(self, event):
        if not event:
            return
        self.renderRegisters(event.get("context", {}))
        self.txtBreakpointDetails.setPlainText(event.get("detailText", ""))
        self.labBreakpointEventSummary.setText(event.get("summary", self._translate("searchMemoryForm", "尚未命中断点")))

    def appendBreakpointEvent(self, event):
        row = self.tabBreakpointEvents.rowCount()
        self.tabBreakpointEvents.insertRow(row)
        values = [
            event.get("time", ""),
            event.get("type", ""),
            event.get("pc", ""),
            event.get("targetAddress", ""),
            event.get("symbolText", ""),
            event.get("instruction", ""),
        ]
        for column, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            if column == 0:
                item.setData(Qt.UserRole, event)
            self.tabBreakpointEvents.setItem(row, column, item)
        self.tabBreakpointEvents.selectRow(row)

    def buildBreakpointEvent(self, message_data):
        memory_info = message_data.get("memory", {}) or {}
        symbol_info = message_data.get("symbol", {}) or {}
        address_text = str(message_data.get("address", ""))
        symbol_text = ""
        if symbol_info.get("moduleName") or symbol_info.get("name"):
            symbol_text = "%s!%s" % (symbol_info.get("moduleName", ""), symbol_info.get("name", ""))
        info_text = exception_info(message_data, data_info.proc_info.get("arch", "")).get_info()
        try:
            inspect_info = data_info.rpc.inspect_address(hex(self.parseAddress(address_text)), self.spinInspectBytes.value(), self.spinDisasmCount.value())
        except Exception:
            inspect_info = {}
        disassembly_lines = []
        for instruction in inspect_info.get("disassembly", []) or []:
            disassembly_lines.append("%s %s" % (instruction.get("address", ""), instruction.get("text", "")))
        detail_parts = [info_text]
        if disassembly_lines:
            detail_parts.append(self._translate("searchMemoryForm", "附近反汇编:"))
            detail_parts.append("\n".join(disassembly_lines))
        event = {
            "time": time.strftime("%H:%M:%S", time.localtime()),
            "type": memory_info.get("operation", message_data.get("type", "")),
            "pc": address_text,
            "targetAddress": str(memory_info.get("address", "")),
            "symbolText": symbol_text,
            "instruction": message_data.get("ins", ""),
            "context": message_data.get("context", {}) or {},
            "detailText": "\n\n".join(part for part in detail_parts if part),
            "summary": self._translate("searchMemoryForm", "最近命中: %s -> %s") % (
                address_text,
                message_data.get("ins", ""),
            ),
            "inspectInfo": inspect_info,
        }
        return event

    def onBreakpointEventSelectionChanged(self):
        row = self.tabBreakpointEvents.currentRow()
        if row < 0:
            return
        item = self.tabBreakpointEvents.item(row, 0)
        if item is None:
            return
        event = item.data(Qt.UserRole)
        if not event:
            return
        self.renderBreakpointDetail(event)

    def my_message_handler(self, messgae_data):
        try:
            if "exception" == messgae_data["__tag"]:
                handle_exception.handle(messgae_data)
            elif "set_soft_breakpoint" == messgae_data["__tag"]:
                addr = int(messgae_data["break_addr"], 16)
                index = self.find_soft_breakpoint_from_list(addr)
                if index != -1:
                    data_info.rpc.api._script.post(self.wrapper_to_post("set_soft_breakpoint_ret", 0))
                    return
                save_soft_breakpoint = data_info.soft_breakpoint_struct.copy()
                save_soft_breakpoint["break_addr"] = int(messgae_data["break_addr"], 16)
                save_soft_breakpoint["break_len"] = messgae_data["break_len"]
                save_soft_breakpoint["ins_content"] = messgae_data["ins_content"]
                with data_info.soft_breakpoint_runtime_lock:
                    data_info.soft_breakpoint_runtime.append(save_soft_breakpoint)
                data_info.rpc.api._script.post(self.wrapper_to_post("set_soft_breakpoint_ret", 0))
            elif "resume_soft_breakpoint" == messgae_data["__tag"]:
                addr = int(messgae_data["addr"], 16)
                index = self.find_soft_breakpoint_from_list(addr)
                if index == -1:
                    raise Exception("soft_breakpoint no found")
                send_dict = {"msg": 1}
                data_info.rpc.api._script.post(self.wrapper_to_post("resume_soft_breakpoint_ret", send_dict))
            elif "show_details" == messgae_data["__tag"]:
                event = self.buildBreakpointEvent(messgae_data)
                self.breakpointEvents.append(event)
                self.appendBreakpointEvent(event)
                self.renderBreakpointDetail(event)
                self.appendResult(event.get("detailText", ""))
                inspect_info = event.get("inspectInfo", {})
                if inspect_info:
                    self.txtInspectAddress.setText(event.get("pc", ""))
                    self.renderInspectInfo(inspect_info)
                self.detailTabs.setCurrentWidget(self.breakpointTab)
        except Exception as ex:
            self.appendResult(self._translate("searchMemoryForm", "断点事件处理失败: ") + str(ex))

    def resultMenuShow(self, _point=None):
        right_menu = QMenu(self.tabResults)
        inspect_action = QAction(self._translate("searchMemoryForm", "分析选中地址"), self, triggered=self.inspectSelectedResult)
        use_break_action = QAction(self._translate("searchMemoryForm", "用于断点地址"), self, triggered=self.useSelectedAddressForBreakpoint)
        clear_action = QAction(self._translate("searchMemoryForm", "清空结果"), self, triggered=self.clearResults)
        right_menu.addAction(inspect_action)
        right_menu.addAction(use_break_action)
        right_menu.addSeparator()
        right_menu.addAction(clear_action)
        right_menu.exec_(QCursor.pos())

    def consoleMenuShow(self, _point=None):
        right_menu = QMenu(self.txtConsole)
        clear_action = QAction(self._translate("searchMemoryForm", "清空控制台"), self, triggered=self.txtConsole.clear)
        right_menu.addAction(clear_action)
        right_menu.exec_(QCursor.pos())

    def closeEvent(self, event):
        worker = self.searchWorker
        if worker is not None:
            worker.cancel()
            self.releaseSearchWorker(worker)
        super(searchMemoryForm, self).closeEvent(event)
