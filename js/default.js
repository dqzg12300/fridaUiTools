//默认使用,后面再搞点默认hook功能

function initMessage(){
  var message={};
  message["jsname"]="default";
  return message;
}

function hook_native() {
}

function hook_java(){
    Java.perform(function(){
    });
}
//查找java的函数
function showMethods(inputClass,inputMethod){
    var msg= initMessage()
    console.log("enter js showMethods")
    Java.perform(function(){
        var cnt=0;
        Java.enumerateLoadedClassesSync().forEach(function(className){
            if (inputClass.length>0){
                if(className.toUpperCase().indexOf(inputClass.toUpperCase())<0){
                    return;
                }
            }
            // console.log("loaded: "+className);
            try{
                var classModel= Java.use(className);
                var methods=classModel.class.getDeclaredMethods();
                for(var i=0;i<methods.length;i++){
                    var methodName=methods[i].getName()
                    if (inputMethod.length>0){
                        if(methodName.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                            return;
                        }
                    }
                    cnt+=1;
                    msg["data"]="className:"+className+"----method:"+methodName;
                    send(msg)
                }
            }catch(ex){

            }
        })
        msg["data"]="find count:"+cnt;
        send(msg)
    });
}
//查找so的符号
function showExport(inputModule,inputMethod,isExport){
    var msg= initMessage()
    var cnt=0;
    console.log("enter js showExport")
    Process.enumerateModules().forEach(function(module){
        if (inputClass.length>0){
            if(module.name.toUpperCase().indexOf(inputModule.toUpperCase())<0){
                return;
            }
        }
        if(isExport){
            module.enumerateExports().forEach(function(edata){
                if (inputMethod.length>0){
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

function recvMessage(){
    recv('input',function(data){
        console.log("recv enter");
        var payload=data.payload;
        var func= payload["func"];
        if(func=="showMethods"){
            var className=payload["className"];
            var methodName=payload["methodName"];
            showMethods(className,methodName);
        }else if (func=="showExport"){
            var moduleName=payload["moduleName"];
            var methodName=payload["methodName"];
            var isExport=payload["isExport"];
            showMethods(moduleName,methodName,isExport);
        }
    });
}


function main(){
    var msg= initMessage();
    msg["init"]="default.js init hook success";
    send(msg);
    hook_java();
    hook_native();
    recvMessage();
}


setImmediate(main);