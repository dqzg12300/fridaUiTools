(function(){
//
// const arm64CM = new CModule(`
// #include <gum/gumstalker.h>
// #include <stdio.h>
// #include <string.h>
// #include <stdlib.h>
//
// extern void on_message(const gchar *message);
// static void log(const gchar *format, ...);
// static void on_arm64_before(GumCpuContext *cpu_context, gpointer user_data);
// static void on_arm64_after(GumCpuContext *cpu_context, gpointer user_data);
//
// void hello() {
//     on_message("Hello form CModule");
// }
//
// gpointer shared_mem[] = {0, 0};
//
// gpointer 
// get_shared_mem() 
// {
//     return shared_mem;
// }
//
//
// static void
// log(const gchar *format, ...)
// {
//     gchar *message;
//     va_list args;
//
//     va_start(args, format);
//     message = g_strdup_vprintf(format, args);
//     va_end(args);
//
//     on_message(message);
//     g_free(message);
// }
//
//
// void transform(GumStalkerIterator *iterator,
//                GumStalkerOutput *output,
//                gpointer user_data)
// {
//     cs_insn *insn;
//
//     gpointer base = *(gpointer*)user_data;
//     gpointer end = *(gpointer*)(user_data + sizeof(gpointer));
//    
//     while (gum_stalker_iterator_next(iterator, &insn))
//     {
//         gboolean in_target = (gpointer)insn->address >= base && (gpointer)insn->address < end;
//         if(in_target)
//         {
//             log("%p\t%s\t%s", (gpointer)insn->address, insn->mnemonic, insn->op_str);
//             gum_stalker_iterator_put_callout(iterator, on_arm64_before, (gpointer) insn->address, NULL);
//         }
//         gum_stalker_iterator_keep(iterator);
//         if(in_target) 
//         {
//             gum_stalker_iterator_put_callout(iterator, on_arm64_after, (gpointer) insn->address, NULL);
//         }
//     }
// }
//
//
// const gchar * cpu_format = "
//     0x%x\t0x%x\t0x%x\t0x%x\t0x%x
//     \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
//     \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
//     \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
//     \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
//     \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
//     \t0x%x\t0x%x\t0x%x
//     ";
//
// static void
// on_arm64_before(GumCpuContext *cpu_context,
//         gpointer user_data)
// {
//
// }
//
// static void
// on_arm64_after(GumCpuContext *cpu_context,
//         gpointer user_data)
// {
//
// }
//
// `, {
//     on_message: new NativeCallback(messagePtr => {
//         const message = messagePtr.readUtf8String();
//         var msg=initMessage();
//         msg["data"]=message;
//         send(msg);
//         console.log(message);
//         // send(message)
//       }, 'void', ['pointer']),
// });

function klog(data,...args){
    for (let item of args){
        data+="\t"+item;
    }
    var message={};
    message["jsname"]="jni_trace_new";
    message["data"]=data;
    send(message);
}


function initMessage(){
  var message={};
  message["jsname"]="sktrace";
  return message;
}

const userData = Memory.alloc(Process.pageSize);
function stalkerTraceRangeC(tid, base, size) {
    // const hello = new NativeFunction(cm.hello, 'void', []);
    // hello();
    userData.writePointer(base)
    const pointerSize = Process.pointerSize;
    userData.add(pointerSize).writePointer(base.add(size))

    Stalker.follow(tid, {
        transform: arm64CM.transform,
        // onEvent: cm.process,
        data: userData /* user_data */
    })
}

//
// function stalkerTraceRange(tid, base, size) {
//     Stalker.follow(tid, {
//         transform: (iterator) => {
//             const instruction = iterator.next();
//             const startAddress = instruction.address;
//             const isModuleCode = startAddress.compare(base) >= 0 &&
//                 startAddress.compare(base.add(size)) < 0;
//             // const isModuleCode = true;
//             do {
//                 iterator.keep();
//                 if (isModuleCode) {
//                     var address=ptr(instruction["address"]-moduleBase);
//                     send({
//                         type: 'inst',
//                         tid: tid,
//                         block: startAddress,
//                         val: JSON.stringify(instruction),
//                         jsname:"sktrace",
//                         moduleBase:moduleBase,
//                         address:address,
//                     })
//
//                     iterator.putCallout((context) => {
//                         var callOutAddress=ptr(context.pc-moduleBase)
//                         // if (offsetAddr>0 && callOutAddress.compare(offsetAddr)<0){
//                         //     return;
//                         // }
//                         send({
//                             type: 'ctx',
//                             tid: tid,
//                             val: JSON.stringify(context),
//                             jsname:"sktrace",
//                             moduleBase:moduleBase,
//                             address:callOutAddress
//                         })
//                     })
//
//                 }
//             } while (iterator.next() !== null);
//             // if(flag){
//             //     send(data)
//             // }
//         }
//     })
// }


// function traceAddr(addr) {
//     let moduleMap = new ModuleMap();
//     let targetModule = moduleMap.find(addr);
//     var msg=initMessage();
//     msg["data"]=JSON.stringify(targetModule);
//     send(msg);
//     let exports = targetModule.enumerateExports();
//     let symbols = targetModule.enumerateSymbols();
//
//     Interceptor.attach(addr, {
//         onEnter: function(args) {
//             this.tid = Process.getCurrentThreadId()
//             // stalkerTraceRangeC(this.tid, targetModule.base, targetModule.size)
//             stalkerTraceRange(this.tid, targetModule.base, targetModule.size)
//         },
//         onLeave: function(ret) {
//             Stalker.unfollow(this.tid);
//             Stalker.garbageCollect()
//             send({
//                 type: "fin",
//                 tid: this.tid,
//                 jsname:"sktrace"
//             })
//         }
//     })
// }


let moduleBase;
let pre_regs = [];
let infoMap = new Map();
let detailInsMap = new Map();
let regs_map = new Map();

function formatArm64Regs(context) {
    let regs = []
    regs.push(context.x0);
    regs.push(context.x1);
    regs.push(context.x2);
    regs.push(context.x3);
    regs.push(context.x4);
    regs.push(context.x5);
    regs.push(context.x6);
    regs.push(context.x7);
    regs.push(context.x8);
    regs.push(context.x9);
    regs.push(context.x10);
    regs.push(context.x11);
    regs.push(context.x12);
    regs.push(context.x13);
    regs.push(context.x14);
    regs.push(context.x15);
    regs.push(context.x16);
    regs.push(context.x17);
    regs.push(context.x18);
    regs.push(context.x19);
    regs.push(context.x20);
    regs.push(context.x21);
    regs.push(context.x22);
    regs.push(context.x23);
    regs.push(context.x24);
    regs.push(context.x25);
    regs.push(context.x26);
    regs.push(context.x27);
    regs.push(context.x28);
    regs.push(context.fp);
    regs.push(context.lr);
    regs.push(context.sp);
    regs.push(context.pc);
    regs_map.set('x0', context.x0);
    regs_map.set('x1', context.x1);
    regs_map.set('x2', context.x2);
    regs_map.set('x3', context.x3);
    regs_map.set('x4', context.x4);
    regs_map.set('x5', context.x5);
    regs_map.set('x6', context.x6);
    regs_map.set('x7', context.x7);
    regs_map.set('x8', context.x8);
    regs_map.set('x9', context.x9);
    regs_map.set('x10', context.x10);
    regs_map.set('x11', context.x11);
    regs_map.set('x12', context.x12);
    regs_map.set('x13', context.x13);
    regs_map.set('x14', context.x14);
    regs_map.set('x15', context.x15);
    regs_map.set('x16', context.x16);
    regs_map.set('x17', context.x17);
    regs_map.set('x18', context.x18);
    regs_map.set('x19', context.x19);
    regs_map.set('x20', context.x20);
    regs_map.set('x21', context.x21);
    regs_map.set('x22', context.x22);
    regs_map.set('x23', context.x23);
    regs_map.set('x24', context.x24);
    regs_map.set('x25', context.x25);
    regs_map.set('x26', context.x26);
    regs_map.set('x27', context.x27);
    regs_map.set('x28', context.x28);
    regs_map.set('fp', context.fp);
    regs_map.set('lr', context.lr);
    regs_map.set('sp', context.sp);
    regs_map.set('pc', context.pc);
    return regs;
}

function getRegsString(index) {
    let reg;
    if (index === 31) {
        reg = "sp"
    } else {
        reg = "x" + index;
    }
    return reg;
}

function isRegsChange(context, ins) {
    let currentRegs = formatArm64Regs(context);
    let entity = {};
    let logInfo = "";
    // 打印寄存器信息
    for (let i = 0; i < 32; i++) {
        if (i === 30) {
            continue
        }
        let preReg = pre_regs[i] ? pre_regs[i] : 0x0;
        let currentReg = currentRegs[i];
        if (Number(preReg) !== Number(currentReg)) {
            if (logInfo === "") {
                //尝试读取string
                let changeString = "";
                try {
                    let nativePointer = new NativePointer(currentReg);
                    changeString = nativePointer.readCString();
                } catch (e) {
                    changeString = "";
                }
                if (changeString !== "") {
                    currentReg = currentReg + " (" + changeString + ")";
                }
                logInfo = " " + getRegsString(i) + ": " + preReg + " --> " + currentReg + ", ";
            } else {
                logInfo = logInfo + " " + getRegsString(i) + ": " + preReg + " --> " + currentReg + ", ";
            }
        }
    }

    entity.info = logInfo;
    pre_regs = currentRegs;
    return entity;
}


function stalkerTraceRange(tid, base, size, offsetAddr) {
    Stalker.follow(tid, {
        transform: (iterator) => {
            const instruction = iterator.next();
            const startAddress = instruction.address;
            const isModuleCode = startAddress.compare(base) >= 0 &&
                startAddress.compare(base.add(size)) < 0;
            do {
                iterator.keep();
                if (isModuleCode) {
                    var offsetAddr=ptr(instruction["address"] - base);

                    let lastInfo = '[' +offsetAddr + ']' + '\t' + ptr(instruction["address"]) + '\t' + (instruction+';').padEnd(30,' ');
                    let address = instruction.address - base;
                    detailInsMap.set(String(address), JSON.stringify(instruction));
                    infoMap.set(String(address), lastInfo);

                    iterator.putCallout((context) => {
                        let offset = Number(context.pc) - base;
                        let detailIns = detailInsMap.get(String(offset));

                        let insinfo = infoMap.get(String(offset));
                        let entity = isRegsChange(context, detailIns);
                        let info = insinfo + '\t#' + entity.info;

                        let next_pc = context.pc.add(4);
                        let insn_next = Instruction.parse(next_pc);
                        insinfo = '[' + ptr(insn_next["address"] - base) + ']' + '\t' + ptr(insn_next["address"]) + '\t' + (insn_next + ';').padEnd(30,' ');
                        let mnemonic = insn_next.mnemonic;
                        if (mnemonic.startsWith("b.") || mnemonic === "b" || mnemonic === "bl" || mnemonic === "br" ||  mnemonic === "bx" || mnemonic.startsWith("bl") || mnemonic.startsWith("bx")) {
                            info = info + '\n' + insinfo + '\t#';
                        }
                        console.log(info);
                    });
                }
            } while (iterator.next() !== null);
        }
    })
}


function traceAddr(addr,base_addr) {
    let moduleMap = new ModuleMap();
    let targetModule = moduleMap.find(addr);

    console.log('-----start trace：', addr, '------');
    moduleBase = base_addr;
    Interceptor.attach(addr, {
        onEnter: function(args) {
            klog("enter ",addr);
            this.tid = Process.getCurrentThreadId();
            stalkerTraceRange(this.tid,targetModule.base,targetModule.size,addr);
        },
        onLeave: function(ret) {
            Stalker.unfollow(this.tid);
            Stalker.garbageCollect();
            klog('-----end trace------');
        }
    });
}

/**
 * from jnitrace-egine
 */
function watcherLib(libname, callback) {
    const dlopenRef = Module.findExportByName(null, "dlopen");
    const dlsymRef = Module.findExportByName(null, "dlsym");
    const dlcloseRef = Module.findExportByName(null, "dlclose");

    if (dlopenRef !== null && dlsymRef !== null && dlcloseRef !== null) {
        const dlopen = new NativeFunction(dlopenRef, "pointer", ["pointer", "int"]);
        Interceptor.replace(dlopen, new NativeCallback((filename, mode) => {
            const path = filename.readCString();
            const retval = dlopen(filename, mode);

            if (path !== null) {
                if (checkLibrary(path)) {
                    // eslint-disable-next-line @typescript-eslint/no-base-to-string
                    trackedLibs.set(retval.toString(), true);
                } else {
                    // eslint-disable-next-line @typescript-eslint/no-base-to-string
                    libBlacklist.set(retval.toString(), true);
                }
            }

            return retval;
        }, "pointer", ["pointer", "int"]));
    }
}

function trace(symbol,offset){
    const targetModule = Process.getModuleByName(libname);
    moduleBase=targetModule.base;
    let targetAddress = null;
    if(symbol.length>0) {
        targetAddress = targetModule.findExportByName(symbol);
    } else if(offset.length>0) {
        var offsetData=parseInt(offset,16);
        offsetAddr=ptr(offsetData);
        klog("offsetAddr",offsetAddr);
        targetAddress = targetModule.base.add(ptr(offsetData));
    }
    traceAddr(targetAddress)
}


function spawn_hook(library_name,symbol,offset){
    Interceptor.attach(Module.findExportByName(null, 'android_dlopen_ext'),{
        onEnter: function(args){
            // first arg is the path to the library loaded
            var library_path = Memory.readCString(args[0])
            if( library_path.includes(library_name)){
                var msg=initMessage();
                msg["data"]="[...] Loading library : " + library_path;
                send(msg)
                this.library_loaded = 1
            }
        },
        onLeave: function(args){
            // if it's the library we want to hook, hooking it
            if(this.library_loaded ==  1){
                var msg=initMessage();
                msg["data"]="[+] Loaded";
                send(msg)
                trace(symbol,offset);
                this.library_loaded = 0
            }
        }
    })
}

var msg= initMessage();
msg["init"]="sktrace.js init hook success";
send(msg);
const libname = "%moduleName%";
var isSpawn="%spawn%";
var symbol="%symbol%";
var offset="%offset%";
var offsetAddr=0
msg= initMessage();
msg["data"]='----- start trace -----'+libname;
send(msg);
if(isSpawn) {
    spawn_hook(libname,symbol,offset);
} else {
    // const modules = Process.enumerateModules();
    trace(symbol,offset);
}
})();
