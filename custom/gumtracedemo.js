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
const triggerMode = "export";
const triggerModuleName = "libnative-lib.so";
const traceModuleWhitelist = ["libnative-lib.so"];
const traceOutputPath = "/data/local/tmp/gumtrace.log";
const traceThreadId = 0;
const traceOptions = 0;
const allowedThreadIds = [];
const triggerOffsets = [4660];
const triggerExports = ["Java_com_example_gumtracedemo_NativeHelper_stringOps", "Java_com_example_gumtracedemo_NativeHelper_memoryOps"];
const stopTraceOnLeave = true;
const allowRepeatedTrace = false;
const traceModuleNames = traceModuleWhitelist.length > 0 ? traceModuleWhitelist.join(",") : triggerModuleName;

var gumtraceState = {
    handle: null,
    init: null,
    run: null,
    unrun: null,
    tracing: false,
    installedOffsets: {},
    installedExports: {},
    watchingLoad: false,
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

function shouldTraceCurrentThread() {
    if (allowedThreadIds.length === 0) {
        return true;
    }
    var currentTid = Process.getCurrentThreadId();
    if (allowedThreadIds.indexOf(currentTid) === -1) {
        klog("gumtrace", "skip thread", currentTid, "allowed=" + allowedThreadIds.join(","));
        return false;
    }
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
    if (triggerOffsets.length === 0) {
        klog("gumtrace", "no trigger offsets configured");
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
                if (!shouldTraceCurrentThread()) {
                    return;
                }
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

function installExportHooks() {
    var targetModule = Process.findModuleByName(triggerModuleName);
    if (targetModule === null) {
        klog("gumtrace", "target module not loaded yet", triggerModuleName);
        return false;
    }
    if (triggerExports.length === 0) {
        klog("gumtrace", "no trigger exports configured");
        return false;
    }
    triggerExports.forEach(function (exportName) {
        var key = triggerModuleName + "!" + exportName;
        if (gumtraceState.installedExports[key]) {
            return;
        }
        var exportPtr = Module.findExportByName(triggerModuleName, exportName);
        if (exportPtr === null) {
            klog("gumtrace", "export not found", key);
            return;
        }
        gumtraceState.installedExports[key] = true;
        klog("gumtrace", "install export trigger", key, exportPtr.toString());
        Interceptor.attach(exportPtr, {
            onEnter(args) {
                this.traceStarted = false;
                if (!shouldTraceCurrentThread()) {
                    return;
                }
                if (allowRepeatedTrace === false && gumtraceState.tracing) {
                    return;
                }
                if (startGumTrace(traceOutputPath)) {
                    this.traceStarted = true;
                    klog("gumtrace", "enter", key, "arg0=" + args[0], "arg1=" + args[1]);
                }
            },
            onLeave(retval) {
                if (this.traceStarted) {
                    klog("gumtrace", "leave", key, "retval=" + retval);
                    if (stopTraceOnLeave) {
                        stopGumTrace();
                    }
                }
            }
        });
    });
    return true;
}

function watchModuleLoad(installer) {
    if (gumtraceState.watchingLoad) {
        return;
    }
    gumtraceState.watchingLoad = true;
    var dlopenExt = Module.findExportByName(null, "android_dlopen_ext");
    if (dlopenExt === null) {
        installer();
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
                installer();
            }
        }
    });
    installer();
}

var call_funs = {};
call_funs.gumtrace_start = function (args) {
    var output = (args || "").trim();
    startGumTrace(output || traceOutputPath);
};
call_funs.gumtrace_stop = function () {
    stopGumTrace();
};
call_funs.gumtrace_install = function () {
    if (triggerMode === "offset") {
        installOffsetHooks();
        return;
    }
    if (triggerMode === "export") {
        installExportHooks();
        return;
    }
    klog("gumtrace", "manual mode has no install step");
};
call_funs.gumtrace_help = function () {
    klog("gumtrace", "template", "%customFileName%");
    klog("gumtrace", "mode", triggerMode, "triggerModule=" + triggerModuleName);
    klog("gumtrace", "trace modules", traceModuleNames, "threads=" + JSON.stringify(allowedThreadIds));
    klog("gumtrace", "output", traceOutputPath, "stopOnLeave=" + stopTraceOnLeave, "repeat=" + allowRepeatedTrace);
}

rpc.exports.callnormal = function (methodName, args) {
    if (call_funs[methodName]) {
        call_funs[methodName](args || "");
        return;
    }
    klog("gumtrace", "unknown call_funs", methodName);
};
setImmediate(function () {{
    klog("init", "%customFileName% loaded");
    klog("gumtrace", "export trigger trace", triggerModuleName, JSON.stringify(triggerExports));
    klog("gumtrace", "modules", traceModuleNames, traceOutputPath, "threads=" + JSON.stringify(allowedThreadIds));
    watchModuleLoad(installExportHooks);
}});
