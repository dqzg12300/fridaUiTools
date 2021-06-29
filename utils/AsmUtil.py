from capstone import *
from keystone import *
import re,struct

def disasm(cmbidx,code):
    outdata=""
    if cmbidx==1:
        cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    else:
        cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for i in cs.disasm(code,len(code)):
        outdata+="%s %s"%(i.mnemonic,i.op_str)
    return outdata

def asm(cmbidx,code):
    outdata=""
    if cmbidx==1:
        ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
    else:
        ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    buff, count = ks.asm(code)
    # outdata+="%s = [ " % code
    # for i in buff:
    #     outdata+="%02x " % i
    # outdata+="]"
    for i in buff:
        outdata+="%02x " % i
    return outdata

def StrToHexSplit(input):
    buf = bytes(0)
    lines = re.split(r'[\r\n ]',input)
    for code in lines:
        if len (code) <= 0:
            continue
        num = int(code,16)
        bnum = struct.pack('B',num)
        buf += bnum
    return buf
