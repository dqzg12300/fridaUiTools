function klog(data){
    var message={};
    message["jsname"]="%customName%";
    message["data"]=data;
    send(message);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="%customName%";
    message["data"]=data;
    message[key]=value;
    send(message);
}

function native_hook(){

}


function java_hook(){
    Java.perform(function(){
        
    })
}


function spawn_hook(library_name){
    Interceptor.attach(Module.findExportByName(null, 'android_dlopen_ext'),{
        onEnter: function(args){
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
                native_hook(library_name)
                this.library_loaded = 0
            }
        }
    })
}

function main(){
	klogData("","init","%customFileName% init hook success");
	var isSpawn = "%spawn%";
    var moduleName = "%moduleName%" // 目标模块
	if (isSpawn) {
        spawn_hook(moduleName)
    } else {
        native_hook(moduleName)
    }
}

setImmediate(main);
