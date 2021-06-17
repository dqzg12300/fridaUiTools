//默认使用,后面再搞点默认hook功能

function initMessage(){
  var message={};
  message["jsname"]="default";
  return message;
}

//查找java的函数
function showMethods(postdata){
    var inputClass=postdata["className"];
    var inputMethod=postdata["methodName"];
    var hasMethod=postdata["hasMethod"];
    var msg= initMessage()
    console.log("enter js showMethods")
    Java.perform(function(){
        var cnt=0;
        Java.enumerateLoadedClassesSync().forEach(function(className){
            if (inputClass && inputClass.length>0){
                if(className.toUpperCase().indexOf(inputClass.toUpperCase())<0){
                    return;
                }
            }
            if(!hasMethod){
                cnt+=1;
                msg["data"]="className:"+className;
                send(msg);
                return;
            }
            // console.log("loaded: "+className);
            try{
                var classModel= Java.use(className);
                var methods=classModel.class.getDeclaredMethods();
                for(var i=0;i<methods.length;i++){
                    var methodName=methods[i].getName()
                    if (inputMethod && inputMethod.length>0){
                        if(methodName.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                            return;
                        }
                    }
                    cnt+=1;
                    msg["data"]="className:"+className+"----method:"+methodName;
                    send(msg);
                }
            }catch(ex){

            }
        })
        msg["data"]="find count:"+cnt;
        send(msg)
    });
}
//查找so的符号
function showExport(postdata){
    var inputModule=postdata["moduleName"];
    var inputMethod=postdata["methodName"];
    var showType=postdata["showType"];
    var hasMethod=postdata["hasMethod"];
    var msg= initMessage()
    var cnt=0;
    console.log("enter js showExport")
    Process.enumerateModules().forEach(function(module){
        if (inputClass && inputClass.length>0){
            if(module.name.toUpperCase().indexOf(inputModule.toUpperCase())<0){
                return;
            }
        }
        if(!hasMethod){
                cnt+=1;
                msg["data"]="module:"+module.name;
                send(msg);
                return;
            }
        if(showType=="Export"){
            module.enumerateExports().forEach(function(edata){
                if (inputMethod && inputMethod.length>0){
                    if(edata.name.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                        return;
                    }
                }
                cnt+=1;
                msg["data"]="module:"+module.name+"----exportName:"+edata.name+"----address:"+edata.address+"----type:"+edata.type;
                send(msg)
            });
        }else{
            module.enumerateSymbols().forEach(function(edata){
                if (inputMethod.length>0){
                    if(edata.name.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                        return;
                    }
                }
                cnt+=1;
                msg["data"]="module:"+module.name+"----symbolName:"+edata.name+"----address:"+edata.address+"----type:"+edata.type;
                send(msg)
            });
        }
    });
}

function dumpPtr(postdata){
    var inputModule=postdata["moduleName"];
    var inputAddress=postdata["address"];
    var dumpType=postdata["dumpType"];
    var size=postdata["size"];
    var msg= initMessage()
    console.log("enter js dumpPtr")
    if(inputModule && inputModule.length>0){
        var moduleBase=Module.findBaseAddress(inputModule);
        if(!moduleBase){
            msg["data"]="not found "+inputModule;
            send(msg)
            return;
        }
        var dumpAddr= moduleBase.add(inputAddress);
        if(dumpType=="hexdump"){
            msg["data"]="base:"+moduleBase+",dump address:"+dumpAddr+"\n"+hexdump(ptr(dumpAddr),{length:size});
        }else if(dumpType=="string"){
            msg["data"]="base:"+moduleBase+",dump address:"+dumpAddr+"\n"+ ptr(dumpAddr).readCString();
        }
        send(msg);
    }else{
        if(dumpType=="hexdump"){
            msg["data"]="dump address:"+ptr(inputAddress)+"\n"+hexdump(ptr(inputAddress),{length:size});
        }else if(dumpType=="string"){
            msg["data"]="dump address:"+ptr(inputAddress)+"\n"+ ptr(inputAddress).readCString();
        }
        send(msg);
    }
}

function recvMessage(){
    while(true){
        var op=recv('input',function(data){
            console.log("recv enter");
            var payload=data.payload;
            var func= payload["func"];
            if(func=="showMethods"){
                showMethods(payload);
            }else if (func=="showExport"){
                showExport(payload);
            }else if (func=="dumpPtr"){
                dumpPtr(payload);
            }
        });
        op.wait();
    }


}


function main(){
    var msg= initMessage();
    msg["init"]="default.js init hook success";
    send(msg);
    recvMessage();
}


setImmediate(main);