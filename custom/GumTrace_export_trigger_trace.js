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
const triggerModuleName = "libssl.so";
const traceModuleNames = "libssl.so,libcrypto.so";
const traceOutputPath = "/data/local/tmp/gumtrace_ssl.log";
const triggerExports = ["SSL_read", "SSL_write"];
const traceThreadId = 0;
const traceOptions = 0;
const stopTraceOnLeave = true;

var gumtraceState = {
    handle: null,
    init: null,
    run: null,
    unrun: null,
    tracing: false,
    installedExports: {},
    waitingDlopen: false,
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

function startGumTrace() {
    if (!ensureGumTraceLoaded()) {
        return false;
    }
    if (gumtraceState.tracing) {
        return true;
    }
    gumtraceState.init(
        Memory.allocUtf8String(traceModuleNames),
        Memory.allocUtf8String(traceOutputPath),
        traceThreadId,
        traceOptions
    );
    gumtraceState.run();
    gumtraceState.tracing = true;
    klog("gumtrace", "trace started", traceModuleNames, traceOutputPath, "thread=" + traceThreadId, "options=" + traceOptions);
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

function installExportHooks() {
    var targetModule = Process.findModuleByName(triggerModuleName);
    if (targetModule === null) {
        klog("gumtrace", "target module not loaded yet", triggerModuleName);
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
                if (startGumTrace()) {
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

function watchModuleLoad() {
    if (gumtraceState.waitingDlopen) {
        return;
    }
    gumtraceState.waitingDlopen = true;
    var dlopenExt = Module.findExportByName(null, "android_dlopen_ext");
    if (dlopenExt === null) {
        installExportHooks();
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
                installExportHooks();
            }
        }
    });
    installExportHooks();
}

var call_funs = {};
call_funs.gumtrace_start = function () {
    startGumTrace();
};
call_funs.gumtrace_stop = function () {
    stopGumTrace();
};
call_funs.gumtrace_install = function () {
    installExportHooks();
};
call_funs.gumtrace_help = function () {
    klog("gumtrace", "template", "%customFileName%");
    klog("gumtrace", "edit triggerModuleName/triggerExports/traceModuleNames for your target");
    klog("gumtrace", "current", triggerModuleName, JSON.stringify(triggerExports), traceModuleNames, traceOutputPath);
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
    klog("gumtrace", "export trigger template", triggerModuleName, JSON.stringify(triggerExports));
    klog("gumtrace", "good for SSL/compression/JNI exported native functions");
    watchModuleLoad();
});
