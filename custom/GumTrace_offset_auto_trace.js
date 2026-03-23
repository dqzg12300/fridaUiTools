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
const triggerModuleName = "libtarget.so";
const traceModuleNames = "libtarget.so";
const traceOutputPath = "/data/local/tmp/gumtrace_offset.log";
const triggerOffsets = [0x1234];
const traceThreadId = 0;
const traceOptions = 0;
const stopTraceOnLeave = true;
const allowRepeatedTrace = false;

var gumtraceState = {
    handle: null,
    init: null,
    run: null,
    unrun: null,
    tracing: false,
    installedOffsets: {},
    loadHookInstalled: false,
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

function startGumTrace(outputPath) {
    if (!ensureGumTraceLoaded()) {
        return false;
    }
    if (gumtraceState.tracing) {
        klog("gumtrace", "trace already running", outputPath || traceOutputPath);
        return true;
    }
    gumtraceState.init(
        Memory.allocUtf8String(traceModuleNames),
        Memory.allocUtf8String(outputPath || traceOutputPath),
        traceThreadId,
        traceOptions
    );
    gumtraceState.run();
    gumtraceState.tracing = true;
    klog("gumtrace", "trace started", traceModuleNames, outputPath || traceOutputPath, "thread=" + traceThreadId, "options=" + traceOptions);
    return true;
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

function installOffsetHooks() {
    var targetModule = Process.findModuleByName(triggerModuleName);
    if (targetModule === null) {
        klog("gumtrace", "target module not loaded yet", triggerModuleName);
        return false;
    }
    triggerOffsets.forEach(function (offset) {
        var key = triggerModuleName + "@" + offset;
        if (gumtraceState.installedOffsets[key]) {
            return;
        }
        var targetAddress = targetModule.base.add(offset);
        gumtraceState.installedOffsets[key] = true;
        klog("gumtrace", "install offset trigger", key, targetAddress.toString());
        Interceptor.attach(targetAddress, {
            onEnter(args) {
                this.traceStarted = false;
                if (allowRepeatedTrace === false && gumtraceState.tracing) {
                    return;
                }
                if (startGumTrace(traceOutputPath)) {
                    this.traceStarted = true;
                    klog("gumtrace", "offset onEnter", key, "x0=" + this.context.x0, "lr=" + this.context.lr);
                }
            },
            onLeave(retval) {
                if (this.traceStarted) {
                    klog("gumtrace", "offset onLeave", key, "retval=" + retval);
                    if (stopTraceOnLeave) {
                        stopGumTrace();
                    }
                }
            }
        });
    });
    return true;
}

function watchModuleLoad() {
    if (gumtraceState.loadHookInstalled) {
        return;
    }
    gumtraceState.loadHookInstalled = true;
    var dlopenExt = Module.findExportByName(null, "android_dlopen_ext");
    if (dlopenExt === null) {
        klog("gumtrace", "android_dlopen_ext not found, trying immediate install only");
        installOffsetHooks();
        return;
    }
    Interceptor.attach(dlopenExt, {
        onEnter(args) {
            this.shouldInstall = false;
            var pathSo = args[0].readCString();
            if (pathSo && pathSo.indexOf(triggerModuleName) > -1) {
                this.shouldInstall = true;
            }
        },
        onLeave() {
            if (this.shouldInstall) {
                installOffsetHooks();
            }
        }
    });
    installOffsetHooks();
}

var call_funs = {};
call_funs.gumtrace_start = function () {
    startGumTrace(traceOutputPath);
};
call_funs.gumtrace_stop = function () {
    stopGumTrace();
};
call_funs.gumtrace_install = function () {
    installOffsetHooks();
};
call_funs.gumtrace_help = function () {
    klog("gumtrace", "template", "%customFileName%");
    klog("gumtrace", "edit triggerModuleName/traceModuleNames/triggerOffsets before use");
    klog("gumtrace", "current", triggerModuleName, JSON.stringify(triggerOffsets), traceOutputPath);
};

rpc.exports.callnormal = function (methodName, args) {
    if (call_funs[methodName]) {
        call_funs[methodName](args || "");
        return;
    }
    klog("gumtrace", "unknown call_funs", methodName);
};

setImmediate(function () {
    klog("init", "%customFileName% loaded");
    klog("gumtrace", "offset auto trace template", triggerModuleName, traceOutputPath);
    klog("gumtrace", "remember to upload libGumTrace.so before tracing");
    watchModuleLoad();
});
