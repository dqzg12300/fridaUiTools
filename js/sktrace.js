(function(){

const arm64CM = new CModule(`
#include <gum/gumstalker.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

extern void on_message(const gchar *message);
static void log(const gchar *format, ...);
static void on_arm64_before(GumCpuContext *cpu_context, gpointer user_data);
static void on_arm64_after(GumCpuContext *cpu_context, gpointer user_data);

void hello() {
    on_message("Hello form CModule");
}

gpointer shared_mem[] = {0, 0};

gpointer 
get_shared_mem() 
{
    return shared_mem;
}


static void
log(const gchar *format, ...)
{
    gchar *message;
    va_list args;

    va_start(args, format);
    message = g_strdup_vprintf(format, args);
    va_end(args);

    on_message(message);
    g_free(message);
}


void transform(GumStalkerIterator *iterator,
               GumStalkerOutput *output,
               gpointer user_data)
{
    cs_insn *insn;

    gpointer base = *(gpointer*)user_data;
    gpointer end = *(gpointer*)(user_data + sizeof(gpointer));
    
    while (gum_stalker_iterator_next(iterator, &insn))
    {
        gboolean in_target = (gpointer)insn->address >= base && (gpointer)insn->address < end;
        if(in_target)
        {
            log("%p\t%s\t%s", (gpointer)insn->address, insn->mnemonic, insn->op_str);
            gum_stalker_iterator_put_callout(iterator, on_arm64_before, (gpointer) insn->address, NULL);
        }
        gum_stalker_iterator_keep(iterator);
        if(in_target) 
        {
            gum_stalker_iterator_put_callout(iterator, on_arm64_after, (gpointer) insn->address, NULL);
        }
    }
}


const gchar * cpu_format = "
    0x%x\t0x%x\t0x%x\t0x%x\t0x%x
    \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
    \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
    \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
    \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
    \t0x%x\t0x%x\t0x%x\t0x%x\t0x%x
    \t0x%x\t0x%x\t0x%x
    ";

static void
on_arm64_before(GumCpuContext *cpu_context,
        gpointer user_data)
{

}

static void
on_arm64_after(GumCpuContext *cpu_context,
        gpointer user_data)
{

}

`, {
    on_message: new NativeCallback(messagePtr => {
        const message = messagePtr.readUtf8String();
        var msg=initMessage();
        msg["data"]=message;
        send(msg);
        console.log(message);
        // send(message)
      }, 'void', ['pointer']),
});

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


function stalkerTraceRange(tid, base, size) {
    Stalker.follow(tid, {
        transform: (iterator) => {
            const instruction = iterator.next();
            const startAddress = instruction.address;
            const isModuleCode = startAddress.compare(base) >= 0 &&
                startAddress.compare(base.add(size)) < 0;
            // const isModuleCode = true;
            do {
                iterator.keep();
                if (isModuleCode) {
                    var address=ptr(instruction["address"]-moduleBase);
                    send({
                        type: 'inst',
                        tid: tid,
                        block: startAddress,
                        val: JSON.stringify(instruction),
                        jsname:"sktrace",
                        moduleBase:moduleBase,
                        address:address,
                    })

                    iterator.putCallout((context) => {
                        var callOutAddress=ptr(context.pc-moduleBase)
                        send({
                            type: 'ctx',
                            tid: tid,
                            val: JSON.stringify(context),
                            jsname:"sktrace",
                            moduleBase:moduleBase,
                            address:callOutAddress
                        })

                    })

                }
            } while (iterator.next() !== null);
            // if(flag){
            //     send(data)
            // }
        }
    })
}


function traceAddr(addr) {
    let moduleMap = new ModuleMap();
    let targetModule = moduleMap.find(addr);
    var msg=initMessage();
    msg["data"]=JSON.stringify(targetModule);
    send(msg);
    let exports = targetModule.enumerateExports();
    let symbols = targetModule.enumerateSymbols();
    // send({
    //     type: "module",
    //     targetModule
    // })
    // send({
    //     type: "sym",


    // })
    Interceptor.attach(addr, {
        onEnter: function(args) {
            this.tid = Process.getCurrentThreadId()
            // stalkerTraceRangeC(this.tid, targetModule.base, targetModule.size)
            stalkerTraceRange(this.tid, targetModule.base, targetModule.size)
        },
        onLeave: function(ret) {
            Stalker.unfollow(this.tid);
            Stalker.garbageCollect()
            send({
                type: "fin",
                tid: this.tid,
                jsname:"sktrace"
            })
        }
    })
}


function traceSymbol(symbol) {

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
var moduleBase=0;
const libname = "%moduleName%";
var isSpawn="%spawn%";
var symbol="%symbol%";
var offset="%offset%";
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
