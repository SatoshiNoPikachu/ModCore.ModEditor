# -*- coding: utf-8 -*- 

from ui.Ui_Item import *
from QJsonData import *
from NewItemGUI import *
from ItemDelegate import *
from CollectionGUI import *
from DataBase import *


class ItemGUI(QWidget, Ui_Item):
    def __init__(self, parent=None, field: str = "", key: str = "", item_name: str = "", guid: str = "",
                 replace_key: bool = False, mod_info: dict = None, mod_path: str = "", readonly: bool = False):
        super(ItemGUI, self).__init__(parent)
        self.setupUi(self)
        self.field = field
        self.item_name = item_name
        self.guid = guid
        self.mod_info = mod_info
        self.mod_path = mod_path
        self.tab_key = key
        self.replace_key = replace_key
        self.readonly = readonly
        self.treeView.setItemDelegateForColumn(1, ItemDelegate(self.field, self.treeView))
        self.treeView.setItemDelegateForColumn(4, EnableDelegate(self.treeView))
        self.treeView.setSortingEnabled(True)
        self.treeView.header().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        self.treeView.header().setSortIndicator(4, Qt.SortOrder.DescendingOrder)
        self.treeView.setDragEnabled(True)
        if Config.AutoResize:
            self.treeView.header().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        self.treeView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        if readonly:
            self.treeView.customContextMenuRequested.connect(self.on_tree_view_readonly_custom_context_menu_requested)
        else:
            self.treeView.customContextMenuRequested.connect(self.on_tree_view_custom_context_menu_requested)

        self.showInvalidButton.setText(self.tr("Show invalid entries"))
        self.show_invalid = False
        self.showInvalidButton.clicked.connect(self.on_show_invalid_button_clicked)

        self.lineEdit.textChanged.connect(self.on_line_edit_text_changed)

        self.addSpecialButton()

    def addSpecialButton(self):
        pass

    def setTabKey(self, key: str):
        self.tab_key = key

    def load_json_data(self, json_data: dict, is_modify: bool = False):
        self.model = QJsonModel(self.field, is_modify=is_modify, readonly=self.readonly)
        self.model.loadJson(json_data)
        self.proxy_model = QJsonProxyModel(self.treeView)
        self.proxy_model.setSourceModel(self.model)
        self.treeView.setModel(self.proxy_model)
        # for i in range(self.model.columnCount()):
        #     self.treeView.resizeColumnToContents(i)

    @log_exception(True)
    def on_show_invalid_button_clicked(self, checked: bool = False) -> None:
        if not self.show_invalid:
            self.showInvalidButton.setText(self.tr("Hide invalid entries"))
            self.proxy_model.setVaildFilter(False)
            self.show_invalid = True
        else:
            self.showInvalidButton.setText(self.tr("Show invalid entries"))
            self.proxy_model.setVaildFilter(True)
            self.show_invalid = False

    @log_exception(True)
    def on_line_edit_text_changed(self, key: str) -> None:
        self.proxy_model.setKeyFilter(key)

    @log_exception(True)
    def on_tree_view_readonly_custom_context_menu_requested(self, pos: QPoint):
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        model = index.model()
        if hasattr(model, 'mapToSource'):
            srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
        else:
            srcModel, item, srcIndex = model, index.internalPointer(), index

        if item.parent is None:
            return

        menu = QMenu(self.treeView)

        if item.type() == "list" or item.type() == "dict":
            pExpandAct = QAction(self.tr("Expand All"), menu)
            pExpandAct.triggered.connect(self.on_act_expand_all)
            menu.addAction(pExpandAct)

        if item.field() in DataBase.RefNameList or item.field() in DataBase.RefGuidList or item.field() == "ScriptableObject":
            if item.type() == "list":
                pSaveListAct = QAction(self.tr("Save List Collection"), menu)
                pSaveListAct.triggered.connect(self.on_save_ref_list_item)
                menu.addAction(pSaveListAct)
        elif item.field() == "WarpType" or item.field() == "WarpRef" or item.field() is None or item.field() == "" or \
                item.field() == "SpecialWarp" or item.field() == "None" or item.field() == "Boolean" or item.field() == "Int32" or item.field() == "Single" or item.field() == "String":
            pass
        else:
            if item.type() == "dict":
                pSaveAct = QAction(self.tr("Save Collection"), menu)
                pSaveAct.triggered.connect(self.on_save_item)
                menu.addAction(pSaveAct)
            elif item.type() == "list":
                pSaveListAct = QAction(self.tr("Save List Collection"), menu)
                pSaveListAct.triggered.connect(self.on_save_list_item)
                menu.addAction(pSaveListAct)

        if len(menu.actions()):
            menu.popup(self.sender().mapToGlobal(pos))

    @log_exception(True)
    def on_tree_view_custom_context_menu_requested(self, pos: QPoint) -> None:
        index = self.treeView.currentIndex()
        if not index.isValid():
            return

        model = index.model()
        if hasattr(model, 'mapToSource'):
            srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
        else:
            srcModel, item, srcIndex = model, index.internalPointer(), index

        if item.parent is None:
            return

        menu = QMenu(self.treeView)
        if item.field() == "SpecialWarp" and item.depth() == 1:
            pDeleteAct = QAction(self.tr("Delete"), menu)
            pDeleteAct.triggered.connect(self.on_del_item)
            menu.addAction(pDeleteAct)

        if item.parent().type() == "list" and item.depth() > 1:
            pDeleteAct = QAction(self.tr("Delete"), menu)
            pDeleteAct.triggered.connect(self.on_del_item_from_list)
            menu.addAction(pDeleteAct)

        if item.type() == "list" or item.type() == "dict":
            pExpandAct = QAction(self.tr("Expand All"), menu)
            pExpandAct.triggered.connect(self.on_act_expand_all)
            menu.addAction(pExpandAct)

            # pCollapseAct = QAction(self.tr("Collapse All"), menu)
            # pCollapseAct.triggered.connect(self.on_act_collapse_all)
            # menu.addAction(pCollapseAct)

        if item.type() == "list" and item.field() == "WarpRef":
            pDelListAct = QAction(self.tr("Delete Whole List"), menu)
            pDelListAct.triggered.connect(self.on_del_list_item)
            menu.addAction(pDelListAct)

        if item.field() in DataBase.RefNameList or item.field() in DataBase.RefGuidList or item.field() == "ScriptableObject":
            if item.type() == "list":
                pRefAct = QAction(self.tr("Append Reference"), menu)

                pSaveListAct = QAction(self.tr("Save List Collection"), menu)
                pSaveListAct.triggered.connect(self.on_save_ref_list_item)
                menu.addAction(pSaveListAct)

                pNewListAct = QAction(self.tr("Load List Collection"), menu)
                pNewListAct.triggered.connect(self.on_load_ref_list_item)
                menu.addAction(pNewListAct)

                if item.key() == "InventorySlots":
                    pEmptyRefAct = QAction(self.tr("Append Inventory Slot"), menu)
                    pEmptyRefAct.triggered.connect(self.on_add_empty_ref_item)
                    menu.addAction(pEmptyRefAct)
            else:
                pRefAct = QAction(self.tr("Reference"), menu)
            pRefAct.triggered.connect(self.on_add_ref_item)
            menu.addAction(pRefAct)
        elif item.field() == "WarpType" or item.field() == "WarpRef" or item.field() is None or item.field() == "" or \
                item.field() == "SpecialWarp" or item.field() == "None" or item.field() == "Boolean" or item.field() == "Int32" or item.field() == "Single" or item.field() == "String":
            pass
        else:
            if item.depth() == 1:
                pCopyAct = QAction(self.tr("Copy Template and Overwrite"), menu)
                pCopyAct.triggered.connect(self.on_copy_item)
                menu.addAction(pCopyAct)

                if item.type() == "list":
                    pAddAct = QAction(self.tr("Append Template Entries"), menu)
                    pAddAct.triggered.connect(self.on_add_item_to_list)
                    menu.addAction(pAddAct)

            if item.type() == "dict":
                pCopyCollAct = QAction(self.tr("Copy Collection and Overwrite"), menu)
                pCopyCollAct.triggered.connect(self.on_copy_coll_item)
                menu.addAction(pCopyCollAct)

                pSaveAct = QAction(self.tr("Save Collection"), menu)
                pSaveAct.triggered.connect(self.on_save_item)
                menu.addAction(pSaveAct)

            if item.type() == "list":
                pNewAct = QAction(self.tr("New Empty Entry"), menu)
                pNewAct.triggered.connect(self.on_new_item_to_list)
                menu.addAction(pNewAct)

                pNewAct = QAction(self.tr("Load Collection"), menu)
                pNewAct.triggered.connect(self.on_load_item)
                menu.addAction(pNewAct)

                pSaveListAct = QAction(self.tr("Save List Collection"), menu)
                pSaveListAct.triggered.connect(self.on_save_list_item)
                menu.addAction(pSaveListAct)

                pNewListAct = QAction(self.tr("Load List Collection"), menu)
                pNewListAct.triggered.connect(self.on_load_list_item)
                menu.addAction(pNewListAct)

                pDelListAct = QAction(self.tr("Delete Whole List"), menu)
                pDelListAct.triggered.connect(self.on_del_list_item)
                menu.addAction(pDelListAct)

        if len(menu.actions()):
            menu.popup(self.sender().mapToGlobal(pos))

    def collapse_children(self, index: QModelIndex) -> None:
        if index.isValid():
            for i in range(index.model().rowCount(index)):
                child_index = index.child(i, 0)
                self.collapse_children(child_index)
            self.treeView.collapse(index)

    @log_exception(True)
    def on_act_collapse_all(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            self.collapse_children(index)

    @log_exception(True)
    def on_act_expand_all(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            self.treeView.expandRecursively(index)

    @log_exception(True)
    def on_del_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index
            self.model.deleteItem(srcIndex)

    @log_exception(True)
    def on_del_item_from_list(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        self.model.removeListItem(index)

    @log_exception(True)
    def on_del_list_item(self, checked: bool = False) -> None:
        reply = QMessageBox.question(self, self.tr("Warning"), self.tr("Sure you want to delete the whole list?"),
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.No)
        if reply == QMessageBox.Yes:
            index = self.treeView.currentIndex()
            self.model.removeAllListChild(index)

    @log_exception(True)
    def on_add_item_to_list(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

            select = SelectGUI(self.treeView, field_name=self.field, mode=SelectGUI.Append)
            select.exec_()

            if select.write_flag:
                if self.field in DataBase.AllPath:
                    template_key = select.lineEdit.text().split("(")[0]
                    if template_key in DataBase.AllPath[self.field]:
                        with open(DataBase.AllPath[self.field][template_key], 'r', encoding='utf-8') as f:
                            data = json.load(f)[item.key()]
                        if type(data) is list:
                            for sub_data in data:
                                child_key = 0
                                while str(child_key) in item.mChilds:
                                    child_key += 1
                                if self.replace_key:
                                    replace_l10n_key(sub_data, self.mod_info["Namespace"],
                                                     self.item_name, self.guid, item.key(),
                                                     child_key)
                                self.model.addJsonItem(srcIndex, sub_data, item.field(), str(child_key))
                        return

    @log_exception(True)
    def on_new_item_to_list(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

        if item.field() in DataBase.AllBaseJsonData:
            data = DataBase.AllBaseJsonData[item.field()]
            if item.field() in DataBase.AllEnum:
                data = 0
            child_key = 0
            while str(child_key) in item.mChilds:
                child_key += 1
            self.model.addJsonItem(srcIndex, data, item.field(), str(child_key))
            return

    @log_exception(True)
    def on_load_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index
        if item.field() not in DataBase.AllCollection or len(DataBase.AllCollection[item.field()]) == 0:
            QMessageBox.information(self, self.tr("Info"),
                                    self.tr("The related collection is empty, please add the collection first"))
            return
        self.loadCollection = CollectionGUI(item.field(), DataBase.AllCollection, self)
        self.loadCollection.setWindowTitle(item.field() + self.tr(" type collection list"))
        self.loadCollection.exec_()

        name = self.loadCollection.lineEdit.text()

        if self.loadCollection.write_flag and name in DataBase.AllCollection[item.field()]:
            child_key = 0
            while str(child_key) in item.mChilds:
                child_key += 1
            data = copy.deepcopy(DataBase.AllCollection[item.field()][name])
            if self.replace_key:
                replace_l10n_key(data, self.mod_info["Namespace"], self.item_name, self.guid,
                                 item.key(), child_key)
            self.model.addJsonItem(srcIndex, data, item.field(), str(child_key))
            return

    @log_exception(True)
    def on_load_list_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index
        if item.field() not in DataBase.AllListCollection or len(DataBase.AllListCollection[item.field()]) == 0:
            QMessageBox.information(self, self.tr("Info"),
                                    self.tr("The related collection is empty, please add the collection first"))
            return
        self.loadCollection = CollectionGUI(item.field(), DataBase.AllListCollection, self)
        self.loadCollection.setWindowTitle(item.field() + self.tr(" type collection list"))
        self.loadCollection.exec_()

        name = self.loadCollection.lineEdit.text()

        if self.loadCollection.write_flag and name in DataBase.AllListCollection[item.field()]:
            for i in range(len(DataBase.AllListCollection[item.field()][name])):
                child_key = 0
                while str(child_key) in item.mChilds:
                    child_key += 1
                data = copy.deepcopy(DataBase.AllListCollection[item.field()][name][i])
                if self.replace_key:
                    replace_l10n_key(data, self.mod_info["Namespace"], self.item_name,
                                     self.guid,
                                     item.key(), child_key)
                self.model.addJsonItem(srcIndex, data, item.field(), str(child_key))
            return

    @log_exception(True)
    def on_load_ref_list_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index
        if item.field() not in DataBase.AllListCollection or len(DataBase.AllListCollection[item.field()]) == 0:
            QMessageBox.information(self, self.tr("Info"),
                                    self.tr("The related collection is empty, please add the collection first"))
            return
        self.loadCollection = CollectionGUI(item.field(), DataBase.AllListCollection, self)
        self.loadCollection.setWindowTitle(item.field() + self.tr(" type collection list"))
        self.loadCollection.exec_()

        warpTypeItem = item.brother(item.key() + "WarpType")
        warpDataItem = item.brother(item.key() + "WarpData")
        if warpTypeItem is None or warpDataItem is None:
            return

        name = self.loadCollection.lineEdit.text()

        if self.loadCollection.write_flag and name in DataBase.AllListCollection[item.field()]:
            for i in range(len(DataBase.AllListCollection[item.field()][name])):
                data = copy.deepcopy(DataBase.AllListCollection[item.field()][name][i])
                self.add_ref_item(data, item, index)
            return

    @log_exception(True)
    def on_save_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

        self.newSave = NewItemGUI(self)
        self.newSave.buttonBox.accepted.connect(lambda: self.on_new_save_button_box_accepted(item))
        self.newSave.setWindowTitle(self.tr("Add ") + item.field() + self.tr(" type collection"))
        self.newSave.exec_()

    @log_exception(True)
    def on_save_list_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

        self.newSaveList = NewItemGUI(self)
        self.newSaveList.buttonBox.accepted.connect(lambda: self.on_new_save_list_button_box_accepted(item))
        self.newSaveList.setWindowTitle(self.tr("Add ") + item.field() + self.tr("[] type collection"))
        self.newSaveList.exec_()

    @log_exception(True)
    def on_save_ref_list_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

        self.newSaveList = NewItemGUI(self)
        self.newSaveList.buttonBox.accepted.connect(lambda: self.on_new_save_ref_list_button_box_accepted(item))
        self.newSaveList.setWindowTitle(self.tr("Add ") + item.field() + self.tr("[] type collection"))
        self.newSaveList.exec_()

    @log_exception(True)
    def on_new_save_button_box_accepted(self, item: QJsonTreeItem):
        name = self.newSave.lineEdit.text()
        if not name:
            return
        if item.field() not in DataBase.AllCollection:
            DataBase.AllCollection[item.field()] = {}
        if name in DataBase.AllCollection[item.field()]:
            reply = QMessageBox.question(self, self.tr("Warning"), self.tr("Cover the collection of the same name?"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        DataBase.AllCollection[item.field()][name] = self.model.to_json(item)

    @log_exception(True)
    def on_new_save_list_button_box_accepted(self, item: QJsonTreeItem):
        name = self.newSaveList.lineEdit.text()
        if not name:
            return
        if item.field() not in DataBase.AllListCollection:
            DataBase.AllListCollection[item.field()] = {}
        if name in DataBase.AllListCollection[item.field()]:
            reply = QMessageBox.question(self, self.tr("Warning"), self.tr("Cover the collection of the same name?"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        DataBase.AllListCollection[item.field()][name] = self.model.to_json(item)

    @log_exception(True)
    def on_new_save_ref_list_button_box_accepted(self, item: QJsonTreeItem):
        name = self.newSaveList.lineEdit.text()
        if not name:
            return
        warpTypeItem = item.brother(item.key() + "WarpType")
        warpDataItem = item.brother(item.key() + "WarpData")
        if warpTypeItem is None or warpDataItem is None:
            return

        if item.field() not in DataBase.AllListCollection:
            DataBase.AllListCollection[item.field()] = {}
        if name in DataBase.AllListCollection[item.field()]:
            reply = QMessageBox.question(self, self.tr("Warning"), self.tr("Cover the collection of the same name?"),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        DataBase.AllListCollection[item.field()][name] = self.model.to_json(warpDataItem)

    @log_exception(True)
    def on_copy_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

            select = SelectGUI(self.treeView, field_name=self.field, mode=SelectGUI.Copy)
            select.exec_()

            if select.write_flag:
                if self.field in DataBase.AllPath:
                    template_key = select.lineEdit.text().split("(")[0]
                    if template_key in DataBase.AllPath[self.field]:
                        with open(DataBase.AllPath[self.field][template_key], 'r', encoding='utf-8') as f:
                            data = json.load(f)[item.key()]
                        if self.replace_key:
                            replace_l10n_key(data, self.mod_info["Namespace"], self.item_name,
                                             self.guid)
                        self.model.deleteItem(srcIndex)
                        self.model.addJsonItem(srcIndex.parent(), data, item.field(), item.key())
                        return

    @log_exception(True)
    def on_copy_coll_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

            if item.field() not in DataBase.AllCollection or len(DataBase.AllCollection[item.field()]) == 0:
                QMessageBox.information(self, self.tr("Info"),
                                        self.tr("The related collection is empty, please add the collection first"))
                return
            self.loadCollection = CollectionGUI(item.field(), DataBase.AllCollection, self)
            self.loadCollection.setWindowTitle(item.field() + self.tr(" type collection"))
            self.loadCollection.exec_()

            name = self.loadCollection.lineEdit.text()
            if self.loadCollection.write_flag and name in DataBase.AllCollection[item.field()]:
                self.model.deleteItem(srcIndex)
                data = copy.deepcopy(DataBase.AllCollection[item.field()][name])
                if self.replace_key:
                    replace_l10n_key(data, self.mod_info["Namespace"], self.item_name,
                                     self.guid)
                self.model.addJsonItem(srcIndex.parent(), data, item.field(), item.key())
                return

    def add_ref_item(self, data: str, item, index: QModelIndex):
        field = item.field()

        if data == "":
            if item.type() == "list":
                reply = QMessageBox.question(self, self.tr('Warning'),
                                             self.tr('Sure you want to delete the whole list?'),
                                             QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
                if reply != QMessageBox.Yes:
                    return
            self.model.addRefWarp(index, data)

        elif field in DataBase.RefGuidList:
            if item.field() == "CardData":
                if data in DataBase.AllCardData:
                    self.model.addRefWarp(index, DataBase.AllCardData[data])
                    return
            else:
                if data in DataBase.AllGuid[item.field()]:
                    self.model.addRefWarp(index, DataBase.AllGuid[item.field()][data])
                    return

        elif field == "ScriptableObject":
            if (t := resolve_ref_type(data)) is None:
                QMessageBox.warning(self, self.tr('Warning'), self.tr('Unspecified type, should be "Type|DataKey"'))
            elif (d := DataBase.AllScriptableObject.get(t)) is None:
                reply = QMessageBox.question(self, self.tr('Information'),
                                             self.tr("Type %s not found, still reference?") % t,
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.model.addRefWarp(index, data)
            elif (v := d.get(data)) is None:
                self.model.addRefWarp(index, data)
            else:
                self.model.addRefWarp(index, v)

        elif field in DataBase.RefNameList:
            self.model.addRefWarp(index, remove_postfix(data))

    @log_exception(True)
    def on_add_ref_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

            select = SelectGUI(self.treeView, field_name=item.field(), mode=SelectGUI.Ref)
            select.exec_()

            if select.write_flag:
                self.add_ref_item(select.lineEdit.text(), item, index)

    @log_exception(True)
    def on_add_empty_ref_item(self, checked: bool = False) -> None:
        index = self.treeView.currentIndex()
        if index.isValid():
            model = index.model()
            if hasattr(model, 'mapToSource'):
                srcModel, item, srcIndex = model.getSourceModelItemIndex(index)
            else:
                srcModel, item, srcIndex = model, index.internalPointer(), index

            child_key = 0
            while str(child_key) in item.mChilds:
                child_key += 1
            srcModel.addJsonItem(srcIndex, {"m_FileID": "", "m_PathID": ""}, None, str(child_key))
