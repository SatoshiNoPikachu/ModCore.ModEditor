# -*- coding: utf-8 -*- 

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Ui_Select import *
from Ui_Collection import *
from DataBase import *


class SelectGUI(QDialog, Ui_Select):
    Ref = 0
    NewData = 1
    Copy = 2
    Append = 3
    Special = 4
    NewModify = 5

    def __init__(self, parent=None, field_name: str = "", checked: bool = False, type: int = 0,
                 auto_replace_key_guid: bool = False):
        super(SelectGUI, self).__init__(parent)
        self.setupUi(self)
        self.field_name = field_name
        self.write_flag = False
        self.auto_replace_key_guid = auto_replace_key_guid
        self.modify_type = None
        self.setWindowTitle(self.tr("Add ") + field_name + self.tr(" Reference Type"))
        self.checked_type = None
        self.use_def = False

        if type == SelectGUI.NewData:
            self.setWindowTitle(self.tr("Choose a ") + field_name + self.tr(" Template"))
            label = QLabel(self.tr("Name"), self)
            self.name_editor = QLineEdit(self)
            self.verticalLayout.insertWidget(0, self.name_editor)
            self.verticalLayout.insertWidget(0, label)
            if not self.auto_replace_key_guid:
                self.buttonBox.addButton(QDialogButtonBox.StandardButton.YesToAll).setText(
                    self.tr("Auto Replace LocalizationKey"))
            else:
                self.buttonBox.addButton(QDialogButtonBox.StandardButton.YesToAll).setText(
                    self.tr("No Replace LocalizationKey"))
            self.buttonBox.addButton(QDialogButtonBox.StandardButton.Yes).setText(
                self.tr("Use Default Template"))

        if type == SelectGUI.NewModify:
            self.setWindowTitle(self.tr("Choose a ") + field_name + self.tr(" Object"))
            label = QLabel(self.tr("Name"), self)
            self.name_editor = QLineEdit(self)
            self.verticalLayout.insertWidget(0, self.name_editor)
            self.verticalLayout.insertWidget(0, label)

        if type == SelectGUI.Copy:
            self.setWindowTitle(self.tr("Copy ") + field_name + self.tr(" Entries"))

        if type == SelectGUI.Append:
            self.setWindowTitle(self.tr("Append ") + field_name + self.tr(" Entries"))

        if type == SelectGUI.Special:
            self.setWindowTitle(self.tr("Add Special Entry"))

        try:
            if self.field_name == "CardData":
                ref_list = []
                self.checkBoxList = {}
                for key in DataBase.AllRef[self.field_name].keys():
                    check_box = QCheckBox()
                    check_box.setText(key)
                    if checked:
                        check_box.setChecked(True)
                    check_box.stateChanged.connect(self.on_CardDataCheckBoxStateChanged)
                    self.checkBoxList[key] = check_box
                    self.comboBox.addItems(DataBase.AllRef[self.field_name][key])
                    ref_list.extend(DataBase.AllRef[self.field_name][key])
                    self.horizontalLayout_CheckBox.addWidget(check_box)
                self.m_completer = QCompleter(ref_list, self)

            elif self.field_name == "GameSourceModify":
                ref_list = []
                self.checkBoxList = {}
                for key in DataBase.AllRef["CardData"].keys():
                    check_box = QCheckBox()
                    check_box.setText(key)
                    if checked:
                        check_box.setChecked(True)
                    check_box.stateChanged.connect(self.on_GameSourceModifyCheckBoxStateChanged)
                    self.checkBoxList[key] = check_box
                    self.comboBox.addItems(DataBase.AllRef["CardData"][key])
                    ref_list.extend(DataBase.AllRef["CardData"][key])
                    self.horizontalLayout_CheckBox.addWidget(check_box)
                for i, key in enumerate(DataBase.AllGuid.keys()):
                    if key == "CardData":
                        continue
                    check_box = QCheckBox()
                    check_box.setText(key)
                    if checked:
                        check_box.setChecked(True)
                    check_box.stateChanged.connect(self.on_GameSourceModifyCheckBoxStateChanged)
                    self.checkBoxList[key] = check_box
                    self.comboBox.addItems(list(DataBase.AllGuid[key].keys()))
                    ref_list.extend(list(DataBase.AllGuid[key]))
                    self.horizontalLayout_CheckBox2.addWidget(check_box, i // 12, i % 12)
                self.m_completer = QCompleter(ref_list, self)

            elif self.field_name == "DataObjectModify":
                target = DataBase.AllRef
                ref_list = []
                self.checkBoxList = {}
                for i, key in enumerate(sorted(target.keys())):
                    check_box = QCheckBox()
                    check_box.setText(key)
                    if checked:
                        check_box.setChecked(True)

                    check_box.stateChanged.connect(self.on_dom_check_box_state_changed)
                    self.checkBoxList[key] = check_box

                    # data = target[key]
                    # self.comboBox.addItems(data)
                    # if isinstance(data, dict):
                    #     keys = [item for v in data.values() if isinstance(v, list) for item in v]
                    # else:
                    #     keys = data if isinstance(data, list) else []
                    # ref_list.extend(keys)

                    self.horizontalLayout_CheckBox2.addWidget(check_box, i // 12, i % 12)
                self.m_completer = QCompleter(ref_list, self)

            elif self.field_name in DataBase.AllEnum:
                self.comboBox.addItems(DataBase.AllEnum[self.field_name].keys())
                self.m_completer = QCompleter(DataBase.AllEnum[self.field_name].keys(), self)
            elif self.field_name in DataBase.AllRef:
                self.comboBox.addItems(DataBase.AllRef[self.field_name])
                self.m_completer = QCompleter(DataBase.AllRef[self.field_name], self)

            elif self.field_name == "ScriptableObject":
                ref_list = []
                self.checkBoxList = {}
                for key in DataBase.AllScriptableObject.keys():
                    if key == "CardData" or key.find("Tag") != -1:
                        check_box = QCheckBox()
                        check_box.setText(key)
                        if checked:
                            check_box.setChecked(True)
                        self.checkBoxList[key] = check_box
                        check_box.stateChanged.connect(self.on_so_check_box_state_changed)
                        # if key == "CardData":
                        #     for sub_key in DataBase.AllRef[key].keys():
                        #         self.comboBox.addItems(DataBase.AllRef[key][sub_key])
                        #         ref_list.extend(DataBase.AllRef[key][sub_key])
                        # else:
                        #     self.comboBox.addItems(DataBase.AllRef[key])
                        #     ref_list.extend(DataBase.AllRef[key])
                        self.horizontalLayout_CheckBox.addWidget(check_box)
                # self.comboBox.addItems(DataBase.AllScriptableObject.keys())
                self.m_completer = QCompleter(ref_list, self)

            elif self.field_name == "BlueprintCardDataCardTabGroup":
                self.comboBox.addItems(DataBase.AllBlueprintTab)
                self.m_completer = QCompleter(DataBase.AllBlueprintTab, self)
            elif self.field_name == "BlueprintCardDataCardTabSubGroup":
                self.comboBox.addItems(DataBase.AllBlueprintSubTab)
                self.m_completer = QCompleter(DataBase.AllBlueprintSubTab, self)
            elif self.field_name == "ItemCardDataCardTabGpGroup":
                self.comboBox.addItems(DataBase.AllItemTabGpGroup)
                self.m_completer = QCompleter(DataBase.AllItemTabGpGroup, self)
            elif self.field_name == "CardDataCardFilterGroup":
                self.comboBox.addItems(DataBase.AllCardFilterGroup)
                self.m_completer = QCompleter(DataBase.AllCardFilterGroup, self)
            elif self.field_name == "CharacterPerkPerkGroup":
                self.comboBox.addItems(DataBase.AllRef["PerkGroup"])
                self.m_completer = QCompleter(DataBase.AllRef["PerkGroup"], self)
            elif self.field_name == "VisibleGameStatStatListTab":
                self.comboBox.addItems(DataBase.AllRef["StatListTab"])
                self.m_completer = QCompleter(DataBase.AllRef["StatListTab"], self)
            elif self.field_name == "PlayerCharacterJournalName":
                self.comboBox.addItems(DataBase.AllRef["ContentDisplayer"])
                self.m_completer = QCompleter(DataBase.AllRef["ContentDisplayer"], self)
            else:
                self.m_completer = QCompleter([], self)

            self.m_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.m_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.m_completer.activated[str].connect(self.on_Choosed)
            self.lineEdit.setCompleter(self.m_completer)
            self.comboBox.currentTextChanged.connect(self.on_Choosed)
            self.buttonBox.clicked.connect(self.on_accepted)
        except Exception as ex:
            QtCore.qWarning(bytes(traceback.format_exc(), encoding="utf-8"))

    @log_exception(True)
    def on_CardDataCheckBoxStateChanged(self, a0: int):
        self.comboBox.clear()
        reflist = []
        for key in DataBase.AllRef[self.field_name].keys():
            if self.checkBoxList[key].isChecked():
                reflist.extend(DataBase.AllRef[self.field_name][key])
                self.comboBox.addItems(DataBase.AllRef[self.field_name][key])
        self.m_completer.setModel(QStringListModel(reflist, self.m_completer))

    @log_exception(True)
    def on_GameSourceModifyCheckBoxStateChanged(self, a0: int):
        self.comboBox.clear()
        ref_list = []
        for key in self.checkBoxList.keys():
            if self.checkBoxList[key].isChecked():
                if key in DataBase.AllRef["CardData"]:
                    ref_list.extend(DataBase.AllRef["CardData"][key])
                    self.comboBox.addItems(DataBase.AllRef["CardData"][key])
                elif key in DataBase.AllGuid:
                    ref_list.extend(list(DataBase.AllGuid[key].keys()))
                    self.comboBox.addItems(list(DataBase.AllGuid[key].keys()))
        self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))

    @log_exception(True)
    def on_dom_check_box_state_changed(self, state: int):
        self.comboBox.clear()
        self.checked_type = None
        ref_list = []

        target = DataBase.AllRef

        if state != 2:
            self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))
            return

        sender = self.sender()
        for key, cb in self.checkBoxList.items():
            if cb is not sender:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
                continue

            if key in target:
                data = target[key]
                if isinstance(data, dict):
                    keys = [item for v in data.values() if isinstance(v, list) for item in v]
                else:
                    keys = data if isinstance(data, list) else []
                ref_list.extend(keys)
                self.comboBox.addItems(keys)
                self.checked_type = key
        self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))

    @log_exception(True)
    def on_so_check_box_state_changed(self, state: int):
        self.comboBox.clear()
        ref_list = []

        if state != 2:
            self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))
            return

        target = DataBase.AllScriptableObject

        sender = self.sender()
        for key, cb in self.checkBoxList.items():
            if cb is not sender:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
                continue

            if (data := target.get(key)) is None:
                continue

            ref_list.extend(data)
            self.comboBox.addItems(data)
        self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))

    @log_exception(True)
    def on_Choosed(self, name):
        self.lineEdit.setText(name)

    @log_exception(True)
    def on_accepted(self, button: QAbstractButton):
        if button == self.buttonBox.button(QDialogButtonBox.Ok):
            self.write_flag = True
            return

        if button == self.buttonBox.button(QDialogButtonBox.Yes):
            self.write_flag = True
            self.use_def = True
            return

        if button == self.buttonBox.button(QDialogButtonBox.YesToAll):
            self.write_flag = True
            self.auto_replace_key_guid = not self.auto_replace_key_guid
