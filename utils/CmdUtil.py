
import subprocess


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
    return str(result)

def execCmd(cmd):
    text = exec(cmd)
    if len(text)>0:
        text+="\ncmd命令执行"+cmd
    else:
        text ="cmd命令执行" + cmd
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

def adbshellCmd(cmd,deviceType=1):
    cmdstart="adb shell su -c '%s'"
    if deviceType==2:
        cmdstart="adb shell su 0 '%s'"
    cmd=cmdstart%cmd
    text = exec(cmd)
    if len(text) > 0:
        text += "\ncmd命令执行" + cmd
    else:
        text = "cmd命令执行" + cmd
    return text