//还不太明白为什么Memory.protect后就异常了。查清楚了再看看怎么搞。

(function(){

function klog(data){
    var message={};
    message["jsname"]="patchCode";
    message["data"]=data;
    send(message);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="patchCode";
    message["data"]=data;
    message[key]=value;
    send(message);
}

function dis(base,address, number) {
    for (var i = 0; i < number; i++) {
        var ins = Instruction.parse(address);
        klog("address:" + ptr(address-base) + "--dis:" + ins.toString());
        address = ins.next;
    }
}

function patchFunc(moduleName,address,code){
    klog(moduleName+","+address+","+code);
    var module = Process.getModuleByName(moduleName);
    var base=module.base;
    klog("+++++++++++patch "+address+"++++++++++++ pre")
    dis(base,base.add(address), 10);
    Memory.protect(base.add(address), 32, 'rwx');
    base.add(address).writeByteArray(code);
    klog("+++++++++++patch "+address+"++++++++++++ over")
    dis(base,base.add(address), 10);
}

function spawn_hook(library_name,patchJson){
    Interceptor.attach(Module.findExportByName(null, 'android_dlopen_ext'),{
        onEnter: function(args){
            // first arg is the path to the library loaded
            var library_path = Memory.readCString(args[0])
            if( library_path.includes(library_name)){
                klog("[...] Loading library : " + library_path);
                this.library_loaded = 1
            }
        },
        onLeave: function(args){
            // if it's the library we want to hook, hooking it
            if(this.library_loaded ==  1){
                klog("[+] Loaded");
                patchTask(library_name, patchJson)
                this.library_loaded = 0
            }
        }
    })
}

function patchTask(moduleName,patchJson){
    var patchList=JSON.parse(patchJson);
    for(var item in patchList){
        var patchdata=patchList[item];
        var addr=ptr(parseInt(item,16))
        var code=[];
        var codestr=patchdata["code"];
        var moduleName=patchdata["moduleName"];
        var codesplit=codestr.split(" ");
        for(var idx in codesplit){
            code.push(parseInt("0x"+codesplit[idx],16));
        }
        patchFunc(moduleName,addr,code);
    }
}

function main(){
    var isSpawn = "%spawn%";
    var moduleName = "%moduleName%" // 目标模块
    var patchJson='{PATCHLIST}';

    klogData("","init","patchCode.js init hook success");
    if (isSpawn) {
        spawn_hook(moduleName, patchJson)
    } else {
        patchTask(moduleName,patchJson);
    }
}

setImmediate(main)
})();
