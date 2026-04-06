if (typeof klog !== 'function') {
    function klog(data, ...args) {
        for (let item of args) {
            data += "\t" + item;
        }
        var message = {};
        message["jsname"] = "custom";
        message["data"] = data;
        send(message);
    }
}

if (typeof call_funs === 'undefined' || !call_funs) {
    var call_funs = {};
}

function _safeStr(v) {
    try {
        if (v === null) return "null";
        if (v === undefined) return "undefined";
        return String(v);
    } catch (e) {
        return "[toString error: " + e + "]";
    }
}

function _safeJson(v) {
    try {
        return JSON.stringify(v);
    } catch (e) {
        return _safeStr(v);
    }
}

function _getJavaStack() {
    try {
        var Log = Java.use('android.util.Log');
        var Throwable = Java.use('java.lang.Throwable');
        return Log.getStackTraceString(Throwable.$new());
    } catch (e) {
        return "[stack unavailable: " + e + "]";
    }
}

function _shouldLogKey(key) {
    try {
        if (key === null || key === undefined) return true;
        var s = String(key);
        return true;
    } catch (e) {
        return true;
    }
}

function _hookSystemProperties() {
    try {
        var SP = Java.use('android.os.SystemProperties');
        klog('[custom] hooking android.os.SystemProperties');

        try {
            var ov = SP.get.overload('java.lang.String');
            ov.implementation = function (key) {
                var ret = ov.call(this, key);
                try {
                    if (_shouldLogKey(key)) {
                        klog('[custom] SystemProperties.get(key)', 'key=' + _safeStr(key), 'ret=' + _safeStr(ret));
                    }
                } catch (e) {
                    klog('[custom] SystemProperties.get(key) log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook SystemProperties.get(String) failed', _safeStr(e));
        }

        try {
            var ov2 = SP.get.overload('java.lang.String', 'java.lang.String');
            ov2.implementation = function (key, def) {
                var ret = ov2.call(this, key, def);
                try {
                    if (_shouldLogKey(key)) {
                        klog('[custom] SystemProperties.get(key,def)', 'key=' + _safeStr(key), 'def=' + _safeStr(def), 'ret=' + _safeStr(ret));
                    }
                } catch (e) {
                    klog('[custom] SystemProperties.get(key,def) log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook SystemProperties.get(String,String) failed', _safeStr(e));
        }

        try {
            var ov3 = SP.getInt.overload('java.lang.String', 'int');
            ov3.implementation = function (key, def) {
                var ret = ov3.call(this, key, def);
                try {
                    if (_shouldLogKey(key)) {
                        klog('[custom] SystemProperties.getInt', 'key=' + _safeStr(key), 'def=' + _safeStr(def), 'ret=' + _safeStr(ret));
                    }
                } catch (e) {
                    klog('[custom] SystemProperties.getInt log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook SystemProperties.getInt failed', _safeStr(e));
        }

        try {
            var ov4 = SP.getLong.overload('java.lang.String', 'long');
            ov4.implementation = function (key, def) {
                var ret = ov4.call(this, key, def);
                try {
                    if (_shouldLogKey(key)) {
                        klog('[custom] SystemProperties.getLong', 'key=' + _safeStr(key), 'def=' + _safeStr(def), 'ret=' + _safeStr(ret));
                    }
                } catch (e) {
                    klog('[custom] SystemProperties.getLong log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook SystemProperties.getLong failed', _safeStr(e));
        }

        try {
            var ov5 = SP.getBoolean.overload('java.lang.String', 'boolean');
            ov5.implementation = function (key, def) {
                var ret = ov5.call(this, key, def);
                try {
                    if (_shouldLogKey(key)) {
                        klog('[custom] SystemProperties.getBoolean', 'key=' + _safeStr(key), 'def=' + _safeStr(def), 'ret=' + _safeStr(ret));
                    }
                } catch (e) {
                    klog('[custom] SystemProperties.getBoolean log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook SystemProperties.getBoolean failed', _safeStr(e));
        }

        try {
            var ov6 = SP.set.overload('java.lang.String', 'java.lang.String');
            ov6.implementation = function (key, val) {
                klog('[custom] SystemProperties.set', 'key=' + _safeStr(key), 'val=' + _safeStr(val));
                return ov6.call(this, key, val);
            };
        } catch (e) {
            klog('[custom] hook SystemProperties.set failed', _safeStr(e));
        }

    } catch (e) {
        klog('[custom] android.os.SystemProperties unavailable', _safeStr(e));
    }
}

function _hookJavaSystem() {
    try {
        var JSys = Java.use('java.lang.System');
        klog('[custom] hooking java.lang.System');

        try {
            var ov = JSys.getProperty.overload('java.lang.String');
            ov.implementation = function (key) {
                var ret = ov.call(this, key);
                try {
                    klog('[custom] System.getProperty(key)', 'key=' + _safeStr(key), 'ret=' + _safeStr(ret));
                } catch (e) {
                    klog('[custom] System.getProperty(key) log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook System.getProperty(String) failed', _safeStr(e));
        }

        try {
            var ov2 = JSys.getProperty.overload('java.lang.String', 'java.lang.String');
            ov2.implementation = function (key, def) {
                var ret = ov2.call(this, key, def);
                try {
                    klog('[custom] System.getProperty(key,def)', 'key=' + _safeStr(key), 'def=' + _safeStr(def), 'ret=' + _safeStr(ret));
                } catch (e) {
                    klog('[custom] System.getProperty(key,def) log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook System.getProperty(String,String) failed', _safeStr(e));
        }

        try {
            var ov3 = JSys.getenv.overload('java.lang.String');
            ov3.implementation = function (key) {
                var ret = ov3.call(this, key);
                try {
                    klog('[custom] System.getenv(key)', 'key=' + _safeStr(key), 'ret=' + _safeStr(ret));
                } catch (e) {
                    klog('[custom] System.getenv(key) log error', _safeStr(e));
                }
                return ret;
            };
        } catch (e) {
            klog('[custom] hook System.getenv(String) failed', _safeStr(e));
        }

    } catch (e) {
        klog('[custom] java.lang.System unavailable', _safeStr(e));
    }
}

function _hookBuildFields() {
    try {
        var Build = Java.use('android.os.Build');
        klog('[custom] Build fields snapshot'
            , 'MODEL=' + _safeStr(Build.MODEL.value)
            , 'BRAND=' + _safeStr(Build.BRAND.value)
            , 'MANUFACTURER=' + _safeStr(Build.MANUFACTURER.value)
            , 'DEVICE=' + _safeStr(Build.DEVICE.value)
            , 'PRODUCT=' + _safeStr(Build.PRODUCT.value)
            , 'HARDWARE=' + _safeStr(Build.HARDWARE.value)
            , 'FINGERPRINT=' + _safeStr(Build.FINGERPRINT.value)
        );
    } catch (e) {
        klog('[custom] Build fields read failed', _safeStr(e));
    }

    try {
        var BuildVersion = Java.use('android.os.Build$VERSION');
        klog('[custom] Build.VERSION snapshot'
            , 'SDK_INT=' + _safeStr(BuildVersion.SDK_INT.value)
            , 'RELEASE=' + _safeStr(BuildVersion.RELEASE.value)
            , 'CODENAME=' + _safeStr(BuildVersion.CODENAME.value)
            , 'INCREMENTAL=' + _safeStr(BuildVersion.INCREMENTAL.value)
        );
    } catch (e) {
        klog('[custom] Build.VERSION read failed', _safeStr(e));
    }
}

function _hookNativeGetprop() {
    var targets = [
        { lib: 'libc.so', name: '__system_property_get' },
        { lib: 'libc.so', name: '__system_property_read' },
        { lib: 'libc.so', name: '__system_property_read_callback' }
    ];

    targets.forEach(function (t) {
        try {
            var addr = Module.findExportByName(t.lib, t.name);
            if (!addr) {
                klog('[custom] native export not found', t.lib + '!' + t.name);
                return;
            }
            klog('[custom] hooking native', t.lib + '!' + t.name, addr);

            if (t.name === '__system_property_get') {
                Interceptor.attach(addr, {
                    onEnter: function (args) {
                        this.key = '';
                        this.buf = args[1];
                        try {
                            this.key = Memory.readCString(args[0]);
                        } catch (e) {
                            this.key = '[read key failed: ' + e + ']';
                        }
                    },
                    onLeave: function (retval) {
                        try {
                            var retLen = retval.toInt32();
                            var val = '';
                            if (this.buf && retLen >= 0) {
                                try {
                                    val = Memory.readCString(this.buf);
                                } catch (e) {
                                    val = '[read val failed: ' + e + ']';
                                }
                            }
                            klog('[custom] __system_property_get', 'key=' + _safeStr(this.key), 'ret=' + retLen, 'val=' + _safeStr(val));
                        } catch (e) {
                            klog('[custom] __system_property_get onLeave error', _safeStr(e));
                        }
                    }
                });
            } else if (t.name === '__system_property_read') {
                Interceptor.attach(addr, {
                    onEnter: function (args) {
                        this.pi = args[0];
                        this.namePtr = args[1];
                        this.valuePtr = args[2];
                    },
                    onLeave: function (retval) {
                        try {
                            var name = '';
                            var value = '';
                            if (!this.namePtr.isNull()) {
                                try { name = Memory.readCString(this.namePtr); } catch (e) { name = '[name read failed: ' + e + ']'; }
                            }
                            if (!this.valuePtr.isNull()) {
                                try { value = Memory.readCString(this.valuePtr); } catch (e) { value = '[value read failed: ' + e + ']'; }
                            }
                            klog('[custom] __system_property_read', 'name=' + _safeStr(name), 'value=' + _safeStr(value), 'ret=' + _safeStr(retval));
                        } catch (e) {
                            klog('[custom] __system_property_read onLeave error', _safeStr(e));
                        }
                    }
                });
            } else if (t.name === '__system_property_read_callback') {
                Interceptor.attach(addr, {
                    onEnter: function (args) {
                        klog('[custom] __system_property_read_callback', 'pi=' + args[0], 'callback=' + args[1], 'cookie=' + args[2]);
                    }
                });
            }
        } catch (e) {
            klog('[custom] hook native failed', t.lib + '!' + t.name, _safeStr(e));
        }
    });
}

Java.perform(function () {
    try {
        klog('[custom] getprop hook init');
        _hookSystemProperties();
        _hookJavaSystem();
        _hookBuildFields();
        klog('[custom] getprop java hooks installed');
    } catch (e) {
        klog('[custom] Java.perform error', _safeStr(e));
    }
});

setImmediate(function () {
    try {
        _hookNativeGetprop();
    } catch (e) {
        klog('[custom] native hook init error', _safeStr(e));
    }
});

call_funs.demo = function (args) {
    Java.perform(function () {
        try {
            var key = 'ro.build.version.sdk';
            if (args !== undefined && args !== null) {
                if (typeof args === 'string') {
                    key = args;
                } else if (typeof args === 'object' && args.key) {
                    key = String(args.key);
                }
            }

            klog('[custom] demo start', 'args=' + _safeJson(args), 'key=' + _safeStr(key));

            var SP = null;
            try {
                SP = Java.use('android.os.SystemProperties');
            } catch (e) {
                klog('[custom] demo SystemProperties unavailable', _safeStr(e));
            }

            if (SP) {
                try {
                    var v1 = SP.get(key);
                    klog('[custom] demo SystemProperties.get', 'key=' + _safeStr(key), 'ret=' + _safeStr(v1));
                } catch (e) {
                    klog('[custom] demo SystemProperties.get error', _safeStr(e));
                }

                try {
                    var v2 = SP.get(key, 'N/A');
                    klog('[custom] demo SystemProperties.get(key,def)', 'key=' + _safeStr(key), 'ret=' + _safeStr(v2));
                } catch (e) {
                    klog('[custom] demo SystemProperties.get(key,def) error', _safeStr(e));
                }
            }

            try {
                var JSys = Java.use('java.lang.System');
                var javaVer = JSys.getProperty('java.version', 'N/A');
                klog('[custom] demo System.getProperty', 'key=java.version', 'ret=' + _safeStr(javaVer));
            } catch (e) {
                klog('[custom] demo System.getProperty error', _safeStr(e));
            }

            klog('[custom] demo done');
        } catch (e) {
            klog('[custom] demo exception', _safeStr(e));
        }
    });
};

call_funs.getprop = function (args) {
    Java.perform(function () {
        try {
            var key = '';
            var defVal = 'N/A';
            if (typeof args === 'string') {
                key = args;
            } else if (args && typeof args === 'object') {
                key = args.key ? String(args.key) : '';
                if (args.def !== undefined && args.def !== null) {
                    defVal = String(args.def);
                }
            }

            if (!key) {
                klog('[custom] getprop TODO: missing key, use call_funs.getprop("ro.build.version.sdk")');
                return;
            }

            var SP = Java.use('android.os.SystemProperties');
            var ret = SP.get(key, defVal);
            klog('[custom] active getprop', 'key=' + _safeStr(key), 'def=' + _safeStr(defVal), 'ret=' + _safeStr(ret));
        } catch (e) {
            klog('[custom] active getprop error', _safeStr(e));
        }
    });
};