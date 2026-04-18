from DataBase import DataBase


def remove_postfix(text: str) -> str:
    if not text.endswith(')'):
        return text
    i = text.rfind('(')
    if i == -1:
        return text
    return text[:i]


def is_uid_type(type_name: str) -> bool:
    return type_name in DataBase.AllGuid


def get_mod_display_name(mod_info: dict):
    table = mod_info.get('Name')
    if isinstance(table, dict):
        f = next(iter(table), None)
        if f is not None:
            name = table[f]
            if isinstance(name, str):
                return name

    return mod_info['Namespace']


def get_mod_version(mod_info: dict):
    ver = mod_info.get('Version')
    if isinstance(ver, str):
        return ver
    return None


def resolve_data_key(key: str):
    i = key.find('@')
    if i == -1:
        return '', key
    return key[:i], key[i + 1:]
