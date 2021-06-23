import os


def execCmd(cmd):
    cmddata = os.popen(cmd)
    text = cmddata.read()
    cmddata.close()
    if len(text)>0:
        text+="\ncmd命令执行"+cmd+"完毕"
    else:
        text ="cmd命令执行" + cmd + "完毕"
    return text

def adbshellCmd(cmd,deviceType=1):
    cmdstart="adb shell su -c '%s'"
    if deviceType==2:
        cmdstart="adb shell su 0 '%s'"
    cmd=cmdstart%cmd
    cmddata = os.popen(cmd)
    text = cmddata.read()
    cmddata.close()
    if len(text) > 0:
        text += "\ncmd命令执行" + cmd + "完毕"
    else:
        text = "cmd命令执行" + cmd + "完毕"
    return text