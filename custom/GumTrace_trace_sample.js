function klog(data, ...args) {
    for (let item of args) {
        data += "\t" + item;
    }
    var message = {};
    message["jsname"] = "jni_trace_new";
    message["data"] = data;
    send(message);
}

const gumTraceSoPath = "/data/local/tmp/libGumTrace.so";
const targetModules = "libtarget.so";
const traceLogPath = "/data/local/tmp/gumtrace.log";
const traceThreadId = 0;
const traceOptions = 0;
const autoTraceEnabled = false;
const autoTraceOffset = 0x0;

var gumtraceState = {
    handle: null,
    init: null,
    run: null,
    unrun: null,
    tracing: false,
    autoInstalled: false,
};

function ensureGumTraceLoaded() {
    if (gumtraceState.handle !== null) {
        return true;
    }
    var dlopenPtr = Module.findExportByName(null, "dlopen");
    var dlsymPtr = Module.findExportByName(null, "dlsym");
    if (dlopenPtr === null || dlsymPtr === null) {
        klog("gumtrace", "dlopen/dlsym not found");
        return false;
    }
    var dlopen = new NativeFunction(dlopenPtr, "pointer", ["pointer", "int"]);
    var dlsym = new NativeFunction(dlsymPtr, "pointer", ["pointer", "pointer"]);
    var handle = dlopen(Memory.allocUtf8String(gumTraceSoPath), 2);
    if (handle.isNull()) {
        klog("gumtrace", "dlopen failed", gumTraceSoPath, "try: adb shell setenforce 0");
        return false;
    }
    gumtraceState.handle = handle;
    gumtraceState.init = new NativeFunction(dlsym(handle, Memory.allocUtf8String("init")), "void", ["pointer", "pointer", "int", "int"]);
    gumtraceState.run = new NativeFunction(dlsym(handle, Memory.allocUtf8String("run")), "void", []);
    gumtraceState.unrun = new NativeFunction(dlsym(handle, Memory.allocUtf8String("unrun")), "void", []);
    klog("gumtrace", "library loaded", gumTraceSoPath);
    return true;
}

function startGumTrace(moduleNames, outputPath, threadId, options) {
    if (!ensureGumTraceLoaded()) {
        return;
    }
    if (gumtraceState.tracing) {
        klog("gumtrace", "trace already running", outputPath);
        return;
    }
    var moduleNamesPtr = Memory.allocUtf8String(moduleNames || targetModules);
    var outputPathPtr = Memory.allocUtf8String(outputPath || traceLogPath);
    gumtraceState.init(moduleNamesPtr, outputPathPtr, threadId, options);
    gumtraceState.run();
    gumtraceState.tracing = true;
    klog("gumtrace", "trace started", moduleNames || targetModules, outputPath || traceLogPath, "thread=" + threadId, "options=" + options);
}

function stopGumTrace() {
    if (gumtraceState.handle === null || gumtraceState.tracing === false) {
        klog("gumtrace", "trace is not running");
        return;
    }
    gumtraceState.unrun();
    gumtraceState.tracing = false;
    klog("gumtrace", "trace stopped");
}

var call_funs = {};
call_funs.gumtrace_start = function (args) {
    var argsSp = (args || "").split(",");
    var modules = argsSp[0] && argsSp[0].trim() ? argsSp[0].trim() : targetModules;
    var output = argsSp[1] && argsSp[1].trim() ? argsSp[1].trim() : traceLogPath;
    var threadId = argsSp[2] && argsSp[2].trim() ? parseInt(argsSp[2].trim()) : traceThreadId;
    var options = argsSp[3] && argsSp[3].trim() ? parseInt(argsSp[3].trim()) : traceOptions;
    startGumTrace(modules, output, threadId, options);
};
call_funs.gumtrace_stop = function () {
    stopGumTrace();
};
call_funs.gumtrace_help = function () {
    klog("gumtrace", "usage", "gumtrace_start(moduleNames,outputPath,threadId,options)");
    klog("gumtrace", "example", "gumtrace_start(libfoo.so,/data/local/tmp/gum.log,0,0)");
};

rpc.exports.callnormal = function (methodName, args) {
    if (call_funs[methodName]) {
        call_funs[methodName](args || "");
        return;
    }
    klog("gumtrace", "unknown call_funs", methodName);
};

function installAutoTrace() {
    if (!autoTraceEnabled) {
        klog("gumtrace", "auto trace disabled", "edit autoTraceEnabled/autoTraceOffset or use call_funs.gumtrace_start manually");
        return;
    }
    if (autoTraceOffset <= 0) {
        klog("gumtrace", "autoTraceOffset is invalid", "set a valid function offset before enabling auto trace");
        return;
    }
    var firstTarget = targetModules.split(",")[0].trim();
    var dlopenExt = Module.findExportByName(null, "android_dlopen_ext");
    if (dlopenExt === null) {
        klog("gumtrace", "android_dlopen_ext not found", "use manual start instead");
        return;
    }
    Interceptor.attach(dlopenExt, {
        onEnter(args) {
            this.shouldHook = false;
            var pathSo = args[0].readCString();
            if (pathSo && pathSo.indexOf(firstTarget) > -1) {
                this.shouldHook = true;
            }
        },
        onLeave() {
            if (!this.shouldHook || gumtraceState.autoInstalled) {
                return;
            }
            var targetModule = Process.findModuleByName(firstTarget);
            if (targetModule === null) {
                klog("gumtrace", "target module not found after load", firstTarget);
                return;
            }
            gumtraceState.autoInstalled = true;
            var targetAddress = targetModule.base.add(autoTraceOffset);
            klog("gumtrace", "install auto trace", firstTarget, targetAddress.toString());
            Interceptor.attach(targetAddress, {
                onEnter() {
                    if (gumtraceState.tracing === false) {
                        this.started = true;
                        startGumTrace(targetModules, traceLogPath, traceThreadId, traceOptions);
                    }
                },
                onLeave() {
                    if (this.started) {
                        stopGumTrace();
                    }
                }
            });
        }
    });
}

setImmediate(function () {
    klog("init", "%customFileName% GumTrace template loaded");
    klog("gumtrace", "upload libGumTrace.so to /data/local/tmp first");
    klog("gumtrace", "default target", targetModules, traceLogPath);
    installAutoTrace();
});
