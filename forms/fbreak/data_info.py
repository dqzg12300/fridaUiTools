
import threading

from forms.fbreak import rpcFunc

PACKAGE = 'com.mpt.myapplication'
# 远过程调用类
rpc: rpcFunc.rpcFunc = None
# 输入命令行参数
args: dict = None

soft_breakpoint_runtime_lock = threading.Lock()

proc_info = {
    'arch': '',
    'platform': '',
    'pagesize': 0,
    'pointersize': 0,
    'mem_protect': []
}


break_point_info = {
    'break_addr': 0,
    'break_len': 0,
    'current_pc': 0,
    'current_lr':0,
    'break_page_info': [],
    'cmd': 0
}

# 这种只是一个结构体，使用的时候拷贝一份
soft_breakpoint_struct = {
    'break_addr': 0,
    'break_len': 0,
    'ins_content': b'',
    'break_page_info': [],
    'index': 0,
    'cmd': 0
}

# 存入的是 _soft_breakpoint_struct 不删除断点，有可能占用大量空间
soft_breakpoint_runtime = []
# cmd 1 表示是此异常 处理
# cmd 2 表示是此软断点 处理
# cmd 100 表示不是此断点触发的异常不处理
'''
{'message': 'access violation accessing 0x789c516400', 
'type': 'access-violation', 'address': '0x789c4a7980',
'memory': {'operation': 'read', 'address': '0x789c516400'},
'context': {'pc': '0x789c4a7980', 'sp': '0x7fd69eb500',
'x0': '0x1', 'x1': '0x0', 'x2': '0x50', 'x3': '0x3',
'x4': '0x7fd69e9c40', 'x5': '0x8000000000000000',
'x6': '0x10', 'x7': '0x7f7f7f7f7f7f7f7f', 'x8': '0x789c516400',
'x9': '0xedb465ee8c790dab', 'x10': '0x1', 'x11': '0x0', 'x12': '0x7fd69e9d60', 'x13': '0x20', 'x14': '0x7fd69eb0a8',
'x15': '0x29aaaaab', 'x16': '0x7bb8b25740', 'x17': '0x7bd12f1180', 'x18': '0x7bda194000', 'x19': '0xb400007a86a6fbe0', 'x20': '0x0', 'x21': '0xb400007a86a6fbe0', 'x22': '0x7bd9972000', 'x23': '0xb400007a86a6fc90', 'x24': '0x790e06db70', 'x25': '0xb4000079f6a74a70', 'x26': '0x7bd9972000', 'x27': '0x37', 'x28': '0x7fd69eb560', 'fp': '0x7fd69eb530', 'lr': '0x789c4a797c'},
 'nativeContext': '0x7fd69ea320', '__tag': 'exception'}
'''

'''
{'message': 'breakpoint triggered', 'type': 'breakpoint', 'address': '0x7124263984', 'context': {'pc': '0x7124263984', 'sp': '0x7ffd5b23f0', 'x0': '0x1', 'x1': '0x0', 'x2': '0x50', 'x3': '0x3', 'x4': '0x7ffd5b0b30', 'x5': '0x8000000000000000', 'x6': '0x10', 'x7': '0x7f7f7f7f7f7f7f7f', 'x8': '0x71242d2400', 'x9': '0xa', 'x10': '0x1', 'x11': '0x0', 'x12': '0x7ffd5b0c50', 'x13': '0x20', 'x14': '0x7ffd5b1f98', 'x15': '0x29aaaaab', 'x16': '0x7433187740', 'x17': '0x7433ed5180', 'x18': '0x744899a000', 'x19': '0xb400007307448be0', 'x20': '0x0', 'x21': '0xb400007307448be0', 'x22': '0x7447853000', 'x23': '0xb400007307448c90', 'x24': '0x718c46eb70', 'x25': '0xb400007277455100', 'x26': '0x7447853000', 'x27': '0x37', 'x28': '0x7ffd5b2450', 'fp': '0x7ffd5b2420', 'lr': '0x712426397c'}, 'nativeContext': '0x7ffd5b1210', '__tag': 'exception'}
[{'break_addr': 485937789316, 'break_len': 4, 'ins_content': b')\x05\x00\x11'}]
'''
