import configparser
import os


class IniConfig():
    def __init__(self):
        root_dir = os.path.abspath('.')
        self.cf = configparser.ConfigParser()
        self.configPath=root_dir + "/config/conf.ini"

    def read(self,section,key):
        self.cf.read(self.configPath)
        return self.cf.get(section,key)

    def write(self,section,key,value):
        self.cf.read(self.configPath)
        self.cf.set(section,key,value)
        self.cf.write(open(self.configPath,"w",encoding="utf-8"))

