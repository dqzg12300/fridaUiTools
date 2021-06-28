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