import json
import hexdump

test_str = '''
{
	"message": "access violation accessing 0x70de452b58",
	"type": "access-violation",
	"address": "0x70de4507f4",
	"memory": {
		"operation": "read",
		"address": "0x70de452b58"
	},
	"context": {
		"pc": "0x70de4507f4",
		"sp": "0x7fed291a80",
		"x0": "0x1",
		"x1": "0x0",
		"x2": "0x50",
		"x3": "0x3",
		"x4": "0x7fed2901c0",
		"x5": "0x8000000000000000",
		"x6": "0x10",
		"x7": "0x7f7f7f7f7f7f7f7f",
		"x8": "0x70de452b58",
		"x9": "0xd4085fd8c86b9ffb",
		"x10": "0x1",
		"x11": "0x0",
		"x12": "0x7fed2902e0",
		"x13": "0x20",
		"x14": "0x7fed291628",
		"x15": "0x29aaaaab",
		"x16": "0x73e5fbd740",
		"x17": "0x73e4304180",
		"x18": "0x73f09ae000",
		"x19": "0xb4000072bf32fbe0",
		"x20": "0x0",
		"x21": "0xb4000072bf32fbe0",
		"x22": "0x73f05d8000",
		"x23": "0xb4000072bf32fc90",
		"x24": "0x713c3ee1a8",
		"x25": "0xb40000722f3347f0",
		"x26": "0x73f05d8000",
		"x27": "0x37",
		"x28": "0x7fed291b00",
		"fp": "0x7fed291ad0",
		"lr": "0x70de4507e4"
	},
	"nativeContext": "0x7fed2908a0",
	"__tag": "show_details",
	"data": "0a000000",
	"symbol": {
		"address": "0x70de4507f4",
		"name": "Java_com_mpt_myapplication_MainActivity_testFunc+0x6c",
		"moduleName": "libnative-lib.so",
		"fileName": "",
		"lineNumber": 0
	},
	"ins": "ldr w9, [x8]",
	"operands": [{
		"type": "reg",
		"value": "w9"
	}, {
		"type": "mem",
		"value": {
			"base": "x8",
			"disp": 0
		}
	}]
}
'''


class exception_info:
    def __init__(self, info: dict, arch:str):
        self._info = info
        self._arch = arch
        self._out_dict = {}
        self._wrapper_info()
        
    def __handle_reg_str(self, reg_str: str):
        ret_str = ''
        if ('arm64' == self._arch):
            ret_str = reg_str.replace('w', 'x')
        elif ('arm' == self._arch):
            ret_str = reg_str
        else:
            raise Exception(self._arch, "not support")
        return ret_str

    def _handle_operands(self, operands_list):
        ret_dict = {}
        context = self._info['context']
        for item in operands_list:
            if 'reg' == item['type']:
                reg_name = self.__handle_reg_str(item['value'])
                ret_dict[reg_name] = context[reg_name]
            elif 'mem' == item['type']:
                reg_name = self.__handle_reg_str(item['value']['base'])
                ret_dict[reg_name] = context[reg_name]
        return ret_dict

    def _wrapper_info(self):
        memory = self._info['memory']
        self._out_dict['type'] = memory['operation']
        self._out_dict['data target address'] = memory['address']

        symbol = self._info["symbol"]
        pc_str = symbol['address'] + " "
        # 如果能解析出来符号则解析
        if symbol["moduleName"]:
            pc_str = pc_str + symbol["moduleName"] + "!" + symbol["name"]
        self._out_dict['PC'] = pc_str
        self._out_dict['ins'] = self._info["ins"]

        operands = self._info["operands"]
        self._out_dict['Register'] = self._handle_operands(operands)

        data = self._info['data']
        self._out_dict['data'] = hexdump.hexdump(hexdump.dehex(data), result="return")

    # 递归打印dict
    def _print_dict(self, dic: dict):
        for key in dic.keys():
            item = dic[key]
            if dict != type(item):
                print(key + ":", item)
            else:
                print(key+":")
                self._print_dict(item)

    def print_info(self):
        self._print_dict(self._out_dict)
        print()

    def _get_dict(self, dic: dict):
        result=""
        for key in dic.keys():
            item = dic[key]
            if dict != type(item):
                # print(key + ":", item)
                result+=key + ":"+str(item)+"\n"
            else:
                result += key + ":\n"
                result+=self._get_dict(item)
        return result

    def get_info(self):
        return self._get_dict(self._out_dict)


if __name__ == '__main__':
    m_info = exception_info(json.loads(test_str), 'arm64')
    m_info.print_info()
