(function(){

function klog(data){
var message={};
message["jsname"]="cookieDump";
message["data"]=data;
send(message);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="cookieDump";
    message["data"]=data;
    message[key]=value;
    send(message);
}

function getHandle(object) {
    var handle = null;
    try {
        handle = object.$handle;
    } catch (e) {
        console.error(e)
    }
    if (handle == null) {
        try {
            handle = object.$h;
        } catch (e) {
            console.error(e)
        }

    }
    return handle;
}


function get_self_process_name() {
    var openPtr = Module.getExportByName('libc.so', 'open');
    var open = new NativeFunction(openPtr, 'int', ['pointer', 'int']);

    var readPtr = Module.getExportByName("libc.so", "read");
    var read = new NativeFunction(readPtr, "int", ["int", "pointer", "int"]);

    var closePtr = Module.getExportByName('libc.so', 'close');
    var close = new NativeFunction(closePtr, 'int', ['int']);

    var path = Memory.allocUtf8String("/proc/self/cmdline");
    var fd = open(path, 0);
    if (fd != -1) {
        var buffer = Memory.alloc(0x1000);

        var result = read(fd, buffer, 0x1000);
        close(fd);
        result = ptr(buffer).readCString();
        return result;
    }

    return "-1";
}

//解析dex结构体，取到dex的起始位置和大小，然后把文件给dump出来
//dex_file.h 结构体所在的文件
//结构体的字段部分如下。
//   const uint8_t* const begin_;
//   const size_t size_;
//   const uint8_t* const data_begin_;
//   const size_t data_size_;
//   const std::string location_;
//   const uint32_t location_checksum_;
//   const Header* const header_;
//根据上面的结构，知道了begin的偏移位置和size的偏移位置。下面是对dexptr的hexdump查看
//722bab9640  a0 90 65 2b 72 00 00 00 34 20 ea 95 71 00 00 00  ..e+r...4 ..q...
//722bab9650  60 50 08 00 00 00 00 00 88 32 f4 95 71 00 00 00  `P.......2..q...
//722bab9660  c0 0a 28 00 00 00 00 00 41 00 00 00 00 00 00 00  ..(.....A.......
//722bab9670  3e 00 00 00 00 00 00 00 80 ed a8 2b 72 00 00 00  >..........+r...
function save(dexptr){
    var base=ptr(dexptr).add(Process.pointerSize*1).readPointer();
    var dexSize=ptr(dexptr).add(Process.pointerSize*2).readUInt();
    var process_name=get_self_process_name();

    var dex_path = "/data/data/" + process_name + "/files/"+dexSize+"_cookieDump.dex";
    // console.log(dex_path);
    // console.log("base:",ptr(base),"size:",ptr(dexSize));
    var savefile=new File(dex_path,"w");
    if(savefile){
        var buffer=ptr(base).readByteArray(dexSize);
        savefile.write(buffer);
        savefile.flush();
        savefile.close();
        klog("[dump] "+dex_path);
    }
}

function dumpClassLoader(clsLoader){
    Java.perform(function(){
        try{
            //下面是要取到BaseDexClassLoader->
            // pathList(dalvik.system.DexPathList)->
            // dexElements(dalvik.system.DexPathList$Element)->
            // dexFile(dalvik.system.DexFile)->
            // mCookie(Object)
            var baseDexClassLoaderClass=Java.use("dalvik.system.BaseDexClassLoader")
            var dexPathListClass=Java.use("dalvik.system.DexPathList")
            var elementClass=Java.use("dalvik.system.DexPathList$Element")
            var dexfileClass=Java.use("dalvik.system.DexFile");
            var baseDexClassLoader=Java.cast(clsLoader,baseDexClassLoaderClass);
            var pathListObj=baseDexClassLoader.pathList.value;
            var pathList=Java.cast(pathListObj,dexPathListClass);
            var elementObj=pathList.dexElements.value;

            for(var i=0;i<elementObj.length;i++) {
                var element = Java.cast(elementObj[i], elementClass);
                var dexFileObj = element.dexFile.value;
                var dexFile = Java.cast(dexFileObj, dexfileClass);
                var mcookie = dexFile.mCookie.value;
                var handler = getHandle(mcookie);
                console.log(handler);
                // 根据安卓源码中的下面这段，知道cookie是通过ConvertJavaArrayToDexFiles这个函数转换成dex_files的
                // std::vector<const DexFile*> dex_files;
                // const OatFile* oat_file;
                // if (!ConvertJavaArrayToDexFiles(env, cookie, /*out*/ dex_files, /*out*/ oat_file)) {
                //     VLOG(class_linker) << "Failed to find dex_file";
                //     DCHECK(env->ExceptionCheck());
                //     return nullptr;
                //   }
                //根据安卓源码下面这段，知道cookie的实际类型应该是arrayObject
                // static bool ConvertJavaArrayToDexFiles(
                // JNIEnv* env,
                // jobject arrayObject,
                // /*out*/ std::vector<const DexFile*>& dex_files,
                // /*out*/ const OatFile*& oat_file){
                //
                //   jarray array = reinterpret_cast<jarray>(arrayObject);
                //   jsize array_size = env->GetArrayLength(array);
                //   if (env->ExceptionCheck() == JNI_TRUE) {
                //     return false;
                //   }
                //
                //   // TODO: Optimize. On 32bit we can use an int array.
                //   jboolean is_long_data_copied;
                //   jlong* long_data = env->GetLongArrayElements(reinterpret_cast<jlongArray>(array),
                //                                                &is_long_data_copied);
                //   if (env->ExceptionCheck() == JNI_TRUE) {
                //     return false;
                //   }
                //根据上面也知道了如何从mcookie中获取出dexfile数组的方式
                var env = Java.vm.tryGetEnv();
                var length = env.getArrayLength(handler);
                var dexptrs = env.getLongArrayElements(handler, 0);
                for(var x=0;x<length;x++){
                    //这个列表是个c++的DexFile的指针数组。所以按指针大小进行偏移获取每一个
                    var dexptr= ptr(dexptrs).add(x*Process.pointerSize).readPointer();
                    // console.log(hexdump(dexptr,{length:0x70}));
                    //DexFile的数据，将dex写入文件保存
                    try{
                        save(dexptr);
                    }catch(ex){
                        klog("write err:"+ex);
                    }

                }
            }
        }catch(ex){
            console.log("dumpClassLoader err:"+ex);
        }
    })
}

function dumpAll(){
    Java.perform(function(){
        Java.enumerateClassLoadersSync().forEach(function(classLoader){
            dumpClassLoader(classLoader);
        })
    })
}

function main(){
    klogData("","init","cookieDump.js init hook success")
    dumpAll();
}

setImmediate(main);

})();
