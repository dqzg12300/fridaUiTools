
(function(){

function arraybuffer2hexstr(buffer)
{
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


function generate_pattern(input, byte_length)
{
    var pattern = null;
    var addr = 0;
    var array_buffer = null;
    switch(byte_length)
    {
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
        default:
            pattern = 'error'
    }
    return pattern
}

function readValue(addr, input, byte_length)
{
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

function init_scan_range()
{
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

function new_scan_by_addr(addr_start, addr_end, input, byte_length)
{
    var m_count = 0
    g_data = {}
    init_value = input
    init_byte_length = byte_length

    var _addr_start = new NativePointer(addr_start)
    var _addr_end = new NativePointer(addr_end)
    var pattern = generate_pattern(init_value, init_byte_length)
    if(pattern == 'error')
    {
        console.log('ERROR:The byte_length can only be 1, 2, 4, 8 and undefined?')
    }
    var searchResult_list = Memory.scanSync(_addr_start, _addr_end - _addr_start, pattern)
    for(index in searchResult_list)
    {
        g_data[searchResult_list[index].address] = input
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

function new_scan_by_protect(protection, input, byte_length)
{
    var m_count = 0
    var searchResult_list = []

    g_data = {}
    init_value = input
    init_byte_length = byte_length

    var pattern = generate_pattern(init_value, init_byte_length)
    if(pattern == 'error')
    {
        console.log('ERROR:The byte_length can only be 1, 2, 4, 8 and undefined?')
    }
    var range_list = Process.enumerateRangesSync(protection)
    for(var index in range_list)
    {
        try{
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
    if(m_count < 100)
    {
        for(var key in g_data)
        {
            console.log("address: " + '' + key + '' + "  value: "+ '' + g_data[key] + '');
        }
    }
    return m_count;
}

function new_scan_by_addr_unknownValue(addr_start, addr_end, reference, byte_length)
{
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

function new_scan_by_addr_larger(addr_start, addr_end, value, byte_length)
{
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

function new_scan_by_addr_littler(addr_start, addr_end, value, byte_length)
{
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

function new_scan_by_addr_between(addr_start, addr_end, value1, value2, byte_length)
{
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

function next_scan_equal(value)
{
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

function next_scan_unchange()
{
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

function next_scan_change()
{
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

function next_scan_littler(value)
{
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

function next_scan_larger(value)
{
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

function next_scan_between(value1, value2)
{
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

function next_scan_increase()
{
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

function next_scan_decrease()
{
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
function set_read_write_break(addr, size, pattern)
{
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
                console.log(details.address)

                //处理异常
                Memory.protect(address, size, 'rwx')
                return true;
        })
        //制造异常 <--> 设置读写断点
        Memory.protect(address, size, pattern)
}

})