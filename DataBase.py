# -*- coding: utf-8 -*-
import csv
from pathlib import Path
import ujson as json
import os
import copy
from glob import glob

from Config import Config
from DataPack import DataPack
from utils import *
from MyLogger import *


def replace_l10n_key(data: dict, mod_name: str, obj_name: str, guid: str = "",
                     entry_key: str = "", index: int = -1):
    if isinstance(data, list):
        for item in data:
            replace_l10n_key(item, mod_name, obj_name, guid)
        return
    elif not isinstance(data, dict):
        return
    for key, v in data.items():
        if key == "LocalizationKey" and v != "":
            if Config.ReplaceDefText and 'DefaultText' in data and (dt := DataBase.AllSimpCn.get(v)):
                data['DefaultText'] = dt['original']

            entry = v[v.rfind("_"):]
            if entry_key != "" and index > 0:
                st_idx = entry.rfind(entry_key)
                end_idx = entry[st_idx:].find("]") + st_idx
                entry = entry[:st_idx + len(entry_key) + 1] + str(index) + entry[end_idx:]
            data[key] = mod_name + "_" + obj_name + entry
        elif isinstance(v, dict):
            replace_l10n_key(v, mod_name, obj_name, guid, entry_key, index)
        elif isinstance(v, list):
            for item in v:
                replace_l10n_key(item, mod_name, obj_name, guid, entry_key, index)
        elif key == "ParentObjectID":
            data["ParentObjectID"] = ""


def delete_keys_from_dict(src_dict, key: str):
    for field in list(src_dict.keys()):
        if field == key:
            del src_dict[field]
        elif type(src_dict[field]) == dict:
            delete_keys_from_dict(src_dict[field], key)


class DataBase(DataPack):
    DataDir = None
    CurModName = ""
    CurModPath = None

    AllSpecialTypeField = {"CardData": ["BlueprintCardDataCardTabGroup", "BlueprintCardDataCardTabSubGroup",
                                        "ItemCardDataCardTabGpGroup", "MatchTypeWarpData", "MatchTagWarpData",
                                        "CardDataCardFilterGroup"],
                           "CharacterPerk": ["CharacterPerkPerkGroup"],
                           "GameStat": ["VisibleGameStatStatListTab"],
                           "CardTabGroup": ["BlueprintCardDataCardTabGroup"],
                           "PlayerCharacter": ["PlayerCharacterJournalName"]}
    AllMetaField = {"$matchTargets": "SpecialWarp"}

    AllBlueprintTab = []
    AllBlueprintSubTab = []
    AllItemTabGpGroup = []
    AllCardFilterGroup = []

    AllRef = {}  # DataBase.AllRef["ActionTag"] -> list[Ref]              DataBase.AllRef["CardData"]["Item"] -> list[RefTrans]
    AllGuid = {}  # DataBase.AllGuid["GameStat"][Ref] -> Guid              DataBase.AllGuid["CardData"]["Item"][RefTrans] -> Guid
    AllGuidPlain = {}  # DataBase.AllGuidPlain[RefTrans/Ref] -> Guid
    AllGuidPlainRev = {}  # DataBase.AllGuidPlainRev[Guid] -> RefTrans/Ref
    AllCardData = {}  # DataBase.AllCardData[RefTrans] -> CardData Guid
    AllPath = {}  # DataBase.AllPath["GameStat"][Ref] -> FilePath
    AllPathPlain = {}  # DataBase.AllPathPlain[Ref] -> FilePath
    AllScriptableObject: dict[str, dict[str, str]] = {}
    AllScriptableObjectRev = {}
    AllCollection = {}  # DataBase.AllCollection["CardsDropCollection"][CustomName] -> json data
    AllListCollection = {}  # DataBase.AllListCollection["CardsDropCollection"][CustomName] -> List json data

    AllSimpCn = {}  # DataBase.AllSimpCn[key] -> {origin, trans}
    AllTranDict = {}  # DataBase.AllTranDict[origin] -> trans
    AllModSimpCn = {}

    def __init__(self):
        pass

    @staticmethod
    def loadDataBase(data_dir: str, lan: str):
        DataBase.DataDir = data_dir

        if not os.path.exists(DataBase.DataDir + "/Mods"):
            os.mkdir(DataBase.DataDir + "/Mods")

        DataBase.load_packs(data_dir)
        DataBase.load_special_type_field()
        DataBase.load_collection()
        DataBase.load_game_simp_cn()

    @staticmethod
    def LoadModData(mod_name, mod_dir):
        DataBase.CurModName = mod_name

        DataBase.AllRef = {}
        DataBase.AllGuid = {}
        DataBase.AllGuidPlain = {}
        DataBase.AllGuidPlainRev = {}
        DataBase.AllCardData = {}
        DataBase.AllPath = {}
        DataBase.AllScriptableObject = {}
        DataBase.AllScriptableObjectRev = {}

        DataBase.AllRef.update(copy.deepcopy(DataBase.AllRefBase))
        DataBase.AllGuid.update(copy.deepcopy(DataBase.AllGuidBase))
        DataBase.AllGuidPlain.update(copy.deepcopy(DataBase.AllGuidPlainBase))
        DataBase.AllCardData.update(copy.deepcopy(DataBase.AllCardDataBase))
        DataBase.AllPath.update(copy.deepcopy(DataBase.AllPathBase))
        DataBase.AllScriptableObject.update(copy.deepcopy(DataBase.AllScriptableObjectBase))

        DataBase.AllRef["CardData"]["Mod"] = []
        DataBase.AllRef["CardData"]["ModsWork"] = []
        DataBase.AllRef["ContentDisplayer"] = []

        DataBase.AllModSimpCn = {}

        path_mod = Path(mod_dir)
        path_mod.mkdir(parents=True, exist_ok=True)

        DataBase.CurModPath = path_root = path_mod.parent

        path_res = path_root / "Resource"
        path_tex = path_res / "Texture2D"
        # path_audio = path_res / "Audio"

        DataBase.load_mod_tex(path_tex, f'{mod_name}:')

        path_lz = path_root / f"Resource/Localization/{Config.L10nFileName}.csv"
        if path_lz.exists() and path_lz.is_file():
            with path_lz.open("r", encoding='utf-8') as f:
                lines = f.readlines(-1)
                for line in lines:
                    keys = line.split(',')
                    if len(keys) > 3:
                        if line.find('"') != -1:
                            new_keys = line.split('"')
                            if len(new_keys) == 3 and new_keys[0][-1] == ',' and new_keys[2][0] == ',':
                                DataBase.AllModSimpCn[f'{mod_name}_{new_keys[0][-1]}'] = {
                                    "original": new_keys[1].replace('"', ''),
                                    "translate": new_keys[2][1:].replace("\n", "")}
                    elif len(keys) == 3:
                        DataBase.AllModSimpCn[f'{mod_name}_{keys[0]}'] = {"original": keys[1].replace('"', ''),
                                                                          "translate": keys[2].replace("\n", "")}
                    else:
                        QtCore.qWarning("Wrong Format Key")

        for p in path_mod.iterdir():
            if not p.is_dir():
                continue

            p = p.name

            if p in DataBase.RefGuidList:
                for file in [y for x in os.walk(mod_dir + r"/" + p) for y in glob(os.path.join(x[0], '*.json'))]:
                    file_name = os.path.basename(file)
                    guid = None
                    with open(file, "rb") as f:
                        data = f.read(-1)
                        guid_idx = data.find(b'"UniqueID"')
                        if guid_idx == -1:
                            continue
                        start_mark = data.find(b'"', guid_idx + len('"UniqueID"'))
                        if start_mark == -1:
                            continue
                        end_mark = data.find(b'"', start_mark + 1)
                        if end_mark == -1:
                            continue
                        guid = data[start_mark + 1:end_mark].decode()
                    if guid is None or guid == "":
                        continue
                    ref = f'{mod_name}:{file_name[:-5]}'
                    ref_so = f'{p}|{ref}'
                    if p == "CardData":
                        DataBase.AllRef[p]["Mod"].append(ref)
                        DataBase.AllGuid[p].update({ref: guid})
                        DataBase.AllGuidPlain.update({ref: guid})
                        DataBase.AllCardData.update({ref: guid})
                        DataBase.AllPath[p].update({ref: file})
                        DataBase.AllScriptableObject.setdefault(p, {})
                        DataBase.AllScriptableObject[p].update({ref_so: remove_postfix(ref_so)})
                    else:
                        DataBase.AllRef[p].append(ref)
                        DataBase.AllGuid[p].update({ref: guid})
                        DataBase.AllGuidPlain.update({ref: guid})
                        DataBase.AllPath[p].update({ref: file})
                        DataBase.AllScriptableObject.setdefault(p, {})
                        DataBase.AllScriptableObject[p].update({ref_so: remove_postfix(ref_so)})
            # elif p == "GameSourceModify":
            #     pass
            elif p == "ScriptableObject":
                for sub_dir in os.listdir(mod_dir + r"/" + p):
                    for file in [y for x in os.walk(mod_dir + r"/" + p + r"/" + sub_dir) for y in
                                 glob(os.path.join(x[0], '*.json'))]:
                        file_name = os.path.basename(file)
                        if sub_dir == "ContentPage":
                            if file_name.endswith("Default.json"):
                                name_parts = file_name.split("_")
                                if len(name_parts) > 2:
                                    DataBase.AllRef["ContentDisplayer"].append(name_parts[0] + "_" + name_parts[1])
                        if file.endswith(".json"):
                            ref = f'{mod_name}:{file_name[:-5]}'
                            DataBase.AllRef[sub_dir].append(ref)
                            DataBase.AllPath[sub_dir].update({ref: file})

                            ref_so = f'{sub_dir}|{ref}'
                            DataBase.AllScriptableObject.setdefault(sub_dir, {})
                            DataBase.AllScriptableObject[sub_dir].update({ref_so: ref_so})

        DataBase.load_work_ml(path_root)
        DataBase.load_mods_work_dir()

        for key in DataBase.AllPath:
            DataBase.AllPathPlain.update(copy.deepcopy(DataBase.AllPath[key]))

        DataBase.AllGuidPlainRev = {v: k for k, v in DataBase.AllGuidPlain.items()}
        DataBase.AllScriptableObjectRev = {t: {v: k for k, v in d.items()} for t, d in
                                           DataBase.AllScriptableObject.items()}

    @classmethod
    def load_mods_work_dir(cls):
        if Config.ModsWorkDir == "":
            return

        path_mwd = Path(Config.ModsWorkDir)
        if not path_mwd.is_absolute():
            path_mwd = Path(cls.DataDir) / path_mwd

        if not path_mwd.is_dir():
            return

        for d in path_mwd.iterdir():
            if not d.is_dir():
                continue

            ns = cls.load_work_mc(d)
            if ns == cls.CurModName:
                continue

            cls.load_work_ml(d)

    @classmethod
    def load_work_mc(cls, path: Path) -> str:
        path_meta = path / "ModMeta.json"

        if not path_meta.exists() or not path_meta.is_file():
            return ""

        try:
            with path_meta.open('r', encoding='utf-8') as f:
                ns = json.load(f).get("Namespace")
        except:
            return ""

        if not isinstance(ns, str) or ns == "":
            return ""

        if ns == cls.CurModName:
            return ns

        path_data = path / "Data"
        prefix = f'{ns}:'
        cls.load_work_mod_uo(path_data, prefix)
        cls.load_work_mod_so(path_data, prefix)
        cls.load_mod_tex(path / "Resource/Texture2D", prefix)

        return ns

    @classmethod
    def load_work_ml(cls, path: Path):
        path_info = path / "ModInfo.json"
        if not path_info.exists():
            return

        try:
            with path_info.open('r', encoding='utf-8') as f:
                name = json.load(f).get("Name")
        except:
            return

        if not isinstance(name, str) or name == "":
            return

        prefix = f'{name}_'
        cls.load_work_mod_uo(path, prefix)
        cls.load_work_mod_so(path, "")
        cls.load_mod_audio(path / "Resource/Audio", "")

    @classmethod
    def load_work_mod_uo(cls, path: Path, prefix: str):
        if not path.exists() or not path.is_dir():
            return

        for d in path.iterdir():
            t = d.name

            if not d.is_dir() or t not in cls.AllGuid:
                continue

            is_card = t == "CardData"

            for p in d.rglob('*.json'):
                if not p.is_file():
                    continue

                with p.open("rb") as f:
                    data = f.read(-1)
                    guid_idx = data.find(b'"UniqueID"')
                    if guid_idx == -1:
                        continue
                    start_mark = data.find(b'"', guid_idx + len('"UniqueID"'))
                    if start_mark == -1:
                        continue
                    end_mark = data.find(b'"', start_mark + 1)
                    if end_mark == -1:
                        continue
                    guid = data[start_mark + 1:end_mark].decode()

                if guid is None or guid == "":
                    continue

                ref = prefix + p.stem
                if is_card:
                    cls.AllRef[t]["ModsWork"].append(ref)
                    cls.AllCardData.update({ref: guid})
                else:
                    cls.AllRef[t].append(ref)

                cls.AllGuid[t].update({ref: guid})
                cls.AllGuidPlain.update({ref: guid})
                cls.AllPath[t].update({ref: str(p)})

                ref_so = f'{t}|{ref}'
                cls.AllScriptableObject.setdefault(t, {})
                cls.AllScriptableObject[t].update({ref_so: remove_postfix(ref_so)})

    @classmethod
    def load_work_mod_so(cls, path: Path, prefix: str):
        path = path / "ScriptableObject"

        if not path.exists() or not path.is_dir():
            return

        for d in path.iterdir():
            t = d.name

            if not d.is_dir() or t not in cls.AllRef:
                continue

            for p in d.rglob('*.json'):
                if not p.is_file():
                    continue

                ref = prefix + p.stem
                cls.AllRef[t].append(ref)
                cls.AllPath[t].update({ref: str(p)})

                ref_so = f'{t}|{ref}'
                cls.AllScriptableObject.setdefault(t, {})
                cls.AllScriptableObject[t].update({ref_so: ref_so})

    @classmethod
    def load_mod_audio(cls, path: Path, prefix: str):
        if not path.exists() or not path.is_dir():
            return

        ext_audio = {".wav"}

        for file in path.iterdir():
            if not file.is_file():
                continue

            if file.suffix.lower() in ext_audio:
                cls.AllRef["AudioClip"].append(file.stem)

    @classmethod
    def load_mod_tex(cls, path: Path, prefix: str):
        if not path.exists() or not path.is_dir():
            return

        ext_tex = {".png", ".jpg", ".jpeg"}

        for file in path.rglob('*'):
            if not file.is_file():
                continue

            if file.suffix.lower() in ext_tex:
                cls.AllRef["Sprite"].append(f'{prefix}{file.stem}')

    @staticmethod
    def load_special_type_field():
        for key, item_list in DataBase.AllSpecialTypeField.items():
            if key in DataBase.AllTypeField:
                for item in item_list:
                    DataBase.AllTypeField[key][item] = "SpecialWarp"

    @staticmethod
    def load_collection():
        if os.path.exists(DataBase.DataDir + r"/Mods/" + r"Collection.json"):
            with open(DataBase.DataDir + r"/Mods/" + r"Collection.json", "r", encoding='utf-8') as f:
                DataBase.AllCollection = json.load(f)

        for key in DataBase.AllBaseJsonData.keys():
            if key not in DataBase.AllCollection:
                DataBase.AllCollection[key] = {}
            DataBase.AllCollection[key]["Empty Default"] = DataBase.AllBaseJsonData[key]

        if os.path.exists(DataBase.DataDir + r"/Mods/" + r"ListCollection.json"):
            with open(DataBase.DataDir + r"/Mods/" + r"ListCollection.json", "r", encoding='utf-8') as f:
                DataBase.AllListCollection = json.load(f)

    @staticmethod
    def save_collection():
        with open(DataBase.DataDir + r"/Mods/" + r"Collection.json", "w", encoding='utf-8') as f:
            json.dump(DataBase.AllCollection, f)

        with open(DataBase.DataDir + r"/Mods/" + r"ListCollection.json", "w", encoding='utf-8') as f:
            json.dump(DataBase.AllListCollection, f)

    @staticmethod
    def loop_load_mod_simp_cn(json, mod_name: str, simpCn_dict: dict = None):
        if type(json) is dict:
            for key, item in json.items():
                if type(item) == str:
                    if key == "LocalizationKey" and item.startswith(mod_name):
                        if simpCn_dict is not None and type(simpCn_dict) is dict:
                            if item not in simpCn_dict:
                                if "DefaultText" in json:
                                    simpCn_dict[item] = {"original": json["DefaultText"], "translate": ""}
                            else:
                                if "DefaultText" in json:
                                    simpCn_dict[item]["original"] = json["DefaultText"]
                        else:
                            if item not in DataBase.AllModSimpCn:
                                if "DefaultText" in json:
                                    DataBase.AllModSimpCn[item] = {"original": json["DefaultText"], "translate": ""}
                            else:
                                if "DefaultText" in json:
                                    DataBase.AllModSimpCn[item]["original"] = json["DefaultText"]
                elif type(item) == list:
                    for sub_item in item:
                        DataBase.loop_load_mod_simp_cn(sub_item, mod_name, simpCn_dict)
                elif type(item) == dict:
                    DataBase.loop_load_mod_simp_cn(item, mod_name, simpCn_dict)
        elif type(json) is list:
            for value in json:
                DataBase.loop_load_mod_simp_cn(value, mod_name, simpCn_dict)

    @classmethod
    def load_mod_simp_cn(cls, mod_dir):
        p = Path(mod_dir)
        if p.name == "Data":
            p = p.parent
        p = p / f"Resource/Localization/{Config.L10nFileName}.csv"
        if not p.exists():
            return

        for key, dt in cls.read_l10n_file(p):
            cls.AllModSimpCn[f'{cls.CurModName}_{key}'] = dt

    @staticmethod
    def auto_translation_duplicates(mod_dir):
        DataBase.load_mod_simp_cn(mod_dir)
        if len(DataBase.AllTranDict) == 0:
            for item in DataBase.AllSimpCn.values():
                if not item["original"] in DataBase.AllTranDict and "translate" in item and item["translate"] != "":
                    DataBase.AllTranDict[item["original"]] = item["translate"]
        for item in DataBase.AllModSimpCn.values():
            if not item["original"] in DataBase.AllTranDict and "translate" in item and item["translate"] != "":
                DataBase.AllTranDict[item["original"]] = item["translate"]
        for item in DataBase.AllModSimpCn.values():
            if "translate" in item and item["translate"] == "":
                if item["original"] in DataBase.AllTranDict:
                    item["translate"] = DataBase.AllTranDict[item["original"]]
        DataBase.save_mod_simp_cn(mod_dir, False)

    @staticmethod
    def delete_obsolete(mod_dir: str, mod_name: str):
        DataBase.load_mod_simp_cn(mod_dir)
        files = [y for x in os.walk(mod_dir) for y in glob(os.path.join(x[0], '*.json'))]
        ModSimpCnDict = {}
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    DataBase.loop_load_mod_simp_cn(data, mod_name, ModSimpCnDict)
            except Exception as ex:
                QtCore.qWarning(traceback.format_exc())
        obsolete_keys = set(DataBase.AllModSimpCn.keys()).difference(ModSimpCnDict.keys())
        for key in obsolete_keys:
            del DataBase.AllModSimpCn[key]
        DataBase.save_mod_simp_cn(mod_dir, False)

    @staticmethod
    def format_all_localization_key(mod_dir: str, mod_name: str):
        DataBase.load_mod_simp_cn(mod_dir)
        files = [y for x in os.walk(mod_dir) for y in glob(os.path.join(x[0], '*.json'))]
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    DataBase.loop_format_simp_cn(data, mod_name)
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)
            except Exception as ex:
                QtCore.qWarning(traceback.format_exc())
        DataBase.save_mod_simp_cn(mod_dir, False)

    @staticmethod
    def dump_all_json_file_without_ensure_ascii(mod_dir: str, mod_name: str):
        files = [y for x in os.walk(mod_dir) for y in glob(os.path.join(x[0], '*.json'))]
        for file in files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)
            except Exception as ex:
                QtCore.qWarning(traceback.format_exc())

    @staticmethod
    def loop_format_simp_cn(json, mod_name: str):
        if type(json) is dict:
            for key, item in json.items():
                if type(item) == str:
                    if key == "LocalizationKey" and json[key] != "":
                        if not item.startswith(mod_name):
                            json[key] = mod_name + "_" + json[key]
                        if json[key] not in DataBase.AllModSimpCn:
                            if "DefaultText" in json:
                                DataBase.AllModSimpCn[json[key]] = {"original": json["DefaultText"], "translate": ""}
                        else:
                            if "DefaultText" in json:
                                DataBase.AllModSimpCn[json[key]]["original"] = json["DefaultText"]
                elif type(item) == list:
                    for sub_item in item:
                        DataBase.loop_format_simp_cn(sub_item, mod_name)
                elif type(item) == dict:
                    DataBase.loop_format_simp_cn(item, mod_name)
        elif type(json) is list:
            for value in json:
                DataBase.loop_format_simp_cn(value, mod_name)

    @staticmethod
    def save_mod_simp_cn(mod_dir, loadSrc: bool = True):
        p = Path(mod_dir)
        if p.name == "Data":
            p = p.parent
        p = p / f"Resource/Localization/{Config.L10nFileName}.csv"
        if not p.parent.exists():
            return

        prefix = f'{DataBase.CurModName}_'
        prefixLen = len(prefix)

        if loadSrc:
            DataBase.load_mod_simp_cn(mod_dir)
        with p.open("w", encoding='utf-8') as f:
            for key in DataBase.AllModSimpCn:
                if key.startswith(prefix):
                    f.write(key[prefixLen:])
                else:
                    f.write(key)
                f.write(',"')
                f.write(DataBase.AllModSimpCn[key]["original"].replace("\n", "\\n").replace("\t", "\\t"))
                f.write('",')
                f.write(DataBase.AllModSimpCn[key]["translate"].replace("\n", "\\n").replace("\t", "\\t"))
                f.write('\n')

    @classmethod
    @log_exception()
    def load_game_simp_cn(cls):
        p = cls.MainPack.path / 'SimpCn.csv'
        if not p.exists():
            return

        for key, dt in cls.read_l10n_file(p, Config.L10nFileName == 'En'):
            if not dt['translate']:
                continue

            cls.AllSimpCn[key] = dt

    @classmethod
    def read_l10n_file(cls, path: Path, reverse=False):
        with path.open('r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)

            for row in reader:
                row_len = len(row)
                if row_len < 2:
                    QtCore.qWarning(f'Localization error line: {reader.line_num}')
                    continue

                if row_len == 2:
                    yield row[0], {'original': row[1], 'translate': ''}
                    continue

                if reverse:
                    yield row[0], {'original': row[-1], 'translate': row[1]}
                else:
                    yield row[0], {'original': row[1], 'translate': row[-1]}
