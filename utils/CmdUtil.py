import os
import subprocess

cmdhead="adb shell su -c "       #切换使用adb shell su -c 和 adb shell su 0

def exec(cmd):
    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.PIPE  # 重定向输入值
    )
    proc.stdin.close()  # 既然没有命令行窗口，那就关闭输入
    result = proc.stdout.read()  # 读取cmd执行的输出结果（是byte类型，需要decode）
    proc.stdout.close()
    return result.decode(encoding="utf-8")

def execCmd(cmd):
    text = exec(cmd)
    if len(text)>0:
        text+="\ncmd命令执行"+cmd
    else:
        text ="cmd命令执行" + cmd
    return text

def execCmdData(cmd):
    text = exec(cmd)
    return text

def dumpdexInit(packageName):
    path = "/data/data/" + packageName + "/files/" + "/dump_dex_" + packageName
    res=""
    res += adbshellCmd("mkdir -p " + path)+"\n"
    res += adbshellCmd("chmod 0777 " + "/data/data/" + packageName + "/files/")+"\n"
    res += adbshellCmd("chmod 0777 " + path)+"\n"
    return res

def fartInit(savepath):
    res=""
    res += adbshellCmd("mkdir -p " + savepath)+"\n"
    res += adbshellCmd("chmod 0777 " + savepath)+"\n"
    return res

def adbshellCmd(cmd):
    cmd="%s '%s'"%(cmdhead,cmd)
    text = exec(cmd)
    if len(text) > 0:
        text += "\ncmd命令执行" + cmd
    else:
        text = "cmd命令执行" + cmd
    return text

def adbshellCmdEnd(cmd,end):
    cmd="%s '%s' %s"%(cmdhead,cmd,end)
    text = exec(cmd)
    if len(text) > 0:
        text += "\ncmd命令执行" + cmd
    else:
        text = "cmd命令执行" + cmd
    return text

def fix_so(arch, origin_so_name, so_name, base, size):
    if arch == "arm":
        os.system("adb push exec/android/SoFixer32 /data/local/tmp/SoFixer")
    elif arch == "arm64":
        os.system("adb push exec/android/SoFixer64 /data/local/tmp/SoFixer")
    os.system("adb shell chmod +x /data/local/tmp/SoFixer")
    os.system("adb push " + so_name + " /data/local/tmp/" + so_name)
    print("adb shell /data/local/tmp/SoFixer -m " + base + " -s /data/local/tmp/" + so_name + " -o /data/local/tmp/" + so_name + ".fix.so")
    os.system("adb shell /data/local/tmp/SoFixer -m " + base + " -s /data/local/tmp/" + so_name + " -o /data/local/tmp/" + so_name + ".fix.so")
    os.system("adb pull /data/local/tmp/" + so_name + ".fix.so " + origin_so_name + "_" + base + "_" + str(size) + "_fix.so")
    os.system("adb shell rm /data/local/tmp/" + so_name)
    os.system("adb shell rm /data/local/tmp/" + so_name + ".fix.so")
    os.system("adb shell rm /data/local/tmp/SoFixer")
    return origin_so_name + "_" + base + "_" + str(size) + "_fix.so"