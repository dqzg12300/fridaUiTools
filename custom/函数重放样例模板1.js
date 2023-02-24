function klog(data,...args){
    for (let item of args){
        data+="\t"+item;
    }
    var message={};
    message["jsname"]="jni_trace_new";
    message["data"]=data;
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
klog("init","%customFileName% init hook success");