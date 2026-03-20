import configparser
import os


class IniConfig():
    def __init__(self):
        root_dir = os.path.abspath('.')
        self.cf = configparser.ConfigParser()
        self.configPath = root_dir + "/config/conf.ini"

    def _load(self):
        self.cf.read(self.configPath, encoding="utf-8")

    def read(self, section, key, fallback=""):
        self._load()
        if self.cf.has_option(section, key):
            return self.cf.get(section, key)
        return fallback

    def write(self, section, key, value):
        self._load()
        if not self.cf.has_section(section):
            self.cf.add_section(section)
        self.cf.set(section, key, "" if value is None else str(value))
        with open(self.configPath, "w", encoding="utf-8") as config_file:
            self.cf.write(config_file)

    def read_section(self, section):
        self._load()
        if not self.cf.has_section(section):
            return {}
        return dict(self.cf.items(section))

