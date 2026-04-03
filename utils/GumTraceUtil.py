import json


MODE_MANUAL = "manual"
MODE_OFFSET = "offset"
MODE_EXPORT = "export"


def split_csv(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).replace("\n", ",").split(",")
    return [str(item).strip() for item in items if str(item).strip()]


def split_int_csv(value):
    result = []
    for item in split_csv(value):
        try:
            result.append(int(item, 0))
        except Exception:
            continue
    return result


def stringify_bool(value):
    return "true" if bool(value) else "false"


def quote_string(value):
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def quote_str_list(values):
    return json.dumps(split_csv(values), ensure_ascii=False)


def quote_int_list(values):
    return "[" + ", ".join(str(item) for item in split_int_csv(values)) + "]"


COMMON_BLOCK = """function klog(data, ...args) {{
    for (let item of args) {{
        data += \"\\t\" + item;
    }}
    var message = {{}};
    message[\"jsname\"] = \"jni_trace_new\";
    message[\"data\"] = data;
    send(message);
}}

const gumTraceSoPath = {gumtrace_so_path};
const triggerMode = {trigger_mode};
const triggerModuleName = {trigger_module_name};
const traceModuleWhitelist = {trace_module_whitelist};
const traceOutputPath = {trace_output_path};
const traceThreadId = {trace_thread_id};
const traceOptions = {trace_options};
const allowedThreadIds = {allowed_thread_ids};
const triggerOffsets = {trigger_offsets};
const triggerExports = {trigger_exports};
const stopTraceOnLeave = {stop_trace_on_leave};
const allowRepeatedTrace = {allow_repeated_trace};
const traceModuleNames = traceModuleWhitelist.length > 0 ? traceModuleWhitelist.join(\",\") : triggerModuleName;

var gumtraceState = {{
    handle: null,
    init: null,
    run: null,
    unrun: null,
    tracing: false,
    installedOffsets: {{}},
    installedExports: {{}},
    watchingLoad: false,
}};

function ensureGumTraceLoaded() {{
    if (gumtraceState.handle !== null) {{
        return true;
    }}
    var dlopenPtr = Module.findExportByName(null, \"dlopen\");
    var dlsymPtr = Module.findExportByName(null, \"dlsym\");
    if (dlopenPtr === null || dlsymPtr === null) {{
        klog(\"gumtrace\", \"dlopen/dlsym not found\");
        return false;
    }}
    var dlopen = new NativeFunction(dlopenPtr, \"pointer\", [\"pointer\", \"int\"]);
    var dlsym = new NativeFunction(dlsymPtr, \"pointer\", [\"pointer\", \"pointer\"]);
    var handle = dlopen(Memory.allocUtf8String(gumTraceSoPath), 2);
    if (handle.isNull()) {{
        klog(\"gumtrace\", \"dlopen failed\", gumTraceSoPath, \"try: adb shell setenforce 0\");
        return false;
    }}
    gumtraceState.handle = handle;
    gumtraceState.init = new NativeFunction(dlsym(handle, Memory.allocUtf8String(\"init\")), \"void\", [\"pointer\", \"pointer\", \"int\", \"int\"]);
    gumtraceState.run = new NativeFunction(dlsym(handle, Memory.allocUtf8String(\"run\")), \"void\", []);
    gumtraceState.unrun = new NativeFunction(dlsym(handle, Memory.allocUtf8String(\"unrun\")), \"void\", []);
    klog(\"gumtrace\", \"library loaded\", gumTraceSoPath);
    return true;
}}

function shouldTraceCurrentThread() {{
    if (allowedThreadIds.length === 0) {{
        return true;
    }}
    var currentTid = Process.getCurrentThreadId();
    if (allowedThreadIds.indexOf(currentTid) === -1) {{
        klog(\"gumtrace\", \"skip thread\", currentTid, \"allowed=\" + allowedThreadIds.join(\",\"));
        return false;
    }}
    return true;
}}

function startGumTrace(outputPath) {{
    if (!ensureGumTraceLoaded()) {{
        return false;
    }}
    if (gumtraceState.tracing) {{
        klog(\"gumtrace\", \"trace already running\", outputPath || traceOutputPath);
        return true;
    }}
    gumtraceState.init(
        Memory.allocUtf8String(traceModuleNames),
        Memory.allocUtf8String(outputPath || traceOutputPath),
        traceThreadId,
        traceOptions
    );
    gumtraceState.run();
    gumtraceState.tracing = true;
    klog(\"gumtrace\", \"trace started\", traceModuleNames, outputPath || traceOutputPath, \"thread=\" + traceThreadId, \"options=\" + traceOptions);
    return true;
}}

function stopGumTrace() {{
    if (gumtraceState.handle === null || gumtraceState.tracing === false) {{
        klog(\"gumtrace\", \"trace is not running\");
        return;
    }}
    gumtraceState.unrun();
    gumtraceState.tracing = false;
    klog(\"gumtrace\", \"trace stopped\");
}}

function installOffsetHooks() {{
    var targetModule = Process.findModuleByName(triggerModuleName);
    if (targetModule === null) {{
        klog(\"gumtrace\", \"target module not loaded yet\", triggerModuleName);
        return false;
    }}
    if (triggerOffsets.length === 0) {{
        klog(\"gumtrace\", \"no trigger offsets configured\");
        return false;
    }}
    triggerOffsets.forEach(function (offset) {{
        var key = triggerModuleName + \"@\" + offset;
        if (gumtraceState.installedOffsets[key]) {{
            return;
        }}
        var targetAddress = targetModule.base.add(offset);
        gumtraceState.installedOffsets[key] = true;
        klog(\"gumtrace\", \"install offset trigger\", key, targetAddress.toString());
        Interceptor.attach(targetAddress, {{
            onEnter(args) {{
                this.traceStarted = false;
                if (!shouldTraceCurrentThread()) {{
                    return;
                }}
                if (allowRepeatedTrace === false && gumtraceState.tracing) {{
                    return;
                }}
                if (startGumTrace(traceOutputPath)) {{
                    this.traceStarted = true;
                    klog(\"gumtrace\", \"offset onEnter\", key, \"x0=\" + this.context.x0, \"lr=\" + this.context.lr);
                }}
            }},
            onLeave(retval) {{
                if (this.traceStarted) {{
                    klog(\"gumtrace\", \"offset onLeave\", key, \"retval=\" + retval);
                    if (stopTraceOnLeave) {{
                        stopGumTrace();
                    }}
                }}
            }}
        }});
    }});
    return true;
}}

function installExportHooks() {{
    var targetModule = Process.findModuleByName(triggerModuleName);
    if (targetModule === null) {{
        klog(\"gumtrace\", \"target module not loaded yet\", triggerModuleName);
        return false;
    }}
    if (triggerExports.length === 0) {{
        klog(\"gumtrace\", \"no trigger exports configured\");
        return false;
    }}
    triggerExports.forEach(function (exportName) {{
        var key = triggerModuleName + \"!\" + exportName;
        if (gumtraceState.installedExports[key]) {{
            return;
        }}
        var exportPtr = Module.findExportByName(triggerModuleName, exportName);
        if (exportPtr === null) {{
            klog(\"gumtrace\", \"export not found\", key);
            return;
        }}
        gumtraceState.installedExports[key] = true;
        klog(\"gumtrace\", \"install export trigger\", key, exportPtr.toString());
        Interceptor.attach(exportPtr, {{
            onEnter(args) {{
                this.traceStarted = false;
                if (!shouldTraceCurrentThread()) {{
                    return;
                }}
                if (allowRepeatedTrace === false && gumtraceState.tracing) {{
                    return;
                }}
                if (startGumTrace(traceOutputPath)) {{
                    this.traceStarted = true;
                    klog(\"gumtrace\", \"enter\", key, \"arg0=\" + args[0], \"arg1=\" + args[1]);
                }}
            }},
            onLeave(retval) {{
                if (this.traceStarted) {{
                    klog(\"gumtrace\", \"leave\", key, \"retval=\" + retval);
                    if (stopTraceOnLeave) {{
                        stopGumTrace();
                    }}
                }}
            }}
        }});
    }});
    return true;
}}

function watchModuleLoad(installer) {{
    if (gumtraceState.watchingLoad) {{
        return;
    }}
    gumtraceState.watchingLoad = true;
    var dlopenExt = Module.findExportByName(null, \"android_dlopen_ext\");
    if (dlopenExt === null) {{
        installer();
        return;
    }}
    Interceptor.attach(dlopenExt, {{
        onEnter(args) {{
            this.shouldInstall = false;
            var pathSo = args[0].readCString();
            if (pathSo && pathSo.indexOf(triggerModuleName) > -1) {{
                this.shouldInstall = true;
            }}
        }},
        onLeave() {{
            if (this.shouldInstall) {{
                installer();
            }}
        }}
    }});
    installer();
}}

var call_funs = {{}};
call_funs.gumtrace_start = function (args) {{
    var output = (args || \"\").trim();
    startGumTrace(output || traceOutputPath);
}};
call_funs.gumtrace_stop = function () {{
    stopGumTrace();
}};
call_funs.gumtrace_install = function () {{
    if (triggerMode === \"offset\") {{
        installOffsetHooks();
        return;
    }}
    if (triggerMode === \"export\") {{
        installExportHooks();
        return;
    }}
    klog(\"gumtrace\", \"manual mode has no install step\");
}};
call_funs.gumtrace_help = function () {{
    klog(\"gumtrace\", \"template\", \"%customFileName%\");
    klog(\"gumtrace\", \"mode\", triggerMode, \"triggerModule=\" + triggerModuleName);
    klog(\"gumtrace\", \"trace modules\", traceModuleNames, \"threads=\" + JSON.stringify(allowedThreadIds));
    klog(\"gumtrace\", \"output\", traceOutputPath, \"stopOnLeave=\" + stopTraceOnLeave, \"repeat=\" + allowRepeatedTrace);
}}

rpc.exports.callnormal = function (methodName, args) {{
    if (call_funs[methodName]) {{
        call_funs[methodName](args || \"\");
        return;
    }}
    klog(\"gumtrace\", \"unknown call_funs\", methodName);
}};
"""

MANUAL_BLOCK = """setImmediate(function () {{
    klog(\"init\", \"%customFileName% loaded\");
    klog(\"gumtrace\", \"manual mode\", \"upload libGumTrace.so first\");
    klog(\"gumtrace\", \"modules\", traceModuleNames, traceOutputPath);
    klog(\"gumtrace\", \"use call_funs.gumtrace_start / gumtrace_stop\");
}});
"""

OFFSET_BLOCK = """setImmediate(function () {{
    klog(\"init\", \"%customFileName% loaded\");
    klog(\"gumtrace\", \"offset auto trace\", triggerModuleName, JSON.stringify(triggerOffsets));
    klog(\"gumtrace\", \"modules\", traceModuleNames, traceOutputPath, \"threads=\" + JSON.stringify(allowedThreadIds));
    watchModuleLoad(installOffsetHooks);
}});
"""

EXPORT_BLOCK = """setImmediate(function () {{
    klog(\"init\", \"%customFileName% loaded\");
    klog(\"gumtrace\", \"export trigger trace\", triggerModuleName, JSON.stringify(triggerExports));
    klog(\"gumtrace\", \"modules\", traceModuleNames, traceOutputPath, \"threads=\" + JSON.stringify(allowedThreadIds));
    watchModuleLoad(installExportHooks);
}});
"""


def build_gumtrace_script(config):
    mode = config.get("mode", MODE_MANUAL)
    script = COMMON_BLOCK.format(
        gumtrace_so_path=quote_string(config.get("gumTraceSoPath", "/data/local/tmp/libGumTrace.so")),
        trigger_mode=quote_string(mode),
        trigger_module_name=quote_string(config.get("triggerModuleName", "libtarget.so")),
        trace_module_whitelist=quote_str_list(config.get("traceModuleWhitelist", "libtarget.so")),
        trace_output_path=quote_string(config.get("traceOutputPath", "/data/local/tmp/gumtrace.log")),
        trace_thread_id=int(str(config.get("traceThreadId", 0) or 0), 0),
        trace_options=int(str(config.get("traceOptions", 0) or 0), 0),
        allowed_thread_ids=quote_int_list(config.get("allowedThreadIds", "")),
        trigger_offsets=quote_int_list(config.get("triggerOffsets", "")),
        trigger_exports=quote_str_list(config.get("triggerExports", "")),
        stop_trace_on_leave=stringify_bool(config.get("stopTraceOnLeave", True)),
        allow_repeated_trace=stringify_bool(config.get("allowRepeatedTrace", False)),
    )
    if mode == MODE_OFFSET:
        script += OFFSET_BLOCK
    elif mode == MODE_EXPORT:
        script += EXPORT_BLOCK
    else:
        script += MANUAL_BLOCK
    return script
