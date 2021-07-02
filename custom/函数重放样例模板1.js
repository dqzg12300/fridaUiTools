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

function call_aa(arg1,arg2){
    Java.perform(function(){
        console.log(arg1,arg2);
    });
}
var call_funs={};
call_funs.calldemo1=function(args){
	console.log("call demo1");
	var argsSp=args.split(",");
	call_aa(parseInt(argsSp[0]),parseInt(argsSp[1]));
}
call_funs.calldemo2=function(args){
	console.log("call demo1");
	var argsSp=args.split(",");
	call_aa(parseInt(argsSp[0]),parseInt(argsSp[1]));
}

rpc.exports.callnormal=function(methodName,args){
	var argsSp=args.split(",");
	call_funs[methodName](args);
}
klogData("","init","%customFileName% init hook success");