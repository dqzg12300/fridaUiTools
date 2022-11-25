class rpcFunc:
    def __init__(self, exports):
        self.api = exports

    def get_device_arch(self):
        return self.api.getdevicearch()

    def get_platform(self):
        return self.api.getplatform()

    def get_pointer_size(self):
        return self.api.getpointersize()

    def get_page_size(self):
        return self.api.getpagesize()

    def get_module(self, name):
        return self.api.getmodule(name)

    def get_export_by_name(self, so_name, symbol_name):
        return self.api.getexportbyname(so_name, symbol_name)

    def set_exception_handler(self):
        self.api.setexceptionhandler()

    def set_page_protect(self, addr, protect):
        self.api.setpageprotect(hex(addr), protect)

    def get_protect_ranges(self):
        return self.api.getprotectranges()

    def read_data(self, addr, length, type):
        raw_data = self.api.readdata(addr, length)
        print(raw_data)
