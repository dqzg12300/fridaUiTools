//来源FridaContainer
(function(){

function klog(data){
    var message={};
    message["jsname"]="FCAnd_Jnitrace";
    message["data"]=data;
    send(message);
    // console.log(data);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="FCAnd_Jnitrace";
    message["data"]=data;
    message[key]=value;
    send(message);
    // console.log(data);
}

function getLR(context) {
    if (Process.arch == 'arm') {
        return context.lr;
    }
    else if (Process.arch == 'arm64') {
        return context.lr;
    }
    else {
        klog('getLR\t not support current arch: ' + Process.arch);
    }
    return ptr(0);
}

class BacktraceJSONContainer {
    address;
    module;
    // public readonly symbol: DebugSymbol | null;
    constructor(address, module) {
        this.address = address;
        this.module = module;
        // this.symbol = symbol;
    }
}

class MethodData {
    tag = 'MethodData';
    methodname;
    args;
    retval;
    methodDef;
    jnival;
    backtrace;


    constructor(ctx, methodname, methodDef, args, retval) {
        this.methodname = methodname;
        this.methodDef = methodDef;
        this.args = args;
        this.jnival = { 'args': [], 'ret': null };
        // let bt = Thread.backtrace(ctx, Backtracer.ACCURATE); //  Backtracer.FUZZY
        // this.backtrace = bt.map((addr: NativePointer): BacktraceJSONContainer => {
        //     return new BacktraceJSONContainer(
        //         addr,
        //         Process.findModuleByAddress(addr),
        //         DebugSymbol.fromAddress(addr)
        //     );
        // });
        let addr = getLR(ctx);
        if (ptr(0) != addr) {
            this.backtrace = [new BacktraceJSONContainer(addr, Process.findModuleByAddress(addr))];
        }
        else {
            this.backtrace = [];
        }
        let argTypes = this.methodDef.args;
        for (let i = 0; i < argTypes.length; i++) {
            let ptr = args[i];
            let argType = argTypes[i];
            let argval = MethodData.getFridaValue(argType, ptr);
            this.jnival.args.push({ argType: argType, argVal: argval });
        }
        if (null != retval) {
            this.setRetval(retval);
        }
    }

    setRetval(retval) {
        this.retval = retval;
        let retType = this.methodDef.ret;
        let retVal = MethodData.getFridaValue(this.methodDef.ret, retval);
        this.jnival.ret = { retType: retType, retVal: retVal };
    }
    toString() {
        return JSON.stringify(this);
    }

    static getFridaValue(type, ptr) {
        if (null == ptr || 0 == ptr.toInt32()) {
            return ptr;
        }
        if (type.endsWith('*')) {
            if (type.startsWith('char')) {
                return ptr.readCString();
            }
            else if (type.startsWith('jchar')) {
                let res = null;
                try {
                    let tmp = ptr.readUtf16String();
                    if (tmp) {
                        if (tmp[0].charCodeAt(0) < 0x80) {
                            for (let i = 0; i < tmp.length; ++i) {
                                if (tmp.charCodeAt(i) > 0x80) {
                                    tmp = tmp.substring(0, i);
                                    break;
                                }
                            }
                        }
                        if (tmp.length < 2) {
                            tmp += "(hex:0x" + ptr.readU16().toString(16) + ")";
                        }
                    }
                    res = tmp;
                }
                catch (e) {
                }
                return res == null ? "" : res;
            }
            else {
                try {
                    return ptr.readPointer();
                }
                catch (e) {
                    return ptr;
                }
            }
        }
        else {
            if ('jstring' === type) {
                return Java.vm.getEnv().stringFromJni(ptr);
            }
            else if ('jclass' === type) {
                return Java.vm.getEnv().getClassName(ptr);
            }
            return ptr;
        }
    }
}

const jni_env_json_1 =[
  {
    "name": "reserved0",
    "args": [

    ],
    "ret": "void"
  },
  {
    "name": "reserved1",
    "args": [

    ],
    "ret": "void"
  },
  {
    "name": "reserved2",
    "args": [

    ],
    "ret": "void"
  },
  {
    "name": "reserved3",
    "args": [

    ],
    "ret": "void"
  },
  {
    "name": "GetVersion",
    "args": [
      "JNIEnv*"
    ],
    "ret": "jint"
  },
  {
    "name": "DefineClass",
    "args": [
      "JNIEnv*",
      "char*",
      "jobject",
      "jbyte*",
      "jsize"
    ],
    "ret": "jclass"
  },
  {
    "name": "FindClass",
    "args": [
      "JNIEnv*",
      "char*"
    ],
    "ret": "jclass"
  },
  {
    "name": "FromReflectedMethod",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jmethodID"
  },
  {
    "name": "FromReflectedField",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jfieldID"
  },
  {
    "name": "ToReflectedMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jboolean"
    ],
    "ret": "jobject"
  },
  {
    "name": "GetSuperclass",
    "args": [
      "JNIEnv*",
      "jclass"
    ],
    "ret": "jclass"
  },
  {
    "name": "IsAssignableFrom",
    "args": [
      "JNIEnv*",
      "jclass",
      "jclass"
    ],
    "ret": "jboolean"
  },
  {
    "name": "ToReflectedField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jboolean"
    ],
    "ret": "jobject"
  },
  {
    "name": "Throw",
    "args": [
      "JNIEnv*",
      "jthrowable"
    ],
    "ret": "jint"
  },
  {
    "name": "ThrowNew",
    "args": [
      "JNIEnv*",
      "jclass",
      "char*"
    ],
    "ret": "jint"
  },
  {
    "name": "ExceptionOccurred",
    "args": [
      "JNIEnv*"
    ],
    "ret": "jthrowable"
  },
  {
    "name": "ExceptionDescribe",
    "args": [
      "JNIEnv*"
    ],
    "ret": "void"
  },
  {
    "name": "ExceptionClear",
    "args": [
      "JNIEnv*"
    ],
    "ret": "void"
  },
  {
    "name": "FatalError",
    "args": [
      "JNIEnv*",
      "char*"
    ],
    "ret": "void"
  },
  {
    "name": "PushLocalFrame",
    "args": [
      "JNIEnv*",
      "jint"
    ],
    "ret": "jint"
  },
  {
    "name": "PopLocalFrame",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jobject"
  },
  {
    "name": "NewGlobalRef",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jobject"
  },
  {
    "name": "DeleteGlobalRef",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "void"
  },
  {
    "name": "DeleteLocalRef",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "void"
  },
  {
    "name": "IsSameObject",
    "args": [
      "JNIEnv*",
      "jobject",
      "jobject"
    ],
    "ret": "jboolean"
  },
  {
    "name": "NewLocalRef",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jobject"
  },
  {
    "name": "EnsureLocalCapacity",
    "args": [
      "JNIEnv*",
      "jint"
    ],
    "ret": "jint"
  },
  {
    "name": "AllocObject",
    "args": [
      "JNIEnv*",
      "jclass"
    ],
    "ret": "jobject"
  },
  {
    "name": "NewObject",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jobject"
  },
  {
    "name": "NewObjectV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jobject"
  },
  {
    "name": "NewObjectA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jobject"
  },
  {
    "name": "GetObjectClass",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jclass"
  },
  {
    "name": "IsInstanceOf",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass"
    ],
    "ret": "jboolean"
  },
  {
    "name": "GetMethodID",
    "args": [
      "JNIEnv*",
      "jclass",
      "char*",
      "char*"
    ],
    "ret": "jmethodID"
  },
  {
    "name": "CallObjectMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jobject"
  },
  {
    "name": "CallObjectMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jobject"
  },
  {
    "name": "CallObjectMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jobject"
  },
  {
    "name": "CallBooleanMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallBooleanMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallBooleanMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallByteMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallByteMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallByteMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallCharMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jchar"
  },
  {
    "name": "CallCharMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jchar"
  },
  {
    "name": "CallCharMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jchar"
  },
  {
    "name": "CallShortMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jshort"
  },
  {
    "name": "CallShortMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jshort"
  },
  {
    "name": "CallShortMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jshort"
  },
  {
    "name": "CallIntMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jint"
  },
  {
    "name": "CallIntMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jint"
  },
  {
    "name": "CallIntMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jint"
  },
  {
    "name": "CallLongMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jlong"
  },
  {
    "name": "CallLongMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jlong"
  },
  {
    "name": "CallLongMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jlong"
  },
  {
    "name": "CallFloatMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallFloatMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallFloatMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallDoubleMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallDoubleMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallDoubleMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallVoidMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "..."
    ],
    "ret": "void"
  },
  {
    "name": "CallVoidMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "va_list"
    ],
    "ret": "void"
  },
  {
    "name": "CallVoidMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "void"
  },
  {
    "name": "CallNonvirtualObjectMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jobject"
  },
  {
    "name": "CallNonvirtualObjectMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jobject"
  },
  {
    "name": "CallNonvirtualObjectMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jobject"
  },
  {
    "name": "CallNonvirtualBooleanMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallNonvirtualBooleanMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallNonvirtualBooleanMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallNonvirtualByteMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallNonvirtualByteMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallNonvirtualByteMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallNonvirtualCharMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jchar"
  },
  {
    "name": "CallNonvirtualCharMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jchar"
  },
  {
    "name": "CallNonvirtualCharMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jchar"
  },
  {
    "name": "CallNonvirtualShortMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jshort"
  },
  {
    "name": "CallNonvirtualShortMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jshort"
  },
  {
    "name": "CallNonvirtualShortMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jshort"
  },
  {
    "name": "CallNonvirtualIntMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jint"
  },
  {
    "name": "CallNonvirtualIntMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jint"
  },
  {
    "name": "CallNonvirtualIntMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jint"
  },
  {
    "name": "CallNonvirtualLongMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jlong"
  },
  {
    "name": "CallNonvirtualLongMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jlong"
  },
  {
    "name": "CallNonvirtualLongMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jlong"
  },
  {
    "name": "CallNonvirtualFloatMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallNonvirtualFloatMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallNonvirtualFloatMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallNonvirtualDoubleMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallNonvirtualDoubleMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallNonvirtualDoubleMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallNonvirtualVoidMethod",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "void"
  },
  {
    "name": "CallNonvirtualVoidMethodV",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "void"
  },
  {
    "name": "CallNonvirtualVoidMethodA",
    "args": [
      "JNIEnv*",
      "jobject",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "void"
  },
  {
    "name": "GetFieldID",
    "args": [
      "JNIEnv*",
      "jclass",
      "char*",
      "char*"
    ],
    "ret": "jfieldID"
  },
  {
    "name": "GetObjectField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jobject"
  },
  {
    "name": "GetBooleanField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jboolean"
  },
  {
    "name": "GetByteField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jbyte"
  },
  {
    "name": "GetCharField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jchar"
  },
  {
    "name": "GetShortField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jshort"
  },
  {
    "name": "GetIntField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jint"
  },
  {
    "name": "GetLongField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jlong"
  },
  {
    "name": "GetFloatField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jfloat"
  },
  {
    "name": "GetDoubleField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID"
    ],
    "ret": "jdouble"
  },
  {
    "name": "SetObjectField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jobject"
    ],
    "ret": "void"
  },
  {
    "name": "SetBooleanField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jboolean"
    ],
    "ret": "void"
  },
  {
    "name": "SetByteField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jbyte"
    ],
    "ret": "void"
  },
  {
    "name": "SetCharField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jchar"
    ],
    "ret": "void"
  },
  {
    "name": "SetShortField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jshort"
    ],
    "ret": "void"
  },
  {
    "name": "SetIntField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "SetLongField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jlong"
    ],
    "ret": "void"
  },
  {
    "name": "SetFloatField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jfloat"
    ],
    "ret": "void"
  },
  {
    "name": "SetDoubleField",
    "args": [
      "JNIEnv*",
      "jobject",
      "jfieldID",
      "jdouble"
    ],
    "ret": "void"
  },
  {
    "name": "GetStaticMethodID",
    "args": [
      "JNIEnv*",
      "jclass",
      "char*",
      "char*"
    ],
    "ret": "jmethodID"
  },
  {
    "name": "CallStaticObjectMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jobject"
  },
  {
    "name": "CallStaticObjectMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jobject"
  },
  {
    "name": "CallStaticObjectMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jobject"
  },
  {
    "name": "CallStaticBooleanMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallStaticBooleanMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallStaticBooleanMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jboolean"
  },
  {
    "name": "CallStaticByteMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallStaticByteMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallStaticByteMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jbyte"
  },
  {
    "name": "CallStaticCharMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jchar"
  },
  {
    "name": "CallStaticCharMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jchar"
  },
  {
    "name": "CallStaticCharMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jchar"
  },
  {
    "name": "CallStaticShortMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jshort"
  },
  {
    "name": "CallStaticShortMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jshort"
  },
  {
    "name": "CallStaticShortMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jshort"
  },
  {
    "name": "CallStaticIntMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jint"
  },
  {
    "name": "CallStaticIntMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jint"
  },
  {
    "name": "CallStaticIntMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jint"
  },
  {
    "name": "CallStaticLongMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jlong"
  },
  {
    "name": "CallStaticLongMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jlong"
  },
  {
    "name": "CallStaticLongMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jlong"
  },
  {
    "name": "CallStaticFloatMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallStaticFloatMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallStaticFloatMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jfloat"
  },
  {
    "name": "CallStaticDoubleMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallStaticDoubleMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallStaticDoubleMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "jdouble"
  },
  {
    "name": "CallStaticVoidMethod",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "..."
    ],
    "ret": "void"
  },
  {
    "name": "CallStaticVoidMethodV",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "va_list"
    ],
    "ret": "void"
  },
  {
    "name": "CallStaticVoidMethodA",
    "args": [
      "JNIEnv*",
      "jclass",
      "jmethodID",
      "jvalue*"
    ],
    "ret": "void"
  },
  {
    "name": "GetStaticFieldID",
    "args": [
      "JNIEnv*",
      "jclass",
      "char*",
      "char*"
    ],
    "ret": "jfieldID"
  },
  {
    "name": "GetStaticObjectField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jobject"
  },
  {
    "name": "GetStaticBooleanField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jboolean"
  },
  {
    "name": "GetStaticByteField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jbyte"
  },
  {
    "name": "GetStaticCharField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jchar"
  },
  {
    "name": "GetStaticShortField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jshort"
  },
  {
    "name": "GetStaticIntField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jint"
  },
  {
    "name": "GetStaticLongField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jlong"
  },
  {
    "name": "GetStaticFloatField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jfloat"
  },
  {
    "name": "GetStaticDoubleField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID"
    ],
    "ret": "jdouble"
  },
  {
    "name": "SetStaticObjectField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jobject"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticBooleanField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jboolean"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticByteField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jbyte"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticCharField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jchar"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticShortField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jshort"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticIntField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticLongField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jlong"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticFloatField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jfloat"
    ],
    "ret": "void"
  },
  {
    "name": "SetStaticDoubleField",
    "args": [
      "JNIEnv*",
      "jclass",
      "jfieldID",
      "jdouble"
    ],
    "ret": "void"
  },
  {
    "name": "NewString",
    "args": [
      "JNIEnv*",
      "jchar*",
      "jsize"
    ],
    "ret": "jstring"
  },
  {
    "name": "GetStringLength",
    "args": [
      "JNIEnv*",
      "jstring"
    ],
    "ret": "jsize"
  },
  {
    "name": "GetStringChars",
    "args": [
      "JNIEnv*",
      "jstring",
      "jboolean*"
    ],
    "ret": "jchar*"
  },
  {
    "name": "ReleaseStringChars",
    "args": [
      "JNIEnv*",
      "jstring",
      "jchar*"
    ],
    "ret": "void"
  },
  {
    "name": "NewStringUTF",
    "args": [
      "JNIEnv*",
      "char*"
    ],
    "ret": "jstring"
  },
  {
    "name": "GetStringUTFLength",
    "args": [
      "JNIEnv*",
      "jstring"
    ],
    "ret": "jsize"
  },
  {
    "name": "GetStringUTFChars",
    "args": [
      "JNIEnv*",
      "jstring",
      "jboolean*"
    ],
    "ret": "char*"
  },
  {
    "name": "ReleaseStringUTFChars",
    "args": [
      "JNIEnv*",
      "jstring",
      "char*"
    ],
    "ret": "void"
  },
  {
    "name": "GetArrayLength",
    "args": [
      "JNIEnv*",
      "jarray"
    ],
    "ret": "jsize"
  },
  {
    "name": "NewObjectArray",
    "args": [
      "JNIEnv*",
      "jsize",
      "jclass",
      "jobject"
    ],
    "ret": "jobjectArray"
  },
  {
    "name": "GetObjectArrayElement",
    "args": [
      "JNIEnv*",
      "jobjectArray",
      "jsize"
    ],
    "ret": "jobject"
  },
  {
    "name": "SetObjectArrayElement",
    "args": [
      "JNIEnv*",
      "jobjectArray",
      "jsize",
      "jobject"
    ],
    "ret": "void"
  },
  {
    "name": "NewBooleanArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jbooleanArray"
  },
  {
    "name": "NewByteArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jbyteArray"
  },
  {
    "name": "NewCharArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jcharArray"
  },
  {
    "name": "NewShortArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jshortArray"
  },
  {
    "name": "NewIntArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jintArray"
  },
  {
    "name": "NewLongArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jlongArray"
  },
  {
    "name": "NewFloatArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jfloatArray"
  },
  {
    "name": "NewDoubleArray",
    "args": [
      "JNIEnv*",
      "jsize"
    ],
    "ret": "jdoubleArray"
  },
  {
    "name": "GetBooleanArrayElements",
    "args": [
      "JNIEnv*",
      "jbooleanArray",
      "jboolean*"
    ],
    "ret": "jboolean*"
  },
  {
    "name": "GetByteArrayElements",
    "args": [
      "JNIEnv*",
      "jbyteArray",
      "jboolean*"
    ],
    "ret": "jbyte*"
  },
  {
    "name": "GetCharArrayElements",
    "args": [
      "JNIEnv*",
      "jcharArray",
      "jboolean*"
    ],
    "ret": "jchar*"
  },
  {
    "name": "GetShortArrayElements",
    "args": [
      "JNIEnv*",
      "jshortArray",
      "jboolean*"
    ],
    "ret": "jshort*"
  },
  {
    "name": "GetIntArrayElements",
    "args": [
      "JNIEnv*",
      "jintArray",
      "jboolean*"
    ],
    "ret": "jint*"
  },
  {
    "name": "GetLongArrayElements",
    "args": [
      "JNIEnv*",
      "jlongArray",
      "jboolean*"
    ],
    "ret": "jlong*"
  },
  {
    "name": "GetFloatArrayElements",
    "args": [
      "JNIEnv*",
      "jfloatArray",
      "jboolean*"
    ],
    "ret": "jfloat*"
  },
  {
    "name": "GetDoubleArrayElements",
    "args": [
      "JNIEnv*",
      "jdoubleArray",
      "jboolean*"
    ],
    "ret": "jdouble*"
  },
  {
    "name": "ReleaseBooleanArrayElements",
    "args": [
      "JNIEnv*",
      "jbooleanArray",
      "jboolean*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseByteArrayElements",
    "args": [
      "JNIEnv*",
      "jbyteArray",
      "jbyte*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseCharArrayElements",
    "args": [
      "JNIEnv*",
      "jcharArray",
      "jchar*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseShortArrayElements",
    "args": [
      "JNIEnv*",
      "jshortArray",
      "jshort*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseIntArrayElements",
    "args": [
      "JNIEnv*",
      "jintArray",
      "jint*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseLongArrayElements",
    "args": [
      "JNIEnv*",
      "jlongArray",
      "jlong*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseFloatArrayElements",
    "args": [
      "JNIEnv*",
      "jfloatArray",
      "jfloat*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "ReleaseDoubleArrayElements",
    "args": [
      "JNIEnv*",
      "jdoubleArray",
      "jdouble*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "GetBooleanArrayRegion",
    "args": [
      "JNIEnv*",
      "jbooleanArray",
      "jsize",
      "jsize",
      "jboolean*"
    ],
    "ret": "void"
  },
  {
    "name": "GetByteArrayRegion",
    "args": [
      "JNIEnv*",
      "jbyteArray",
      "jsize",
      "jsize",
      "jbyte*"
    ],
    "ret": "void"
  },
  {
    "name": "GetCharArrayRegion",
    "args": [
      "JNIEnv*",
      "jcharArray",
      "jsize",
      "jsize",
      "jchar*"
    ],
    "ret": "void"
  },
  {
    "name": "GetShortArrayRegion",
    "args": [
      "JNIEnv*",
      "jshortArray",
      "jsize",
      "jsize",
      "jshort*"
    ],
    "ret": "void"
  },
  {
    "name": "GetIntArrayRegion",
    "args": [
      "JNIEnv*",
      "jintArray",
      "jsize",
      "jsize",
      "jint*"
    ],
    "ret": "void"
  },
  {
    "name": "GetLongArrayRegion",
    "args": [
      "JNIEnv*",
      "jlongArray",
      "jsize",
      "jsize",
      "jlong*"
    ],
    "ret": "void"
  },
  {
    "name": "GetFloatArrayRegion",
    "args": [
      "JNIEnv*",
      "jfloatArray",
      "jsize",
      "jsize",
      "jfloat*"
    ],
    "ret": "void"
  },
  {
    "name": "GetDoubleArrayRegion",
    "args": [
      "JNIEnv*",
      "jdoubleArray",
      "jsize",
      "jsize",
      "jdouble*"
    ],
    "ret": "void"
  },
  {
    "name": "SetBooleanArrayRegion",
    "args": [
      "JNIEnv*",
      "jbooleanArray",
      "jsize",
      "jsize",
      "jboolean*"
    ],
    "ret": "void"
  },
  {
    "name": "SetByteArrayRegion",
    "args": [
      "JNIEnv*",
      "jbyteArray",
      "jsize",
      "jsize",
      "jbyte*"
    ],
    "ret": "void"
  },
  {
    "name": "SetCharArrayRegion",
    "args": [
      "JNIEnv*",
      "jcharArray",
      "jsize",
      "jsize",
      "jchar*"
    ],
    "ret": "void"
  },
  {
    "name": "SetShortArrayRegion",
    "args": [
      "JNIEnv*",
      "jshortArray",
      "jsize",
      "jsize",
      "jshort*"
    ],
    "ret": "void"
  },
  {
    "name": "SetIntArrayRegion",
    "args": [
      "JNIEnv*",
      "jintArray",
      "jsize",
      "jsize",
      "jint*"
    ],
    "ret": "void"
  },
  {
    "name": "SetLongArrayRegion",
    "args": [
      "JNIEnv*",
      "jlongArray",
      "jsize",
      "jsize",
      "jlong*"
    ],
    "ret": "void"
  },
  {
    "name": "SetFloatArrayRegion",
    "args": [
      "JNIEnv*",
      "jfloatArray",
      "jsize",
      "jsize",
      "jfloat*"
    ],
    "ret": "void"
  },
  {
    "name": "SetDoubleArrayRegion",
    "args": [
      "JNIEnv*",
      "jdoubleArray",
      "jsize",
      "jsize",
      "jdouble*"
    ],
    "ret": "void"
  },
  {
    "name": "RegisterNatives",
    "args": [
      "JNIEnv*",
      "jclass",
      "JNINativeMethod*",
      "jint"
    ],
    "ret": "jint"
  },
  {
    "name": "UnregisterNatives",
    "args": [
      "JNIEnv*",
      "jclass"
    ],
    "ret": "jint"
  },
  {
    "name": "MonitorEnter",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jint"
  },
  {
    "name": "MonitorExit",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jint"
  },
  {
    "name": "GetJavaVM",
    "args": [
      "JNIEnv*",
      "JavaVM**"
    ],
    "ret": "jint"
  },
  {
    "name": "GetStringRegion",
    "args": [
      "JNIEnv*",
      "jstring",
      "jsize",
      "jsize",
      "jchar*"
    ],
    "ret": "void"
  },
  {
    "name": "GetStringUTFRegion",
    "args": [
      "JNIEnv*",
      "jstring",
      "jsize",
      "jsize",
      "char*"
    ],
    "ret": "void"
  },
  {
    "name": "GetPrimitiveArrayCritical",
    "args": [
      "JNIEnv*",
      "jarray",
      "jboolean*"
    ],
    "ret": "void"
  },
  {
    "name": "ReleasePrimitiveArrayCritical",
    "args": [
      "JNIEnv*",
      "jarray",
      "void*",
      "jint"
    ],
    "ret": "void"
  },
  {
    "name": "GetStringCritical",
    "args": [
      "JNIEnv*",
      "jstring",
      "jboolean*"
    ],
    "ret": "jchar"
  },
  {
    "name": "ReleaseStringCritical",
    "args": [
      "JNIEnv*",
      "jstring",
      "jchar*"
    ],
    "ret": "void"
  },
  {
    "name": "NewWeakGlobalRef",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jweak"
  },
  {
    "name": "DeleteWeakGlobalRef",
    "args": [
      "JNIEnv*",
      "jweak"
    ],
    "ret": "void"
  },
  {
    "name": "ExceptionCheck",
    "args": [
      "JNIEnv*"
    ],
    "ret": "jboolean"
  },
  {
    "name": "NewDirectByteBuffer",
    "args": [
      "JNIEnv*",
      "void*",
      "jlong"
    ],
    "ret": "jobject"
  },
  {
    "name": "GetDirectBufferAddress",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "void"
  },
  {
    "name": "GetDirectBufferCapacity",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jlong"
  },
  {
    "name": "GetObjectRefType",
    "args": [
      "JNIEnv*",
      "jobject"
    ],
    "ret": "jobjectRefType"
  }
]

const jni_struct_array = [
    "reserved0",
    "reserved1",
    "reserved2",
    "reserved3",
    "GetVersion",
    "DefineClass",
    "FindClass",
    "FromReflectedMethod",
    "FromReflectedField",
    "ToReflectedMethod",
    "GetSuperclass",
    "IsAssignableFrom",
    "ToReflectedField",
    "Throw",
    "ThrowNew",
    "ExceptionOccurred",
    "ExceptionDescribe",
    "ExceptionClear",
    "FatalError",
    "PushLocalFrame",
    "PopLocalFrame",
    "NewGlobalRef",
    "DeleteGlobalRef",
    "DeleteLocalRef",
    "IsSameObject",
    "NewLocalRef",
    "EnsureLocalCapacity",
    "AllocObject",
    "NewObject",
    "NewObjectV",
    "NewObjectA",
    "GetObjectClass",
    "IsInstanceOf",
    "GetMethodID",
    "CallObjectMethod",
    "CallObjectMethodV",
    "CallObjectMethodA",
    "CallBooleanMethod",
    "CallBooleanMethodV",
    "CallBooleanMethodA",
    "CallByteMethod",
    "CallByteMethodV",
    "CallByteMethodA",
    "CallCharMethod",
    "CallCharMethodV",
    "CallCharMethodA",
    "CallShortMethod",
    "CallShortMethodV",
    "CallShortMethodA",
    "CallIntMethod",
    "CallIntMethodV",
    "CallIntMethodA",
    "CallLongMethod",
    "CallLongMethodV",
    "CallLongMethodA",
    "CallFloatMethod",
    "CallFloatMethodV",
    "CallFloatMethodA",
    "CallDoubleMethod",
    "CallDoubleMethodV",
    "CallDoubleMethodA",
    "CallVoidMethod",
    "CallVoidMethodV",
    "CallVoidMethodA",
    "CallNonvirtualObjectMethod",
    "CallNonvirtualObjectMethodV",
    "CallNonvirtualObjectMethodA",
    "CallNonvirtualBooleanMethod",
    "CallNonvirtualBooleanMethodV",
    "CallNonvirtualBooleanMethodA",
    "CallNonvirtualByteMethod",
    "CallNonvirtualByteMethodV",
    "CallNonvirtualByteMethodA",
    "CallNonvirtualCharMethod",
    "CallNonvirtualCharMethodV",
    "CallNonvirtualCharMethodA",
    "CallNonvirtualShortMethod",
    "CallNonvirtualShortMethodV",
    "CallNonvirtualShortMethodA",
    "CallNonvirtualIntMethod",
    "CallNonvirtualIntMethodV",
    "CallNonvirtualIntMethodA",
    "CallNonvirtualLongMethod",
    "CallNonvirtualLongMethodV",
    "CallNonvirtualLongMethodA",
    "CallNonvirtualFloatMethod",
    "CallNonvirtualFloatMethodV",
    "CallNonvirtualFloatMethodA",
    "CallNonvirtualDoubleMethod",
    "CallNonvirtualDoubleMethodV",
    "CallNonvirtualDoubleMethodA",
    "CallNonvirtualVoidMethod",
    "CallNonvirtualVoidMethodV",
    "CallNonvirtualVoidMethodA",
    "GetFieldID",
    "GetObjectField",
    "GetBooleanField",
    "GetByteField",
    "GetCharField",
    "GetShortField",
    "GetIntField",
    "GetLongField",
    "GetFloatField",
    "GetDoubleField",
    "SetObjectField",
    "SetBooleanField",
    "SetByteField",
    "SetCharField",
    "SetShortField",
    "SetIntField",
    "SetLongField",
    "SetFloatField",
    "SetDoubleField",
    "GetStaticMethodID",
    "CallStaticObjectMethod",
    "CallStaticObjectMethodV",
    "CallStaticObjectMethodA",
    "CallStaticBooleanMethod",
    "CallStaticBooleanMethodV",
    "CallStaticBooleanMethodA",
    "CallStaticByteMethod",
    "CallStaticByteMethodV",
    "CallStaticByteMethodA",
    "CallStaticCharMethod",
    "CallStaticCharMethodV",
    "CallStaticCharMethodA",
    "CallStaticShortMethod",
    "CallStaticShortMethodV",
    "CallStaticShortMethodA",
    "CallStaticIntMethod",
    "CallStaticIntMethodV",
    "CallStaticIntMethodA",
    "CallStaticLongMethod",
    "CallStaticLongMethodV",
    "CallStaticLongMethodA",
    "CallStaticFloatMethod",
    "CallStaticFloatMethodV",
    "CallStaticFloatMethodA",
    "CallStaticDoubleMethod",
    "CallStaticDoubleMethodV",
    "CallStaticDoubleMethodA",
    "CallStaticVoidMethod",
    "CallStaticVoidMethodV",
    "CallStaticVoidMethodA",
    "GetStaticFieldID",
    "GetStaticObjectField",
    "GetStaticBooleanField",
    "GetStaticByteField",
    "GetStaticCharField",
    "GetStaticShortField",
    "GetStaticIntField",
    "GetStaticLongField",
    "GetStaticFloatField",
    "GetStaticDoubleField",
    "SetStaticObjectField",
    "SetStaticBooleanField",
    "SetStaticByteField",
    "SetStaticCharField",
    "SetStaticShortField",
    "SetStaticIntField",
    "SetStaticLongField",
    "SetStaticFloatField",
    "SetStaticDoubleField",
    "NewString",
    "GetStringLength",
    "GetStringChars",
    "ReleaseStringChars",
    "NewStringUTF",
    "GetStringUTFLength",
    "GetStringUTFChars",
    "ReleaseStringUTFChars",
    "GetArrayLength",
    "NewObjectArray",
    "GetObjectArrayElement",
    "SetObjectArrayElement",
    "NewBooleanArray",
    "NewByteArray",
    "NewCharArray",
    "NewShortArray",
    "NewIntArray",
    "NewLongArray",
    "NewFloatArray",
    "NewDoubleArray",
    "GetBooleanArrayElements",
    "GetByteArrayElements",
    "GetCharArrayElements",
    "GetShortArrayElements",
    "GetIntArrayElements",
    "GetLongArrayElements",
    "GetFloatArrayElements",
    "GetDoubleArrayElements",
    "ReleaseBooleanArrayElements",
    "ReleaseByteArrayElements",
    "ReleaseCharArrayElements",
    "ReleaseShortArrayElements",
    "ReleaseIntArrayElements",
    "ReleaseLongArrayElements",
    "ReleaseFloatArrayElements",
    "ReleaseDoubleArrayElements",
    "GetBooleanArrayRegion",
    "GetByteArrayRegion",
    "GetCharArrayRegion",
    "GetShortArrayRegion",
    "GetIntArrayRegion",
    "GetLongArrayRegion",
    "GetFloatArrayRegion",
    "GetDoubleArrayRegion",
    "SetBooleanArrayRegion",
    "SetByteArrayRegion",
    "SetCharArrayRegion",
    "SetShortArrayRegion",
    "SetIntArrayRegion",
    "SetLongArrayRegion",
    "SetFloatArrayRegion",
    "SetDoubleArrayRegion",
    "RegisterNatives",
    "UnregisterNatives",
    "MonitorEnter",
    "MonitorExit",
    "GetJavaVM",
    "GetStringRegion",
    "GetStringUTFRegion",
    "GetPrimitiveArrayCritical",
    "ReleasePrimitiveArrayCritical",
    "GetStringCritical",
    "ReleaseStringCritical",
    "NewWeakGlobalRef",
    "DeleteWeakGlobalRef",
    "ExceptionCheck",
    "NewDirectByteBuffer",
    "GetDirectBufferAddress",
    "GetDirectBufferCapacity",
    "GetObjectRefType"
];


function getJNIFunctionAdress(jnienv_addr, func_name) {
    var offset = jni_struct_array.indexOf(func_name) * Process.pointerSize;
    return jnienv_addr.add(offset).readPointer();
}

function getJNIAddr(name) {
    var env = Java.vm.getEnv();
    var env_ptr = env.handle.readPointer();
    const addr = getJNIFunctionAdress(env_ptr, name);
    return addr;
}

function hookJNI(name, callbacksOrProbe, data) {
    const addr = getJNIAddr(name);
    return Interceptor.attach(addr, callbacksOrProbe);
}

function traceAllJNISimply() {
    // 遍历 Hook Jni 函数
    jni_struct_array.forEach(function (func_name, idx) {
        if (!func_name.includes("reserved")) {
            hookJNI(func_name, {
                onEnter(args) {
                    // 触发时将信息保存到对象中
                    klog("onEnter "+func_name);
                    let md = new MethodData(this.context, func_name, jni_env_json_1[idx], args);
                    this.md = md;
                },
                onLeave(retval) {
                    // 退出时将返回值追加到对象中
                    this.md.setRetval(retval);
                    // 发送日志
                    klog(JSON.stringify({ tid: this.threadId, status: "jnitrace", data: this.md }));
                }
            });
        }
    });
}

function hook_jni(library_name, function_name){
    // To get the list of exports
    Module.enumerateExportsSync(library_name).forEach(function(symbol){
        klog(symbol.name);
        if(symbol.name.indexOf(function_name)!=-1){
            klog("[...] Hooking : " + library_name + " -> " + function_name + " at " + symbol.address)
            Interceptor.attach(symbol.address,{
                onEnter: function(args){
                    traceAllJNISimply();
                },
                onLeave: function(args){
                    // Prevent from displaying junk from other functions
                    Interceptor.detachAll()
                    klog("[-] Detaching all interceptors")
                }
            })
        }
    })
}

Java.perform(function() {
    klogData("","init","FCAnd_Jnitrace.js init hook success")
    var library_name = "%moduleName%" // ex: libsqlite.so
    var function_name = "%methodName%" // ex: JNI_OnLoad
    if(library_name=="" || function_name==""){
        klog("not set module or method,jni trace all");
        traceAllJNISimply();
        return;
    }
    klog("module:"+library_name+ "\tmethod:"+function_name);
    var isSpawn="%spawn%";
    if(isSpawn){
        Interceptor.attach(Module.findExportByName(null, 'android_dlopen_ext'),{
            onEnter: function(args){
                // first arg is the path to the library loaded
                var library_path = Memory.readCString(args[0])
                this.library_loaded=0;
                if( library_path.includes(library_name)){
                    klog("[...] Loading library : " + library_path)
                    this.library_loaded = 1
                }
            },
            onLeave: function(args){
                // if it's the library we want to hook, hooking it
                if(this.library_loaded ==  1){
                    klog("[+] Loaded")
                    hook_jni(library_name, function_name)
                    this.library_loaded = 0
                }
            }
        })
    }else{
        hook_jni(library_name, function_name);
    }
});

})();
