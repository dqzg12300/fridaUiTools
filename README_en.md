# fridaUiTools

**English**| [中文](README.md)

A frida interface tool for organizing scripts。Referenced from ZenTracer project

support：win、mac、linux

## update 2022-01-08

add switch language

## update 2022-12-28

add switch frida16，add anti frida

## update 2022-12-02

repair searchMemory module

## update 2022-11-25

add searchMemory modul。refer from [基于frida的android游戏内存扫描器_初稿](https://www.52pojie.cn/forum.php?mod=viewthread&tid=913009&highlight=)
add memory breakpoint。refer from [fridaMemoryAccessTrace](https://github.com/asmjmp0/fridaMemoryAccessTrace)

##  Hook（Before attaching a process use）

> * Capture tool r0capture
> * jnitrace
> * java encrypt
> * ssl pining（refer from DroidSSLUnpinning）
> * java function trace（refer from ZenTracer）
> * native function hook
> * stalker（refer from sktrace）
> * frida_hook_libart
> * unpack（refer from frida_dump、FRIDA-DEXDump、fart）
> * custom js
> * patch code


## Work（After attaching the process use）

> * fart unpack
> * DUMPDex unpack
> * dump addr
> * dump so
> * wallBreak

## Run

1、To run under mac, you need to enter the command to enter the root directory to run

~~~
cd fridaUiTools
./kmainForm_15
~~~

2、The packaged application in release, the suffixes `_14`, `_15`, `_16` respectively indicate the different versions of frida used when packaging

## log description

### 1、oplog

is a log of all output from software operations。

### 2、outlog

All logs returned by js are outputting logs. And save it in the logs directory

### 3、current hook list

The list of currently selected hook scripts is displayed. It can be saved for later loading and use directly.



## UI

![image-20230114220753559](.\img\image-20230114220753559.png)

![image-20230114220901689](.\img\image-20230114220901689.png)

![image-20230114221036915](.\img\image-20230114221036915.png)


## Instructions for use

There are many places in the software that use cached data. Cache data is the list of modules and classes saved after attaching a process. This facilitates intelligent retrieval. Therefore, when using it for the first time, attach the target process first, and then the cached data will be available for use.

If fart is used for the first time, you need to click upload so of fart in the upload and download menu bar.

## demo

When a new device is used for the first time, it needs to upload frida-server first. Then select the corresponding frida-server to start. Then you can choose the function to hook.
![](.\fridaUiToolsDemo.gif)

## Thanks

* [jnitrace](https://github.com/chame1eon/jnitrace)
* [r0capture](https://github.com/r0ysue/r0capture)
* [ZenTracer](https://github.com/hluwa/ZenTracer)
* [DroidSSLUnpinning](https://github.com/WooyunDota/DroidSSLUnpinning)
* [frida_dump](https://github.com/lasting-yang/frida_dump)
* [FRIDA-DEXDump](https://github.com/hluwa/FRIDA-DEXDump)
* [FART](https://github.com/hanbinglengyue/FART)
* [sktrace](https://github.com/bmax121/sktrace)
* [Wallbreaker](https://github.com/hluwa/Wallbreaker)