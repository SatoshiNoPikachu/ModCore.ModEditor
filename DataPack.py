import yaml
import ujson as json
from pathlib import Path

from Config import Config
from utils import remove_postfix
from MyLogger import *


class PackInfo:

    @classmethod
    def load_packs(cls, path: str):
        path: Path = Path(path) / 'DataPackage'

        for p in path.iterdir():
            if not p.is_dir():
                continue

            p_info = p / 'PackInfo.json'
            if not p_info.exists():
                continue

            try:
                with p_info.open('r', encoding='utf-8') as f:
                    info = json.load(f)
                    yield PackInfo(p, info['Name'], info.get('Version', ''), info.get('IsMainPack', False))
            except Exception as e:
                QtCore.qWarning(str(e))

    def __init__(self, path: Path, name: str, version: str, main: bool):
        self.path = path
        self.name = name
        self.version = version
        self.is_main_pack = main


class DataPack:
    Packs: dict[str, PackInfo] = {}
    MainPack: PackInfo = None

    RefNameList: set[str] = set()
    RefGuidList: set[str] = set()
    SupportList: set[str] = {'GameSourceModify', 'DataObjectModify'}

    AllRefBase: dict[str, list[str] | dict[str, list[str]]] = {}
    AllObjNameBase: dict[str, dict[str, str]] = {}
    AllScriptableObjectBase: dict[str, dict[str, str]] = {}

    AllGuidBase: dict[str, dict[str, str | dict[str, str]]] = {}
    AllGuidPlainBase: dict[str, str] = {}
    AllCardDataBase: dict[str, str] = {}

    AllPathBase: dict[str, dict[str, str]] = {}

    AllBaseJsonData: dict[str, dict] = {}

    AllTypeField: dict[str, dict[str, str]] = {}
    AllEnum: dict[str, dict[str, int]] = {}
    AllEnumRev: dict[str, dict[int, str]] = {}

    AllAlias: dict[str, dict[str, str]] = {}
    AllComment: dict[str, dict[str, str]] = {}
    AllNotes: dict[str, dict[str, str]] = {}

    @classmethod
    def load_packs(cls, path: str):
        for info in PackInfo.load_packs(path):
            if info.is_main_pack:
                if cls.MainPack is not None:
                    continue
                cls.MainPack = info
                cls.Packs[info.name] = info
                continue

            if info.name in cls.Packs:
                continue

            cls.Packs[info.name] = info

        if cls.MainPack is None:
            raise Exception('Not installed main package!')

        cls.load_pack(cls.MainPack)

        for pack in cls.Packs.values():
            if pack == cls.MainPack:
                continue
            cls.load_pack(pack)

    @classmethod
    def load_pack(cls, pack: PackInfo):
        path = pack.path

        cls.load_name(path)

        cls.load_guid(path)

        cls.load_path(path)

        cls.load_base_json(path)

        cls.load_type_struct(path)

        cls.load_doc(path)

    @classmethod
    def load_name(cls, path: Path):
        dir_name = path / 'Name'
        if not dir_name.exists():
            return

        for p in dir_name.iterdir():
            if p.is_file() and p.suffix == '.json':
                type_name = p.stem
                ps = (p,)
            elif p.is_dir():
                type_name = p.name
                ps = (s for s in p.iterdir() if s.is_file() and s.suffix == '.json')
            else:
                continue

            if type_name in cls.AllRefBase:
                continue

            cls.RefNameList.add(type_name)
            ref_base = cls.AllRefBase[type_name] = []
            so_base = cls.AllScriptableObjectBase[type_name] = {}
            name_base = cls.AllObjNameBase[type_name] = {}

            prefix = f'{type_name}|'

            for pf in ps:
                with pf.open('r', encoding='utf-8') as f:
                    data: dict = json.load(f)

                ref_base.extend(data.keys())

                for k, v in data.items():
                    so_base[prefix + k] = prefix + v

                    name_base[v] = k

    @classmethod
    def load_guid(cls, path: Path):
        dir_guid = path / 'GUID'
        if not dir_guid.exists():
            return

        for p in dir_guid.iterdir():
            if p.is_file() and p.suffix == '.json':
                type_name = p.stem
                if type_name in cls.AllRefBase:
                    continue

                cls.RefGuidList.add(type_name)
                cls.SupportList.add(type_name)

                with p.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                cls.AllRefBase[type_name] = list(data.keys())
                cls.AllGuidBase[type_name] = data
                cls.AllGuidPlainBase.update(data)
                cls.AllScriptableObjectBase[type_name] = {(v := f'{type_name}|{k}'): remove_postfix(v) for k in data}
                continue
            elif not p.is_dir() or p.name != 'CardData':
                continue

            type_name = 'CardData'
            if type_name in cls.AllRefBase:
                continue

            cls.RefGuidList.add(type_name)
            cls.SupportList.add(type_name)
            ref_base = cls.AllRefBase[type_name] = {}
            guid_base = cls.AllGuidBase[type_name] = {}
            so_base = cls.AllScriptableObjectBase[type_name] = {}

            for ps in p.glob('*.json'):
                if not ps.is_file():
                    continue

                with ps.open('r', encoding='utf-8') as f:
                    data = json.load(f)

                ref_base[ps.stem] = list(data.keys())
                guid_base[ps.stem] = data
                cls.AllGuidPlainBase.update(data)
                cls.AllCardDataBase.update(data)

                for k in data:
                    v = f'CardData|{k}'
                    so_base[v] = remove_postfix(v)

    @classmethod
    def load_path(cls, path: Path):
        dir_obj = path / 'Objects'
        if not dir_obj.exists():
            return

        for p in dir_obj.iterdir():
            if not p.is_dir():
                continue

            type_name = p.name
            if type_name in cls.AllPathBase:
                continue

            path_base = cls.AllPathBase[type_name] = {}

            for f in p.rglob('*.json'):
                path_base[f.stem] = str(f)

    @classmethod
    def load_base_json(cls, path: Path):
        dir_base_json = path / 'BaseJson'
        if not dir_base_json.exists():
            return

        for p in dir_base_json.glob('*.json'):
            if not p.is_file():
                continue

            type_name = p.stem
            if type_name in cls.AllBaseJsonData:
                continue

            with p.open('r', encoding='utf-8') as f:
                cls.AllBaseJsonData[type_name] = json.load(f)

    @classmethod
    def load_type_struct(cls, path: Path):
        dir_type = path / 'TypeStruct'
        if not dir_type.exists():
            return

        for p in dir_type.glob('*.json'):
            if not p.is_file():
                continue

            type_name = p.stem
            if type_name in cls.AllTypeField:
                continue

            with p.open('r', encoding='utf-8') as f:
                data = json.load(f)

            cls.AllTypeField[type_name] = data['Fields']

        dir_enum = dir_type / 'Enum'
        if not dir_enum.exists():
            return

        for p in dir_enum.glob('*.json'):
            if not p.is_file():
                continue

            with p.open('r', encoding='utf-8') as f:
                cls.AllEnum[p.stem] = data = json.load(f)
                cls.AllEnumRev[p.stem] = {v: k for k, v in data.items()}

    @classmethod
    def load_doc(cls, path: Path):
        dir_doc = path / ('Doc' if Config.Language == 'zh_CN' else 'Doc-En')
        if not dir_doc.exists():
            return

        for p in dir_doc.glob('*.yml'):
            if not p.is_file():
                continue

            type_name = p.stem

            with p.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            alias = cls.AllAlias.setdefault(type_name, {})
            comment = cls.AllComment.setdefault(type_name, {})
            notes = cls.AllNotes.setdefault(type_name, {})

            for field, doc in data.items():
                alias[field] = '' if (v := doc.get('Alias')) is None else str(v)
                comment[field] = '' if (v := doc.get('Comment')) is None else str(v)
                notes[field] = '' if (v := doc.get('Note')) is None else str(v)

    @classmethod
    def get_alias(cls, type_name: str, field: str):
        alias = cls.AllAlias.get(type_name)
        return alias.get(field) if alias else None

    @classmethod
    def get_comment(cls, type_name: str, field: str):
        comment = cls.AllComment.get(type_name)
        return comment.get(field) if comment else None
