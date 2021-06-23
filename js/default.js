//默认使用,后面再搞点默认hook功能
(function(){

function klog(data){
    var message={};
    message["jsname"]="default";
    message["data"]=data;
    send(message);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="default";
    message["data"]=data;
    message[key]=value;
    send(message);
}

//查找java的函数
function showMethods(postdata){
    var inputClass=postdata["className"];
    var inputMethod=postdata["methodName"];
    var hasMethod=postdata["hasMethod"];

    console.log("enter js showMethods")
    Java.perform(function(){
        var cnt=0;
        Java.enumerateLoadedClassesSync().forEach(function(className){
            if (inputClass && inputClass.length>0){
                if(className.toUpperCase().indexOf(inputClass.toUpperCase())<0){
                    return;
                }
            }
            if(!hasMethod){
                cnt+=1;
                klog("className:"+className)
                return;
            }
            // console.log("loaded: "+className);
            try{
                var classModel= Java.use(className);
                var methods=classModel.class.getDeclaredMethods();
                for(var i=0;i<methods.length;i++){
                    var methodName=methods[i].getName()
                    if (inputMethod && inputMethod.length>0){
                        if(methodName.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                            return;
                        }
                    }
                    cnt+=1;
                    klog("className:"+className+"----method:"+methodName)
                }
            }catch(ex){

            }
        })
        klog("find count:"+cnt);
    });
}
//查找so的符号
function showExport(postdata){
    var inputModule=postdata["moduleName"];
    var inputMethod=postdata["methodName"];
    var showType=postdata["showType"];
    var hasMethod=postdata["hasMethod"];
    var cnt=0;
    console.log("enter js showExport")
    Process.enumerateModules().forEach(function(module){
        if (inputClass && inputClass.length>0){
            if(module.name.toUpperCase().indexOf(inputModule.toUpperCase())<0){
                return;
            }
        }
        if(!hasMethod){
                cnt+=1;
                klog("module:"+module.name)
                return;
            }
        if(showType=="Export"){
            module.enumerateExports().forEach(function(edata){
                if (inputMethod && inputMethod.length>0){
                    if(edata.name.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                        return;
                    }
                }
                cnt+=1;
                klog("module:"+module.name+"----exportName:"+edata.name+"----address:"+edata.address+"----type:"+edata.type)
            });
        }else{
            module.enumerateSymbols().forEach(function(edata){
                if (inputMethod.length>0){
                    if(edata.name.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                        return;
                    }
                }
                cnt+=1;
                klog("module:"+module.name+"----symbolName:"+edata.name+"----address:"+edata.address+"----type:"+edata.type)
            });
        }
    });
}

function dumpPtr(postdata){
    var inputModule=postdata["moduleName"];
    var inputAddress=postdata["address"];
    var dumpType=postdata["dumpType"];
    var size=postdata["size"];
    console.log("enter js dumpPtr")
    if(inputModule && inputModule.length>0){
        var moduleBase=Module.findBaseAddress(inputModule);
        if(!moduleBase){
            klog("not found "+inputModule)
            return;
        }
        var dumpAddr= moduleBase.add(inputAddress);
        if(dumpType=="hexdump"){
            klog("base:"+moduleBase+",dump address:"+dumpAddr+"\n"+hexdump(ptr(dumpAddr),{length:size}))
        }else if(dumpType=="string"){
            klog("base:"+moduleBase+",dump address:"+dumpAddr+"\n"+ ptr(dumpAddr).readCString())
        }
    }else{
        if(dumpType=="hexdump"){
            klog("dump address:"+ptr(inputAddress)+"\n"+hexdump(ptr(inputAddress),{length:size}))
        }else if(dumpType=="string"){
            klog("dump address:"+ptr(inputAddress)+"\n"+ ptr(inputAddress).readCString());
        }
    }
}

function dumpSo(postdata){
    Java.perform(function () {
        var currentApplication = Java.use("android.app.ActivityThread").currentApplication();
        var dir = currentApplication.getApplicationContext().getFilesDir().getPath();
        var libso = Process.getModuleByName(postdata["moduleName"]);
        klog("[name]:"+ libso.name);
        klog("[base]:"+ libso.base);
        klog("[size]:"+ ptr(libso.size));
        klog("[path]:"+ libso.path);
        var file_path = dir + "/" + libso.name + "_" + libso.base + "_" + ptr(libso.size) + ".so";
        var file_handle = new File(file_path, "wb");
        if (file_handle && file_handle != null) {
            Memory.protect(ptr(libso.base), libso.size, 'rwx');
            var libso_buffer = ptr(libso.base).readByteArray(libso.size);
            file_handle.write(libso_buffer);
            file_handle.flush();
            file_handle.close();
            klog("[dump]:"+ file_path);
        }
    });
}

function dumpFart(postdata){
    var tp=postdata["type"];
    var className=postdata["className"];
    if(tp==1){
        console.log(dump_class);
    }else if(tp==2){
        console.log(fart);
    }
}

function searchInfo(postdata){
    Java.perform(function(){
        var baseName=postdata["baseName"];
        var searchType=postdata["type"];
        var appinfo={};
        appinfo["type"]=searchType;
        var count=0;
        if(searchType=="export"){
            var module=Process.getModuleByName(baseName);
            var exports=module.enumerateExports();
            appinfo["export"]=exports;
            count=exports.length;
        }else if(searchType=="symbol"){
            var module=Process.getModuleByName(baseName);
            var symbols=module.enumerateSymbols();
            appinfo["symbol"]=symbols;
            count=symbols.length;
        }else if(searchType=="method"){
            var classModel=Java.use(baseName);
            var methods=classModel.class.getDeclaredMethods();
            appinfo["method"]=[]
            methods.forEach(function (method){
                var methodName = method.getName();
                appinfo["method"].push(methodName);
            });
            count=methods.length;
        }
        klogData("appinfo_search count:"+count,"appinfo_search",JSON.stringify(appinfo))
    });
}

function recvMessage(){
    while(true){
        var op=recv('input',function(data){
            console.log("recv enter");
            var payload=data.payload;
            var func= payload["func"];
            if(func=="showMethods"){
                showMethods(payload);
            }else if (func=="showExport"){
                showExport(payload);
            }else if (func=="dumpPtr"){
                dumpPtr(payload);
            }else if (func=="searchInfo"){
                searchInfo(payload);
            }else if(func=="dumpSoPtr"){
                dumpSo(payload);
            }else if(func=="fart"){
                dumpFart(payload);
            }
        });
        op.wait();
    }
}

//动态取一些附加的app信息传给py
function loadAppInfo(){
    Java.perform(function(){
        var appinfo={};
        appinfo["modules"]=Process.enumerateModules();
        appinfo["classes"]=Java.enumerateLoadedClassesSync()
        appinfo["spawn"]="%spawn%"
        klogData("加载appinfo","appinfo",JSON.stringify(appinfo))
    })
}

function main(){
    klogData("","init","default.js init hook success")
    loadAppInfo();
    recvMessage();
}
setImmediate(main);

})();
