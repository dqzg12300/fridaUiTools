import json

import click
from PyQt5.QtWidgets import QDialog, QMessageBox, QInputDialog
from ui.wallBreaker import Ui_Wallbreaker
from PyQt5 import QtCore


class DvmDescConverter:
    def __init__(self, desc):
        self.dvm_desc = desc

    def to_java(self):
        result = str(self.dvm_desc).strip()
        dim = 0
        while result.startswith('['):
            result = result[1:]
            dim += 1
        if result.startswith('L') and result.endswith(';'):
            result = result[1: -1]
        result = result.replace('/', '')
        result += "[]" * dim
        return result

    def short_name(self):
        result = self.to_java()
        if '.' in result:
            result = result[result.rindex(".") + 1:]
        return result


class wallBreakerForm(QDialog, Ui_Wallbreaker):
    def __init__(self, parent=None):
        super(wallBreakerForm, self).__init__(parent)
        self.setupUi(self)
        self.btnClassSearch.clicked.connect(self.classSearch)
        self.btnClassDump.clicked.connect(self.classDump)
        self.btnObjectSearch.clicked.connect(self.objectSearch)
        self.btnObjectDump.clicked.connect(self.objectDump)
        self.btnFieldRead.clicked.connect(self.fieldRead)
        self.btnClearUI.clicked.connect(self.clearUi)
        self.listClasses.itemClicked.connect(self.ClassItemClick)
        self.txtClassName.textChanged.connect(self.changeClass)
        self.classes = None
        self.api = None
        self._mainForm = None
        self._translate = QtCore.QCoreApplication.translate

    def initData(self):
        self.listClasses.clear()
        if not self.classes:
            return
        for item in self.classes:
            self.listClasses.addItem(item)

    def ClassItemClick(self, item):
        self.txtClassName.setText(item.text())

    def changeClass(self, data):
        if not self.classes:
            return
        self.listClasses.clear()
        if len(data) > 0:
            for item in self.classes:
                if data in item:
                    self.listClasses.addItem(item)
        else:
            for item in self.classes:
                self.listClasses.addItem(item)

    def clearUi(self):
        self.txtClassName.setText("")
        self.setResultText("")
        self.txtAddress.setText("")

    # --- 结果显示 ---
    def setResultText(self, text):
        """设置结果文本（清空旧内容后写入）"""
        if hasattr(self.txtSearchData, 'setReadOnly'):
            try:
                self.txtSearchData.setReadOnly(False)
            except Exception:
                pass
        if hasattr(self.txtSearchData, 'setText'):
            self.txtSearchData.setText(text)
        elif hasattr(self.txtSearchData, 'setPlainText'):
            self.txtSearchData.setPlainText(text)
        if hasattr(self.txtSearchData, 'setReadOnly'):
            try:
                self.txtSearchData.setReadOnly(True)
            except Exception:
                pass

    def appendLog(self, logstr):
        """兼容旧调用，追加文本"""
        if hasattr(self.txtSearchData, 'append'):
            self.txtSearchData.setReadOnly(False)
            self.txtSearchData.append(logstr)
            self.txtSearchData.setReadOnly(True)
        elif hasattr(self.txtSearchData, 'appendPlainText'):
            self.txtSearchData.appendPlainText(logstr)

    # --- API 检查 ---
    def _checkApi(self):
        if self.api is None:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm", "未设置api,可能附加失败"))
            return False
        return True

    def _checkClassName(self):
        if len(self.txtClassName.text()) <= 0:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm", "未填写类名"))
            return False
        return True

    # --- RPC 封装 ---
    def class_match(self, pattern):
        return self.api.class_match(pattern)

    def class_use(self, name):
        return json.loads(self.api.class_use(name))

    def object_get_classname(self, handle):
        return self.api.object_get_class(handle)

    def object_get_field(self, handle, field, as_class=None):
        return self.api.object_get_field(handle, field, as_class)

    def object_search(self, clazz, stop=False):
        return self.api.object_search(clazz, stop)

    # --- 核心功能 ---
    def map_dump(self, handle, pretty_print=False, **kwargs):
        result = "{}'s Map Entries {{".format(handle)
        pairs = self.api.map_dump(handle)
        for key in pairs:
            result += "\n\t{} => {}".format(key, pairs[key])
        result += "\n}\n"
        return result

    def collection_dump(self, handle, pretty_print=False, **kwargs):
        result = "{}'s Collection Entries {{".format(handle)
        array = self.api.collection_dump(handle)
        for i in range(0, len(array)):
            result += "\n\t{} => {}".format(i, array[i])
        result += "\n}\n"
        return result

    def object_dump(self, handle, as_class=None, **kwargs):
        special_render = {
            "java.util.Map": self.map_dump,
            "java.util.Collection": self.collection_dump
        }
        handle = str(handle)
        if as_class is None:
            as_class = self.object_get_classname(handle)
        result = self.class_dump(as_class, handle=handle, **kwargs)
        for clazz in special_render:
            if not self.api.instance_of(handle, clazz):
                continue
            result += special_render[clazz](handle, **kwargs)
        return result

    def class_dump(self, name, handle=None, pretty_print=False, short_name=True):
        target = self.class_use(name)
        result = ""
        class_name = str(target['name'])
        if '.' in class_name:
            pkg = class_name[:class_name.rindex('.')]
            class_name = class_name[class_name.rindex('.') + 1:]
            result += "package {};\n\n".format(pkg)

        result += "class {}".format(class_name) + " {\n\n"

        def handle_fields(fields, can_preview=None):
            _handle = handle
            if can_preview is None:
                can_preview = _handle is not None
            elif can_preview and _handle is None:
                _handle = target['name']
            append = ""
            original_class = None if handle is None else self.object_get_classname(handle)
            for field in fields:
                try:
                    field = field[0]
                    t = DvmDescConverter(field['type'])
                    t = t.short_name() if short_name else t.to_java()
                    append += '\t'
                    append += "static " if field['isStatic'] else ""
                    append += t + " "
                    value = None
                    if can_preview:
                        value = self.object_get_field(handle=_handle,
                                                      field=field['name'],
                                                      as_class=name if original_class and original_class != name else None)
                    append += '{};{}\n'.format(field["name"], " => {}".format(value) if value is not None else "")
                except:
                    append += "<unknown error>\n"
            append += '\n'
            return append

        static_fields = target['staticFields']
        instance_fields = target['instanceFields']

        result += "\t/* static fields */\n"
        result += handle_fields(static_fields.values(), can_preview=True)
        result += "\t/* instance fields */\n"
        result += handle_fields(instance_fields.values())

        def handle_methods(methods):
            append = ""
            for method in methods:
                try:
                    if short_name:
                        args_s = [DvmDescConverter(arg).short_name() for arg in method['arguments']]
                    else:
                        args_s = [DvmDescConverter(arg).to_java() for arg in method['arguments']]
                    args = ", ".join(args_s)
                    append += '\t'
                    append += "static " if method['isStatic'] else ""
                    retType = DvmDescConverter(method['retType'])
                    retType = retType.short_name() if short_name else retType.to_java()
                    retType = retType + " " if not method['isConstructor'] else ""
                    append += retType
                    append += method['name'] + '(' + args + ");\n"
                except:
                    append += "<unknown error>({})\n".format(method)
            return append

        constructors = target['constructors']
        instance_methods = target['instanceMethods']
        static_methods = target['staticMethods']

        result += "\t/* constructor methods */\n"
        result += handle_methods(constructors) + "\n"
        result += "\t/* static methods */\n"
        for name in static_methods:
            result += handle_methods(static_methods[name])
        result += "\n"
        result += "\t/* instance methods */\n"
        for name in instance_methods:
            result += handle_methods(instance_methods[name])
        result += "\n}\n"
        return result

    # --- 按钮动作 ---
    def classSearch(self):
        if not self._checkClassName() or not self._checkApi():
            return
        try:
            instances = self.api.class_match(self.txtClassName.text())
            self.setResultText("// Class Search: {}\n// Found: {} classes\n\n{}".format(
                self.txtClassName.text(), len(instances), "\n".join(instances)))
        except Exception as ex:
            self.setResultText("// Error: " + str(ex))

    def classDump(self):
        if not self._checkClassName() or not self._checkApi():
            return
        try:
            result = self.class_dump(self.txtClassName.text(), pretty_print=False, short_name=True)
            self.setResultText(result)
        except Exception as ex:
            self.setResultText("// Error: " + str(ex))

    def objectSearch(self):
        if not self._checkClassName() or not self._checkApi():
            return
        try:
            instances = self.object_search(self.txtClassName.text(), stop=False)
            lines = ["// Object Search: {}".format(self.txtClassName.text()),
                     "// Found: {} instances\n".format(len(instances))]
            for handle in instances:
                lines.append("[{}]: {}".format(handle, instances[handle]))
            self.setResultText("\n".join(lines))
        except Exception as ex:
            self.setResultText("// Error: " + str(ex))

    def objectDump(self):
        if not self._checkClassName() or not self._checkApi():
            return
        address = self.txtAddress.text()
        if len(address) <= 0:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm", "未填写地址"))
            return
        try:
            res = self.object_dump(int(address, 16), as_class=self.txtClassName.text(),
                                   pretty_print=False, short_name=True)
            self.setResultText(res)
        except Exception as ex:
            self.setResultText("// Error: " + str(ex))

    def fieldRead(self):
        """读取指定对象实例的某个字段值"""
        if not self._checkApi():
            return
        address = self.txtAddress.text()
        className = self.txtClassName.text()
        if not address:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm", "未填写地址"))
            return
        field_name, ok = QInputDialog.getText(self, "Field Read",
                                              self._translate("wallBreakerForm", "输入字段名："))
        if not ok or not field_name:
            return
        try:
            value = self.object_get_field(
                handle=str(int(address, 16)),
                field=field_name,
                as_class=className if className else None)
            self.setResultText("// Field Read\n// Object: {}\n// Field: {}\n\n{}".format(
                address, field_name, value))
        except Exception as ex:
            self.setResultText("// Error: " + str(ex))
