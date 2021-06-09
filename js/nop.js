//默认无勾选时使用,后面再搞点默认hook功能

function hook_native() {
    console.log("nop.js hook_native")
}

function hook_java(){
    console.log("nop.js hook_java")
    Java.perform(function(){
    });
}


function main(){
    hook_java();
    hook_native();
}

setImmediate(main);