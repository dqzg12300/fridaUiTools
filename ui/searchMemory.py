# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets


class Ui_searchMemory(object):
    def setupUi(self, searchMemory):
        searchMemory.setObjectName("searchMemory")
        searchMemory.resize(1220, 740)
        searchMemory.setMinimumSize(QtCore.QSize(980, 620))

        self.rootLayout = QtWidgets.QVBoxLayout(searchMemory)
        self.rootLayout.setContentsMargins(6, 6, 6, 6)
        self.rootLayout.setSpacing(6)

        self.mainSplitter = QtWidgets.QSplitter(searchMemory)
        self.mainSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.mainSplitter.setChildrenCollapsible(False)
        self.mainSplitter.setObjectName("mainSplitter")

        self.sidebarWidget = QtWidgets.QWidget(self.mainSplitter)
        self.sidebarWidget.setObjectName("sidebarWidget")
        self.sidebarWidget.setMinimumWidth(300)
        self.sidebarWidget.setMaximumWidth(360)
        self.sidebarLayout = QtWidgets.QVBoxLayout(self.sidebarWidget)
        self.sidebarLayout.setContentsMargins(0, 0, 0, 0)
        self.sidebarLayout.setSpacing(0)

        self.controlTabs = QtWidgets.QTabWidget(self.sidebarWidget)
        self.controlTabs.setObjectName("controlTabs")
        self.controlTabs.setDocumentMode(True)
        self.controlTabs.setTabPosition(QtWidgets.QTabWidget.North)

        self.searchPage = QtWidgets.QWidget()
        self.searchPage.setObjectName("searchPage")
        self.searchPageLayout = QtWidgets.QVBoxLayout(self.searchPage)
        self.searchPageLayout.setContentsMargins(8, 8, 8, 8)
        self.searchPageLayout.setSpacing(8)

        self.searchGroup = QtWidgets.QWidget(self.searchPage)
        self.searchGroup.setObjectName("searchGroup")
        self.searchGroupLayout = QtWidgets.QVBoxLayout(self.searchGroup)
        self.searchGroupLayout.setContentsMargins(0, 0, 0, 0)
        self.searchGroupLayout.setSpacing(8)

        self.searchForm = QtWidgets.QFormLayout()
        self.searchForm.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.searchForm.setHorizontalSpacing(8)
        self.searchForm.setVerticalSpacing(8)

        self.labValueType = QtWidgets.QLabel(self.searchGroup)
        self.labValueType.setObjectName("labValueType")
        self.cmbValueType = QtWidgets.QComboBox(self.searchGroup)
        self.cmbValueType.setObjectName("cmbValueType")
        self.cmbValueType.setEditable(False)
        self.searchForm.addRow(self.labValueType, self.cmbValueType)

        self.labSearchValue = QtWidgets.QLabel(self.searchGroup)
        self.labSearchValue.setObjectName("labSearchValue")
        self.txtSearchValue = QtWidgets.QLineEdit(self.searchGroup)
        self.txtSearchValue.setObjectName("txtSearchValue")
        self.searchForm.addRow(self.labSearchValue, self.txtSearchValue)

        self.labSearchBase = QtWidgets.QLabel(self.searchGroup)
        self.labSearchBase.setObjectName("labSearchBase")
        self.txtSearchBase = QtWidgets.QLineEdit(self.searchGroup)
        self.txtSearchBase.setObjectName("txtSearchBase")
        self.searchForm.addRow(self.labSearchBase, self.txtSearchBase)

        self.labSearchSize = QtWidgets.QLabel(self.searchGroup)
        self.labSearchSize.setObjectName("labSearchSize")
        self.txtSearchSize = QtWidgets.QLineEdit(self.searchGroup)
        self.txtSearchSize.setObjectName("txtSearchSize")
        self.searchForm.addRow(self.labSearchSize, self.txtSearchSize)

        self.labProtect = QtWidgets.QLabel(self.searchGroup)
        self.labProtect.setObjectName("labProtect")
        self.cmbProtect = QtWidgets.QComboBox(self.searchGroup)
        self.cmbProtect.setObjectName("cmbProtect")
        self.cmbProtect.setEditable(True)
        self.searchForm.addRow(self.labProtect, self.cmbProtect)

        self.labModuleFilter = QtWidgets.QLabel(self.searchGroup)
        self.labModuleFilter.setObjectName("labModuleFilter")
        self.txtModuleFilter = QtWidgets.QLineEdit(self.searchGroup)
        self.txtModuleFilter.setObjectName("txtModuleFilter")
        self.searchForm.addRow(self.labModuleFilter, self.txtModuleFilter)

        self.labWorkers = QtWidgets.QLabel(self.searchGroup)
        self.labWorkers.setObjectName("labWorkers")
        self.spinWorkers = QtWidgets.QSpinBox(self.searchGroup)
        self.spinWorkers.setObjectName("spinWorkers")
        self.spinWorkers.setMinimum(1)
        self.spinWorkers.setMaximum(16)
        self.searchForm.addRow(self.labWorkers, self.spinWorkers)

        self.labResultLimit = QtWidgets.QLabel(self.searchGroup)
        self.labResultLimit.setObjectName("labResultLimit")
        self.spinResultLimit = QtWidgets.QSpinBox(self.searchGroup)
        self.spinResultLimit.setObjectName("spinResultLimit")
        self.spinResultLimit.setMinimum(10)
        self.spinResultLimit.setMaximum(50000)
        self.spinResultLimit.setSingleStep(100)
        self.searchForm.addRow(self.labResultLimit, self.spinResultLimit)

        self.labSearchNote = QtWidgets.QLabel(self.searchGroup)
        self.labSearchNote.setObjectName("labSearchNote")
        self.txtSearchNote = QtWidgets.QLineEdit(self.searchGroup)
        self.txtSearchNote.setObjectName("txtSearchNote")
        self.searchForm.addRow(self.labSearchNote, self.txtSearchNote)

        self.searchGroupLayout.addLayout(self.searchForm)

        self.searchButtonLayout = QtWidgets.QGridLayout()
        self.searchButtonLayout.setHorizontalSpacing(8)
        self.searchButtonLayout.setVerticalSpacing(8)

        self.btnSearchAll = QtWidgets.QPushButton(self.searchGroup)
        self.btnSearchAll.setObjectName("btnSearchAll")
        self.searchButtonLayout.addWidget(self.btnSearchAll, 0, 0, 1, 1)

        self.btnSearchRange = QtWidgets.QPushButton(self.searchGroup)
        self.btnSearchRange.setObjectName("btnSearchRange")
        self.searchButtonLayout.addWidget(self.btnSearchRange, 0, 1, 1, 1)

        self.btnSearchStop = QtWidgets.QPushButton(self.searchGroup)
        self.btnSearchStop.setObjectName("btnSearchStop")
        self.searchButtonLayout.addWidget(self.btnSearchStop, 1, 0, 1, 1)

        self.btnRefreshRanges = QtWidgets.QPushButton(self.searchGroup)
        self.btnRefreshRanges.setObjectName("btnRefreshRanges")
        self.searchButtonLayout.addWidget(self.btnRefreshRanges, 1, 1, 1, 1)

        self.searchGroupLayout.addLayout(self.searchButtonLayout)
        self.searchPageLayout.addWidget(self.searchGroup)
        self.searchPageLayout.addStretch(1)
        self.controlTabs.addTab(self.searchPage, "")

        self.inspectPage = QtWidgets.QWidget()
        self.inspectPage.setObjectName("inspectPage")
        self.inspectPageLayout = QtWidgets.QVBoxLayout(self.inspectPage)
        self.inspectPageLayout.setContentsMargins(8, 8, 8, 8)
        self.inspectPageLayout.setSpacing(8)

        self.inspectGroup = QtWidgets.QWidget(self.inspectPage)
        self.inspectGroup.setObjectName("inspectGroup")
        self.inspectLayout = QtWidgets.QVBoxLayout(self.inspectGroup)
        self.inspectLayout.setContentsMargins(0, 0, 0, 0)
        self.inspectLayout.setSpacing(8)

        self.inspectForm = QtWidgets.QFormLayout()
        self.inspectForm.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.inspectForm.setHorizontalSpacing(8)
        self.inspectForm.setVerticalSpacing(8)

        self.labInspectAddress = QtWidgets.QLabel(self.inspectGroup)
        self.labInspectAddress.setObjectName("labInspectAddress")
        self.txtInspectAddress = QtWidgets.QLineEdit(self.inspectGroup)
        self.txtInspectAddress.setObjectName("txtInspectAddress")
        self.inspectForm.addRow(self.labInspectAddress, self.txtInspectAddress)

        self.labInspectBytes = QtWidgets.QLabel(self.inspectGroup)
        self.labInspectBytes.setObjectName("labInspectBytes")
        self.spinInspectBytes = QtWidgets.QSpinBox(self.inspectGroup)
        self.spinInspectBytes.setObjectName("spinInspectBytes")
        self.spinInspectBytes.setMinimum(16)
        self.spinInspectBytes.setMaximum(4096)
        self.spinInspectBytes.setSingleStep(16)
        self.inspectForm.addRow(self.labInspectBytes, self.spinInspectBytes)

        self.labDisasmCount = QtWidgets.QLabel(self.inspectGroup)
        self.labDisasmCount.setObjectName("labDisasmCount")
        self.spinDisasmCount = QtWidgets.QSpinBox(self.inspectGroup)
        self.spinDisasmCount.setObjectName("spinDisasmCount")
        self.spinDisasmCount.setMinimum(4)
        self.spinDisasmCount.setMaximum(128)
        self.inspectForm.addRow(self.labDisasmCount, self.spinDisasmCount)

        self.inspectLayout.addLayout(self.inspectForm)

        self.inspectButtonLayout = QtWidgets.QHBoxLayout()
        self.inspectButtonLayout.setSpacing(8)
        self.btnInspect = QtWidgets.QPushButton(self.inspectGroup)
        self.btnInspect.setObjectName("btnInspect")
        self.inspectButtonLayout.addWidget(self.btnInspect)

        self.btnUseSelectedForInspect = QtWidgets.QPushButton(self.inspectGroup)
        self.btnUseSelectedForInspect.setObjectName("btnUseSelectedForInspect")
        self.inspectButtonLayout.addWidget(self.btnUseSelectedForInspect)

        self.inspectLayout.addLayout(self.inspectButtonLayout)
        self.inspectPageLayout.addWidget(self.inspectGroup)
        self.inspectPageLayout.addStretch(1)
        self.controlTabs.addTab(self.inspectPage, "")

        self.breakpointPage = QtWidgets.QWidget()
        self.breakpointPage.setObjectName("breakpointPage")
        self.breakpointPageLayout = QtWidgets.QVBoxLayout(self.breakpointPage)
        self.breakpointPageLayout.setContentsMargins(8, 8, 8, 8)
        self.breakpointPageLayout.setSpacing(8)

        self.breakpointGroup = QtWidgets.QWidget(self.breakpointPage)
        self.breakpointGroup.setObjectName("breakpointGroup")
        self.breakpointLayout = QtWidgets.QVBoxLayout(self.breakpointGroup)
        self.breakpointLayout.setContentsMargins(0, 0, 0, 0)
        self.breakpointLayout.setSpacing(8)

        self.breakpointForm = QtWidgets.QFormLayout()
        self.breakpointForm.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.breakpointForm.setHorizontalSpacing(8)
        self.breakpointForm.setVerticalSpacing(8)

        self.labBreakModule = QtWidgets.QLabel(self.breakpointGroup)
        self.labBreakModule.setObjectName("labBreakModule")
        self.txtBreakModule = QtWidgets.QLineEdit(self.breakpointGroup)
        self.txtBreakModule.setObjectName("txtBreakModule")
        self.breakpointForm.addRow(self.labBreakModule, self.txtBreakModule)

        self.labBreakOffset = QtWidgets.QLabel(self.breakpointGroup)
        self.labBreakOffset.setObjectName("labBreakOffset")
        self.txtBreakOffset = QtWidgets.QLineEdit(self.breakpointGroup)
        self.txtBreakOffset.setObjectName("txtBreakOffset")
        self.breakpointForm.addRow(self.labBreakOffset, self.txtBreakOffset)

        self.labBreakSymbol = QtWidgets.QLabel(self.breakpointGroup)
        self.labBreakSymbol.setObjectName("labBreakSymbol")
        self.txtBreakSymbol = QtWidgets.QLineEdit(self.breakpointGroup)
        self.txtBreakSymbol.setObjectName("txtBreakSymbol")
        self.breakpointForm.addRow(self.labBreakSymbol, self.txtBreakSymbol)

        self.labBreakAddress = QtWidgets.QLabel(self.breakpointGroup)
        self.labBreakAddress.setObjectName("labBreakAddress")
        self.txtBreakAddress = QtWidgets.QLineEdit(self.breakpointGroup)
        self.txtBreakAddress.setObjectName("txtBreakAddress")
        self.breakpointForm.addRow(self.labBreakAddress, self.txtBreakAddress)

        self.labBreakSize = QtWidgets.QLabel(self.breakpointGroup)
        self.labBreakSize.setObjectName("labBreakSize")
        self.spinBreakSize = QtWidgets.QSpinBox(self.breakpointGroup)
        self.spinBreakSize.setObjectName("spinBreakSize")
        self.spinBreakSize.setMinimum(1)
        self.spinBreakSize.setMaximum(256)
        self.breakpointForm.addRow(self.labBreakSize, self.spinBreakSize)

        self.breakpointLayout.addLayout(self.breakpointForm)

        self.breakpointButtonLayout = QtWidgets.QGridLayout()
        self.breakpointButtonLayout.setHorizontalSpacing(8)
        self.breakpointButtonLayout.setVerticalSpacing(8)

        self.btnUseSelectedForBreak = QtWidgets.QPushButton(self.breakpointGroup)
        self.btnUseSelectedForBreak.setObjectName("btnUseSelectedForBreak")
        self.breakpointButtonLayout.addWidget(self.btnUseSelectedForBreak, 0, 0, 1, 1)

        self.btnResolveBreakAddress = QtWidgets.QPushButton(self.breakpointGroup)
        self.btnResolveBreakAddress.setObjectName("btnResolveBreakAddress")
        self.breakpointButtonLayout.addWidget(self.btnResolveBreakAddress, 0, 1, 1, 1)

        self.btnSetBreakpoint = QtWidgets.QPushButton(self.breakpointGroup)
        self.btnSetBreakpoint.setObjectName("btnSetBreakpoint")
        self.breakpointButtonLayout.addWidget(self.btnSetBreakpoint, 1, 0, 1, 1)

        self.btnShowModules = QtWidgets.QPushButton(self.breakpointGroup)
        self.btnShowModules.setObjectName("btnShowModules")
        self.breakpointButtonLayout.addWidget(self.btnShowModules, 1, 1, 1, 1)

        self.breakpointLayout.addLayout(self.breakpointButtonLayout)

        self.labBreakpointStatus = QtWidgets.QLabel(self.breakpointGroup)
        self.labBreakpointStatus.setWordWrap(True)
        self.labBreakpointStatus.setObjectName("labBreakpointStatus")
        self.breakpointLayout.addWidget(self.labBreakpointStatus)

        self.breakpointPageLayout.addWidget(self.breakpointGroup)
        self.breakpointPageLayout.addStretch(1)
        self.controlTabs.addTab(self.breakpointPage, "")

        self.sidebarLayout.addWidget(self.controlTabs)

        self.workspaceSplitter = QtWidgets.QSplitter(self.mainSplitter)
        self.workspaceSplitter.setOrientation(QtCore.Qt.Vertical)
        self.workspaceSplitter.setChildrenCollapsible(False)
        self.workspaceSplitter.setObjectName("workspaceSplitter")

        self.resultsGroup = QtWidgets.QGroupBox(self.workspaceSplitter)
        self.resultsGroup.setObjectName("resultsGroup")
        self.resultsLayout = QtWidgets.QVBoxLayout(self.resultsGroup)
        self.resultsLayout.setContentsMargins(8, 10, 8, 8)
        self.resultsLayout.setSpacing(8)

        self.resultsHeaderLayout = QtWidgets.QHBoxLayout()
        self.resultsHeaderLayout.setContentsMargins(0, 0, 0, 0)

        self.labSearchStatus = QtWidgets.QLabel(self.resultsGroup)
        self.labSearchStatus.setObjectName("labSearchStatus")
        self.resultsHeaderLayout.addWidget(self.labSearchStatus)
        self.resultsHeaderLayout.addStretch(1)

        self.btnClearResults = QtWidgets.QPushButton(self.resultsGroup)
        self.btnClearResults.setObjectName("btnClearResults")
        self.resultsHeaderLayout.addWidget(self.btnClearResults)

        self.resultsLayout.addLayout(self.resultsHeaderLayout)

        self.tabResults = QtWidgets.QTableWidget(self.resultsGroup)
        self.tabResults.setObjectName("tabResults")
        self.tabResults.setColumnCount(0)
        self.tabResults.setRowCount(0)
        self.resultsLayout.addWidget(self.tabResults)

        self.detailTabs = QtWidgets.QTabWidget(self.workspaceSplitter)
        self.detailTabs.setObjectName("detailTabs")
        self.detailTabs.setDocumentMode(True)

        self.inspectTab = QtWidgets.QWidget()
        self.inspectTab.setObjectName("inspectTab")
        self.inspectTabLayout = QtWidgets.QVBoxLayout(self.inspectTab)
        self.inspectTabLayout.setContentsMargins(6, 6, 6, 6)
        self.inspectTabLayout.setSpacing(6)

        self.labInspectSummary = QtWidgets.QLabel(self.inspectTab)
        self.labInspectSummary.setWordWrap(True)
        self.labInspectSummary.setObjectName("labInspectSummary")
        self.inspectTabLayout.addWidget(self.labInspectSummary)

        self.inspectPreviewSplitter = QtWidgets.QSplitter(self.inspectTab)
        self.inspectPreviewSplitter.setOrientation(QtCore.Qt.Horizontal)
        self.inspectPreviewSplitter.setChildrenCollapsible(False)
        self.inspectPreviewSplitter.setObjectName("inspectPreviewSplitter")

        self.hexGroup = QtWidgets.QGroupBox(self.inspectPreviewSplitter)
        self.hexGroup.setObjectName("hexGroup")
        self.hexLayout = QtWidgets.QVBoxLayout(self.hexGroup)
        self.hexLayout.setContentsMargins(8, 10, 8, 8)
        self.hexLayout.setSpacing(6)

        self.txtHexDump = QtWidgets.QPlainTextEdit(self.hexGroup)
        self.txtHexDump.setReadOnly(True)
        self.txtHexDump.setObjectName("txtHexDump")
        self.hexLayout.addWidget(self.txtHexDump)

        self.disasmGroup = QtWidgets.QGroupBox(self.inspectPreviewSplitter)
        self.disasmGroup.setObjectName("disasmGroup")
        self.disasmLayout = QtWidgets.QVBoxLayout(self.disasmGroup)
        self.disasmLayout.setContentsMargins(8, 10, 8, 8)
        self.disasmLayout.setSpacing(6)

        self.tabDisasm = QtWidgets.QTableWidget(self.disasmGroup)
        self.tabDisasm.setObjectName("tabDisasm")
        self.tabDisasm.setColumnCount(0)
        self.tabDisasm.setRowCount(0)
        self.disasmLayout.addWidget(self.tabDisasm)

        self.inspectTabLayout.addWidget(self.inspectPreviewSplitter, 1)
        self.detailTabs.addTab(self.inspectTab, "")

        self.breakpointTab = QtWidgets.QWidget()
        self.breakpointTab.setObjectName("breakpointTab")
        self.breakpointTabLayout = QtWidgets.QVBoxLayout(self.breakpointTab)
        self.breakpointTabLayout.setContentsMargins(6, 6, 6, 6)
        self.breakpointTabLayout.setSpacing(6)

        self.labBreakpointEventSummary = QtWidgets.QLabel(self.breakpointTab)
        self.labBreakpointEventSummary.setWordWrap(True)
        self.labBreakpointEventSummary.setObjectName("labBreakpointEventSummary")
        self.breakpointTabLayout.addWidget(self.labBreakpointEventSummary)

        self.breakpointEventSplitter = QtWidgets.QSplitter(self.breakpointTab)
        self.breakpointEventSplitter.setOrientation(QtCore.Qt.Vertical)
        self.breakpointEventSplitter.setChildrenCollapsible(False)
        self.breakpointEventSplitter.setObjectName("breakpointEventSplitter")

        self.breakpointEventGroup = QtWidgets.QGroupBox(self.breakpointEventSplitter)
        self.breakpointEventGroup.setObjectName("breakpointEventGroup")
        self.breakpointEventLayout = QtWidgets.QVBoxLayout(self.breakpointEventGroup)
        self.breakpointEventLayout.setContentsMargins(8, 10, 8, 8)
        self.breakpointEventLayout.setSpacing(6)

        self.tabBreakpointEvents = QtWidgets.QTableWidget(self.breakpointEventGroup)
        self.tabBreakpointEvents.setObjectName("tabBreakpointEvents")
        self.tabBreakpointEvents.setColumnCount(0)
        self.tabBreakpointEvents.setRowCount(0)
        self.breakpointEventLayout.addWidget(self.tabBreakpointEvents)

        self.breakpointDetailWidget = QtWidgets.QWidget(self.breakpointEventSplitter)
        self.breakpointDetailWidget.setObjectName("breakpointDetailWidget")
        self.breakpointDetailLayout = QtWidgets.QHBoxLayout(self.breakpointDetailWidget)
        self.breakpointDetailLayout.setContentsMargins(0, 0, 0, 0)
        self.breakpointDetailLayout.setSpacing(6)

        self.registerGroup = QtWidgets.QGroupBox(self.breakpointDetailWidget)
        self.registerGroup.setObjectName("registerGroup")
        self.registerLayout = QtWidgets.QVBoxLayout(self.registerGroup)
        self.registerLayout.setContentsMargins(8, 10, 8, 8)
        self.registerLayout.setSpacing(6)

        self.tabRegisters = QtWidgets.QTableWidget(self.registerGroup)
        self.tabRegisters.setObjectName("tabRegisters")
        self.tabRegisters.setColumnCount(0)
        self.tabRegisters.setRowCount(0)
        self.registerLayout.addWidget(self.tabRegisters)
        self.breakpointDetailLayout.addWidget(self.registerGroup, 3)

        self.breakpointDetailGroup = QtWidgets.QGroupBox(self.breakpointDetailWidget)
        self.breakpointDetailGroup.setObjectName("breakpointDetailGroup")
        self.breakpointDetailGroupLayout = QtWidgets.QVBoxLayout(self.breakpointDetailGroup)
        self.breakpointDetailGroupLayout.setContentsMargins(8, 10, 8, 8)
        self.breakpointDetailGroupLayout.setSpacing(6)

        self.txtBreakpointDetails = QtWidgets.QPlainTextEdit(self.breakpointDetailGroup)
        self.txtBreakpointDetails.setReadOnly(True)
        self.txtBreakpointDetails.setObjectName("txtBreakpointDetails")
        self.breakpointDetailGroupLayout.addWidget(self.txtBreakpointDetails)
        self.breakpointDetailLayout.addWidget(self.breakpointDetailGroup, 4)

        self.breakpointTabLayout.addWidget(self.breakpointEventSplitter, 1)
        self.detailTabs.addTab(self.breakpointTab, "")

        self.consoleTab = QtWidgets.QWidget()
        self.consoleTab.setObjectName("consoleTab")
        self.consoleTabLayout = QtWidgets.QVBoxLayout(self.consoleTab)
        self.consoleTabLayout.setContentsMargins(6, 6, 6, 6)
        self.consoleTabLayout.setSpacing(6)

        self.txtConsole = QtWidgets.QPlainTextEdit(self.consoleTab)
        self.txtConsole.setReadOnly(True)
        self.txtConsole.setObjectName("txtConsole")
        self.consoleTabLayout.addWidget(self.txtConsole)
        self.detailTabs.addTab(self.consoleTab, "")

        self.rootLayout.addWidget(self.mainSplitter)

        self.retranslateUi(searchMemory)

        self.mainSplitter.setStretchFactor(0, 0)
        self.mainSplitter.setStretchFactor(1, 1)
        self.workspaceSplitter.setStretchFactor(0, 1)
        self.workspaceSplitter.setStretchFactor(1, 1)
        self.inspectPreviewSplitter.setStretchFactor(0, 1)
        self.inspectPreviewSplitter.setStretchFactor(1, 1)
        self.breakpointEventSplitter.setStretchFactor(0, 1)
        self.breakpointEventSplitter.setStretchFactor(1, 1)
        self.mainSplitter.setSizes([320, 900])
        self.workspaceSplitter.setSizes([320, 320])
        self.inspectPreviewSplitter.setSizes([420, 420])
        self.breakpointEventSplitter.setSizes([180, 220])
        QtCore.QMetaObject.connectSlotsByName(searchMemory)

    def retranslateUi(self, searchMemory):
        _translate = QtCore.QCoreApplication.translate
        searchMemory.setWindowTitle(_translate("searchMemory", "Memory Workbench"))

        self.controlTabs.setTabText(self.controlTabs.indexOf(self.searchPage), _translate("searchMemory", "搜索"))
        self.controlTabs.setTabText(self.controlTabs.indexOf(self.inspectPage), _translate("searchMemory", "分析"))
        self.controlTabs.setTabText(self.controlTabs.indexOf(self.breakpointPage), _translate("searchMemory", "断点"))

        self.labValueType.setText(_translate("searchMemory", "类型："))
        self.labSearchValue.setText(_translate("searchMemory", "值："))
        self.labSearchBase.setText(_translate("searchMemory", "起始地址："))
        self.labSearchSize.setText(_translate("searchMemory", "范围大小："))
        self.labProtect.setText(_translate("searchMemory", "保护："))
        self.labModuleFilter.setText(_translate("searchMemory", "模块过滤："))
        self.labWorkers.setText(_translate("searchMemory", "线程数："))
        self.labResultLimit.setText(_translate("searchMemory", "结果上限："))
        self.labSearchNote.setText(_translate("searchMemory", "备注："))
        self.btnSearchAll.setText(_translate("searchMemory", "全局搜索"))
        self.btnSearchRange.setText(_translate("searchMemory", "范围搜索"))
        self.btnSearchStop.setText(_translate("searchMemory", "停止"))
        self.btnRefreshRanges.setText(_translate("searchMemory", "刷新内存图"))

        self.labInspectAddress.setText(_translate("searchMemory", "地址："))
        self.labInspectBytes.setText(_translate("searchMemory", "读取字节："))
        self.labDisasmCount.setText(_translate("searchMemory", "反汇编条数："))
        self.btnInspect.setText(_translate("searchMemory", "分析地址"))
        self.btnUseSelectedForInspect.setText(_translate("searchMemory", "使用选中地址"))

        self.labBreakModule.setText(_translate("searchMemory", "模块："))
        self.labBreakOffset.setText(_translate("searchMemory", "偏移："))
        self.labBreakSymbol.setText(_translate("searchMemory", "符号："))
        self.labBreakAddress.setText(_translate("searchMemory", "绝对地址："))
        self.labBreakSize.setText(_translate("searchMemory", "监控字节："))
        self.btnUseSelectedForBreak.setText(_translate("searchMemory", "使用选中地址"))
        self.btnResolveBreakAddress.setText(_translate("searchMemory", "解析地址"))
        self.btnSetBreakpoint.setText(_translate("searchMemory", "设置断点"))
        self.btnShowModules.setText(_translate("searchMemory", "查看模块"))
        self.labBreakpointStatus.setText(_translate("searchMemory", "等待设置断点"))

        self.resultsGroup.setTitle(_translate("searchMemory", "搜索结果"))
        self.labSearchStatus.setText(_translate("searchMemory", "等待开始搜索"))
        self.btnClearResults.setText(_translate("searchMemory", "清空结果"))

        self.detailTabs.setTabText(self.detailTabs.indexOf(self.inspectTab), _translate("searchMemory", "地址分析"))
        self.labInspectSummary.setText(_translate("searchMemory", "尚未选择地址"))
        self.hexGroup.setTitle(_translate("searchMemory", "Hexdump"))
        self.disasmGroup.setTitle(_translate("searchMemory", "反汇编"))

        self.detailTabs.setTabText(self.detailTabs.indexOf(self.breakpointTab), _translate("searchMemory", "断点事件"))
        self.labBreakpointEventSummary.setText(_translate("searchMemory", "尚未命中断点"))
        self.breakpointEventGroup.setTitle(_translate("searchMemory", "事件列表"))
        self.registerGroup.setTitle(_translate("searchMemory", "寄存器"))
        self.breakpointDetailGroup.setTitle(_translate("searchMemory", "事件详情"))

        self.detailTabs.setTabText(self.detailTabs.indexOf(self.consoleTab), _translate("searchMemory", "控制台"))
