(function(){

function initMessage(){
  var message={};
  message["jsname"]="ZenTracer";
  return message;
}

function log(text) {
    var packet = {
        'cmd': 'log',
        'data': text
    };
    var msg= initMessage()
    msg["data"]="ZenTracer:::" + JSON.stringify(packet)
    send(msg)
}

function klog(data){
    var message={};
    message["jsname"]="ZenTracer";
    message["data"]=data;
    send(message);
}

function enter(tid, tname, cls, method, args) {
    var packet = {
        'cmd': 'enter',
        'data': [tid, tname, cls, method, args]
    };
    var msg= initMessage()
    msg["data"]="ZenTracer:::" + JSON.stringify(packet)
    send(msg)
}

function exit(tid, retval) {
    var packet = {
        'cmd': 'exit',
        'data': [tid, retval]
    };
    var msg= initMessage()
    msg["data"]="ZenTracer:::" + JSON.stringify(packet)
    send(msg)
}

function getTid() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getId();
}

function getTName() {
    var Thread = Java.use("java.lang.Thread")
    return Thread.currentThread().getName();
}
function getStack(){
		return Java.use("android.util.Log").getStackTraceString(Java.use("java.lang.Exception").$new());
	}

function traceClass(clsname) {
    try {
        var target = Java.use(clsname);
        var methods = target.class.getDeclaredMethods();
        var stack="%stack%";
        var hookInit="%hookInit%";
        var methodNames=[]
        methods.forEach(function (method) {
            methodNames.push(method.getName());
        });
        if(hookInit){
            // var methodConstructors=target.class.getDeclaredConstructors();
            // console.log("hook:"+methodConstructors);
            methodNames.push("$init");
        }
        methodNames.forEach(function (methodName) {
            // var methodName = method.getName();
            //测试的时候发现这个hook了，应用出现崩溃的情况。就跳过了
            if (clsname=="android.os.Bundle" && methodName.indexOf("writeToParcel")!=0){
                return;
            }
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
                    if(stack){
                        var stackLog=getStack();
                        klog(stackLog);
                    }
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
                    // if (match(matchRegEx[index], aClass)) {
                    if (aClass==matchRegEx[index]) {
                        var is_black = false;
                        for (var i in blackRegEx) {
                            if (match(blackRegEx[i]["class"], aClass)) {
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
})();
