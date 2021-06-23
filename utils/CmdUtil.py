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