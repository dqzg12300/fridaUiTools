
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

function safeGetClassName(java_class) {
    var fallback = ptr(java_class).toString();
    if (typeof Java === 'undefined' || !Java.available || !Java.vm) {
        return fallback;
    }
    try {
        return Java.vm.tryGetEnv().getClassName(java_class);
    } catch (e) {
        return fallback;
    }
}

function hook_RegisterNatives(addrRegisterNatives) {
    if (addrRegisterNatives == null) {
        klog("RegisterNatives symbol not found");
        return;
    }

    Interceptor.attach(addrRegisterNatives, {
        onEnter: function (args) {
            klog("[RegisterNatives] method_count:", args[3]);
            let java_class = args[1];
            let class_name = safeGetClassName(java_class);
            let methods_ptr = ptr(args[2]);
            let method_count = parseInt(args[3]);

            for (let i = 0; i < method_count; i++) {
                let name_ptr = ptr(methods_ptr.add(i * Process.pointerSize * 3)).readPointer();
                let sig_ptr = ptr(methods_ptr.add(i * Process.pointerSize * 3 + Process.pointerSize)).readPointer();
                let fnPtr_ptr = ptr(methods_ptr.add(i * Process.pointerSize * 3 + Process.pointerSize * 2)).readPointer();

                let name = ptr(name_ptr).readCString();
                let sig = ptr(sig_ptr).readCString();
                let symbol = DebugSymbol.fromAddress(fnPtr_ptr);
                klog("[RegisterNatives] java_class:", class_name, "name:", name, "sig:", sig, "fnPtr:", fnPtr_ptr, "fnOffset:", symbol, "callee:", DebugSymbol.fromAddress(this.returnAddress));
            }
        }
    });
}

function find_RegisterNatives() {
    klog("init","hook_RegisterNatives.js init hook success");
    let addrRegisterNatives = null;

    if (typeof Frida !== 'undefined' && Frida.version != undefined) {
        const major = parseInt(Frida.version.split('.')[0], 10);
        if (major >= 17) {
            const libart = Process.findModuleByName("libart.so");
            if (!libart) {
                klog("libart.so not found");
                return;
            }
            libart.enumerateSymbols().some(symbol => {
                if (symbol.name.indexOf("art") >= 0 &&
                    symbol.name.indexOf("JNI") >= 0 &&
                    symbol.name.indexOf("RegisterNatives") >= 0 &&
                    symbol.name.indexOf("CheckJNI") < 0) {
                    addrRegisterNatives = symbol.address;
                    klog("RegisterNatives is at", symbol.address, symbol.name);
                    hook_RegisterNatives(addrRegisterNatives);
                    return true;
                }
                return false;
            });
            return;
        }
    }

    let symbols = Module.enumerateSymbolsSync("libart.so");
    for (let i = 0; i < symbols.length; i++) {
        let symbol = symbols[i];
        if (symbol.name.indexOf("art") >= 0 &&
            symbol.name.indexOf("JNI") >= 0 &&
            symbol.name.indexOf("RegisterNatives") >= 0 &&
            symbol.name.indexOf("CheckJNI") < 0) {
            addrRegisterNatives = symbol.address;
            klog("RegisterNatives is at", symbol.address, symbol.name);
            hook_RegisterNatives(addrRegisterNatives);
            break;
        }
    }
}

setImmediate(find_RegisterNatives);

})();
