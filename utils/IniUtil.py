import configparser
import os


class IniConfig():
    AI_SECTION = "ai"

    def __init__(self):
        root_dir = os.path.abspath('.')
        self.configPath = os.path.join(root_dir, "config", "conf.ini")
        self.aiConfigPath = os.path.join(root_dir, "config", "ai.local.ini")
        self._migrate_legacy_ai_section()

    def _load(self, path=None):
        parser = configparser.ConfigParser()
        parser.read(path or self.configPath, encoding="utf-8")
        return parser

    def _save(self, parser, path):
        parent_dir = os.path.dirname(path)
        if parent_dir and os.path.exists(parent_dir) is False:
            os.makedirs(parent_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as config_file:
            parser.write(config_file)

    def _section_path(self, section):
        return self.aiConfigPath if section == self.AI_SECTION else self.configPath

    def _migrate_legacy_ai_section(self):
        main_parser = self._load(self.configPath)
        if main_parser.has_section(self.AI_SECTION) is False:
            return

        ai_parser = self._load(self.aiConfigPath)
        ai_changed = False
        if ai_parser.has_section(self.AI_SECTION) is False:
            ai_parser.add_section(self.AI_SECTION)
            ai_changed = True

        for key, value in main_parser.items(self.AI_SECTION):
            current_value = ai_parser.get(self.AI_SECTION, key, fallback="").strip()
            if current_value:
                continue
            ai_parser.set(self.AI_SECTION, key, value)
            ai_changed = True

        if ai_changed:
            self._save(ai_parser, self.aiConfigPath)

        main_parser.remove_section(self.AI_SECTION)
        self._save(main_parser, self.configPath)

    def read(self, section, key, fallback=""):
        parser = self._load(self._section_path(section))
        if parser.has_option(section, key):
            return parser.get(section, key)
        return fallback

    def write(self, section, key, value):
        path = self._section_path(section)
        parser = self._load(path)
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, key, "" if value is None else str(value))
        self._save(parser, path)

    def read_section(self, section):
        parser = self._load(self._section_path(section))
        if not parser.has_section(section):
            return {}
        return dict(parser.items(section))
