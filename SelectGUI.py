# -*- coding: utf-8 -*-
from typing import Any

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ui.Ui_Select import *
from ui.Ui_Collection import *
from DataBase import *


class SelectGUI(QDialog, Ui_Select):
    Ref = 0
    NewData = 1
    Copy = 2
    Append = 3
    Special = 4
    NewModify = 5
    Browser = 6

    def __init__(self, parent=None, field_name: str = "", checked: bool = False, mode: int = 0,
                 replace_key: bool = False):
        super(SelectGUI, self).__init__(parent)
        self.setupUi(self)
        self.field_name = field_name
        self.write_flag = False
        self.replace_key = replace_key
        self.modify_type = None
        self.setWindowTitle(self.tr("Add ") + field_name + self.tr(" Reference Type"))
        self.checked_type = None
        self.use_def = False
        self.type_prefix = False

        if mode == SelectGUI.Ref:
            if field_name == 'Sprite':
                btn = self.buttonBox.addButton(self.tr('Generate Temp Image'), QDialogButtonBox.ActionRole)
                btn.clicked.connect(self.on_new_temp_image)

        elif mode == SelectGUI.NewData:
            self.setWindowTitle(self.tr("Choose a ") + field_name + self.tr(" Template"))
            label = QLabel(self.tr("Name"), self)
            self.name_editor = QLineEdit(self)
            self.verticalLayout.insertWidget(0, self.name_editor)
            self.verticalLayout.insertWidget(0, label)
            if not self.replace_key:
                self.buttonBox.addButton(QDialogButtonBox.StandardButton.YesToAll).setText(
                    self.tr("Auto Replace LocalizationKey"))
            else:
                self.buttonBox.addButton(QDialogButtonBox.StandardButton.YesToAll).setText(
                    self.tr("No Replace LocalizationKey"))
            self.buttonBox.addButton(QDialogButtonBox.StandardButton.Yes).setText(
                self.tr("Use Default Template"))

        elif mode == SelectGUI.NewModify:
            self.setWindowTitle(self.tr("Choose a ") + field_name + self.tr(" Object"))
            label = QLabel(self.tr("Name"), self)
            self.name_editor = QLineEdit(self)
            self.verticalLayout.insertWidget(0, self.name_editor)
            self.verticalLayout.insertWidget(0, label)

        elif mode == SelectGUI.Copy:
            self.setWindowTitle(self.tr("Copy ") + field_name + self.tr(" Entries"))

        elif mode == SelectGUI.Append:
            self.setWindowTitle(self.tr("Append ") + field_name + self.tr(" Entries"))

        elif mode == SelectGUI.Special:
            self.setWindowTitle(self.tr("Add Special Entry"))

        elif mode == SelectGUI.Browser:
            self.setWindowTitle(self.tr('Browse ') + field_name)

        try:
            if field_name == "CardData":
                ref_list = []
                self.checkBoxList = {}
                for key in DataBase.AllRef[field_name].keys():
                    check_box = QCheckBox()
                    check_box.setText(key)
                    if checked:
                        check_box.setChecked(True)
                    check_box.stateChanged.connect(self.on_CardDataCheckBoxStateChanged)
                    self.checkBoxList[key] = check_box
                    self.comboBox.addItems(DataBase.AllRef[field_name][key])
                    ref_list.extend(DataBase.AllRef[field_name][key])
                    self.horizontalLayout_CheckBox.addWidget(check_box)
                self.m_completer = QCompleter(ref_list, self)

            elif field_name == "GameSourceModify":
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
                for i, key in enumerate(k for k in DataBase.AllGuid if k != 'CardData'):
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

            elif field_name == "DataObjectModify":
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
                    self.horizontalLayout_CheckBox2.addWidget(check_box, i // 10, i % 10)
                self.m_completer = QCompleter(ref_list, self)

            elif field_name == "ScriptableObject":
                ref_list = []
                self.checkBoxList = {}
                for key in sorted(DataBase.AllScriptableObject.keys()):
                    if key == "CardData" or key.find("Tag") != -1:
                        check_box = QCheckBox()
                        check_box.setText(key)
                        if checked:
                            check_box.setChecked(True)
                        self.checkBoxList[key] = check_box
                        check_box.stateChanged.connect(self.on_so_check_box_state_changed)
                        self.horizontalLayout_CheckBox.addWidget(check_box)
                self.m_completer = QCompleter(ref_list, self)

            elif field_name in DataBase.AllEnum:
                self.comboBox.addItems(DataBase.AllEnum[field_name].keys())
                self.m_completer = QCompleter(DataBase.AllEnum[field_name].keys(), self)

            elif field_name in DataBase.AllRef:
                if (mode == self.Ref or mode == self.Append) and field_name in DataBase.AllBaseType:
                    check_box = QCheckBox(field_name)
                    check_box.setChecked(True)
                    check_box.stateChanged.connect(self.on_base_type_check_box_state_changed)
                    self.horizontalLayout_CheckBox.addWidget(check_box)

                    self.checkBoxList = {field_name: check_box}
                    for key in sorted(DataBase.AllBaseType[field_name]):
                        check_box = QCheckBox(key)
                        check_box.stateChanged.connect(self.on_base_type_check_box_state_changed)
                        self.checkBoxList[key] = check_box
                        self.horizontalLayout_CheckBox.addWidget(check_box)

                    self.type_prefix = True

                self.comboBox.addItems(DataBase.AllRef[field_name])
                self.m_completer = QCompleter(DataBase.AllRef[field_name], self)

            else:
                self.m_completer = QCompleter([], self)

            self.m_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.m_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.m_completer.activated[str].connect(self.on_Choosed)
            self.lineEdit.setCompleter(self.m_completer)
            self.comboBox.currentTextChanged.connect(self.on_Choosed)
            self.buttonBox.clicked.connect(self.on_accepted)

        except Exception as ex:
            QtCore.qWarning(traceback.format_exc())

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

            target = DataBase.AllRef
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

        sender = self.sender()
        for key, cb in self.checkBoxList.items():
            if cb is not sender:
                cb.blockSignals(True)
                cb.setChecked(False)
                cb.blockSignals(False)
                continue

            if (data := DataBase.AllScriptableObject.get(key)) is None:
                continue

            ref_list.extend(data)
            self.comboBox.addItems(data)
        self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))

    @log_exception(True)
    def on_base_type_check_box_state_changed(self, state: int):
        self.comboBox.clear()
        self.checked_type = None
        ref_list = []

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

            ref_list = DataBase.AllRef[key]
            self.comboBox.addItems(ref_list)
            self.checked_type = key
        self.m_completer.setModel(QStringListModel(ref_list, self.m_completer))

    @log_exception(True)
    def on_Choosed(self, name):
        self.lineEdit.setText(name)

    @log_exception(True)
    def on_accepted(self, button: QAbstractButton):
        if button == self.buttonBox.button(QDialogButtonBox.Ok):
            self.write_flag = True

            if self.type_prefix and self.checked_type != self.field_name:
                self.lineEdit.setText(f'{self.checked_type}|{self.lineEdit.text()}')

            return

        if button == self.buttonBox.button(QDialogButtonBox.Yes):
            self.write_flag = True
            self.use_def = True
            return

        if button == self.buttonBox.button(QDialogButtonBox.YesToAll):
            self.write_flag = True
            self.replace_key = not self.replace_key

    @log_exception(True)
    def on_new_temp_image(self, _):
        dialog = NewTempImgGUI(self, self.lineEdit.text())
        if dialog.exec_() == QDialog.Accepted:
            self.lineEdit.setText(dialog.ref_name())
