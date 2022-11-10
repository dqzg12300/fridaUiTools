function klog(data){
    var message={};
    message["jsname"]="%customName%";
    message["data"]=data;
    // send(message);
    console.log(data);
}
function klogData(data,key,value){
    var message={};
    message["jsname"]="%customName%";
    message["data"]=data;
    message[key]=value;
    // send(message);
    console.log(data);
}

klogData("","init","%customFileName% init hook success");

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