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
function klog(data,...args){
    for (let item of args){
        data+="\t"+item;
    }
    var message={};
    message["jsname"]="jni_trace_new";
    message["data"]=data;
    send(message);
}

function klogData(data,key,value){
    var message={};
    message["jsname"]="default";
    message["data"]=data;
    if(key==null){
        message["outlog"]=value;
    }else{
        message[key]=value;
    }
    send(message);
}
function klogBreak(data){
    var message={};
    message["jsname"]="default";
    message["data"]=data;
    message["breakout"]=data;
    send(message);
}

//查找java的函数



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
    klog("search:"+input+"\t"+byte_length)
    switch(byte_length)
    {
        case 0:
            return input;
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


function next_scan_key(key){
    // var m_count = 0;
    var vdata=readValue(key, init_value, init_byte_length);
    console.log(vdata);
    if(vdata != value)
    {
        delete g_data[key]
    }else{
        g_data[key] = value
    }
    var scanInfoList=[];
    var scanInfo = {};
    scanInfo.key=key;
    scanInfo.value=g_data[key];
    scanInfo.bak=bak;
    scanInfoList.push(scanInfo);
    var data=JSON.stringify(scanInfoList);
    klogData(data,"scanInfoList",data);
    // console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
    return 1;
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
            // var data="address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '';
        }
    }
    var data=JSON.stringify(scanInfoList);
    klogData(data,"scanInfoList",data);
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


function normalizeDexLocation(rawLocation) {
    if (rawLocation === null || rawLocation === undefined) {
        return '';
    }
    try {
        if (typeof rawLocation === 'string') {
            return rawLocation;
        }
        return rawLocation.toString();
    } catch (e) {
        return '' + rawLocation;
    }
}

function classifyDexLocation(location) {
    if (!location) {
        return 'unknown';
    }
    var lower = location.toLowerCase();
    if (lower.indexOf('memory') >= 0 || lower.indexOf('anonymous') >= 0) {
        return 'memory';
    }
    if (lower.indexOf('.apk') >= 0) {
        return 'apk';
    }
    if (lower.indexOf('.jar') >= 0) {
        return 'jar';
    }
    if (lower.indexOf('.dex') >= 0) {
        return 'dex';
    }
    return 'unknown';
}

function collectDexEntries() {
    var dexMap = {};
    var result = [];

    function pushDex(location, classLoaderName, source) {
        var normalizedLocation = normalizeDexLocation(location);
        var key = normalizedLocation + '::' + classLoaderName;
        if (normalizedLocation.length <= 0 || dexMap[key]) {
            return;
        }
        dexMap[key] = true;
        var dexType = classifyDexLocation(normalizedLocation);
        result.push({
            "location": normalizedLocation,
            "classLoader": classLoaderName,
            "source": source,
            "type": dexType,
            "isMemoryDex": dexType == 'memory'
        });
    }

    var application = null;
    try {
        var ActivityThread = Java.use('android.app.ActivityThread');
        application = ActivityThread.currentApplication();
    } catch (e) {}

    if (application) {
        var context = application.getApplicationContext();
        var packageCodePath = '';
        try {
            packageCodePath = context.getPackageCodePath().toString();
        } catch (e) {}
        if (packageCodePath.length > 0) {
            pushDex(packageCodePath, 'Application', 'context.getPackageCodePath');
        }

        try {
            var appInfo = context.getApplicationInfo();
            var sourceDir = normalizeDexLocation(appInfo.sourceDir.value);
            var publicSourceDir = normalizeDexLocation(appInfo.publicSourceDir.value);
            if (sourceDir.length > 0) {
                pushDex(sourceDir, 'ApplicationInfo', 'applicationInfo.sourceDir');
            }
            if (publicSourceDir.length > 0) {
                pushDex(publicSourceDir, 'ApplicationInfo', 'applicationInfo.publicSourceDir');
            }
            try {
                var splitSourceDirs = appInfo.splitSourceDirs.value;
                if (splitSourceDirs) {
                    for (var splitIndex = 0; splitIndex < splitSourceDirs.length; splitIndex++) {
                        pushDex(splitSourceDirs[splitIndex], 'ApplicationInfo', 'applicationInfo.splitSourceDirs');
                    }
                }
            } catch (e) {}
        } catch (e) {}
    }

    try {
        var BaseDexClassLoader = Java.use('dalvik.system.BaseDexClassLoader');
        var DexPathListElement = Java.use('dalvik.system.DexPathList$Element');
        Java.enumerateClassLoaders({
            onMatch: function (loader) {
                try {
                    if (!Java.cast(loader, BaseDexClassLoader)) {
                        return;
                    }
                } catch (e) {
                    return;
                }
                try {
                    var loaderName = loader.toString();
                    var pathList = loader.pathList.value;
                    var dexElements = pathList.dexElements.value;
                    if (!dexElements) {
                        return;
                    }
                    for (var i = 0; i < dexElements.length; i++) {
                        var element = Java.cast(dexElements[i], DexPathListElement);
                        var dexFile = null;
                        var location = '';
                        try {
                            dexFile = element.dexFile.value;
                        } catch (e) {}
                        if (dexFile) {
                            try {
                                location = dexFile.toString();
                            } catch (e) {}
                            if (!location) {
                                try {
                                    location = dexFile.getName();
                                } catch (e) {}
                            }
                        }
                        if (!location) {
                            try {
                                var path = element.path.value;
                                location = normalizeDexLocation(path);
                            } catch (e) {}
                        }
                        if (!location) {
                            try {
                                var file = element.file.value;
                                location = normalizeDexLocation(file);
                            } catch (e) {}
                        }
                        pushDex(location, loaderName, 'BaseDexClassLoader');
                    }
                } catch (e) {}
            },
            onComplete: function () {}
        });
    } catch (e) {}

    return result;
}

//动态取一些附加的app信息传给py
function loadAppInfo(){
    var appinfo={};
    appinfo["modules"] = Process.enumerateModules();
    appinfo["classes"] = [];
    appinfo["dexes"] = [];
    appinfo["spawn"] = "%spawn%";
    appinfo["runtime"] = {
        "processId": Process.id,
        "arch": Process.arch,
        "platform": Process.platform,
        "pointerSize": Process.pointerSize,
        "pageSize": Process.pageSize,
        "codeSigningPolicy": Process.codeSigningPolicy,
        "debuggerAttached": Process.isDebuggerAttached(),
        "currentDir": Process.getCurrentDir(),
        "homeDir": Process.getHomeDir(),
        "tmpDir": Process.getTmpDir(),
        "moduleCount": appinfo["modules"].length,
        "classCount": 0,
        "dexCount": 0
    };
    if (typeof Java === 'undefined' || !Java.available) {
        appinfo["javaUnavailable"] = true;
        return appinfo;
    }
    Java.perform(function(){
        appinfo["classes"]=Java.enumerateLoadedClassesSync();
        appinfo["runtime"]["classCount"] = appinfo["classes"].length;
        try {
            var ActivityThread = Java.use('android.app.ActivityThread');
            var ApplicationInfo = Java.use('android.content.pm.ApplicationInfo');
            var Build = Java.use('android.os.Build');
            var BuildVersion = Java.use('android.os.Build$VERSION');
            var application = ActivityThread.currentApplication();
            if (application) {
                var context = application.getApplicationContext();
                var packageName = context.getPackageName();
                var packageManager = context.getPackageManager();
                var packageInfo = packageManager.getPackageInfo(packageName, 0);
                var appMeta = context.getApplicationInfo();
                var flags = appMeta.flags.value;
                var label = packageManager.getApplicationLabel(appMeta);
                var supportedAbis = Build.SUPPORTED_ABIS.value;
                var minSdkVersion = '';
                try {
                    minSdkVersion = appMeta.minSdkVersion.value;
                } catch (e) {}
                var longVersionCode = '';
                try {
                    longVersionCode = packageInfo.getLongVersionCode();
                } catch (e) {
                    longVersionCode = packageInfo.versionCode.value;
                }
                appinfo["package"] = {
                    "packageName": packageName,
                    "processName": appMeta.processName.value,
                    "appLabel": label ? label.toString() : '',
                    "versionName": packageInfo.versionName.value,
                    "versionCode": '' + longVersionCode,
                    "targetSdk": '' + appMeta.targetSdkVersion.value,
                    "minSdk": '' + minSdkVersion,
                    "uid": '' + appMeta.uid.value,
                    "enabled": !!appMeta.enabled.value,
                    "debuggable": (flags & ApplicationInfo.FLAG_DEBUGGABLE.value) !== 0,
                    "allowBackup": (flags & ApplicationInfo.FLAG_ALLOW_BACKUP.value) !== 0,
                    "testOnly": (flags & ApplicationInfo.FLAG_TEST_ONLY.value) !== 0,
                    "sourceDir": appMeta.sourceDir.value,
                    "publicSourceDir": appMeta.publicSourceDir.value,
                    "dataDir": appMeta.dataDir.value,
                    "nativeLibraryDir": appMeta.nativeLibraryDir.value,
                    "taskAffinity": appMeta.taskAffinity.value,
                    "className": appMeta.className.value,
                    "brand": Build.BRAND.value,
                    "model": Build.MODEL.value,
                    "device": Build.DEVICE.value,
                    "androidVersion": BuildVersion.RELEASE.value,
                    "sdkInt": '' + BuildVersion.SDK_INT.value,
                    "supportedAbis": supportedAbis ? supportedAbis.join(', ') : ''
                };
            }
        } catch (e) {
            appinfo["packageError"] = e.toString();
        }
        try {
            appinfo["dexes"] = collectDexEntries();
            appinfo["runtime"]["dexCount"] = appinfo["dexes"].length;
        } catch (e) {
            appinfo["dexes"] = [];
            appinfo["dexError"] = e.toString();
            appinfo["runtime"]["dexCount"] = 0;
        }
    })
    return appinfo;
}

function main(){
    klog("init","default.js init hook success")
    // 异步获取 Java 类列表，通过 send 消息传回 Python
    var javaCheck = (typeof Java !== 'undefined') ? "Java defined" : "Java undefined";
    var javaAvail = (typeof Java !== 'undefined' && Java.available) ? "available" : "not available";
    klog("init", "Java check: " + javaCheck + ", " + javaAvail)
    if (typeof Java !== 'undefined' && Java.available) {
        klog("init", "entering Java.perform for class_list")
        Java.perform(function(){
            try {
                var classes = Java.enumerateLoadedClassesSync().filter(function(c){
                    return c && !c.startsWith('[');
                });
                var msg = {};
                msg["jsname"] = "default";
                msg["data"] = "class_list loaded: " + classes.length;
                msg["class_list"] = classes;
                send(msg);
            } catch(e) {
                klog("init", "class_list error: " + e.toString());
            }
        });
    } else {
        klog("init", "Java not available, skipping class_list")
    }
}
setImmediate(main);

// 监听 Python 端的 refresh_class_list 请求
function listenClassListRefresh() {
    recv('refresh_class_list', function() {
        if (typeof Java !== 'undefined' && Java.available) {
            Java.perform(function(){
                try {
                    var classes = Java.enumerateLoadedClassesSync().filter(function(c){
                        return c && !c.startsWith('[');
                    });
                    var msg = {};
                    msg["jsname"] = "default";
                    msg["data"] = "class_list refreshed: " + classes.length;
                    msg["class_list"] = classes;
                    send(msg);
                } catch(e) {
                    klog("class_list refresh error: " + e.toString());
                }
            });
        }
        // 重新注册监听，recv 是一次性的
        listenClassListRefresh();
    });
}
listenClassListRefresh();


const arch = Process.arch;
const thumb_erase_maskcode = 0xfffffffffffe

var breakpoint_desc = {
    "breakpoint_ins" :'',
    "writer" : null,
    "thumb_writer":null,
    "thumb_breakpoint_ins":'00be'
    //长度 thumb恒为2 arm,arm64恒为4
};

(_=>{
    switch (arch) {
        case "arm64":
            breakpoint_desc["breakpoint_ins"] = '000020d4'
            breakpoint_desc["writer"] = Arm64Writer
            // break_mem.writeByteArray(hex2buf(breakpoint_ins))
            break
        case "arm":
            breakpoint_desc["breakpoint_ins"] = '700020e1'
            breakpoint_desc["writer"] = ArmWriter
            breakpoint_desc["thumb_writer"]=ThumbWriter
            break
        default:
            klogData(arch,+' not support')
    }
})()

function buf2hex(buffer) { // buffer is an ArrayBuffer
    return Array.prototype.map.call(new Uint8Array(buffer), x => ('00' + x.toString(16)).slice(-2)).join('');
}
function hex2buf(hex){
    return  new Uint8Array(hex.match(/[\da-f]{2}/gi).map(function (h) {return parseInt(h, 16)})).buffer
}

/**
 * @param {NativePointer} pc_addr
 * @returns 是否为thumb,true为thunb,false不是thumb
 * fixme 因为pc拿到的地址恒为偶数，所以不得不用lr来判断
 */
function check_pc_thumb(pc_addr){
    return (pc_addr % 2 == 1)
}


/**
 * @param pc_addr 目标断点
 * @returns {boolean} 返回真是断点，返回假不是断点
 */
function checkbreakpoint(pc_addr){
    switch(arch){
        case "arm64":
            return buf2hex(rpc.exports.readdata(pc_addr,4)) === breakpoint_desc["breakpoint_ins"]
        case "arm":
            if(check_pc_thumb(pc_addr)){
                return buf2hex(rpc.exports.readdata(pc_addr.and(thumb_erase_maskcode),2)) === breakpoint_desc["breakpoint_ins"]
            }else{
                return buf2hex(rpc.exports.readdata(pc_addr,4)) === breakpoint_desc["thumb_breakpoint_ins"]
            }
        default:
            klogData("","scanlog",arch+' not support')
    }
}
/**
 * 通过不同的writer来写不同的断点
 * 原理是先恢复内存保护然后设置软断点
 * 自己的断点被访问后，恢复断点，设置内存保护
 * cmd 1
 *
 * @param break_info 断点信息
 * @param writer 不同的writer
 * @returns {boolean} 返回真假 真表示处理 假表示异常未处理
 */
function resume_pagebreak_write_softbreakpoint(break_info,writer){

    let pc_addr = ptr(break_info['current_pc']);
    let lr_addr = ptr(break_info['current_lr']);

    //如果是thumb指令集地址加1，arm和arm64指令集不需要加1
    if(check_pc_thumb(lr_addr)){
        pc_addr = pc_addr.add(1)

    }
    const break_page_info = break_info['break_page_info'];
    //获取当前指令长度
    const size = Instruction.parse(pc_addr).size;
    //恢复原始的内存保护
    rpc.exports.setpageprotect(break_page_info[0],break_page_info[1])
    //把要写的断点移到下个条指令
    pc_addr = pc_addr.add(size)
    let ins_writer = new writer(pc_addr);
    if(check_pc_thumb(lr_addr)){
        ins_writer = new breakpoint_desc["thumb_writer"](pc_addr.and(thumb_erase_maskcode))
    }

    const store_size = Instruction.parse(pc_addr).size;

    //保存断点消息
    let send_dict = {};
    send_dict['break_addr'] = pc_addr
    send_dict['break_len'] = store_size
    send_dict['ins_content'] = buf2hex(rpc.exports.readdata(pc_addr.and(thumb_erase_maskcode),store_size))
    send_dict['__tag'] = 'set_soft_breakpoint'
    klogBreak(send_dict)

    //等待返回结果
    let payload = null;
    const op = recv('set_soft_breakpoint_ret', function (value) {
        payload = value.payload
    });
    op.wait()
    //写断点
    if(!checkbreakpoint(pc_addr)){
        Memory.patchCode(pc_addr, store_size, function (code) {
            //不同arch的断点写法不一样
            //todo 修复在libc中写代码段崩溃的问题
            switch(arch){
                case "arm64":
                    ins_writer.putBytes(hex2buf(breakpoint_desc["breakpoint_ins"]))
                    ins_writer.flush()
                    break
                case "arm":
                    if(check_pc_thumb(pc_addr)){
                        //thumb
                        ins_writer.putBytes(hex2buf(breakpoint_desc["thumb_breakpoint_ins"]))
                        ins_writer.flush()
                    }else{
                        ins_writer.putBytes(hex2buf(breakpoint_desc["breakpoint_ins"]))
                        ins_writer.flush()
                    }
                    break
                default:
                    klogData("","scanlog",arch+' not support')
            }
        });
    }


    return true
}

/**
 * 通过不同的writer来恢复不同的断点
 * 重新设置页面保护
 * 自己的断点被访问后，恢复断点，设置内存保护
 * cmd 2
 * @param soft_breakpoint_info 断点信息
 * @param writer 不同的writer
 * @returns {boolean} 真表示异常处理 假表示异常没被处理
 */
function resume_softbreakpoint_set_pagebreak(soft_breakpoint_info,writer){

    let pc_addr = ptr(soft_breakpoint_info['break_addr']);
    const size = soft_breakpoint_info['break_len'];
    const content = hex2buf(soft_breakpoint_info['ins_content']); // arraybuffer
    const break_page_info = soft_breakpoint_info['break_page_info'];
    let ins_writer = null
    switch(arch){
        case "arm64":
            ins_writer = new writer(pc_addr);
            break
        case "arm":
            if(check_pc_thumb(pc_addr)){
                ins_writer = new breakpoint_desc["thumb_writer"](pc_addr.and(thumb_erase_maskcode))
            }
            break
        default:
            klogData("","scanlog",arch+' not support')
    }

    //恢复原始字节码
    Memory.patchCode(pc_addr, size, function (code) {
        ins_writer.putBytes(content)
        ins_writer.flush()
    });

    //设置内存保护
    rpc.exports.setpageprotect(break_page_info[0],'---')
    const send_dict = {};
    send_dict['__tag'] = 'resume_soft_breakpoint'
    send_dict['addr'] = pc_addr
    klogBreak(send_dict)

    let info_ret = null;
    const op = recv('resume_soft_breakpoint_ret', function (value) {
        info_ret = value.payload
    });
    op.wait()
    return true
}

/**
 *
 * @param break_info 断点信息
 * @param writer writer
 * @param details 异常信息
 * @returns {boolean}
 */
function  resume_pagebreak_write_softbreakpoint_and_show(break_info,writer,details){
    //先调用cmd1的方法 然后把断点信息发送给py脚本
    const ret = resume_pagebreak_write_softbreakpoint(break_info, writer);
    const data_addr = ptr(break_info['break_addr']);
    let lr_addr = ptr(break_info['current_lr']);
    const data = buf2hex(rpc.exports.readdata(data_addr, break_info['break_len']));
    let _pc = ptr(details['address']);
    if(check_pc_thumb(lr_addr)){
        _pc = _pc.add(1)
    }
    const ins = Instruction.parse(_pc);
    const symbol = DebugSymbol.fromAddress(_pc);
    details['data'] = data
    details['symbol'] = symbol
    details['ins'] = ins.toString()
    details["operands"] = ins["operands"]
    details['__tag'] = "show_details"
    klogBreak(details)
    return ret
}

//返回为true false 表示这个异常是否被处理
function handle_cmd(info,details){

    const cmd = info['cmd'];
    switch (cmd){
        case 1:
            return resume_pagebreak_write_softbreakpoint(info,breakpoint_desc["writer"])
        case 2:
            return resume_softbreakpoint_set_pagebreak(info,breakpoint_desc["writer"])
        case 3:
            return resume_pagebreak_write_softbreakpoint_and_show(info,breakpoint_desc["writer"],details)
        case 100:
            return false
    }
}
rpc.exports.getdevicearch=function(){
    return Process.arch;
}

rpc.exports.getplatform=function(){
    return Process.platform;
}
rpc.exports.getpointersize=function(){
    return Process.pointerSize;
}

rpc.exports.getpagesize=function(){
    return Process.pageSize;
}
rpc.exports.getmodule=function(name){
    return Process.findModuleByName(name);
}

rpc.exports.setexceptionhandler=function(){
    //设置异常处理handler
   Process.setExceptionHandler(function(details){
       let break_info = null;
       details['__tag'] = "exception"
       klogBreak(details)
       const op = recv('exception_ret', function (value) {
           break_info = value.payload
       });
       op.wait()
        return  handle_cmd(break_info,details)
   })
}

function showMethods(inputClass,inputMethod,hasMethod){
    klog("enter showMethods")
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
function showExport(inputModule,inputMethod,showType,hasMethod){
    var cnt=0;
    klog("enter showExport")
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

function dumpPtr(inputModule,inputAddress,dumpType,size){
    klog("enter dumpPtr")
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

function isNativeSharedObjectModule(module) {
    if (!module) {
        return false;
    }
    var moduleName = '';
    var modulePath = '';
    try {
        moduleName = module.name ? module.name.toString().toLowerCase() : '';
    } catch (e) {}
    try {
        modulePath = module.path ? module.path.toString().toLowerCase() : '';
    } catch (e) {}
    return moduleName.indexOf('.so') >= 0 || modulePath.endsWith('.so');
}

function searchInfo(searchType,baseName){
    klog("enter searchInfo",searchType,baseName);
    var appinfo={};
    appinfo["type"]=searchType;
    klog(searchType+" "+baseName);
    var count=0;
    if(searchType=="export"){
        var module=Process.getModuleByName(baseName);
        if (!isNativeSharedObjectModule(module)) {
            appinfo["export"]=[];
            appinfo["error"]="module is not a native shared object";
            return appinfo;
        }
        var exports=module.enumerateExports();
        appinfo["export"]=exports;
        count=exports.length;
    }else if(searchType=="symbol"){
        var module=Process.getModuleByName(baseName);
        if (!isNativeSharedObjectModule(module)) {
            appinfo["symbol"]=[];
            appinfo["error"]="module is not a native shared object";
            return appinfo;
        }
        var symbols=module.enumerateSymbols();
        appinfo["symbol"]=symbols;
        count=symbols.length;
    }else if(searchType=="method"){
        Java.performNow(function () {
            var classModel=Java.use(baseName);
            var methods=classModel.class.getDeclaredMethods();
            appinfo["method"]=[]
            methods.forEach(function (method){
                var methodName = method.getName();
                appinfo["method"].push(methodName);
            });
            count=methods.length;
        })
    }
    return appinfo;
}

function listClasses() {
    var result = [];
    if (typeof Java === 'undefined' || !Java.available) {
        return result;
    }
    Java.performNow(function () {
        for (var attempt = 0; attempt < 10; attempt++) {
            result = Java.enumerateLoadedClassesSync().filter(function (className) {
                return className && !className.startsWith('[');
            });
            if (result.length > 0) {
                break;
            }
            Thread.sleep(0.2);
        }
    });
    return result;
}

rpc.exports.loadappinfo=loadAppInfo;
rpc.exports.listclasses=listClasses;
rpc.exports.showmethods=showMethods;
rpc.exports.showexports=showExport;
rpc.exports.dumpptr=dumpPtr;
rpc.exports.dumpPtr=dumpPtr;
rpc.exports.searchinfo=searchInfo;
rpc.exports.new_scan_by_protect=new_scan_by_protect;
rpc.exports.new_scan_by_addr=new_scan_by_addr;
rpc.exports.next_scan_key=next_scan_key;
rpc.exports.next_scan_equal=next_scan_equal;

rpc.exports.findmodule=function(so_name) {
    var libso = Process.findModuleByName(so_name);
    return libso;
}
rpc.exports.dumpmodule= function(so_name) {
    var libso = Process.findModuleByName(so_name);
    if (libso == null) {
        return -1;
    }
    Memory.protect(ptr(libso.base), libso.size, 'rwx');
    var libso_buffer = ptr(libso.base).readByteArray(libso.size);
    libso.buffer = libso_buffer;
    return libso_buffer;
}

function safeReadCString(address, sizeLimit) {
    try {
        return ptr(address).readCString(sizeLimit);
    } catch (e) {
        return "";
    }
}

function safeReadUtf8String(address, sizeLimit) {
    try {
        return ptr(address).readUtf8String(sizeLimit);
    } catch (e) {
        return "";
    }
}

function normalizeRangeDetails(rangeInfo) {
    var moduleInfo = null;
    try {
        moduleInfo = Process.findModuleByAddress(rangeInfo.base);
    } catch (e) {
        moduleInfo = null;
    }
    var filePath = "";
    if (rangeInfo.file && rangeInfo.file.path) {
        filePath = rangeInfo.file.path;
    }
    return {
        base: rangeInfo.base.toString(),
        size: rangeInfo.size,
        protection: rangeInfo.protection,
        filePath: filePath,
        moduleName: moduleInfo ? moduleInfo.name : ""
    };
}

function collectDisassembly(startAddress, instructionCount) {
    var result = [];
    var cursor = ptr(startAddress);
    var count = parseInt(instructionCount || 0);
    if (count <= 0) {
        count = 16;
    }
    for (var index = 0; index < count; index++) {
        try {
            var ins = Instruction.parse(cursor);
            var symbol = DebugSymbol.fromAddress(ins.address);
            result.push({
                address: ins.address.toString(),
                mnemonic: ins.mnemonic,
                opStr: ins.opStr,
                size: ins.size,
                text: ins.toString(),
                symbolName: symbol && symbol.name ? symbol.name : "",
                moduleName: symbol && symbol.moduleName ? symbol.moduleName : ""
            });
            cursor = ins.next;
        } catch (e) {
            result.push({
                address: cursor.toString(),
                mnemonic: "invalid",
                opStr: "",
                size: 0,
                text: e.toString(),
                symbolName: "",
                moduleName: ""
            });
            break;
        }
    }
    return result;
}

function scanMatchesInto(results, matches, maxResults) {
    for (var index = 0; index < matches.length; index++) {
        results.push(matches[index].address.toString());
        if (maxResults > 0 && results.length >= maxResults) {
            return true;
        }
    }
    return false;
}

function scanReadableChunks(start, rangeSize, pattern, maxResults) {
    var results = [];
    var chunkSize = 0x40000;
    var pageSize = Process.pageSize || 0x1000;
    var offset = 0;
    while (offset < rangeSize) {
        var currentSize = Math.min(chunkSize, rangeSize - offset);
        var cursor = start.add(offset);
        try {
            var matches = Memory.scanSync(cursor, currentSize, pattern);
            if (scanMatchesInto(results, matches, maxResults)) {
                return results;
            }
        } catch (chunkError) {
            var pageOffset = 0;
            while (pageOffset < currentSize) {
                var pageSizeNow = Math.min(pageSize, currentSize - pageOffset);
                var pageCursor = cursor.add(pageOffset);
                try {
                    var pageMatches = Memory.scanSync(pageCursor, pageSizeNow, pattern);
                    if (scanMatchesInto(results, pageMatches, maxResults)) {
                        return results;
                    }
                } catch (pageError) {
                }
                pageOffset += pageSizeNow;
            }
        }
        offset += currentSize;
    }
    return results;
}

rpc.exports.allmodule= function() {
    return Process.enumerateModules()
}
rpc.exports.arch= function() {
    return Process.arch;
}

rpc.exports.getprotectranges=function(){
    return Process.enumerateRanges("---")
}
rpc.exports.hexdump=function(addr,size){
    return hexdump(ptr(addr),{length:size});
}
rpc.exports.cstring=function(addr){
    return ptr(addr).readCString();
}

rpc.exports.getexportbyname=function(so_name,symbol_name){
    return Module.getExportByName(so_name,symbol_name)
}
rpc.exports.getmodules=function (){
    return Process.enumerateModules();
}

rpc.exports.enumerateranges=function (protection, coalesce){
    var protectionText = protection || "r--";
    var shouldCoalesce = coalesce !== false;
    var ranges = Process.enumerateRanges({
        protection: protectionText,
        coalesce: shouldCoalesce
    });
    return ranges.map(normalizeRangeDetails);
}

rpc.exports.scanrange=function(base, size, pattern, limit){
    var start = ptr(base);
    var rangeSize = parseInt(size || 0);
    var maxResults = parseInt(limit || 0);
    if (rangeSize <= 0) {
        return [];
    }
    return scanReadableChunks(start, rangeSize, pattern, maxResults);
}

rpc.exports.inspectaddress=function(addr, byteCount, instructionCount){
    var target = ptr(addr);
    var readBytes = parseInt(byteCount || 0);
    var insCount = parseInt(instructionCount || 0);
    if (readBytes <= 0) {
        readBytes = 96;
    }
    if (insCount <= 0) {
        insCount = 24;
    }
    var rangeInfo = null;
    var moduleInfo = null;
    var symbolInfo = null;
    try {
        rangeInfo = Process.findRangeByAddress(target);
    } catch (e) {
        rangeInfo = null;
    }
    try {
        moduleInfo = Process.findModuleByAddress(target);
    } catch (e) {
        moduleInfo = null;
    }
    try {
        symbolInfo = DebugSymbol.fromAddress(target);
    } catch (e) {
        symbolInfo = null;
    }
    var filePath = "";
    if (rangeInfo && rangeInfo.file && rangeInfo.file.path) {
        filePath = rangeInfo.file.path;
    }
    return {
        address: target.toString(),
        range: rangeInfo ? {
            base: rangeInfo.base.toString(),
            size: rangeInfo.size,
            protection: rangeInfo.protection,
            filePath: filePath
        } : null,
        module: moduleInfo ? {
            name: moduleInfo.name,
            base: moduleInfo.base.toString(),
            size: moduleInfo.size,
            path: moduleInfo.path
        } : null,
        symbol: symbolInfo ? {
            address: symbolInfo.address ? symbolInfo.address.toString() : target.toString(),
            name: symbolInfo.name || "",
            moduleName: symbolInfo.moduleName || "",
            fileName: symbolInfo.fileName || "",
            lineNumber: symbolInfo.lineNumber || 0
        } : null,
        hexdump: hexdump(target, {length: readBytes}),
        cstring: safeReadCString(target, readBytes),
        utf8: safeReadUtf8String(target, readBytes),
        disassembly: collectDisassembly(target, insCount)
    };
}

rpc.exports.readdata=function(pointer,len){
    return ptr(pointer).readByteArray(len)
}
rpc.exports.setpageprotect=function(addr,flag){
    Memory.protect(ptr(addr),Process.pageSize,flag)
}

})();
