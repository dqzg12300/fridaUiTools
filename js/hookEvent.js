(function(){
var jclazz = null;
var jobj = null;
function klog(data){
    var message={};
    message["jsname"]="hookEvent";
    message["data"]=data;
    send(message);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="hookEvent";
    message["data"]=data;
    message[key]=value;
    send(message);
}

function getObjClassName(obj) {
    if (!jclazz) {
        var jclazz = Java.use("java.lang.Class");
    }
    if (!jobj) {
        var jobj = Java.use("java.lang.Object");
    }
    return jclazz.getName.call(jobj.getClass.call(obj));
}

function watch(obj, mtdName) {
    var listener_name = getObjClassName(obj);
    console.log(listener_name)
    var target = Java.use(listener_name);
    if (!target || !mtdName in target) {
        return;
    }
    klog("[WatchEvent] hooking " + mtdName + ": " + listener_name);
    target[mtdName].overloads.forEach(function (overload) {
        overload.implementation = function () {
            //send("[WatchEvent] " + mtdName + ": " + getObjClassName(this));
            klog("[WatchEvent] " + mtdName + ": " + getObjClassName(this))
            return this[mtdName].apply(this, arguments);
        };
    })
}

function OnClickListener() {
    Java.perform(function () {
        klogData("","init","hookEvent.js init hook success");
        //以spawn启动进程的模式来attach的话
        Java.use("android.view.View").setOnClickListener.implementation = function (listener) {
            // console.log("enter setOnClickListener")
            if (listener != null) {
                watch(listener, 'onClick');
            }
            return this.setOnClickListener(listener);
        };

        //如果frida以attach的模式进行attch的话
        // Java.choose("android.view.View$ListenerInfo", {
        //     onMatch: function (instance) {
        //         instance = instance.mOnClickListener.value;
        //         if (instance) {
        //             klog("mOnClickListener name is :" + getObjClassName(instance));
        //             watch(instance, 'onClick');
        //         }
        //     },
        //     onComplete: function () {
        //     }
        // })
    })
}
setImmediate(OnClickListener);
})();
