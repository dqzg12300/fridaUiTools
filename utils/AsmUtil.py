from capstone import *
from keystone import *

def disasm(cmbidx,code):
    outdata=""
    if cmbidx==0:
        cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
    else:
        cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    for i in cs.disasm(code,len(code)):
        outdata+="address:0x%x\t%s\t%s"%(i.address,i.mnemonic,i.op_str)
    return outdata

def asm(cmbidx,code):
    outdata=""
    if cmbidx==0:
        ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
    else:
        ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    buff, count = ks.asm(code)
    outdata+="%s = [ " % code
    for i in buff:
        outdata+="%02x " % i
    outdata+="]"
    return outdata
