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

function recvMessage(){
    recv('input',function(data){
        console.log("recv enter");
        var payload=data.payload;
        var func= payload["func"];
        if(func=="showMethods"){
            var className=payload["className"];
            var methodName=payload["methodName"];
            showMethods(className,methodName);
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