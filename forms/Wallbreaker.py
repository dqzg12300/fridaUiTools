import json

import click
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QMessageBox

from ui.wallBreaker import Ui_Wallbreaker
from PyQt5 import QtCore

class DvmDescConverter:
    def __init__(self, desc):
        self.dvm_desc = desc

    def to_java(self):
        result = str(self.dvm_desc)
        result = result.strip()
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


class wallBreakerForm(QDialog,Ui_Wallbreaker):
    def __init__(self, parent=None):
        super(wallBreakerForm, self).__init__(parent)
        self.setupUi(self)
        self.setWindowOpacity(0.93)
        self.btnClassSearch.clicked.connect(self.classSearch)
        self.btnClassDump.clicked.connect(self.classDump)
        self.btnObjectSearch.clicked.connect(self.objectSearch)
        self.btnObjectDump.clicked.connect(self.objectDump)
        self.btnClearUI.clicked.connect(self.clearUi)
        self.clearUi()
        self.listClasses.itemClicked.connect(self.ClassItemClick)
        self.txtClassName.textChanged.connect(self.changeClass)
        self.classes = None
        self.api=None
        self._translate = QtCore.QCoreApplication.translate

    def initData(self):
        self.listClasses.clear()
        for item in self.classes:
            self.listClasses.addItem(item)

    def ClassItemClick(self, item):
        self.txtClassName.setText(item.text())

    def changeClass(self, data):
        if self.classes==None or len(self.classes)<=0:
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
        self.txtSearchData.setPlainText("")
        self.txtAddress.setText("")

    def class_match(self, pattern):
        return self.api.class_match(pattern)

    def class_use(self, name):
        return json.loads(self.api.class_use(name))

    def object_get_classname(self, handle):
        return self.api.object_get_class(handle)

    def map_dump(self, handle, pretty_print=False, **kwargs):
        result = "{}'s Map Entries {{".format(handle)
        if pretty_print:
            click.secho("{}'s Map Entries ".format(handle), fg='blue', nl=False)
            click.secho("{", fg='red', nl=False)
        pairs = self.api.map_dump(handle)
        for key in pairs:
            result += "\n\t{} => {}".format(key, pairs[key])
            if pretty_print:
                click.secho("\n\t{}".format(key), fg='blue', nl=False)
                click.secho(" => ", nl=False)
                click.secho(pairs[key], fg='bright_cyan', nl=False)

        result += "\n}\n"
        if pretty_print: click.secho("\n}\n", fg='red', nl=False)
        return result

    def collection_dump(self, handle, pretty_print=False, **kwargs):
        result = "{}'s Collection Entries {{".format(handle)
        if pretty_print:
            click.secho("{}'s Collection Entries ".format(handle), fg='blue', nl=False)
            click.secho("{", fg='red', nl=False)
        array = self.api.collection_dump(handle)
        for i in range(0, len(array)):
            result += "\n\t{} => {}".format(i, array[i])
            if pretty_print:
                click.secho("\n\t{}".format(i), fg='blue', nl=False)
                click.secho(" => ", nl=False)
                click.secho(array[i], fg='bright_cyan', nl=False)

        result += "\n}\n"
        if pretty_print: click.secho("\n}\n", fg='red', nl=False)
        return result

    def object_get_field(self, handle, field, as_class=None):
        return self.api.object_get_field(handle, field, as_class)

    def object_search(self, clazz, stop=False):
        return self.api.object_search(clazz, stop)

    def object_dump(self, handle, as_class=None, **kwargs):
        special_render = {
            "java.util.Map": self.map_dump,
            "java.util.Collection": self.collection_dump
        }
        handle = str(handle)
        if as_class is None: as_class = self.object_get_classname(handle)
        result = self.class_dump(as_class, handle=handle, **kwargs)
        for clazz in special_render:
            if not self.api.instance_of(handle, clazz):
                continue
            if "pretty_print" in kwargs and kwargs["pretty_print"]:
                click.secho("\n/* special type dump - {} */".format(clazz), fg="bright_black")
            result += special_render[clazz](handle, **kwargs)
            # fbreak
        return result

    def class_dump(self, name, handle=None, pretty_print=False, short_name=True):
        target = self.class_use(name)
        result = ""
        if pretty_print:
            click.secho("")
        class_name = str(target['name'])
        if '.' in class_name:
            pkg = class_name[:class_name.rindex('.')]
            class_name = class_name[class_name.rindex('.') + 1:]
            result += "package {};\n\n".format(pkg)
            if pretty_print:
                click.secho("package ", fg="blue", nl=False)
                click.secho(pkg + "\n\n", nl=False)

        result += "class {}".format(class_name) + " {\n\n"
        if pretty_print:
            click.secho("class ", fg="blue", nl=False)
            click.secho(class_name, nl=False)
            click.secho(" {\n\n", fg='red', nl=False)

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
                    if pretty_print:
                        click.secho("\t", nl=False)
                    append += "static " if field['isStatic'] else ""
                    if pretty_print:
                        click.secho("static " if field['isStatic'] else "", fg='blue', nl=False)
                    append += t + " "
                    if pretty_print:
                        click.secho(t + " ", fg='blue', nl=False)

                    value = None
                    if can_preview:
                        value = self.object_get_field(handle=_handle,
                                                      field=field['name'],
                                                      as_class=name if original_class and original_class != name else None)
                    append += '{};{}\n'.format(field["name"], " => {}".format(value) if value is not None else "")
                    if pretty_print:
                        click.secho(field['name'], fg='red', nl=False)
                        click.secho(";", nl=False)
                        if value is not None:
                            click.secho(" => ", nl=False)
                            click.secho(value, fg='bright_cyan', nl=False)
                        click.secho("")
                except:
                    append += "<unknown error>\n"
                    if pretty_print:
                        click.secho("<unknown error>", fg="red", nl=False)
                        click.secho()

            append += '\n'
            if pretty_print: click.secho("\n", nl=False)
            return append

        static_fields = target['staticFields']
        instance_fields = target['instanceFields']

        result += "\t/* static fields */\n"
        if pretty_print:
            click.secho("\t/* static fields */", fg="black")
        result += handle_fields(static_fields.values(), can_preview=True)

        result += "\t/* instance fields */\n"
        if pretty_print:
            click.secho("\t/* instance fields */", fg="black")
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
                    if pretty_print:
                        click.secho("\t", nl=False)
                    append += "static " if method['isStatic'] else ""
                    if pretty_print:
                        click.secho("static " if method['isStatic'] else "", fg='blue', nl=False)
                    retType = DvmDescConverter(method['retType'])
                    retType = retType.short_name() if short_name else retType.to_java()
                    retType = retType + " " if not method['isConstructor'] else ""
                    append += retType
                    if pretty_print:
                        click.secho(retType, fg='blue', nl=False)
                    append += method['name'] + '('
                    if pretty_print:
                        click.secho(method['name'], fg='red', nl=False)
                        click.secho("(", nl=False)
                    append += args + ");\n"
                    if pretty_print:
                        for index in range(len(args_s)):
                            click.secho(args_s[index], fg='green', nl=False)
                            if index is not len(args_s) - 1:
                                click.secho(", ", nl=False)
                        click.secho(");\n", nl=False)
                except:
                    append += "<unknown error>({})\n".format(method)
                    if pretty_print:
                        click.secho("<unknown error>({})".format(method), fg="red", nl=False)
                        click.secho("")
            return append

        constructors = target['constructors']
        instance_methods = target['instanceMethods']
        static_methods = target['staticMethods']

        result += "\t/* constructor methods */\n"
        if pretty_print:
            click.secho("\t/* constructor methods */", fg="black")
        result += handle_methods(constructors)
        result += "\n"
        if pretty_print: click.secho("")

        result += "\t/* static methods */\n"
        if pretty_print:
            click.secho("\t/* static methods */", fg="black")
        for name in static_methods:
            result += handle_methods(static_methods[name])
        result += "\n"
        if pretty_print: click.secho("")

        result += "\t/* instance methods */\n"
        if pretty_print:
            click.secho("\t/* instance methods */", fg="black")
        for name in instance_methods:
            result += handle_methods(instance_methods[name])
        result += "\n}\n"
        if pretty_print: click.secho("\n}\n", fg='red', nl=False)
        return result


    def appendLog(self,logstr):
        self.txtSearchData.appendPlainText(logstr)

    def classSearch(self):
        className=self.txtClassName.text()
        if len(className)<=0:
            QMessageBox().information(self, "hint",self._translate("wallBreakerForm","未填写类名"))
            return
        if self.api==None:
            QMessageBox().information(self, "hint",self._translate("wallBreakerForm","未设置api,可能附加失败"))
            return
        instances = self.api.class_match(className)
        self.appendLog("\n".join(instances))

    def classDump(self):
        className = self.txtClassName.text()
        if len(className) <= 0:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm","未填写类名"))
            return
        if self.api==None:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm","未设置api,可能附加失败"))
            return
        result= self.class_dump(className, pretty_print=False, short_name=True)
        self.appendLog(result)

    def objectSearch(self):
        className = self.txtClassName.text()
        if len(className) <= 0:
            QMessageBox().information(self, "hint",self._translate("wallBreakerForm", "未填写类名"))
            return
        if self.api==None:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm","未设置api,可能附加失败"))
            return
        instances = self.object_search(className, stop=False)
        for handle in instances:
            self.appendLog("[{}]: {}".format(handle, instances[handle]))


    def objectDump(self):
        className = self.txtClassName.text()
        address = self.txtAddress.text()
        if len(address) <= 0:
            QMessageBox().information(self, "hint", self._translate("wallBreakerForm","未填写地址"))
            return
        if self.api==None:
            QMessageBox().information(self, "hint",self._translate("wallBreakerForm", "未设置api,可能附加失败"))
            return
        res=self.object_dump(address, as_class=className, pretty_print=False, short_name=True)
        self.appendLog(res)
