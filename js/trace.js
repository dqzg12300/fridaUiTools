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
        var matchRegExMethod = {MATCHREGEXMETHOD};
        var blackRegExMethod = {BLACKREGEXMETHOD};
        var target = Java.use(clsname);
        var methods = target.class.getDeclaredMethods();
        var stack="%stack%";
        var hookInit="%hookInit%";
        var methodNames=[]
        var isMatch="%isMatchMethod%";
        //过滤一下要hook的函数，
        methods.forEach(function (method) {
            if(matchRegExMethod.length>0){
                var flag=false;
                var hasmatch=false;
                for(var i=0;i<matchRegExMethod.length;i++){
                    var matchMethod=matchRegExMethod[i];
                    //如果函数中带小数点，说明这个函数匹配是针对某个类的。
                    if(matchMethod.indexOf("->")!=-1){
                        var matchsplit=matchMethod.split("->");
                        var matchClass= matchsplit[0]
                        var res=false;
                        //上面取出类名，查下这个函数是否应该在该类中过滤。
                        if(isMatch){
                            res=match(matchClass, clsname)
                        }else{
                            res=matchClass==clsname;
                        }
                        if(!res){
                            continue;
                        }
                        hasmatch=true
                    }
                    if(isMatch) {
                        if (method.getName().toUpperCase().indexOf(matchsplit[1].toUpperCase()) != -1) {
                            flag = true;
                            break;
                        }
                    }else{
                        if (method.getName().toUpperCase()== matchsplit[1].toUpperCase()) {
                            flag = true;
                            break;
                        }
                    }
                }
                //如果该类有设置函数过滤，才启动flag判断
                if(hasmatch){
                    if(!flag){
                        // console.log("matchRegExMethod skip ",method.getName());
                        return;
                    }
                }

            }
            if(blackRegExMethod.length>0){
                flag=true;
                var hasmatch=false;
                for(var i=0;i<blackRegExMethod.length;i++){
                    var breakMethod=blackRegExMethod[i];
                    if(breakMethod.indexOf("->")!=-1){
                        var matchsplit=breakMethod.split("->");
                        var matchClass= matchsplit[0]
                        var res=false;
                        //上面取出类名，查下这个函数是否应该在该类中过滤。
                        if(isMatch){
                            res=match(matchClass, clsname)
                        }else{
                            res=matchClass==clsname;
                        }
                        if(!res){
                            continue;
                        }
                        hasmatch=true
                    }
                    if (method.getName().toUpperCase().indexOf(matchsplit[1].toUpperCase()) != -1) {
                        flag = false;
                        break;
                    }
                }

                if(hasmatch) {
                    if(!flag){
                        // console.log("blackRegExMethod skip ",method.getName());
                        return;
                    }
                }
            }
            // console.log(method.getName());
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
            if (clsname=="android.os.Bundle" && methodName.indexOf("writeToParcel")==0){
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
        var isMatch="%isMatch%";
        Java.enumerateLoadedClasses({
            onMatch: function (aClass) {
                for (var index in matchRegEx) {
                    // console.log(matchRegEx[index]);
                    var res=false;
                    if(isMatch){
                        res=match(matchRegEx[index], aClass)
                    }else{
                        res=aClass==matchRegEx[index];
                    }
                    // if (match(matchRegEx[index], aClass)) {
                    if (res) {
                        var is_black = false;
                        for (var i in blackRegEx) {
                            console.log(blackRegEx[i]);
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
