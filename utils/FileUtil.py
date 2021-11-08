
def readFile(path):
    with open(path, "r+", encoding="utf-8") as shFile:
        shdata = shFile.read()
        return shdata

def writeFile(path,data):
    with open(path, "w+", encoding="utf-8") as shFile:
        shFile.write(data)