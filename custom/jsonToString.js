
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

klogData("","init","%customFileName% init hook success");

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