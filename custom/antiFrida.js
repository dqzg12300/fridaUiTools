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

function fridaCheckPass() {
    var pfn_strstr = Module.findExportByName("libc.so", "strstr");
    console.log("hook strstr 111");
    var pfn_pthread_exit = Module.findExportByName(null, "pthread_exit");
    var pthread_exit_func=new NativeFunction(pfn_pthread_exit,"void",["int"]);
    Interceptor.attach(pfn_strstr, {
        onEnter: function (args) {
            this.str1 = Memory.readCString(args[0]);
            this.str2 = Memory.readCString(args[1]);
            if (
                this.str2.indexOf("frida") !== -1 ||
                this.str2.indexOf("gdbus") !== -1 ||
                this.str2.indexOf("gum-js-loop") !== -1 ||
                this.str2.indexOf("gmain") !== -1 ||
                this.str2.indexOf("linjector") !== -1
            ) {
                // console.log("enter strstr replace str1:",this.str1," - " , "str2:", this.str2," thread_id:",Process.getCurrentThreadId());
                this.hook = true;
                pthread_exit_func(0);
            }

        },
        onLeave: function (retval) {
            // if(retval!=0){
            //     console.log("leave str1:",this.str1," - " , "str2:", this.str2," retval:",retval," thread_id:",Process.getCurrentThreadId());
            // }
            if (this.hook) {
                retval.replace(0);
            }
        }
    });
}

klog("test2222");
klogData("","init","%customFileName% init hook success");

fridaCheckPass();