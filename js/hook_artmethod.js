
(function(){

function klog(data){
    var message={};
    message["jsname"]="hook_artmethod";
    message["data"]=data;
    send(message);
}

function klogData(data,key,value){
    var message={};
    message["jsname"]="hook_artmethod";
    message["data"]=data;
    message[key]=value;
    send(message);
}

const STD_STRING_SIZE = 3 * Process.pointerSize;
class StdString {
    constructor() {
        this.handle = Memory.alloc(STD_STRING_SIZE);
    }

    dispose() {
        const [data, isTiny] = this._getData();
        if (!isTiny) {
            Java.api.$delete(data);
        }
    }

    disposeToString() {
        const result = this.toString();
        this.dispose();
        return result;
    }

    toString() {
        const [data] = this._getData();
        return data.readUtf8String();
    }

    _getData() {
        const str = this.handle;
        const isTiny = (str.readU8() & 1) === 0;
        const data = isTiny ? str.add(1) : str.add(2 * Process.pointerSize).readPointer();
        return [data, isTiny];
    }
}

function prettyMethod(method_id, withSignature) {
    const result = new StdString();
    Java.api['art::ArtMethod::PrettyMethod'](result, method_id, withSignature ? 1 : 0);
    return result.disposeToString();
}

function hook_dlopen(module_name, fun) {
    var android_dlopen_ext = Module.findExportByName(null, "android_dlopen_ext");

    if (android_dlopen_ext) {
        Interceptor.attach(android_dlopen_ext, {
            onEnter: function (args) {
                var pathptr = args[0];
                if (pathptr) {
                    this.path = (pathptr).readCString();
                    if (this.path.indexOf(module_name) >= 0) {
                        this.canhook = true;
                        klog("android_dlopen_ext:"+this.path);
                    }
                }
            },
            onLeave: function (retval) {
                if (this.canhook) {
                    fun();
                }
            }
        });
    }
    var dlopen = Module.findExportByName(null, "dlopen");
    if (dlopen) {
        Interceptor.attach(dlopen, {
            onEnter: function (args) {
                var pathptr = args[0];
                if (pathptr) {
                    this.path = (pathptr).readCString();
                    if (this.path.indexOf(module_name) >= 0) {
                        this.canhook = true;
                        klog("dlopen:"+this.path);
                    }
                }
            },
            onLeave: function (retval) {
                if (this.canhook) {
                    fun();
                }
            }
        });
    }
    klog("android_dlopen_ext:"+android_dlopen_ext+",dlopen:"+dlopen);
}


function hook_native() {
    var module_libart = Process.findModuleByName("libart.so");
    var symbols = module_libart.enumerateSymbols();
    var ArtMethod_Invoke = null;
    for (var i = 0; i < symbols.length; i++) {
        var symbol = symbols[i];
        var address = symbol.address;
        var name = symbol.name;
        var indexArtMethod = name.indexOf("ArtMethod");
        var indexInvoke = name.indexOf("Invoke");
        var indexThread = name.indexOf("Thread");
        if (indexArtMethod >= 0
            && indexInvoke >= 0
            && indexThread >= 0
            && indexArtMethod < indexInvoke
            && indexInvoke < indexThread) {
            klog(name);
            ArtMethod_Invoke = address;
        }
    }
    if (ArtMethod_Invoke) {
        Interceptor.attach(ArtMethod_Invoke, {
            onEnter: function (args) {
                var method_name = prettyMethod(args[0], 0);
                if (!(method_name.indexOf("java.") == 0 || method_name.indexOf("android.") == 0)) {
                    klog("ArtMethod Invoke:" + method_name + '  called from:\n' +
                        Thread.backtrace(this.context, Backtracer.ACCURATE)
                            .map(DebugSymbol.fromAddress).join('\n') + '\n');
                }
            }
        });
    }
}

function main() {
    klogData("","init","hook_artmethod.js init hook success");
    hook_dlopen("libart.so", hook_native);
    hook_native();
}

setImmediate(main);

})();
