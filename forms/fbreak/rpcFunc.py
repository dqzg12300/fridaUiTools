class rpcFunc:
    def __init__(self, exports):
        self.api = exports

    def _call(self, *names_and_args):
        if len(names_and_args) <= 0:
            raise AttributeError("missing rpc method name")
        names = names_and_args[0]
        args = names_and_args[1:]
        if not isinstance(names, (list, tuple)):
            names = [names]
        for name in names:
            func = getattr(self.api, name, None)
            if callable(func):
                return func(*args)
        raise AttributeError("rpc method not found: %s" % ",".join(str(item) for item in names))

    def get_device_arch(self):
        return self._call(["getdevicearch", "getDeviceArch"])

    def get_platform(self):
        return self._call(["getplatform", "getPlatform"])

    def get_pointer_size(self):
        return self._call(["getpointersize", "getPointerSize"])

    def get_page_size(self):
        return self._call(["getpagesize", "getPageSize"])

    def get_module(self, name):
        return self._call(["getmodule", "getModule"], name)

    def hexdump(self,addr,size):
        return self._call("hexdump", addr, size)

    def cstring(self,addr):
        return self._call("cstring", addr)

    def get_export_by_name(self, so_name, symbol_name):
        return self._call(["getexportbyname", "getExportByName"], so_name, symbol_name)

    def set_exception_handler(self):
        self._call(["setexceptionhandler", "setExceptionHandler"])

    def set_page_protect(self, addr, protect):
        self._call(["setpageprotect", "setPageProtect"], hex(addr), protect)

    def get_protect_ranges(self):
        return self._call(["getprotectranges", "getProtectRanges"])

    def read_data(self, addr, length, type):
        raw_data = self._call(["readdata", "readData"], addr, length)
        print(raw_data)

    def get_modules(self):
        return self._call(["getmodules", "getModules"])

    def enumerate_ranges(self, protection="r--", coalesce=True):
        return self._call(["enumerateranges", "enumerateRanges"], protection, coalesce)

    def scan_range(self, base, size, pattern, limit=0):
        return self._call(["scanrange", "scanRange"], base, size, pattern, limit)

    def inspect_address(self, addr, byte_count=96, instruction_count=24):
        return self._call(["inspectaddress", "inspectAddress"], addr, byte_count, instruction_count)
