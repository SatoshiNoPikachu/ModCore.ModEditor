import os
from pathlib import Path

import yaml

from MyLogger import log_exception


class ConfigDumper(yaml.SafeDumper):

    def write_line_break(self, data=None):
        super(ConfigDumper, self).write_line_break(data)

        if len(self.indents) == 1:
            super(ConfigDumper, self).write_line_break()

    def represent_none(self, data):
        return self.represent_scalar('tag:yaml.org,2002:null', '')


ConfigDumper.add_representer(type(None), ConfigDumper.represent_none)


class ConfigManager:
    Configs: dict[str, ConfigItem] = {}

    @classmethod
    def load(cls):
        try:
            path = Path(os.getcwd()) / 'settings.yml'
            if not path.exists():
                return

            with path.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                return

            for name, config in cls.Configs.items():
                if group := data.get(config.group):
                    if name in group:
                        config.load(group[name])
        except:
            pass

    @classmethod
    @log_exception(True)
    def save(cls):
        path = Path(os.getcwd()) / 'settings.yml'

        data = {}
        for name, config in cls.Configs.items():
            value = config.value
            if config.type == str and value == '':
                value = None

            data.setdefault(config.group, {})[config.name] = value

        with path.open('w', encoding='utf-8') as f:
            yaml.dump(data, f, Dumper=ConfigDumper, allow_unicode=True, sort_keys=False)


class ConfigItem[T]:
    def __init__(self, name: str, group: str, default: T, can_empty: bool = True):
        self.name = name
        self.group = group
        self.value = default
        self.type = type(default)
        self.can_empty = can_empty

        ConfigManager.Configs[name] = self

    def load(self, value):
        if isinstance(value, self.type):
            if value or self.can_empty:
                self.value = value
        elif self.type == str and value is not None:
            self.value = str(value)

    def __get__(self, instance, owner):
        return self.value


class ConfigMeta(type):
    def __setattr__(cls, name, value):
        config = cls.__dict__.get(name)
        if config:
            config.value = value


class Config(metaclass=ConfigMeta):
    # General
    FactorAppScale = ConfigItem('FactorAppScale', 'General', '')
    Language = ConfigItem('Language', 'General', '')

    # Editor
    ReplaceDefText = ConfigItem('AutoReplaceDefText', 'Editor', True)
    ReplaceKey = ConfigItem('AutoReplaceL10nKey', 'Editor', True)
    AutoResize = ConfigItem('AutoResize', 'Editor', True)
    FieldCompletion = ConfigItem('AutoFieldCompletion', 'Editor', True)
    KeyAlias = ConfigItem('KeyAlias', 'Editor', True)

    # Mod
    L10nFileName = ConfigItem('L10nFileName', 'Mod', "En", can_empty=False)
    ModsWorkDir = ConfigItem('ModsWorkDir', 'Mod', "Mods", can_empty=False)

    # Record
    LastOpenDir = ConfigItem('LastOpenDir', 'Record', '')
