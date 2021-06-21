# frida_tools

frida_tools是一个界面化整理脚本的工具。新人的练手作品。参考项目ZenTracer，觉得既然可以界面化，那么应该可以把功能做的更加完善一些。

功能缝合怪。把一些常用的frida的hook脚本简单统一输出方式后，整合进来。并且将自己觉得常用的功能做成界面调用的。还想动态获取一些信息默认的直接展示。后续会根据自己实战的经验。不断完善这个工具。

##  Hook脚本如下（附加进程前使用）

> * 整合r0capture
> * 整合jnitrace
> * java层的加解密相关自吐
> * ssl pining（整合DroidSSLUnpinning）
> * 模糊匹配函数进行批量hook（整合ZenTracer）
> * 模糊匹配so函数批量hook（参数统一方式打印。所以输出只能做参考）
> * native的sub函数批量hook（参数统一方式打印。所以输出只能做参考）
> * stalker的trace
> * 自定义脚本添加
> * 脱壳相关（整合frida_dump、FRIDA-DEXDump、fart）
> * patch汇编代码
> * 整合frida_hook_libart

## 调用功能如下（附加进程后使用）

> * 模糊匹配类和函数打印（输出时间较长，如果想打印全部。就都填空即可）
> * 模糊匹配so符号打印（输出时间较长，如果想打印全。就都填空即可）
> * dump打印指定地址
> * 特征dump（搜索内存中的指定特征，然后匹配指定大小。是对之前脱壳里面的功能单独抽出）
> * 整合wallbreaker（内存中搜索到类的结构数据打印）

## 应用信息

附加成功时将一些信息带出来给界面展示。目前仅将module列表和class列表展示出来。可以查询函数以及符号

## 日志说明

### 1、操作日志

是对软件操作的所有输出日志。

### 2、输出日志

所有js返回的日志都在输出日志。并且保存在logs目录中

### 3、当前hook列表

当前勾选的hook脚本列表展示。可以保存，方便以后直接加载使用。



## 应用界面





## 感谢

* [jnitrace](https://github.com/chame1eon/jnitrace)
* [r0capture](https://github.com/r0ysue/r0capture)
* [ZenTracer](https://github.com/hluwa/ZenTracer)
* [DroidSSLUnpinning](https://github.com/WooyunDota/DroidSSLUnpinning)
* [frida_dump](https://github.com/lasting-yang/frida_dump)
* [FRIDA-DEXDump](https://github.com/hluwa/FRIDA-DEXDump)
* [FART](https://github.com/hanbinglengyue/FART)

