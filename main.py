# -*- coding: utf-8 -*-
import os

from Config import ConfigManager, Config

ConfigManager.load()
if Config.FactorAppScale:
    os.environ["QT_SCALE_FACTOR"] = Config.FactorAppScale

import shutil
import sys
import traceback
import uuid
from glob import glob
from pathlib import Path

import ujson as json
from PyQt5 import QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import ExportToZip
import Global
import ItemGUI
import ModifyItemGUI
import NewItemGUI
import SelectGUI
from DataBase import DataBase, replace_l10n_key, replace_def_text
from DataPack import MainPackMissingError
from MyLogger import logInit, log_exception
from ui.Ui_Main import Ui_MainWindow
from utils import *

ModEditorVersion = "1.3.3"


class ModEditorGUI(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(ModEditorGUI, self).__init__(parent)
        self.setupUi(self)

        self.trans = QTranslator()
        logInit(os.path.join(QDir.currentPath(), "log.log"))
        self.loadLanguage()

        self.dataInit()
        self.ui_Init()
        self.mod_path = None
        self.mod_info = None
        self.file_model = None
        self.root_depth = 0
        self.tab_item_dict = {}

        Global.MainWindow = self

    @log_exception(True)
    def loadLanguage(self):
        if Config.Language:
            self.trans.load(os.path.join(QDir.currentPath(), "L10n", Config.Language))
            _app = QApplication.instance()
            _app.installTranslator(self.trans)
            self.retranslateUi(self)
        else:
            _app = QApplication.instance()
            _app.removeTranslator(self.trans)
            self.retranslateUi(self)

    def reset(self):
        self.mod_path = None
        self.mod_info = None
        self.file_model = None
        self.root_depth = 0
        self.tab_item_dict = {}
        self.tabWidget.clear()

    @log_exception(True)
    def dataInit(self):
        try:
            DataBase.loadDataBase(QDir.currentPath(), Config.Language)
        except MainPackMissingError:
            QMessageBox.warning(self, self.tr('Warning'), self.tr(
                'The main data package is not installed. The program will not function properly!'))

    def ui_Init(self):
        self.treeView.doubleClicked.connect(self.on_treeViewDoubleClicked)
        self.treeView.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)
        self.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.on_treeViewCustomContextMenuRequested)

        if Config.AutoResize:
            self.action_ResizeMode.setText(self.tr("Turn off auto contents resize"))
        else:
            self.action_ResizeMode.setText(self.tr("Turn on auto contents resize"))

        if Config.ReplaceKey:
            self.action_AutoReplace.setText(self.tr("Turn off auto replace key guid"))
        else:
            self.action_AutoReplace.setText(self.tr("Turn on auto replace key guid"))

        if Config.FieldCompletion:
            self.action_AutoCompleteUpdates.setText(self.tr("Turn off auto completion updates"))
        else:
            self.action_AutoCompleteUpdates.setText(self.tr("Turn on auto completion updates"))

        width = qApp.desktop().availableGeometry(self).width()
        self.splitter.setSizes([int(width * 1 / 8), int(width * 7 / 8)])
        for i in range(self.splitter.count()):
            self.splitter.setCollapsible(i, False)

        self.action_newMod.triggered.connect(self.on_newMod)
        self.action_loadMod.triggered.connect(self.on_loadMod)
        self.action_save.triggered.connect(self.on_saveMod)
        self.action_ExportZip.triggered.connect(self.on_exportZip)
        self.action_ResizeMode.triggered.connect(self.on_actionResizeMode)
        self.action_AutoReplace.triggered.connect(self.on_actionAutoReplace)
        self.action_AutoCompleteUpdates.triggered.connect(self.on_actionCompleteUpdate)
        self.action_AutoTranslationDuplicates.triggered.connect(self.on_actionAutoTranslationDuplicates)
        self.action_DeleteObsoleteTranslation.triggered.connect(self.on_actionDeleteObsoleteTranslation)
        self.action_FormatAllLocalizationKey.triggered.connect(self.on_actionFormatAllLocalizationKey)
        self.action_JsonDumpWithoutEnsureAscii.triggered.connect(self.on_actionJsonDumpWithoutEnsureAscii)

        self.actionChinese.triggered.connect(self.on_select_Chinese)
        self.actionEnglish.triggered.connect(self.on_select_English)

        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setMovable(True)
        self.tabWidget.tabCloseRequested.connect(self.on_tabWidgetTabCloseRequested)
        self.tabWidget.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabWidget.tabBar().customContextMenuRequested.connect(self.on_tabWidgetCustomContextMenuRequested)

        self.setWindowTitle('ModEditor for ModCore')
        self.srcTitle = self.windowTitle() + " " + ModEditorVersion
        self.setWindowTitle(self.srcTitle)

        self.pushButton.clicked.connect(self.on_pushButtonClicked)

        self.quick_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.quick_save.activated.connect(self.on_saveMod)

        self.quick_loadColl = QShortcut(QKeySequence("Ctrl+L"), self)
        self.quick_loadColl.activated.connect(self.on_quick_loadColl)

        self.quick_close = QShortcut(QKeySequence("Esc"), self)
        self.quick_close.activated.connect(self.on_quick_close)

        self.lineEdit.returnPressed.connect(self.on_lineEditReturnPressed)

        self.treeView.installEventFilter(self)
        self.treeView.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        if source is self.treeView:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
                    index = self.treeView.currentIndex()
                    if index.isValid():
                        file_name = Path(self.file_model.fileName(index))

                        clipboard = QApplication.clipboard()
                        clipboard.setText(file_name.stem)
                        return True
        elif source is self.treeView.viewport():
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton and (event.modifiers() & Qt.ControlModifier):
                    index = self.treeView.indexAt(event.pos())
                    if index.isValid():
                        file_path = Path(self.file_model.filePath(index))
                        if file_path.exists():
                            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
                        return True
        return super().eventFilter(source, event)

    @log_exception(True)
    def on_select_Chinese(self, checked: bool = False):
        Config.Language = 'zh_CN'
        ConfigManager.save()
        self.loadLanguage()

    @log_exception(True)
    def on_select_English(self, checked: bool = False):
        Config.Language = ''
        ConfigManager.save()
        self.loadLanguage()

    @log_exception(True)
    def on_actionResizeMode(self, checked: bool = False):
        if Config.AutoResize:
            Config.AutoResize = False
            self.action_ResizeMode.setText(self.tr("Turn on auto contents resize"))
        else:
            Config.AutoResize = True
            self.action_ResizeMode.setText(self.tr("Turn off auto contents resize"))
        ConfigManager.save()

    @log_exception(True)
    def on_actionAutoReplace(self, checked: bool = False):
        if Config.ReplaceKey:
            Config.ReplaceKey = False
            self.action_AutoReplace.setText(self.tr("Turn on auto replace key guid"))
        else:
            Config.ReplaceKey = True
            self.action_AutoReplace.setText(self.tr("Turn off auto replace key guid"))
        ConfigManager.save()

    @log_exception(True)
    def on_actionCompleteUpdate(self, checked: bool = False):
        if Config.FieldCompletion:
            Config.FieldCompletion = False
            self.action_AutoCompleteUpdates.setText(self.tr("Turn on auto completion updates"))
        else:
            Config.FieldCompletion = True
            self.action_AutoCompleteUpdates.setText(self.tr("Turn off auto completion updates"))
        ConfigManager.save()

    @log_exception(True)
    def on_actionAutoTranslationDuplicates(self, checked: bool = False):
        if self.mod_info:
            DataBase.auto_translation_duplicates(self.mod_path)

    @log_exception(True)
    def on_actionDeleteObsoleteTranslation(self, checked: bool = False):
        if self.mod_info:
            reply = QMessageBox.question(self, self.tr('Delete Obsolete'), self.tr(
                'Sure you want to remove the outdated translations? (Note that all translations that are not automatically generated by Editor will be considered obsolete)'),
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                DataBase.delete_obsolete(self.mod_path, self.mod_info["Namespace"])

    @log_exception(True)
    def on_actionFormatAllLocalizationKey(self, checked: bool = False):
        if self.mod_info:
            reply = QMessageBox.question(self, self.tr('Add Prefixes'),
                                         self.tr('Sure you want to add Mod prefixes to all LocalizationKeys?'),
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                DataBase.format_all_localization_key(self.mod_path, self.mod_info["Namespace"])

    @log_exception(True)
    def on_actionJsonDumpWithoutEnsureAscii(self, checked: bool = False):
        if self.mod_info:
            reply = QMessageBox.question(self, self.tr('Warning'), self.tr('Sure you want to do it?'),
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                DataBase.dump_all_json_file_without_ensure_ascii(self.mod_path, self.mod_info["Namespace"])

    @log_exception(True)
    def treeItemRenamed(self, path: str, old_file: str, new_file: str):
        old_tab_key = path + "/" + old_file
        new_tab_key = path + "/" + new_file
        if old_tab_key in self.tab_item_dict:
            self.tab_item_dict[new_tab_key] = self.tab_item_dict[old_tab_key]
            for i in range(self.tabWidget.count()):
                if self.tabWidget.widget(i) == self.tab_item_dict[new_tab_key]["widget"]:
                    if new_file.endswith(".json"):
                        self.tabWidget.setTabText(i, new_file[:-5])
                    else:
                        self.tabWidget.setTabText(i, new_file)
                    break
            self.tab_item_dict[new_tab_key]["widget"].setTabKey(new_tab_key)
            del self.tab_item_dict[old_tab_key]

    def on_tabWidgetCustomContextMenuRequested(self, pos: QPoint):
        pmenu = QMenu(self)
        tabBar = self.tabWidget.tabBar()
        tab = -1
        gpos = self.sender().mapToGlobal(pos)
        posInbar = tabBar.mapFromGlobal(gpos)
        for i in range(tabBar.count()):
            if tabBar.tabRect(i).contains(posInbar):
                tab = i
                break
        if tab >= 0:
            pCloseNowAct = QAction(self.tr("Close(Auto-Save)"), pmenu)
            pCloseNowAct.triggered.connect(lambda: self.on_closeNow(tab))
            pmenu.addAction(pCloseNowAct)

            pCloseRightAct = QAction(self.tr("Close to the Right(Auto-Save)"), pmenu)
            pCloseRightAct.triggered.connect(lambda: self.on_closeRight(tab))
            pmenu.addAction(pCloseRightAct)

            pCloseAllExAct = QAction(self.tr("Close Others(Auto-Save)"), pmenu)
            pCloseAllExAct.triggered.connect(lambda: self.on_closeAllEx(tab))
            pmenu.addAction(pCloseAllExAct)

            pCloseAllAct = QAction(self.tr("Close All(Auto-Save)"), pmenu)
            pCloseAllAct.triggered.connect(lambda: self.on_closeAll(tab))
            pmenu.addAction(pCloseAllAct)
        if len(pmenu.actions()):
            pmenu.popup(self.sender().mapToGlobal(pos))

    def on_closeNow(self, tab: int, checked: bool = False):
        if tab >= 0:
            self.on_tabWidgetTabCloseRequested(tab, False)

    def on_closeRight(self, tab: int, checked: bool = False):
        if tab >= 0:
            for i in reversed(range(tab + 1, self.tabWidget.count())):
                self.on_tabWidgetTabCloseRequested(i, False)

    def on_closeAllEx(self, tab: int, checked: bool = False):
        if tab >= 0:
            for i in reversed(range(tab + 1, self.tabWidget.count())):
                self.on_tabWidgetTabCloseRequested(i, False)
            for i in reversed(range(self.tabWidget.count() - 1)):
                self.on_tabWidgetTabCloseRequested(i, False)

    def on_closeAll(self, tab: int, checked: bool = False):
        if tab >= 0:
            for i in reversed(range(self.tabWidget.count())):
                self.on_tabWidgetTabCloseRequested(i, False)

    def on_lineEditReturnPressed(self):
        self.on_pushButtonClicked()

    def init_completer(self):
        paths = [y for x in os.walk(self.mod_path) for y in glob(os.path.join(x[0], '*.json'))]
        files = list(map(lambda x: x.split(self.mod_path)[1].replace("\\", "/"), paths))
        self.m_completer = QCompleter(files, self.treeView)
        self.m_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.m_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.lineEdit.setCompleter(self.m_completer)

    @log_exception(True)
    def on_pushButtonClicked(self, checked: bool = False):
        tab_key = self.mod_path + self.lineEdit.text()
        if tab_key in self.tab_item_dict:
            self.tabWidget.setCurrentWidget(self.tab_item_dict[tab_key]["widget"])
        else:
            self.openTreeViewItem(self.file_model.index(tab_key))

    @log_exception(True)
    def on_quick_close(self) -> None:
        index = self.tabWidget.currentIndex()
        if index >= 0:
            self.on_tabWidgetTabCloseRequested(index)

    @log_exception(True)
    def on_quick_loadColl(self) -> None:
        DataBase.load_collection()

    def closeEvent(self, event) -> None:
        reply = QMessageBox.question(self, self.tr('Save'), self.tr(
            'Save the changes before exit?(Collection, Localization, Opened files...)'),
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self.on_saveMod()
            event.accept()
        elif reply == QMessageBox.No:
            event.accept()
        else:
            event.ignore()

    @log_exception(True)
    def on_treeViewCustomContextMenuRequested(self, pos: QPoint) -> None:
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        depth = self.treeItemDepth(index)
        file_name = self.file_model.fileName(index)
        file_path = self.file_model.filePath(index)
        pmenu = QMenu(self)
        if self.file_model.isDir(index):
            if depth == 0:
                pass
            elif depth == 1:
                if file_name in DataBase.SupportList:
                    if file_name == "GameSourceModify":
                        pAddAct = QAction(self.tr("New Modify"), pmenu)
                        pAddAct.triggered.connect(self.on_newModify)
                        pmenu.addAction(pAddAct)
                    elif file_name == "DataObjectModify":
                        pAddAct = QAction(self.tr("New Modify"), pmenu)
                        pAddAct.triggered.connect(self.on_new_data_modify)
                        pmenu.addAction(pAddAct)
                    elif file_name != "ScriptableObject":
                        pAddAct = QAction(self.tr("New File"), pmenu)
                        pAddAct.triggered.connect(self.on_new_uo)
                        pmenu.addAction(pAddAct)

                        browse_act = QAction(self.tr("Browse Object"), pmenu)
                        browse_act.triggered.connect(self.on_browse)
                        pmenu.addAction(browse_act)

            elif depth == 2:
                top_parent = self.getDepthParent(index, depth=1)
                if top_parent is None:
                    return
                top_name = self.file_model.fileName(top_parent)
                if top_name == "ScriptableObject":
                    if self.file_model.isDir(index) and file_name in DataBase.AllRef:
                        pAddAct = QAction(self.tr("New File"), pmenu)
                        pAddAct.triggered.connect(self.on_new_so)
                        pmenu.addAction(pAddAct)

                        browse_act = QAction(self.tr("Browse Object"), pmenu)
                        browse_act.triggered.connect(self.on_browse)
                        pmenu.addAction(browse_act)

                elif top_name == "GameSourceModify":
                    pass
                else:
                    pAddAct = QAction(self.tr("New File"), pmenu)
                    pAddAct.triggered.connect(self.on_new_uo)
                    pmenu.addAction(pAddAct)
            else:
                top_parent = self.getDepthParent(index, depth=1)
                if top_parent is None:
                    return
                top_name = self.file_model.fileName(top_parent)
                if top_name in DataBase.SupportList:
                    if top_name == "GameSourceModify" or top_name == "ScriptableObject":
                        pass
                    else:
                        pAddAct = QAction(self.tr("New File"), pmenu)
                        pAddAct.triggered.connect(self.on_new_uo)
                        pmenu.addAction(pAddAct)
        if depth > 1:
            if not self.file_model.isDir(index) and file_name.endswith(".json"):
                if not file_path in self.tab_item_dict:
                    pDeleteAct = QAction(self.tr("Delete"), pmenu)
                    pDeleteAct.triggered.connect(self.on_delCard)
                    pmenu.addAction(pDeleteAct)
        if len(pmenu.actions()):
            pmenu.popup(self.sender().mapToGlobal(pos))

    @log_exception(True)
    def on_browse(self, checked: bool = False):
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        top_parent = self.getDepthParent(index, depth=1)
        if top_parent is None:
            return

        type_name = self.file_model.fileName(index)
        if not type_name:
            return

        select = SelectGUI.SelectGUI(self, field_name=type_name, mode=SelectGUI.SelectGUI.Browser)
        select.exec_()

        if not select.write_flag:
            return

        name = remove_postfix(select.lineEdit.text())
        if not name:
            return

        self.browse_obj(type_name, name)

    def browse_obj(self, type_name, name):
        file_path = DataBase.AllPath[type_name].get(name)
        if file_path is None:
            return

        if file_path in self.tab_item_dict:
            self.tabWidget.setCurrentWidget(self.tab_item_dict[file_path]["widget"])
            return

        with open(file_path, "r", encoding='utf-8') as f:
            data = json.load(f)

        if Config.ReplaceDefText:
            replace_def_text(data)

        item = ItemGUI.ItemGUI(parent=self.tabWidget, field=type_name, key=file_path, item_name=name, readonly=True)
        item.load_json_data(data)

        self.tabWidget.addTab(item, name + self.tr(' (Readonly)'))
        self.tab_item_dict[file_path] = {"widget": item}
        self.tabWidget.setCurrentWidget(item)

    @log_exception(True)
    def on_new_so(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        top_parent = self.getDepthParent(index, depth=1)
        if top_parent is None:
            return

        top_name = self.file_model.fileName(top_parent)
        if top_name != "ScriptableObject":
            return

        type_name = self.file_model.fileName(index)
        file_path = self.file_model.filePath(index)

        select = SelectGUI.SelectGUI(self, field_name=type_name, checked=False, mode=SelectGUI.SelectGUI.NewData,
                                     replace_key=Config.ReplaceKey)
        select.exec_()

        if not select.write_flag:
            return

        try:
            name = select.name_editor.text()
            if name.endswith(')'):
                QMessageBox.warning(self, self.tr("Warning"), self.tr('The name cannot end with ")"'))
                return

            template_key = remove_postfix(select.lineEdit.text())

            path = Path(file_path) / f'{name}.json'
            if path.exists():
                QMessageBox.warning(self, self.tr("Warning"), self.tr('A file with the same name exists'))
                return

            if select.use_def:
                if not name:
                    return

                data = DataBase.AllBaseJsonData.get(type_name)
                if data is None:
                    QMessageBox.warning(self, self.tr("Warning"), self.tr('No default template'))
                    return

                with path.open("w", encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

            elif name and template_key:

                with open(DataBase.AllPath[type_name][template_key], "r", encoding='utf-8') as f:
                    temp_data = json.load(f)

                if select.replace_key and Config.ReplaceKey:
                    replace_l10n_key(temp_data, self.mod_info["Namespace"], name)

                with path.open("w", encoding='utf-8') as f:
                    json.dump(temp_data, f, sort_keys=True, ensure_ascii=False)

            self.openTreeViewItem(self.file_model.index(str(path)))

        except Exception as ex:
            QtCore.qWarning(traceback.format_exc())
        self.init_completer()

    @log_exception(True)
    def on_new_uo(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        top_parent = self.getDepthParent(index, depth=1)
        if top_parent is None:
            return

        file_name = self.file_model.fileName(index)
        if not file_name:
            return

        file_path = self.file_model.filePath(index)
        type_name = self.file_model.fileName(top_parent)

        select = SelectGUI.SelectGUI(self, field_name=type_name, checked=False, mode=SelectGUI.SelectGUI.NewData,
                                     replace_key=Config.ReplaceKey)
        select.exec_()

        if not select.write_flag:
            return

        try:
            name = select.name_editor.text()
            if name.endswith(')'):
                QMessageBox.warning(self, self.tr("Warning"), self.tr('The name cannot end with ")"'))
                return

            template_key = remove_postfix(select.lineEdit.text())

            path = Path(file_path) / f'{name}.json'
            if path.exists():
                QMessageBox.warning(self, self.tr("Warning"), self.tr('A file with the same name exists'))
                return

            if select.use_def:
                if not name:
                    return

                data: dict | None = DataBase.AllBaseJsonData.get(type_name)
                if data is None:
                    QMessageBox.warning(self, self.tr("Warning"), self.tr('No default template'))
                    return

                data = data.copy()
                data['UniqueID'] = uuid.uuid4().hex

                with path.open("w", encoding='utf-8') as f:
                    json.dump(data, f, sort_keys=True, ensure_ascii=False)

            elif name and template_key:

                with open(DataBase.AllPath[type_name][template_key], "r", encoding="utf-8") as f:
                    temp_json = json.load(f)

                temp_json["UniqueID"] = uuid.uuid4().hex

                if select.replace_key and Config.ReplaceKey:
                    replace_l10n_key(temp_json, self.mod_info["Namespace"], name)

                with path.open("w", encoding='utf-8') as f:
                    json.dump(temp_json, f, sort_keys=True, ensure_ascii=False)

            self.openTreeViewItem(self.file_model.index(str(path)))

        except Exception as ex:
            QtCore.qWarning(traceback.format_exc())
            self.init_completer()

    @log_exception(True)
    def on_newModify(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        top_parent = self.getDepthParent(index, depth=1)
        if top_parent is None:
            return

        file_name = self.file_model.fileName(index)
        if not file_name:
            return

        file_path = self.file_model.filePath(index)
        top_name = self.file_model.fileName(top_parent)

        group_name = top_name
        select = SelectGUI.SelectGUI(self, field_name=group_name, checked=False, mode=SelectGUI.SelectGUI.NewModify)
        select.exec_()

        if not select.write_flag:
            return

        target_key = select.lineEdit.text()
        try:
            dir_name = select.name_editor.text()
            if not dir_name or not target_key:
                return

            target_group_name = ""
            target_guid = DataBase.AllGuidPlain[target_key]

            for type_key in DataBase.AllRef["CardData"].keys():
                if target_key in DataBase.AllRef["CardData"][type_key]:
                    target_group_name = "CardData"
                    break

            for group_key in DataBase.AllGuid.keys():
                if target_key in DataBase.AllGuid[group_key]:
                    target_group_name = group_key
                    break

            if not target_group_name or not target_guid:
                return

            card_dir = file_path + "/" + dir_name
            card_path = file_path + "/" + dir_name + "/" + target_guid + ".json"
            if not os.path.exists(card_dir):
                os.mkdir(card_dir)

            if not os.path.exists(card_path):
                with open(card_path, "w", encoding="utf-8") as f:
                    f.write("{\n\n}")
                print(card_path)
                self.openTreeViewItem(self.file_model.index(card_path))
            else:
                QMessageBox.warning(self, self.tr("Warning"), self.tr('A file with the same name exists'))

        except Exception as ex:
            QtCore.qWarning(traceback.format_exc())
        self.init_completer()

    @log_exception(True)
    def on_new_data_modify(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        file_name = self.file_model.fileName(index)
        file_path = self.file_model.filePath(index)
        top_parent = self.getDepthParent(index, depth=1)
        if top_parent is None:
            return

        top_name = self.file_model.fileName(top_parent)
        if not file_name:
            return

        group_name = top_name
        select = SelectGUI.SelectGUI(self, field_name=group_name, checked=False, mode=SelectGUI.SelectGUI.NewModify)
        select.exec_()

        if not select.write_flag:
            return

        type_name = select.checked_type
        if type_name is None:
            return

        try:
            target_key = select.lineEdit.text()
            dir_name = select.name_editor.text()
            dir_name = f'{dir_name}/{type_name}' if dir_name else type_name

            if not target_key:
                return

            target_key = remove_postfix(target_key).replace(":", "@", 1)

            path_dir = Path(file_path) / dir_name
            path_file = path_dir / f'{target_key}.json'

            if not path_dir.exists():
                path_dir.mkdir(parents=True)

            if not os.path.exists(path_file):
                with path_file.open("w", encoding="utf-8") as f:
                    f.write("{\n\n}")
                self.openTreeViewItem(self.file_model.index(str(path_file)))
            else:
                QMessageBox.warning(self, self.tr("Warning"), self.tr('A file with the same name exists'))

        except Exception:
            QtCore.qWarning(traceback.format_exc())
        self.init_completer()

    @log_exception(True)
    def on_delCard(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            file_name = self.file_model.fileName(index)
            file_path = self.file_model.filePath(index)
            top_parent = self.getDepthParent(index, depth=1)
            if top_parent is None:
                return
            top_name = self.file_model.fileName(top_parent)
            reply = QMessageBox.question(self, self.tr("Warning"),
                                         self.tr('Make sure to delete ') + top_name + ":" + file_name + '?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                if self.file_model.isDir(index):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            self.init_completer()

    def saveTabJsonItem(self, index: int):
        item = self.tabWidget.widget(index)
        if isinstance(item, ItemGUI.ItemGUI) and item.readonly:
            return

        treeViewIndex = self.file_model.index(item.tab_key)
        top_parent = self.getDepthParent(treeViewIndex, depth=1)
        if top_parent is None:
            return
        top_name = self.file_model.fileName(top_parent)
        if top_name == "GameSourceModify" or top_name == "DataObjectModify":
            save_data = self.tabWidget.widget(index).treeView.model().sourceModel().to_json()
            self.delGameSourceModifyTemplate(save_data)
        else:
            save_data = self.tabWidget.widget(index).treeView.model().sourceModel().to_json()
        with open(item.tab_key, "w", encoding="utf-8") as f:
            json.dump(save_data, f, sort_keys=True, indent=4, ensure_ascii=False)
        DataBase.loop_load_mod_simp_cn(save_data, self.mod_info["Namespace"])

    @log_exception(True)
    def on_tabWidgetTabCloseRequested(self, index: int, ask: bool = True):
        item = self.tabWidget.widget(index)
        if isinstance(item, ItemGUI.ItemGUI) and item.readonly:
            del self.tab_item_dict[item.tab_key]
            self.tabWidget.removeTab(index)
            return

        if ask:
            reply = QMessageBox.question(self, self.tr('Save'), self.tr('Save the changes before exit?'),
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
        else:
            reply = QMessageBox.Yes

        tab_key = item.tab_key
        if reply == QMessageBox.Yes:
            self.saveTabJsonItem(index)
            del self.tab_item_dict[tab_key]
            self.tabWidget.removeTab(index)
        elif reply == QMessageBox.No:
            del self.tab_item_dict[tab_key]
            self.tabWidget.removeTab(index)
        elif reply == QMessageBox.Cancel:
            return

    def treeItemDepth(self, index: QModelIndex):
        depth = 0
        while index.parent().isValid():
            depth += 1
            index = index.parent()
        return depth - self.root_depth

    def getDepthParent(self, index: QModelIndex, depth: int):
        if self.treeItemDepth(index) < depth:
            return None
        if self.treeItemDepth(index) == depth:
            return index
        if depth < 0:
            return None
        if depth == 0:
            return self.treeView.rootIndex()
        else:
            parent = index.parent()
            while self.treeItemDepth(parent) != depth:
                parent = parent.parent()
            return parent
        return None

    def openTreeViewItem(self, index: QModelIndex):
        tab_key = self.file_model.filePath(index)
        if tab_key in self.tab_item_dict:
            pass
        else:
            top_parent = self.getDepthParent(index, depth=1)
            if top_parent is None:
                return

            top_name = self.file_model.fileName(top_parent)
            file_name = self.file_model.fileName(index)
            file_path = self.file_model.filePath(index)

            if top_name == "GameSourceModify":
                template_ref_trans = DataBase.AllGuidPlainRev[file_name[:-5]]
                for type_key in DataBase.AllRef["CardData"].keys():
                    if template_ref_trans in DataBase.AllRef["CardData"][type_key]:
                        target_group_name = "CardData"
                        break
                for group_key in DataBase.AllGuid.keys():
                    if template_ref_trans in DataBase.AllGuid[group_key]:
                        target_group_name = group_key
                        break
                template_ref = template_ref_trans
                if template_ref_trans.rfind("(") >= 0:
                    template_ref = template_ref_trans[0:template_ref_trans.rfind("(")]
                template_path = DataBase.AllPathPlain[template_ref]
                with open(file_path, 'r', encoding="utf-8") as f:
                    src_json = json.load(f)
                with open(template_path, 'r', encoding="utf-8") as f:
                    template_json = json.load(f)
                    self.loopDelGameSourceModifyTemplateWarpper(template_json)
                src_json.update(template_json)
                if "UniqueID" in src_json:
                    guid = src_json["UniqueID"]
                else:
                    guid = ""
                item = ModifyItemGUI.ModifyItemGUI(parent=self.tabWidget, field=target_group_name, key=tab_key,
                                                   item_name=file_name[:-5], guid=guid,
                                                   replace_key=Config.ReplaceKey,
                                                   mod_info=self.mod_info, mod_path=self.mod_path)
                item.load_json_data(src_json, is_modify=True)

            elif top_name == "DataObjectModify":
                key = file_name[:-5]
                data_type = Path(file_path).parent.name

                ns, key = resolve_data_key(key)

                ref = f'{ns}:{key}' if ns != '' else key

                path_tmp = DataBase.AllPathPlain.get(ref)
                if path_tmp is None:
                    QMessageBox.warning(self, self.tr("Warning"), self.tr('Not found template!'))
                    return

                with open(file_path, 'r', encoding="utf-8") as f:
                    src_json = json.load(f)

                with open(path_tmp, 'r', encoding="utf-8") as f:
                    template_json = json.load(f)
                    self.loopDelGameSourceModifyTemplateWarpper(template_json)
                src_json.update(template_json)

                item = ModifyItemGUI.ModifyItemGUI(parent=self.tabWidget, field=data_type, key=tab_key,
                                                   item_name=file_name[:-5], replace_key=Config.ReplaceKey,
                                                   mod_info=self.mod_info, mod_path=self.mod_path)
                item.load_json_data(src_json, is_modify=True)

            elif top_name in DataBase.RefGuidList:
                with open(file_path, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    if "UniqueID" in data:
                        guid = data["UniqueID"]
                    else:
                        guid = ""
                item = ItemGUI.ItemGUI(parent=self.tabWidget, field=top_name, key=tab_key, item_name=file_name[:-5],
                                       guid=guid, replace_key=Config.ReplaceKey, mod_info=self.mod_info,
                                       mod_path=self.mod_path)
                item.load_json_data(data)
            elif top_name == "ScriptableObject":
                with open(file_path, 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    if "UniqueID" in data:
                        guid = data["UniqueID"]
                    else:
                        guid = ""
                top2nd_parent = self.getDepthParent(index, depth=2)
                top2nd_name = self.file_model.fileName(top2nd_parent)
                item = ItemGUI.ItemGUI(parent=self.tabWidget, field=top2nd_name, key=tab_key, item_name=file_name[:-5],
                                       guid=guid,
                                       replace_key=Config.ReplaceKey,
                                       mod_info=self.mod_info, mod_path=self.mod_path)
                item.load_json_data(data)
            else:
                print("openTreeViewItem Unexport Type")
                return
            self.tabWidget.addTab(item, file_name[:-5])
            self.tab_item_dict[tab_key] = {"widget": item}
        self.tabWidget.setCurrentWidget(self.tab_item_dict[tab_key]["widget"])

    @log_exception(True)
    def on_treeViewDoubleClicked(self, index: QModelIndex):
        if index.isValid() and not self.file_model.isDir(index) and self.file_model.fileName(index).endswith(".json"):
            self.openTreeViewItem(index)

    def loopDelGameSourceModifyTemplateWarpper(self, json):
        for key in list(json.keys()):
            if key.endswith("WarpType"):
                del json[key]
            if key.endswith("WarpData"):
                json[key[:-8]] = json[key]
                del json[key]

    def delGameSourceModifyTemplate(self, json):
        if type(json) == dict:
            for key in list(json.keys()):
                if not key.endswith("WarpType") and not key.endswith("WarpData") and not key.startswith("$"):
                    del json[key]

    @log_exception(True)
    def on_newMod(self, checked: bool = False):
        if self.tab_item_dict:
            QMessageBox.warning(self, self.tr("Warning"), self.tr('Please close all opened files first'))
            return
        self.new_mod = NewItemGUI.NewItemGUI(self)
        self.new_mod.buttonBox.accepted.connect(self.on_newModButtonBoxAccepted)
        self.new_mod.exec_()

    @log_exception(True)
    def on_newModButtonBoxAccepted(self):
        mod_name = self.new_mod.lineEdit.text()
        if not mod_name:
            return
        if os.path.exists(QDir.currentPath() + r"/Mods/" + mod_name):
            QMessageBox.warning(self, self.tr("Warning"), self.tr('Mod folder with the same name exists'))
            return
        shutil.copytree(DataBase.MainPack.path / 'BaseMod', QDir.currentPath() + r"/Mods/" + mod_name)
        self.load_mod(QDir.currentPath() + r"/Mods/" + mod_name)

    @log_exception(True)
    def on_saveMod(self, checked: bool = False):
        if self.mod_info:
            for i in range(self.tabWidget.count()):
                self.saveTabJsonItem(i)
            with open(Path(self.mod_path).parent / "ModMeta.json", "w", encoding="utf-8") as f:
                json.dump(self.mod_info, f, sort_keys=False, indent=2, ensure_ascii=False)
            DataBase.save_collection()
            DataBase.save_mod_simp_cn(self.mod_path)
            DataBase.LoadModData(self.mod_info["Namespace"], self.mod_path)

    @log_exception(True)
    def on_exportZip(self, checked: bool = False):
        new_item = None

        def callback():
            text = new_item.lineEdit.text()
            if text:
                self.on_saveMod()
                ExportToZip.exportToZip(Path(self.mod_path).parent, text)

        if not self.mod_info:
            return

        meta = self.mod_info
        name = get_mod_display_name(meta)
        version = get_mod_version(meta)

        fn = f'{name}-v{version}' if version else name

        new_item = NewItemGUI.NewItemGUI(self)
        new_item.setWindowTitle("Export Zip")
        new_item.label.setText("Enter file name")
        new_item.lineEdit.setText(fn)
        new_item.buttonBox.accepted.connect(callback)
        new_item.exec_()

    @log_exception(True)
    def on_loadMod(self, checked: bool = False):
        if self.tab_item_dict:
            QMessageBox.warning(self, self.tr("Warning"), self.tr('Please close all opened files first'))
            return
        if Config.LastOpenDir == "":
            mod_path = QFileDialog.getExistingDirectory(self, caption=self.tr('Select a Mod folder'),
                                                        directory=QDir.currentPath())
        else:
            mod_path = QFileDialog.getExistingDirectory(self, caption=self.tr('Select a Mod folder'),
                                                        directory=Config.LastOpenDir)
        if mod_path is None or mod_path == "":
            return
        if "ModMeta.json" not in os.listdir(mod_path):
            QMessageBox.warning(self, self.tr("Warning"), self.tr('Not a valid Mod folder'))
            return

        Config.LastOpenDir = str(Path(mod_path).parent.absolute())
        ConfigManager.save()
        self.load_mod(mod_path)

    def load_mod(self, mod_path: str):
        self.reset()
        self.mod_path = mod_path

        with open(self.mod_path + "/ModMeta.json", "r", encoding='utf-8') as f:
            mod_info: dict = json.load(f)
            self.mod_info = mod_info
        if not "Namespace" in mod_info or not mod_info["Namespace"]:
            mod_info["Namespace"] = os.path.basename(self.mod_path)

        mod_info["Namespace"] = mod_info['Namespace'].replace(':', '').replace('@', '')

        self.mod_path += "/Data"

        DataBase.LoadModData(self.mod_info["Namespace"], self.mod_path)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(self.mod_path)
        self.file_model.setReadOnly(False)
        self.file_model.fileRenamed.connect(self.treeItemRenamed)
        self.treeView.setModel(self.file_model)
        self.treeView.setRootIndex(self.file_model.index(self.mod_path))
        self.root_depth = self.treeItemDepth(self.file_model.index(self.mod_path))
        self.treeView.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeView.setDefaultDropAction(Qt.MoveAction)
        self.treeView.setColumnHidden(1, True)
        self.treeView.setColumnHidden(2, True)
        self.treeView.setColumnHidden(3, True)

        name = get_mod_display_name(mod_info)
        version = get_mod_version(mod_info)
        if not version:
            self.setWindowTitle("%s (%s)" % (self.srcTitle, name))
        else:
            self.setWindowTitle("%s (%s)" % (self.srcTitle, f'{name} v{version}'))
        self.init_completer()


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    QTextCodec.setCodecForLocale(QTextCodec.codecForName("UTF-8"))
    app = QApplication(sys.argv)
    main = ModEditorGUI()
    main.show()
    sys.exit(app.exec_())
