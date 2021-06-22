(function(){
function dis(address, number) {
    for (var i = 0; i < number; i++) {
        var ins = Instruction.parse(address);
        console.log("address:" + address + "--dis:" + ins.toString());
        address = ins.next;
    }
}

function patchFunc(moduleName,address,code){
    console.log(moduleName,address,code);
    var module = Process.getModuleByName(moduleName);
    var base=module.base;
    console.log("+++++++++++patch "+address+"++++++++++++ pre")
    dis(base.add(address), 10);
    Memory.protect(base.add(address), 4, 'rwx');
    base.add(address).writeByteArray(code);
    console.log("+++++++++++patch "+address+"++++++++++++ over")
    dis(base.add(address).add(0x1), 10);
}

function main(){
    var patchJson='{PATCHLIST}';
    console.log("patchJson:",patchJson);
    var patchs=JSON.parse(patchJson);
    for(var item in patchs){
        var patchdata=patchs[item];
        var addr=ptr(parseInt(item,16))
        var code=[];
        var codestr=patchdata["code"];
        var moduleName=patchdata["moduleName"];
        var codesplit=codestr.split(" ");
        for(var idx in codesplit){
            code.push(parseInt("0x"+codesplit[idx],16));
        }
        patchFunc(moduleName,addr,code);
    }
}

setImmediate(main)
})()
