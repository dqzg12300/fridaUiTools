import os


def readFile(path):
    with open(path, "r+", encoding="utf-8") as shFile:
        shdata = shFile.read()
        return shdata

def writeFile(path,data):
    with open(path, "w+", encoding="utf-8") as shFile:
        shFile.write(data)

def search(path, name):
    for root, dirs, files in os.walk(path):  # path 为根目录
        if name in dirs or name in files:
            flag = 1  # 判断是否找到文件
            root = str(root)
            dirs = str(dirs)
            return os.path.join(root, dirs)
    return -1