//简单的一键反调试，来源FridaContainer
(function(){

function klog(data){
    var message={};
    message["jsname"]="anti_debug";
    message["data"]=data;
    send(message);
    // console.log(data);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="anti_debug";
    message["data"]=data;
    message[key]=value;
    send(message);
    // console.log(data);
}

function tag_klog(tag,data){
    klog(tag+"\t"+data);
}

function showNativeStacks(context) {
    tag_klog('showNativeStacks', '\tBacktrace:\n\t' + Thread.backtrace(context, Backtracer.ACCURATE).map(DebugSymbol.fromAddress)
        .join('\n\t'));
}

function getLR(context) {
    if (Process.arch == 'arm') {
        return context.lr;
    }
    else if (Process.arch == 'arm64') {
        return context.lr;
    }
    else {
        tag_klog('getLR', 'not support current arch: ' + Process.arch);
    }
    return ptr(0);
}

function getModuleByAddr(addr) {
    var result = null;
    Process.enumerateModules().forEach(function (module) {
        if (module.base <= addr && addr <= (module.base.add(module.size))) {
            result = JSON.stringify(module);
            return false; // 跳出循环
        }
    });
    return result;
}

function anti_fgets() {
    const tag = 'anti_fgets';
    const fgetsPtr = Module.findExportByName(null, 'fgets');
    tag_klog(tag, 'fgets addr: ' + fgetsPtr);
    if (null == fgetsPtr) {
        return;
    }
    var fgets = new NativeFunction(fgetsPtr, 'pointer', ['pointer', 'int', 'pointer']);
    Interceptor.replace(fgetsPtr, new NativeCallback(function (buffer, size, fp) {
        if (null == this) {
            return 0;
        }
        var logTag = null;
        // 进入时先记录现场
        const lr = getLR(this.context);
        // 读取原 buffer
        var retval = fgets(buffer, size, fp);
        var bufstr = buffer.readCString();
        if (null != bufstr) {
            if (bufstr.indexOf("TracerPid:") > -1) {
                buffer.writeUtf8String("TracerPid:\t0");
                logTag = 'TracerPid';
            }
            //State:	S (sleeping)
            else if (bufstr.indexOf("State:\tt (tracing stop)") > -1) {
                buffer.writeUtf8String("State:\tS (sleeping)");
                logTag = 'State';
            }
            // ptrace_stop
            else if (bufstr.indexOf("ptrace_stop") > -1) {
                buffer.writeUtf8String("sys_epoll_wait");
                logTag = 'ptrace_stop';
            }
            //(sankuai.meituan) t
            else if (bufstr.indexOf(") t") > -1) {
                buffer.writeUtf8String(bufstr.replace(") t", ") S"));
                logTag = 'stat_t';
            }
            // SigBlk
            else if (bufstr.indexOf('SigBlk:') > -1) {
                buffer.writeUtf8String('SigBlk:\t0000000000001204');
                logTag = 'SigBlk';
            }
            // frida
            else if (bufstr.indexOf('frida') > -1) {
                buffer.writeUtf8String("");
                logTag = 'frida';
            }
            if (logTag) {
                tag_klog(tag + " " + logTag, bufstr + " -> " + buffer.readCString() + ' lr: ' + lr
                    + "(" + getModuleByAddr(lr) + ")");
                showNativeStacks(this?.context);
            }
        }
        return retval;
    }, 'pointer', ['pointer', 'int', 'pointer']));
}

function anti_ptrace() {
    var ptrace = Module.findExportByName(null, "ptrace");
    if (null != ptrace) {
        ptrace = ptrace.or(1);
        tag_klog('anti_ptrace', "ptrace addr: " + ptrace);
        // Interceptor.attach(ptrace, {
        //     onEnter: function (args) {
        //         DMLog.i('anti_ptrace', 'entry');
        //     }
        // });
        Interceptor.replace(ptrace.or(1), new NativeCallback(function (p1, p2, p3, p4) {
            tag_klog('anti_ptrace', 'entry');
            return 1;
        }, 'long', ['int', "int", 'pointer', 'pointer']));
    }
}

function anti_fork() {
    var fork_addr = Module.findExportByName(null, "fork");
    tag_klog('anti_ptrace', "fork_addr : " + fork_addr);
    if (null != fork_addr) {
        // Interceptor.attach(fork_addr, {
        //     onEnter: function (args) {
        //         DMLog.i('fork_addr', 'entry');
        //     }
        // });
        Interceptor.replace(fork_addr, new NativeCallback(function () {
            tag_klog('fork_addr', 'entry');
            return -1;
        }, 'int', []));
    }
}

function anti_exit() {
    const exit_ptr = Module.findExportByName(null, 'exit');
    tag_klog('anti_exit', "exit_ptr : " + exit_ptr);
    if (null == exit_ptr) {
        return;
    }
    Interceptor.replace(exit_ptr, new NativeCallback(function (code) {
        if (null == this) {
            return 0;
        }
        var lr = getLR(this.context);
        tag_klog('exit debug', 'entry, lr: ' + lr);
        return 0;
    }, 'int', ['int', 'int']));
}

function anti_kill() {
    const kill_ptr = Module.findExportByName(null, 'kill');
    tag_klog('anti_kill', "kill_ptr : " + kill_ptr);
    if (null == kill_ptr) {
        return;
    }
    Interceptor.replace(kill_ptr, new NativeCallback(function (ptid, code) {
        if (null == this) {
            return 0;
        }
        var lr = getLR(this.context);
        tag_klog('kill debug', 'entry, lr: ' + lr);
        showNativeStacks(this.context);
        return 0;
    }, 'int', ['int', 'int']));
}

function anti_debug() {
    anti_fgets();
    anti_exit();
    anti_fork();
    anti_kill();
    anti_ptrace();
}

Java.perform(function() {
    klogData("","init","anti_debug.js init hook success")
    anti_debug();
});

})();
