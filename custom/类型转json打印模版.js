function klog(data,...args){
    for (let item of args){
        data+="\t"+item;
    }
    var message={};
    message["jsname"]="jni_trace_new";
    message["data"]=data;
    send(message);
}

klog("init","%customFileName% init hook success");

Java.perform(function(){
    var mainActivityClazz=Java.use("com.mik.fridaceshi.MainActivity");
    mainActivityClazz.test.implementation=function(arg1){
        try{
            console.log(toJSONString(arg1));
        }
        catch (e){
            console.log(e);
        }
        return this.test(arg1);
    }
})