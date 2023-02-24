//整理的过frida检测
(function(){
function klog(data,...args){
    for (let item of args){
        data+="\t"+item;
    }
    var message={};
    message["jsname"]="anti_frida";
    message["data"]=data;
    send(message);
}

function fridaCheckPass() {
    var pfn_strstr = Module.findExportByName("libc.so", "strstr");
    console.log("hook strstr");

    var keywords=check_str.split(";");
    var pfn_pthread_exit = Module.findExportByName(null, "pthread_exit");
    var pthread_exit_func=new NativeFunction(pfn_pthread_exit,"void",["int"]);
    Interceptor.attach(pfn_strstr, {
        onEnter: function (args) {
            this.str1 = Memory.readCString(args[0]);
            this.str2 = Memory.readCString(args[1]);
            for(var i=0;i<keywords.length;i++){
                if(this.str2.indexOf(keywords[i])!=-1){
                    // klog("strstr keyword:"+keywords[i]);
                    // klog("enter strstr replace str1:"+this.str1+" - " +"str2:"+ this.str2+" thread_id:"+Process.getCurrentThreadId());
                    this.hook = true;
                    if(isExitThread){
                        klog("pthread_exit_func");
                        pthread_exit_func(0);
                    }
                    break;
                }
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


function hooklibc() {
    klog("hook readlink");
    Interceptor.attach(Module.findExportByName(null, "readlink"), {
            onEnter: function (args) {
                // console.log("enter readlink");
                this.pathname = args[0];
                this.buf = args[1];
                this.bufsize = args[2];
            }, onLeave: function (retval) {
                var s2str = this.buf.readCString();
                if (s2str.indexOf("/data/local/tmp/re.frida.server/linjector") != -1) {
                    this.buf.writeUtf8String("/system/framework/boot.art");
                    retval.replace(0x1A);
                    klog("readlink ",s2str);
                }
                //console.log('\nreadlink(' + 's1="' + this.aaa.readCString() + '"' + ', s2="' + this.bbb.readCString() + '"' + ', s3="' + this.ccc + '"' + ')');
            }
        }
    );
    klog("hook readlinkat");
    Interceptor.attach(Module.findExportByName(null, "readlinkat"), {
            onEnter: function (args) {
                // console.log("enter readlinkat");
                this.pathname = args[1];
                this.buf = args[2];
                this.bufsize = args[3];
            }, onLeave: function (retval) {
                var s2str = this.buf.readCString();
                if (s2str.indexOf("/data/local/tmp/re.frida.server/linjector") != -1) {
                    this.buf.writeUtf8String("/system/framework/boot.art");
                    retval.replace(0x1A);
                    klog("readlinkat "+s2str);
                }
                //console.log('\nreadlink(' + 's1="' + this.aaa.readCString() + '"' + ', s2="' + this.bbb.readCString() + '"' + ', s3="' + this.ccc + '"' + ')');
            }
        }
    );

    klog("hook open");
    const openPtr = Module.getExportByName('libc.so', 'open');
    const open = new NativeFunction(openPtr, 'int', ['pointer', 'int']);
    var fakePath = "/data/local/tmp/maps";
    Interceptor.replace(openPtr, new NativeCallback(function (pathnameptr, flag) {
      var pathname = Memory.readUtf8String(pathnameptr);
      if (pathname.indexOf("maps") >= 0 && pathname.indexOf("proc")>=0) {
          klog("replace maps "+pathname);
          var filename = Memory.allocUtf8String(fakePath);
          klog("replace maps over");
          return open(filename, flag);
      }
      if (pathname.indexOf("/su") != -1) {
          klog("replace su");
          var filename = Memory.allocUtf8String("/xxx/su");
          return open(filename, flag);
      }
      var fd = open(pathnameptr, flag);
      return fd;
    }, 'int', ['pointer', 'int']));

    klog("hook openat");
    const openatPtr = Module.getExportByName('libc.so', 'openat');
    const openat = new NativeFunction(openatPtr, 'int', ['int','pointer', 'int','int']);
    Interceptor.replace(openatPtr, new NativeCallback(function (fd,pathnameptr, flag,mode) {
      var pathname = Memory.readUtf8String(pathnameptr);
      if (pathname.indexOf("maps") >= 0) {
          var filename = Memory.allocUtf8String(fakePath);
          klog("replace maps");
          return openat(fd,filename, flag,mode);
      }
      if (pathname.indexOf("/su") != -1) {
          var filename = Memory.allocUtf8String("/xxx/su");
          return openat(fd,filename, flag,mode);
      }
      var fd = openat(fd,pathnameptr, flag,mode);
      return fd;
    }, 'int', ['int','pointer', 'int','int']));

}

function readFile(fileName){
    klog("> Reading file: "+fileName);
    var JString = Java.use("java.lang.String");
    var Files = Java.use("java.nio.file.Files");
    var Paths = Java.use("java.nio.file.Paths");
    var URI = Java.use("java.net.URI");

    var pathName = "file://" + fileName;
    var path = Paths.get(URI.create(pathName));
    var fileBytes = Files.readAllBytes(path);
    var ret = JString.$new(fileBytes);
    return ret;
}

function replaceMaps(){
    var data= readFile("/proc/self/maps");
    var saveFile=new File("/data/local/tmp/maps","w");
    data.split("\n").forEach(function(line){
        if(line.indexOf("tmp")===-1){
            saveFile.write(line+"\n");
        }
    });
    saveFile.close();
}



var antiType="%antiType%";
// 方案1使用的参数
var check_str = "%Keyword%";
var isExitThread="%isExitThread%";

// 方案2使用的参数

klog("init","anti_frida.js init hook success")
if(antiType.indexOf("strstr")!=-1){
    fridaCheckPass();
}
if (antiType.indexOf("libc")!=-1){
    replaceMaps();
    hooklibc();
}
if (antiType.indexOf("svc")!=-1){

}

})();
