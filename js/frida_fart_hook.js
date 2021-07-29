//typed by hanbingle,just for fun!!
//email:edunwu@gmail.com
//只是对Android 8 版本进行了测试，其他版本请自行移植
/*使用说明
首先拷贝fart.so和fart64.so到/data/app目录下，并使用chmod 777 设置好权限,然后就可以使用了。
该frida版fart是使用hook的方式实现的函数粒度的脱壳，仅仅是对类中的所有函数进行了加载，但依然可以解决绝大多数的抽取保护
需要以spawn方式启动app，等待app进入Activity界面后，执行fart()函数即可。如app包名为com.example.test,则
frida -U -f com.example.test -l frida_fart_hook.js --no-pause，然后等待app进入主界面,执行fart()
高级用法：如果发现某个类中的函数的CodeItem没有dump下来，可以调用dump(classname),传入要处理的类名，完成对该类下的所有函数体的dump,dump下来的函数体会追加到bin文件当中。
 */
var ishook_libart = false;
var addrLoadMethod = null;
var addrGetCodeItemLength = null;
var funcGetCodeItemLength = null;
var addrBase64_encode = null;
var funcBase64_encode = null;
var addrFreeptr = null;
var funcFreeptr = null;
var savepath = "%savepath%";
//savepath = "/data/data/com.example.packagename"
var dex_maps = {};
var artmethod_maps = {};


function klog(data){
    var message={};
    message["jsname"]="fart";
    message["data"]=data;
    send(message);
}

function klogData(data,key,value){
    var message={};
    message["jsname"]="fart";
    message["data"]=data;
    message[key]=value;
    send(message);
}
//替换了console.log
console.log = (function (oriLogFunc) {
  return function () {
    //判断配置文件是否开启日志调试
    let arr = []
    arr.push(...arguments)
    klog(JSON.stringify(arr))
  }
})(console.log);

function DexFile(start, size) {
    this.start = start;
    this.size = size;
}

function ArtMethod(dexfile, artmethodptr) {
    this.dexfile = dexfile;
    this.artmethodptr = artmethodptr;
}

function hookart() {
    klogData("","init","frida_fart.js init hook success");
    if (ishook_libart === true) {
        return;
    }
    var module_libext = null;
    if (Process.arch === "arm64") {
        module_libext = Module.load("/data/app/fart64.so");
    } else if (Process.arch === "arm") {
        module_libext = Module.load("/data/app/fart.so");
    }
    if (module_libext != null) {
        addrGetCodeItemLength = module_libext.findExportByName("GetCodeItemLength");
        funcGetCodeItemLength = new NativeFunction(addrGetCodeItemLength, "int", ["pointer"]);
        addrBase64_encode = module_libext.findExportByName("Base64_encode");
        funcBase64_encode = new NativeFunction(addrBase64_encode, "pointer", ["pointer", "int", "pointer"]);
        addrFreeptr = module_libext.findExportByName("Freeptr");
        funcFreeptr = new NativeFunction(addrFreeptr, "void", ["pointer"]);
    }
    var versionData="ClassDataItemIterator";
    if(Java.androidVersion=="10"){
        versionData="ClassAccessor";
    }
    var symbols = Module.enumerateSymbolsSync("libart.so");
    for (var i = 0; i < symbols.length; i++) {
        var symbol = symbols[i];
        //_ZN3art11ClassLinker10LoadMethodERKNS_7DexFileERKNS_21ClassDataItemIteratorENS_6HandleINS_6mirror5ClassEEEPNS_9ArtMethodE
        if (symbol.name.indexOf("ClassLinker") >= 0
            && symbol.name.indexOf("LoadMethod") >= 0
            && symbol.name.indexOf("DexFile") >= 0
            && symbol.name.indexOf(versionData) >= 0
            && symbol.name.indexOf("ArtMethod") >= 0) {
            addrLoadMethod = symbol.address;
            break;
        }
    }

    if (addrLoadMethod != null) {
        Interceptor.attach(addrLoadMethod, {
            onEnter: function (args) {
                this.dexfileptr = args[1];
                this.artmethodptr = args[4];
            },
            onLeave: function (retval) {
                var dexfilebegin = null;
                var dexfilesize = null;
                if (this.dexfileptr != null) {
                    dexfilebegin = Memory.readPointer(ptr(this.dexfileptr).add(Process.pointerSize * 1));
                    dexfilesize = Memory.readU32(ptr(this.dexfileptr).add(Process.pointerSize * 2));
                    var dexfile_path = savepath + "/" + dexfilesize + "_loadMethod.dex";
                    var dexfile_handle = null;
                    try {
                        dexfile_handle = new File(dexfile_path, "r");
                        if (dexfile_handle && dexfile_handle != null) {
                            dexfile_handle.close()
                        }

                    } catch (e) {
                        console.log("filepath:",dexfile_path);
                        dexfile_handle = new File(dexfile_path, "a+");
                        if (dexfile_handle && dexfile_handle != null) {
                            var dex_buffer = ptr(dexfilebegin).readByteArray(dexfilesize);
                            dexfile_handle.write(dex_buffer);
                            dexfile_handle.flush();
                            dexfile_handle.close();
                            console.log("[dumpdex]:", dexfile_path);
                        }
                    }
                }
                var dexfileobj = new DexFile(dexfilebegin, dexfilesize);
                if (dex_maps[dexfilebegin] == undefined) {
                    dex_maps[dexfilebegin] = dexfilesize;
                    console.log("got a dex:", dexfilebegin, dexfilesize);
                }
                if (this.artmethodptr != null) {
                    var artmethodobj = new ArtMethod(dexfileobj, this.artmethodptr);
                    if (artmethod_maps[this.artmethodptr] == undefined) {
                        artmethod_maps[this.artmethodptr] = artmethodobj;
                    }
                }
            }
        });
    }
    ishook_libart = true;
}

function dumpcodeitem(artmethodobj) {
    if (artmethodobj != null) {
        var dexfileobj = artmethodobj.dexfile;
        var dexfilebegin = dexfileobj.start;
        var dexfilesize = dexfileobj.size;
        var dexfile_path = savepath + "/" + dexfilesize + "_" + Process.getCurrentThreadId() + ".dex";
        var dexfile_handle = null;
        try {
            dexfile_handle = new File(dexfile_path, "r");
            if (dexfile_handle && dexfile_handle != null) {
                dexfile_handle.close()
            }

        } catch (e) {
            dexfile_handle = new File(dexfile_path, "a+");
            if (dexfile_handle && dexfile_handle != null) {
                var dex_buffer = ptr(dexfilebegin).readByteArray(dexfilesize);
                dexfile_handle.write(dex_buffer);
                dexfile_handle.flush();
                dexfile_handle.close();
                console.log("[dumpdex]:", dexfile_path);
            }
        }
        var artmethodptr = artmethodobj.artmethodptr;
        var dex_code_item_offset_ = Memory.readU32(ptr(artmethodptr).add(8));
        var dex_method_index_ = Memory.readU32(ptr(artmethodptr).add(12));
        if (dex_code_item_offset_ != null && dex_code_item_offset_ > 0) {
            var dir = savepath;
            var file_path = dir + "/" + dexfilesize + "_" + Process.getCurrentThreadId() + ".bin";
            var file_handle = new File(file_path, "a+");
            if (file_handle && file_handle != null) {
                var codeitemstartaddr = ptr(dexfilebegin).add(dex_code_item_offset_);
                var codeitemlength = funcGetCodeItemLength(ptr(codeitemstartaddr));
                if (codeitemlength != null & codeitemlength > 0) {
                    Memory.protect(ptr(codeitemstartaddr), codeitemlength, 'rwx');
                    var base64lengthptr = Memory.alloc(8);
                    var arr = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00];
                    Memory.writeByteArray(base64lengthptr, arr);
                    var base64ptr = funcBase64_encode(ptr(codeitemstartaddr), codeitemlength, ptr(base64lengthptr));
                    var b64content = ptr(base64ptr).readCString(base64lengthptr.readInt());
                    funcFreeptr(ptr(base64ptr));
                    var content = "{name:ooxx,method_idx:" + dex_method_index_ + ",offset:" + dex_code_item_offset_ + ",code_item_len:" + codeitemlength + ",ins:" + b64content + "};";
                    file_handle.write(content);
                    file_handle.flush();
                    file_handle.close();
                }

            } else {
                console.log("openfile failed,filepath:", file_path);
            }
        }


    }

}

function dumpall() {
    console.log("start dump all CodeItem.......");
    for (var artmethodptr in artmethod_maps) {
        var artmethodobj = artmethod_maps[artmethodptr];
        try {
            dumpcodeitem(artmethodobj);
        } catch (e) {
            console.log("error", e);
        }

    }
    console.log("end dump all CodeItem.......");
}

function dealwithClassLoader(classloaderobj) {
    if (Java.available) {
        Java.perform(function () {
            try {
                var dexfileclass = Java.use("dalvik.system.DexFile");
                var BaseDexClassLoaderclass = Java.use("dalvik.system.BaseDexClassLoader");
                var DexPathListclass = Java.use("dalvik.system.DexPathList");
                var Elementclass = Java.use("dalvik.system.DexPathList$Element");
                var basedexclassloaderobj = Java.cast(classloaderobj, BaseDexClassLoaderclass);
                var tmpobj = basedexclassloaderobj.pathList.value;
                var pathlistobj = Java.cast(tmpobj, DexPathListclass);
                var dexElementsobj = pathlistobj.dexElements.value;
                if (dexElementsobj != null) {
                    for (var i in dexElementsobj) {
                        var obj = dexElementsobj[i];
                        var elementobj = Java.cast(obj, Elementclass);
                        tmpobj = elementobj.dexFile.value;
                        var dexfileobj = Java.cast(tmpobj, dexfileclass);
                        const enumeratorClassNames = dexfileobj.entries();
                        while (enumeratorClassNames.hasMoreElements()) {
                            var className = enumeratorClassNames.nextElement().toString();
                            console.log("start loadclass->", className);
                            var loadclass = classloaderobj.loadClass(className);
                            console.log("after loadclass->", loadclass);
                        }

                    }
                }


            } catch (e) {
                console.log(e)
            }

        });
    }


}

function dumpclass(classes) {
    if (Java.available) {
        Java.perform(function () {
            Java.enumerateClassLoaders({
                onMatch: function (loader) {
                    try {
                        var classNames=classes.split("\n");
                        for (var i=0;i<classNames.length;i++){
                            var className=classNames[i];
                            console.log("start loadclass->", className);
                            var loadclass = loader.loadClass(className);
                            console.log("after loadclass->", loadclass);
                        }
                    } catch (e) {
                        //console.log("error", e);
                    }

                },
                onComplete: function () {
                    //console.log("find  Classloader instance over");
                }
            });
            dumpall(classes);
        });
    }
}

function fart() {
    if (Java.available) {
        Java.perform(function () {
            dumpall();
            //上面是利用被动调用进行函数粒度的dump，对app正常运行过程中自己加载的所有类函数进行dump
            Java.enumerateClassLoaders({
                onMatch: function (loader) {
                    try {
                        klog("start dealwithclassloader:", loader, '\n');
                        dealwithClassLoader(loader);
                    } catch (e) {
                        console.log("error", e);
                    }

                },
                onComplete: function () {
                    //console.log("find  Classloader instance over");
                }
            });
            dumpall();
            //上面为对当前ClassLoader中的所有类进行主动加载，从而完成ArtMethod中的CodeItem的dump
        });
    }
}

function romClassesInvoke(classes){
    Java.perform(function(){
        klog("romClassesInvoke start load");
        var fartExt=Java.use("cn.mik.Fartext");
        if(!fartExt.fartWithClassList){
            klog("fartExt中未找到fartWithClassList函数，可能是未使用Fartext的rom")
            return ;
        }
        fartExt.fartWithClassList(classes);
    })
}

function romFartAllClassLoader(){
    Java.perform(function(){
       var fartExt=Java.use("cn.mik.Fartext");
       if(!fartExt.fartWithClassLoader){
           klog("fartExt中未找到fartWithClassLoader函数，可能是未使用Fartext的rom");
           return;
       }
       Java.enumerateClassLoadersSync().forEach(function(loader){
           klog("romFartAllClassLoader to loader:"+loader);
           if(loader.toString().indexOf("BootClassLoader")==-1){
               klog("fart start loader:"+loader);
               fartExt.fartWithClassLoader(loader);
           }
       })
    });
}

rpc.exports = {
    fart:function(){
        fart();
    },
    fartclass:function(classes){
        dumpclass(classes);
    },
    romfart:function(){
        //调用fartext的api
        romFartAllClassLoader();
    },
    romfartclass:function(classes){
        //调用fartext的api
        romClassesInvoke(classes)
    }
}

setImmediate(hookart);