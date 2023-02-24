
(function(){
function klog(data,...args){
    for (let item of args){
        data+="\t"+item;
    }
    var message={};
    message["jsname"]="hook_RegisterNatives";
    message["data"]=data;
    send(message);
}

function hook_RegisterNatives() {
    klog("init","hook_RegisterNatives.js init hook success");
    var symbols = Module.enumerateSymbolsSync("libart.so");
    var addrRegisterNatives = null;
    for (var i = 0; i < symbols.length; i++) {
        var symbol = symbols[i];

        //_ZN3art3JNI15RegisterNativesEP7_JNIEnvP7_jclassPK15JNINativeMethodi
        if (symbol.name.indexOf("art") >= 0 &&
                symbol.name.indexOf("JNI") >= 0 &&
                symbol.name.indexOf("RegisterNatives") >= 0 &&
                symbol.name.indexOf("CheckJNI") < 0) {
            addrRegisterNatives = symbol.address;
            klog("RegisterNatives is at "+symbol.address+" "+symbol.name);
            break;
        }
    }

    if (addrRegisterNatives != null) {
        Interceptor.attach(addrRegisterNatives, {
            onEnter: function (args) {
                klog("[RegisterNatives] method_count:"+ args[3]);
                var env = args[0];
                var java_class = args[1];
                var class_name = Java.vm.tryGetEnv().getClassName(java_class);
                //console.log(class_name);

                var methods_ptr = ptr(args[2]);

                var method_count = parseInt(args[3]);
                for (var i = 0; i < method_count; i++) {
                    var name_ptr = Memory.readPointer(methods_ptr.add(i * Process.pointerSize * 3));
                    var sig_ptr = Memory.readPointer(methods_ptr.add(i * Process.pointerSize * 3 + Process.pointerSize));
                    var fnPtr_ptr = Memory.readPointer(methods_ptr.add(i * Process.pointerSize * 3 + Process.pointerSize * 2));

                    var name = Memory.readCString(name_ptr);
                    var sig = Memory.readCString(sig_ptr);
                    var find_module = Process.findModuleByAddress(fnPtr_ptr);
                    klog("[RegisterNatives] java_class:"+class_name+" name:"+name+ " sig:"+ sig+ " fnPtr:"+fnPtr_ptr+ " module_name:"+find_module.name+ " module_base:"+ find_module.base+ " offset:"+ ptr(fnPtr_ptr).sub(find_module.base));

                }
            }
        });
    }
}

hook_RegisterNatives()

})();
