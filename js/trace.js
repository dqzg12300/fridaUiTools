function log(text) {
    var packet = {
        'cmd': 'log',
        'data': text
    };
    send("ZenTracer:::" + JSON.stringify(packet))
}

function enter(tid, tname, cls, method, args) {
    var packet = {
        'cmd': 'enter',
        'data': [tid, tname, cls, method, args]
    };
    send("ZenTracer:::" + JSON.stringify(packet))
}

function exit(tid, retval) {
    var packet = {
        'cmd': 'exit',
        'data': [tid, retval]
    };
    send("ZenTracer:::" + JSON.stringify(packet))
}

function getTid() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getId();
}

function getTName() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getName();
}

function traceClass(clsname) {
    try {
        var target = Java.use(clsname);
        var methods = target.class.getDeclaredMethods();
        methods.forEach(function (method) {
            var methodName = method.getName();
            var overloads = target[methodName].overloads;
            overloads.forEach(function (overload) {
                var proto = "(";
                overload.argumentTypes.forEach(function (type) {
                    proto += type.className + ", ";
                });
                if (proto.length > 1) {
                    proto = proto.substr(0, proto.length - 2);
                }
                proto += ")";
                log("hooking: " + clsname + "." + methodName + proto);
                overload.implementation = function () {
                    var args = [];
                    var tid = getTid();
                    var tName = getTName();
                    for (var j = 0; j < arguments.length; j++) {
                        args[j] = arguments[j] + ""
                    }
                    enter(tid, tName, clsname, methodName + proto, args);
                    var retval = this[methodName].apply(this, arguments);
                    exit(tid, "" + retval);
                    return retval;
                }
            });
        });
    } catch (e) {
        log("'" + clsname + "' hook fail: " + e)
    }
}

function match(ex, text) {
    if (ex[1] == ':') {
        var mode = ex[0];
        if (mode == 'E') {
            ex = ex.substr(2, ex.length - 2);
            return ex == text;
        } else if (mode == 'M') {
            ex = ex.substr(2, ex.length - 2);
        } else {
            log("Unknown match mode: " + mode + ", current support M(match) and E(equal)")
        }
    }
    return text.match(ex)
}

if (Java.available) {
    Java.perform(function () {
        log('ZenTracer Start...');
        var matchRegEx = {MATCHREGEX};
        var blackRegEx = {BLACKREGEX};
        Java.enumerateLoadedClasses({
            onMatch: function (aClass) {
                for (var index in matchRegEx) {
                    // console.log(matchRegEx[index]);
                    if (match(matchRegEx[index], aClass)) {
                        var is_black = false;
                        for (var i in blackRegEx) {
                            if (match(blackRegEx[i], aClass)) {
                                is_black = true;
                                log(aClass + "' black by '" + blackRegEx[i] + "'");
                                break;
                            }
                        }
                        if (is_black) {
                            break;
                        }
                        log(aClass + "' match by '" + matchRegEx[index] + "'");
                        traceClass(aClass);
                    }
                }

            },
            onComplete: function () {
                log("Complete.");
            }
        });
    });
}