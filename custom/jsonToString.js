
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

function hook_java(){
    Java.perform(function(){
        var jsonObj=Java.use("org.json.JSONObject");
        jsonObj.toString.overload().implementation=function(){
            var res=this.toString();
            klog(res);
            return res;
        }
    })
}

function main(){
    hook_java();
}

setImmediate(main)