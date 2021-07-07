
(function(){

function klog(data){
    var message={};
    message["jsname"]="traceNative";
    message["data"]=data;
    send(message);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="traceNative";
    message["data"]=data;
    message[key]=value;
    send(message);
}

//打印参数
function hexdumpMem(addr){
    if(Process.findRangeByAddress(addr)){
        return hexdump(ptr(addr),{length:0x40})+"\r\n"
    }else{
        return ptr(addr)+"\r\n";
    }
}
//比较通用的hook地址并且打印5个参数。如果参数是地址就打印下内存信息
function nativeHookFunction(addr,function_name){
    Interceptor.attach(addr,{
        onEnter:function(args){
            this.logs=[];
            this.logs.push("call",function_name);
            this.arg0=args[0];
            this.arg1=args[1];
            this.arg2=args[2];
            this.arg3=args[3];
            this.arg4=args[4];
            this.arg5=args[5];
            var traceback=Thread.backtrace(this.context, Backtracer.ACCURATE).map(DebugSymbol.fromAddress).join('\n') + '\n';
            this.logs.push(traceback);
            this.logs.push("arg0:",hexdumpMem(this.arg0));
            this.logs.push("arg1:",hexdumpMem(this.arg1));
            this.logs.push("arg2:",hexdumpMem(this.arg2));
            this.logs.push("arg3:",hexdumpMem(this.arg3));
            this.logs.push("arg4:",hexdumpMem(this.arg4));
            this.logs.push("arg5:",hexdumpMem(this.arg5));
        },onLeave:function(retval){
            this.logs.push("arg0 leave:",hexdumpMem(this.arg0));
            this.logs.push("arg1 leave:",hexdumpMem(this.arg1));
            this.logs.push("arg2 leave:",hexdumpMem(this.arg2));
            this.logs.push("arg3 leave:",hexdumpMem(this.arg3));
            this.logs.push("arg4 leave:",hexdumpMem(this.arg4));
            this.logs.push("arg5 leave:",hexdumpMem(this.arg5));
            this.logs.push("retval leave:",hexdumpMem(retval));
            // console.log(this.logs);
            klog(this.logs)
        }
    })
}

function native_hook(library_name,function_names){
     var base_addr=Module.getBaseAddress(library_name);
     for(var i=0;i<function_names.length;i++){
         if(function_names[i].toUpperCase().startsWith("SUB_")){
             var address=function_names[i].toUpperCase().replace("SUB_","");
             var addrdata=parseInt(address,16);
             //直接默认非arm64的就函数+1了。不知道怎么判断是不是thumb指令
             if(Process.arch!="arm64"){
                 addrdata+=1;
             }
             var method_addr=base_addr.add(addrdata);
             klog("[...] Hooking : " + library_name + " -> " + function_names[i] + " at " + method_addr);
             nativeHookFunction(method_addr,function_names[i])
         }else{
             var method_addr= Module.getExportByName(library_name,function_names[i]);
             if(method_addr){
                klog("[...] Hooking : " + library_name + " -> " + function_names[i] + " at " + method_addr);
                nativeHookFunction(method_addr,function_names[i])
             }else{
                klog("[...] Hooking : " + library_name + " -> not fount " + function_names[i]);
             }
         }

     }
}

function spawn_hook(library_name,function_names){
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
                native_hook(library_name, function_names)
                this.library_loaded = 0
            }
        }
    })
}

function main(){
    var isSpawn = "%spawn%";
    var moduleName = "%moduleName%" // 目标模块
    var methodName = {methodName} // 目标函数,这里是个列表
    klogData("","init","traceNative.js init hook success");
    if (isSpawn) {
        spawn_hook(moduleName, methodName)
    } else {
        native_hook(moduleName, methodName)
    }
}
setImmediate(main);
})();
