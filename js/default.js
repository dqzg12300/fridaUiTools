//默认使用,后面再搞点默认hook功能



function registGson() {
    // const dexbase64 = gjson_dex;
    // DMLog.i('registGson', 'entry: ' + dexbase64.length);
    //
    // var application = Java.use("android.app.Application");
    // const bytes = new Buffer(dexbase64, 'base64');
    // const dexpath = application.$f.cacheDir + '/gson.jar';
    // const f = new File(dexpath, 'wb+');
    // f.write(bytes.buffer as ArrayBuffer);
    // f.flush()
    // f.close()
    try {
        let dexpath = '/data/local/tmp/r0gson.dex';
        Java.openClassFile(dexpath).load();
    }
    catch (e) {
        var message={};
        message["jsname"]="default";
        message["data"]='exception,请上传gson' + e.toString();
        send(message);
    }
}

function parseObject(data) {
    try {
        const declaredFields = data.class.getDeclaredFields();
        let res = {};
        for (let i = 0; i < declaredFields.length; i++) {
            const field = declaredFields[i];
            field.setAccessible(true);
            const type = field.getType();
            let fdata = field.get(data);
            if (null != fdata) {
                if (type.getName() != "[B") {
                    fdata = fdata.toString();
                }
                else {
                    fdata = Java.array('byte', fdata);
                    fdata = JSON.stringify(fdata);
                }
            }
            // @ts-ignore
            res[field.getName()] = fdata;
        }
        return JSON.stringify(res);
    }
    catch (e) {
        return "parseObject except: " + e.toString();
    }
}

function toJSONString(obj) {
    if (null == obj) {
        return "obj is null";
    }
    let resstr = "";
    let GsonBuilder = null;
    try {
        GsonBuilder = Java.use('com.r0ysue.gson.Gson');
    }
    catch (e) {
        registGson();
        GsonBuilder = Java.use('com.r0ysue.gson.Gson');
    }
    if (null != GsonBuilder) {
        try {
            const gson = GsonBuilder.$new();
            resstr = gson.toJson(obj);
        }
        catch (e) {
            var message={};
            message["jsname"]="default";
            message["data"]='gson.toJson exceipt: ' + e.toString();
            send(message);
            resstr = parseObject(obj);
        }
    }
    return resstr;
}

(function(){

function klog(data){
    var message={};
    message["jsname"]="default";
    message["data"]=data;
    send(message);
}

function klogData(data,key,value){
    var message={};
    message["jsname"]="default";
    message["data"]=data;
    message[key]=value;
    send(message);
}

//查找java的函数
function showMethods(postdata){
    var inputClass=postdata["className"];
    var inputMethod=postdata["methodName"];
    var hasMethod=postdata["hasMethod"];

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
                klog("className:"+className)
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
                    klog("className:"+className+"----method:"+methodName)
                }
            }catch(ex){

            }
        })
        klog("find count:"+cnt);
    });
}


//查找so的符号
function showExport(postdata){
    var inputModule=postdata["moduleName"];
    var inputMethod=postdata["methodName"];
    var showType=postdata["showType"];
    var hasMethod=postdata["hasMethod"];
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
                klog("module:"+module.name)
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
                klog("module:"+module.name+"----exportName:"+edata.name+"----address:"+edata.address+"----type:"+edata.type)
            });
        }else{
            module.enumerateSymbols().forEach(function(edata){
                if (inputMethod.length>0){
                    if(edata.name.toUpperCase().indexOf(inputMethod.toUpperCase())<0){
                        return;
                    }
                }
                cnt+=1;
                klog("module:"+module.name+"----symbolName:"+edata.name+"----address:"+edata.address+"----type:"+edata.type)
            });
        }
    });
}

function dumpPtr(postdata){
    var inputModule=postdata["moduleName"];
    var inputAddress=postdata["address"];
    var dumpType=postdata["dumpType"];
    var size=postdata["size"];
    console.log("enter js dumpPtr")
    if(inputModule && inputModule.length>0){
        var moduleBase=Module.findBaseAddress(inputModule);
        if(!moduleBase){
            klog("not found "+inputModule)
            return;
        }
        var dumpAddr= moduleBase.add(inputAddress);
        if(dumpType=="hexdump"){
            klog("base:"+moduleBase+",dump address:"+dumpAddr+"\n"+hexdump(ptr(dumpAddr),{length:size}))
        }else if(dumpType=="string"){
            klog("base:"+moduleBase+",dump address:"+dumpAddr+"\n"+ ptr(dumpAddr).readCString())
        }
    }else{
        if(dumpType=="hexdump"){
            klog("dump address:"+ptr(inputAddress)+"\n"+hexdump(ptr(inputAddress),{length:size}))
        }else if(dumpType=="string"){
            klog("dump address:"+ptr(inputAddress)+"\n"+ ptr(inputAddress).readCString());
        }
    }
}

function dumpSo(postdata){
    Java.perform(function () {
        var currentApplication = Java.use("android.app.ActivityThread").currentApplication();
        var dir = currentApplication.getApplicationContext().getFilesDir().getPath();
        var libso = Process.getModuleByName(postdata["moduleName"]);
        klog("[name]:"+ libso.name);
        klog("[base]:"+ libso.base);
        klog("[size]:"+ ptr(libso.size));
        klog("[path]:"+ libso.path);
        var file_path = dir + "/" + libso.name + "_" + libso.base + "_" + ptr(libso.size) + ".so";
        var file_handle = new File(file_path, "wb");
        if (file_handle && file_handle != null) {
            Memory.protect(ptr(libso.base), libso.size, 'rwx');
            var libso_buffer = ptr(libso.base).readByteArray(libso.size);
            file_handle.write(libso_buffer);
            file_handle.flush();
            file_handle.close();
            klog("[dump]:"+ file_path);
        }
    });
}

function dumpFart(postdata){
    var tp=postdata["type"];
    var className=postdata["className"];
    if(tp==1){
        console.log(dump_class);
    }else if(tp==2){
        console.log(fart);
    }
}

function searchInfo(postdata){
    Java.perform(function(){
        var baseName=postdata["baseName"];
        var searchType=postdata["type"];
        var appinfo={};
        appinfo["type"]=searchType;
        var count=0;
        if(searchType=="export"){
            var module=Process.getModuleByName(baseName);
            var exports=module.enumerateExports();
            appinfo["export"]=exports;
            count=exports.length;
        }else if(searchType=="symbol"){
            var module=Process.getModuleByName(baseName);
            var symbols=module.enumerateSymbols();
            appinfo["symbol"]=symbols;
            count=symbols.length;
        }else if(searchType=="method"){
            var classModel=Java.use(baseName);
            var methods=classModel.class.getDeclaredMethods();
            appinfo["method"]=[]
            methods.forEach(function (method){
                var methodName = method.getName();
                appinfo["method"].push(methodName);
            });
            count=methods.length;
        }
        klogData("appinfo_search count:"+count,"appinfo_search",JSON.stringify(appinfo))
    });
}


function arraybuffer2hexstr(buffer) {
    var hexArr = Array.prototype.map.call(
      new Uint8Array(buffer),
      function (bit) {
        return ('00' + bit.toString(16)).slice(-2)
      }
    )
    return hexArr.join(' ');
}

function strToUtf8Bytes(str) {
	const utf8 = [];
	  for (let ii = 0; ii < str.length; ii++) {
		let charCode = str.charCodeAt(ii);
		if (charCode < 0x80) utf8.push(charCode);
		else if (charCode < 0x800) {
		  utf8.push(0xc0 | (charCode >> 6), 0x80 | (charCode & 0x3f));
		} else if (charCode < 0xd800 || charCode >= 0xe000) {
		  utf8.push(0xe0 | (charCode >> 12), 0x80 | ((charCode >> 6) & 0x3f), 0x80 | (charCode & 0x3f));
		} else {
		  ii++;
		  charCode = 0x10000 + (((charCode & 0x3ff) << 10) | (str.charCodeAt(ii) & 0x3ff));
		  utf8.push(
			0xf0 | (charCode >> 18),
			0x80 | ((charCode >> 12) & 0x3f),
			0x80 | ((charCode >> 6) & 0x3f),
			0x80 | (charCode & 0x3f),
		  );
		}
	  }
	  //兼容汉字，ASCII码表最大的值为127，大于127的值为特殊字符
	  for(let jj=0;jj<utf8.length;jj++){
		  var code = utf8[jj];
		  if(code>127){
			  utf8[jj] = code - 256;
		  }
	  }
	  return utf8;
}

function strToHexCharCode(str){
		var hexCharCode = [];
		var chars = ["0","1","2","3","4","5","6","7","8","9","A","B","C","D","E","F"];
		for(var i = 0; i < str.length; i++) {
			  var bit = (str[i] & 0x0f0) >> 4;
			  hexCharCode.push(chars[bit]);
			  var bit = str[i] & 0x0f;
			  hexCharCode.push(chars[bit]);
		}
	   return hexCharCode.join("");
}

function generate_pattern(input, byte_length) {
    var pattern = null;
    var addr = 0;
    var array_buffer = null;
    switch(byte_length)
    {
        case 0:
            return pattern;
        case 1: //byte
            if(input >= 0) //无符号
            {
                addr = Memory.alloc(1)
                Memory.writeU8(addr, input)
                array_buffer = Memory.readByteArray(addr, 1)
                pattern = arraybuffer2hexstr(array_buffer)
            }else{ //有符号
                addr = Memory.alloc(1)
                Memory.writeS8(addr, input)
                array_buffer = Memory.readByteArray(addr, 1)
                pattern = arraybuffer2hexstr(array_buffer)
            }
        break;
        case 2: //short
            if(input >= 0)
            {
                addr = Memory.alloc(2)
                Memory.writeU16(addr, input)
                array_buffer = Memory.readByteArray(addr, 2)
                pattern = arraybuffer2hexstr(array_buffer)
            }else{
                addr = Memory.alloc(2)
                Memory.writeS16(addr, input)
                array_buffer = Memory.readByteArray(addr, 2)
                pattern = arraybuffer2hexstr(array_buffer)
            }
        break;
        case 4:
            if(parseInt(input) == input) //int long
            {
                if(input >= 0)
                {
                    addr = Memory.alloc(4)
                    Memory.writeU32(addr, input)
                    array_buffer = Memory.readByteArray(addr, 4)
                    pattern = arraybuffer2hexstr(array_buffer)
                }else{
                    addr = Memory.alloc(4)
                    Memory.writeS32(addr, input)
                    array_buffer = Memory.readByteArray(addr, 4)
                    pattern = arraybuffer2hexstr(array_buffer)
                }
            }else{ //float
                addr = Memory.alloc(4)
                Memory.writeFloat(addr, input)
                array_buffer = Memory.readByteArray(addr, 4)
                pattern = arraybuffer2hexstr(array_buffer)
            }
        break
        case 8:
            if(parseInt(input) == input) //longlong
            {
                if(input >= 0)
                {
                    addr = Memory.alloc(8)
                    Memory.writeU64(addr, input)
                    array_buffer = Memory.readByteArray(addr, 8)
                    pattern = arraybuffer2hexstr(array_buffer)
                }else{
                    addr = Memory.alloc(8)
                    Memory.writeS64(addr, input)
                    array_buffer = Memory.readByteArray(addr, 8)
                    pattern = arraybuffer2hexstr(array_buffer)
                }
            }else{ //double
                addr = Memory.alloc(8)
                Memory.writeDouble(addr, input)
                array_buffer = Memory.readByteArray(addr, 8)
                pattern = arraybuffer2hexstr(array_buffer)
            }
        break;
        case undefined: //string
            // var encoder = new TextEncoder('utf-8')
            // array_buffer = encoder.encode(input)
            pattern = strToHexCharCode(strToUtf8Bytes(input));
        break
        case "": //string
            // var encoder = new TextEncoder('utf-8')
            // array_buffer = encoder.encode(input)
            pattern = strToHexCharCode(strToUtf8Bytes(input));
        break
        default:
            pattern = 'error'
    }
    return pattern
}

function readValue(addr, input, byte_length) {
    var result = 0;
    var _addr = new NativePointer(addr)

    switch(byte_length)
    {
        case 1: //byte
            if(input >= 0) //无符号
            {
                result = Memory.readU8(_addr)
            }else{ //有符号
                result = Memory.readS8(_addr)
            }
        break;
        case 2: //short
            if(input >= 0)
            {
                result = Memory.readU16(_addr)
            }else{
                result = Memory.readS16(_addr)
            }
        break;
        case 4:
            if(parseInt(input) == input) //int long
            {
                if(input >= 0)
                {
                    result = Memory.readU32(_addr)
                }else{
                    result = Memory.readS32(_addr)
                }
            }else{ //float
                result = Memory.readFloat(_addr)
            }
        break
        case 8:
            if(parseInt(input) == input) //longlong
            {
                if(input >= 0)
                {
                    result = Memory.readU64(_addr)
                }else{
                    result = Memory.readS64(_addr)
                }
            }else{ //double
                result = Memory.readDouble(_addr)
            }
        break;
        case undefined: //string
            result = Memory.readUtf8String(_addr)
        break
        default:
            pattern = 'error'
    }
    return result;
}

function init_scan_range() {
    var buffer_length = 1024
    var result = []

    var addr = Module.findExportByName('libc.so', 'popen')
    var popen = new NativeFunction(addr, 'pointer', ['pointer', 'pointer']);

    addr = Module.findExportByName('libc.so', 'fgets')
    var fgets = new NativeFunction(addr, "pointer", ["pointer", "int", "pointer"]);

    addr = Module.findExportByName('libc.so', 'pclose')
    var pclose = new NativeFunction(addr, "int", ["pointer"]);

    var pid = Process.id
    var command = 'cat /proc/' + pid + '/maps |grep LinearAlloc'
    var pfile = popen(Memory.allocUtf8String(command), Memory.allocUtf8String('r'))
    if(pfile == null)
    {
        console.log("popen open failed...");
        return;
    }

    var buffer = Memory.alloc(buffer_length);

    while (fgets(buffer, buffer_length, pfile) > 0) {
        var str = Memory.readUtf8String(buffer);
        result.push([ptr(parseInt(str.substr(0, 8), 16)), ptr(parseInt(str.substr(9, 8), 16))])
    }
    pclose(pfile);
    return result
}

var g_data = {};
var init_value = 0;
var init_byte_length = 0;


function new_scan_by_addr(addr_start, addr_end,bak, input, byte_length) {
    var m_count = 0
    g_data = {}
    init_value = input
    init_byte_length = byte_length

    var _addr_start = new NativePointer(addr_start)
    var _addr_end = new NativePointer(addr_end)
    var pattern = generate_pattern(init_value, init_byte_length)
    if(pattern == 'error')
    {
        var data="ERROR:The byte_length can only be 1, 2, 4, 8 and undefined?";
        klogData(data,"scanlog",data);
        return;
    }
    if(pattern==null){
        var data="pattern is null"
        klogData(data,"scanlog",data);
        return;
    }
    var data="new_scan_by_protect scanSync "+_addr_start+" "+(_addr_end - _addr_start)+" "+pattern;
    klogData(data,"scanlog",data);
    var searchResult_list = Memory.scanSync(_addr_start, _addr_end - _addr_start, pattern)
    for(index in searchResult_list)
    {
        g_data[searchResult_list[index].address] = input
    }
    var scanInfoList=[];
    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            var scanInfo = {};
            scanInfo.key=key;
            scanInfo.value=g_data[key];
            scanInfo.bak=bak;
            scanInfoList.push(scanInfo);
            // klog("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    var data=JSON.stringify(scanInfoList);
    klogData(data,"scanInfoList",data)
    return m_count;
}

function new_scan_by_protect(protection,bak, input, byte_length) {
    var m_count = 0
    var searchResult_list = []

    g_data = {}
    init_value = input
    init_byte_length = byte_length

    var pattern = generate_pattern(init_value, init_byte_length)
    if(pattern == 'error')
    {
        var data="ERROR:The byte_length can only be 1, 2, 4, 8 and undefined?";
        klogData(data,"scanlog",data);
        return;
    }
    if(pattern==null){
        var data="pattern is null";
        klogData(data,"scanlog",data);
        return;
    }
    var range_list = Process.enumerateRangesSync(protection)
    for(var index in range_list)
    {
        try{
            var data="new_scan_by_protect scanSync "+range_list[index].base+" "+range_list[index].size+" "+pattern;
            klogData(data,"scanlog",data);
            searchResult_list = Memory.scanSync(range_list[index].base, range_list[index].size, pattern)
        }catch(e){
            continue
        }
        for(var index1 in searchResult_list)
        {
            g_data[searchResult_list[index1].address] = input
        }
    }
    m_count  = Object.keys(g_data).length
    var scanInfoList=[];
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            var scanInfo = {};
            scanInfo.key=key;
            scanInfo.value=g_data[key];
            scanInfo.bak=bak;
            scanInfoList.push(scanInfo);
            // klog("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    var data=JSON.stringify(scanInfoList)
    klogData(data,"scanInfoList",data)
    return m_count;
}

function new_scan_by_addr_unknownValue(addr_start, addr_end, reference, byte_length) {
    var m_count = 0
    g_data = {}
    init_value = reference
    init_byte_length = byte_length

    var _addr_start = new NativePointer(addr_start)
    var _addr_end = new NativePointer(addr_end)
    while(_addr_start.toInt32() < _addr_end.toInt32())
    {
        g_data[_addr_start] = readValue(_addr_start, init_value, init_byte_length)
        _addr_start = _addr_start.add(byte_length)
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function new_scan_by_addr_larger(addr_start, addr_end, value, byte_length) {
    var m_count = 0
    g_data = {}
    init_value = value
    init_byte_length = byte_length

    var _addr_start = new NativePointer(addr_start)
    var _addr_end = new NativePointer(addr_end)
    while(_addr_start.toInt32() < _addr_end.toInt32())
    {

        var new_value= readValue(_addr_start, init_value, init_byte_length)
        if(new_value > value)
        {
            g_data[_addr_start] = new_value
        }
        _addr_start = _addr_start.add(byte_length)
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function new_scan_by_addr_littler(addr_start, addr_end, value, byte_length) {
    var m_count = 0
    g_data = {}
    init_value = value
    init_byte_length = byte_length

    var _addr_start = new NativePointer(addr_start)
    var _addr_end = new NativePointer(addr_end)
    while(_addr_start.toInt32() < _addr_end.toInt32())
    {

        var new_value= readValue(_addr_start, init_value, init_byte_length)
        if(new_value < value)
        {
            g_data[_addr_start] = new_value
        }
        _addr_start = _addr_start.add(byte_length)
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function new_scan_by_addr_between(addr_start, addr_end, value1, value2, byte_length) {
    var m_count = 0
    g_data = {}
    init_value = value1
    init_byte_length = byte_length

    var _addr_start = new NativePointer(addr_start)
    var _addr_end = new NativePointer(addr_end)
    while(_addr_start.toInt32() < _addr_end.toInt32())
    {

        var new_value= readValue(_addr_start, init_value, init_byte_length)
        if(new_value >= value1 && new_value <= value2)
        {
            g_data[_addr_start] = new_value
        }
        _addr_start = _addr_start.add(byte_length)
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_equal(value){
    var m_count = 0;

    for(key in g_data)
    {
        var vdata=readValue(key, init_value, init_byte_length);
        console.log(vdata);
        if(vdata != value)
        {
            delete g_data[key]
        }else{
            g_data[key] = value
        }
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_unchange(){
    var m_count = 0;

    for(key in g_data)
    {

        if(readValue(key, init_value, init_byte_length) != g_data[key])
        {
            delete g_data[key]
        }
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_change() {
    var m_count = 0;

    for(key in g_data)
    {
        var new_value = readValue(key, init_value, init_byte_length)
        if(new_value == g_data[key])
        {
            delete g_data[key]
        }else{
            g_data[key] = new_value
        }
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_littler(value) {
    var m_count = 0;

    for(key in g_data)
    {
        var new_value = readValue(key, init_value, init_byte_length)
        if(new_value >= value)
        {
            delete g_data[key]
        }else{
            g_data[key] = new_value
        }
    }

    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_larger(value) {
    var m_count = 0;

    for(key in g_data)
    {
        var new_value = readValue(key, init_value, init_byte_length)
        if(new_value <= value)
        {
            delete g_data[key]
        }else{
            g_data[key] = new_value
        }
    }
    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_between(value1, value2) {
    var m_count = 0;

    for(key in g_data)
    {
        var new_value = readValue(key, init_value, init_byte_length)
        if(new_value >= value1 && new_value <= value2)
        {
            g_data[key] = new_value
        }else{
            delete g_data[key]
        }
    }
    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_increase() {
    var m_count = 0;
    for(key in g_data)
    {
        var new_value = readValue(key, init_value, init_byte_length)
        if(new_value <= g_data[key])
        {
            delete g_data[key]
        }else{
            g_data[key] = new_value
        }
    }
    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function next_scan_decrease() {
    var m_count = 0;

    for(key in g_data)
    {
        var new_value = readValue(key, init_value, init_byte_length)
        if(new_value >= g_data[key])
        {
            delete g_data[key]
        }else{
            g_data[key] = new_value
        }
    }
    m_count  = Object.keys(g_data).length
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

//设置读写断点
function set_read_write_break(addr, size, pattern) {
    //设置异常
    Process.setExceptionHandler(function(details){
            //打印信息，e.g. 打印堆栈，打印发生异常的地址，打印引发异常的地址
            /*
                    type: string specifying one of:
                            abort
                            access-violation
                            guard-page
                            illegal-instruction
                            stack-overflow
                            arithmetic
                            breakpoint
                            single-step
                            system
                    address: address where the exception occurred, as a NativePointer
                    memory: if present, is an object containing:
                            operation: the kind of operation that triggered the exception, as a string specifying either read,  write, or execute
                            address: address that was accessed when the exception occurred, as a NativePointer
                    context: object with the keys pc and sp, which are NativePointer objects specifying EIP/RIP/PC and ESP/RSP/SP, respectively, for ia32/x64/arm. Other processor-specific keys are also available, e.g. eax, rax, r0, x0, etc. You may also update register values by assigning to these keys.
                    nativeContext: address of the OS and architecture-specific CPU context struct, as a NativePointer. This is only exposed as a last resort for edge-cases where context isn’t providing enough details. We would however discourage using this and rather submit a pull-request to add the missing bits needed for your use-case.

            */
            // console.log(details.address)
            var data=JSON.stringify(details);
            klogData(data,"setBreak",data)
            //处理异常
            Memory.protect(addr, size, 'rwx')
            return true;
    })
    //制造异常 <--> 设置读写断点
    var data="setBreak "+addr+" "+size+" "+pattern;
    klogData(data,"outlog",data);
    Memory.protect(addr, size, pattern)
}

function recvMessage(){
    while(true){
        var op=recv('input',function(data){
            klog("recv enter");
            var payload=data.payload;
            var func= payload["func"];
            if(func=="showMethods"){
                showMethods(payload);
            }else if (func=="showExport"){
                showExport(payload);
            }else if (func=="dumpPtr"){
                dumpPtr(payload);
            }else if (func=="searchInfo"){
                searchInfo(payload);
            }else if(func=="dumpSoPtr"){
                dumpSo(payload);
            }else if(func=="fart"){
                dumpFart(payload);
            }else if(func=="newScanProtect"){
                new_scan_by_protect(payload["protect"],payload["bak"],payload["value"], payload["size"]);
            }else if(func=="newScanByAddress"){
                new_scan_by_addr(payload["start"],payload["end"],payload["bak"], payload["value"], payload["size"]);
            }else if(func=="getInfo"){
                var mtype=payload["type"];
                if(mtype=="hexdump"){
                    var res=hexdump(ptr(payload["start"]),{length:payload["size"]});
                    klogData(res,"scan_hexdump",res)
                }else if(mtype=="CString"){
                    var res=ptr(payload["start"]).readCString();
                    klogData(res,"scanlog",res)
                }
            }else if(func=="setBreak"){
                set_read_write_break(ptr(payload["start"]),payload["size"],payload["protect"]);
            }

        });
        op.wait();
    }
}

//动态取一些附加的app信息传给py
function loadAppInfo(){
    Java.perform(function(){
        var appinfo={};
        appinfo["modules"]=Process.enumerateModules();
        appinfo["classes"]=Java.enumerateLoadedClassesSync()
        appinfo["spawn"]="%spawn%"
        klogData("加载appinfo","appinfo",JSON.stringify(appinfo))
    })
}

function main(){
    klogData("","init","default.js init hook success")
    loadAppInfo();
    init_scan_range();
    recvMessage();
}
setImmediate(main);

})();
