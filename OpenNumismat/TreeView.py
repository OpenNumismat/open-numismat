from dataclasses import dataclass

from PySide6.QtSql import QSqlQuery
from PySide6.QtCore import Qt, QCollator, QLocale, QEvent
from PySide6.QtWidgets import (
    QDialog,
    QMenu,
    QStyledItemDelegate,
    QToolTip,
    QTreeWidget,
    QTreeWidgetItem,
)

from OpenNumismat.EditCoinDialog.EditCoinDialog import EditCoinDialog
from OpenNumismat.CustomizeTreeDialog import CustomizeTreeDialog
from OpenNumismat.Tools.Gui import statusIcon
from OpenNumismat.Tools.Converters import numberWithFraction, compareYears
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Settings import Settings


@dataclass(slots=True)
class ChildItem():
    label: str
    datas: list
    filters: list


class YearTreeWidgetItem(QTreeWidgetItem):

    def __lt__(self, other):
        left = self.data(0, TreeView.SortDataRole)
        right = other.data(0, TreeView.SortDataRole)

        if not left or not right:
            return super().__lt__(other)

        return compareYears(left[0], right[0]) < 0


class TreeWidgetItem(QTreeWidgetItem):

    def __lt__(self, other):
        left = self.data(0, TreeView.SortDataRole)
        right = other.data(0, TreeView.SortDataRole)

        if not left or not right:
            return super().__lt__(other)

        min_len = min(len(left), len(right))
        collator = self.treeWidget().collator

        for i in reversed(range(min_len)):
            if left[i] == right[i]:
                pass
            else:
                if isinstance(left[i], str) or isinstance(right[i], str):
                    return collator.compare(str(left[i]), str(right[i])) < 0
                else:
                    return left[i] < right[i]

        return len(left) < len(right)


class AutoToolTipDelegate(QStyledItemDelegate):

    def helpEvent(self, event, view, option, index):
        if not event or not view:
            return False

        if event.type() == QEvent.ToolTip:
            rect = view.visualRect(index)
            size = self.sizeHint(option, index)
            width = view.frameRect().width()
            if view.verticalScrollBar().isVisible():
                width -= view.verticalScrollBar().width()
            if rect.x() <= -5 or rect.x() + size.width() > width:
                tooltip = index.data(Qt.DisplayRole)
                QToolTip.showText(event.globalPos(), tooltip, view)
                return True

            if not super().helpEvent(event, view, option, index):
                QToolTip.hideText()
            return True

        return super().helpEvent(event, view, option, index)


class TreeView(QTreeWidget):
    FiltersRole = Qt.UserRole
    FieldsRole = Qt.UserRole + 1
    ParamRole = Qt.UserRole + 2
    ParamChildRole = Qt.UserRole + 3
    SortDataRole = Qt.UserRole + 4

    def __init__(self, treeParam, parent=None):
        super().__init__(parent)

        self.convert_fraction = treeParam.convert_fraction

        self.setHeaderHidden(True)
        self.setAutoScroll(False)

        self.currentItemChanged.connect(self.itemActivatedEvent)
        self.itemExpanded.connect(self.expandedEvent)
        self.collapsed.connect(self.collapsedEvent)

        self.treeParam = treeParam

        # Changing of TreeView is enabled (by signals from model or ListView)
        self.changingEnabled = True

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

        self.setItemDelegate(AutoToolTipDelegate())

    def setModel(self, model, reference):
        self.db = model.database()
        self.model = model
        self.reference = reference

        self.treeParam.rootTitle = model.title
        rootItem = QTreeWidgetItem([model.title, ])
        rootItem.setData(0, self.ParamRole, 0)
        rootItem.setData(0, self.ParamChildRole, 1)
        rootItem.setData(0, self.FiltersRole, '')

        self.addTopLevelItem(rootItem)

    def expandedEvent(self, item):
        self.__fillChilds(item)

        self.resizeColumnToContents(0)

    def __value2label(self, field, text):
        if field == 'status':
            label = Statuses[text]
        elif field == 'year':
            label = text
            if text[0] == '-':
                label = f"{text[1:]} BC"
        elif field == 'value':
            label, _ = numberWithFraction(text, self.convert_fraction)
        else:
            label = text

        return label

    def __record2label(self, record, fields):
        label_parts = []

        for field in fields:
            text = str(record.value(field))
            if text:
                label = self.__value2label(field, text)
                label_parts.append(label)

        if label_parts:
            return ' '.join(label_parts)
        else:
            return self.tr("Other")

    def __processChilds(self, parent_fields, cur_fields, filters):
        child_items = {}

        sql_fields = ','.join(cur_fields + parent_fields)
        sql = f"SELECT DISTINCT {sql_fields} FROM coins"
        if filters:
            sql += f" WHERE {filters}"
        query = QSqlQuery(sql, self.db)
        while query.next():
            record = query.record()

            label = self.__record2label(record, parent_fields)
            if label not in child_items:
                child_items[label] = []

            child_label = self.__record2label(record, cur_fields)

            orig_data = []
            child_filters = []
            for field in cur_fields:
                value = record.value(field)

                orig_data.append(value)
                text = str(value)
                if text:
                    escapedText = text.replace("'", "''")
                    child_filters.append(f"{field}='{escapedText}'")
                else:
                    child_filters.append(f"ifnull({field},'')=''")

            child_item = ChildItem(child_label, orig_data, child_filters)
            child_items[label].append(child_item)

        return child_items

    def __isEmptyChilds(self, child_items):
        if len(child_items) == 0 or \
                (len(child_items[self.tr("Other")]) == 1 and \
                 child_items[self.tr("Other")][0].label == self.tr("Other")):
            return True
        elif len(child_items) == 0 or \
                (len(child_items[self.tr("Other")]) == 2 and \
                 child_items[self.tr("Other")][0].label == self.tr("Other") and \
                 child_items[self.tr("Other")][1].label == self.tr("Other")):
            return True
        else:
            return False

    def __isEmptyChild(self, child_items):
        if len(child_items) == 1 and \
                child_items[0].label == self.tr("Other"):
            return True
        elif len(child_items) == 2 and \
                child_items[0].label == self.tr("Other") and \
                child_items[1].label == self.tr("Other"):
            return True
        else:
            return False

    def __fillRoot(self, item):
        paramIndex = item.data(0, self.ParamRole)
        filters = item.data(0, self.FiltersRole)

        fields = self.treeParam.fieldNames(paramIndex)
        if not fields:
            return

        child_items = self.__processChilds([], fields, filters)
        if self.__isEmptyChilds(child_items):
            paramIndex += 1
            item.setData(0, self.ParamRole, paramIndex)
            item.setData(0, self.ParamChildRole, paramIndex + 1)

            self.__fillRoot(item)
            return

        label = self.tr("Other")
        self.__addChilds(item, child_items[label])

    def __fillChilds(self, item):
        paramChildIndex = item.data(0, self.ParamChildRole)

        self.__fillChilds1(item, paramChildIndex)

    def __fillChilds1(self, item, paramChildIndex):
        paramIndex = item.data(0, self.ParamRole)
        filters = item.data(0, self.FiltersRole)

        fields = self.treeParam.fieldNames(paramIndex)
        if not fields:
            return

        fields_child = self.treeParam.fieldNames(paramChildIndex)
        if not fields_child:
            return

        child_items = self.__processChilds(fields, fields_child, filters)

        good_children = []
        bad_children = []
        for child_label, child in child_items.items():
            if not self.__isEmptyChild(child):
                good_children.append(child_label)
            else:
                bad_children.append(child_label)

        for i in range(item.childCount()):
            child = item.child(i)
            child_label = child.text(0)
            if child.childCount() == 0 and child_label in good_children:
                child.setData(0, self.ParamRole, paramChildIndex)
                child.setData(0, self.ParamChildRole, paramChildIndex + 1)
                self.__addChilds(child, child_items[child_label])

        if bad_children:
            self.__fillChilds1(item, paramChildIndex + 1)

    def __addChilds(self, item, child_items):
        filter_ = item.data(0, self.FiltersRole)
        paramIndex = item.data(0, self.ParamRole)
        paramChildIndex = item.data(0, self.ParamChildRole)
        fields = self.treeParam.fieldNames(paramIndex)

        hasEmpty = False
        for child_item in child_items:
            if child_item.label == self.tr("Other"):
                hasEmpty = True
                continue

            if len(fields) == 1 and fields[0] == 'year':
                child = YearTreeWidgetItem([child_item.label, ])
            else:
                child = TreeWidgetItem([child_item.label, ])
            child.setData(0, self.SortDataRole, child_item.datas)
            child.setData(0, self.ParamRole, paramChildIndex)
            child.setData(0, self.ParamChildRole, paramChildIndex + 1)
            child.setData(0, self.FieldsRole, fields)

            combined_filter = []
            if child_item.filters:
                combined_filter = child_item.filters
            if filter_:
                combined_filter.append(filter_)
            newFilters = ' AND '.join(combined_filter)
            child.setData(0, self.FiltersRole, newFilters)

            if fields[0] == 'status':
                icon = statusIcon(child_item.datas[0])
            else:
                icon = self.reference.getIcon(fields[0], child_item.datas[0])
            if icon:
                child.setIcon(0, icon)

            item.addChild(child)

            # Restore selection
            if newFilters == self.model.extFilter:
                self.currentItemChanged.disconnect(self.itemActivatedEvent)
                self.setCurrentItem(child)
                self.currentItemChanged.connect(self.itemActivatedEvent)

        item.sortChildren(0, Qt.AscendingOrder)

        if hasEmpty and len(fields) == 1 and item.childCount() > 0:
            text = self.tr("Other")
            newFilters = f"ifnull({fields[0]},'')=''"
            if filter_:
                newFilters = f"{filter_} AND {newFilters}"

            child = QTreeWidgetItem([text, ])
            child.setData(0, self.ParamRole, paramChildIndex)
            child.setData(0, self.ParamChildRole, paramChildIndex + 1)
            child.setData(0, self.FiltersRole, newFilters)
            child.setData(0, self.FieldsRole, fields)
            item.addChild(child)

            # Restore selection
            if newFilters == self.model.extFilter:
                self.currentItemChanged.disconnect(self.itemActivatedEvent)
                self.setCurrentItem(child)
                self.currentItemChanged.connect(self.itemActivatedEvent)

    def collapsedEvent(self, _parentItem):
        self.resizeColumnToContents(0)

    def modelChanged(self):
        if self.changingEnabled:
            self.collapseAll()
            rootItem = self.topLevelItem(0)

            self.currentItemChanged.disconnect(self.itemActivatedEvent)
            rootItem.takeChildren()  # remove all children
            self.currentItemChanged.connect(self.itemActivatedEvent)

            self.__fillRoot(rootItem)
            self.expandItem(rootItem)

    def rowChangedEvent(self, current):
        if self.changingEnabled:
            if current.isValid():
                self.collapseAll()
                self.scrollToIndex(current)

    def scrollToIndex(self, index, parent=None):
        if not parent:
            parent = self.topLevelItem(0)

        for i in range(parent.childCount()):
            subItem = parent.child(i)
            fields = subItem.data(0, self.FieldsRole)
            text1 = subItem.text(0)
            textPart = []
            for field in fields:
                index = self.model.index(index.row(),
                                         self.model.fieldIndex(field))
                if field in ('status', 'year'):
                    textPart.append(str(index.data()))
                else:
                    val = str(index.data(Qt.UserRole))
                    if val:
                        textPart.append(val)
            text2 = ' '.join(textPart)
            if text1 == text2 or (not text2 and text1 == self.tr("Other")):
                self.expandItem(parent)
                self.scrollToItem(subItem)
                self.scrollToIndex(index, subItem)
                break

    def scrollToItem(self, item, hint=QTreeWidget.EnsureVisible):
        super().scrollToItem(item, hint)

        parentItem = item.parent()
        if parentItem:
            itemRect = self.visualItemRect(parentItem)
            if itemRect.x() < 0:
                columnWidth = self.columnWidth(0)
                itemWidth = itemRect.width()
                self.horizontalScrollBar().setValue(columnWidth - itemWidth)
            elif self.viewport().width() / 2 < itemRect.x():
                columnWidth = self.columnWidth(0)
                itemWidth = itemRect.width()
                self.horizontalScrollBar().setValue(itemRect.x())

    def itemActivatedEvent(self, current, _previous):
        if current:
            self.scrollToItem(current)
            self.resizeColumnToContents(0)

            self.changingEnabled = False
            filter_ = current.data(0, self.FiltersRole)
            self.model.setAdditionalFilter(filter_)
            self.changingEnabled = True

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act = menu.addAction(self.tr("Add new coin..."), self._addCoin)
        if not (self.model.rowCount() and self.selectedItems()):
            act.setDisabled(True)
        act = menu.addAction(self.tr("Edit coins..."), self._multiEdit)
        if not (self.model.rowCount() and self.selectedItems()):
            act.setDisabled(True)
        menu.addSeparator()
        menu.addAction(self.tr("Customize tree..."), self.customizeTree)
        menu.exec_(self.mapToGlobal(event.pos()))

    def customizeTree(self):
        dialog = CustomizeTreeDialog(self.model, self.treeParam, self)
        if dialog.exec_() == QDialog.Accepted:
            self.treeParam.save()
            self.modelChanged()
        dialog.deleteLater()

    def _addCoin(self):
        self.changingEnabled = False
        storedFilter = self.model.intFilter
        # TODO: This change ListView!
        self.model.setFilter('')
        self.changingEnabled = True

        newRecord = self.model.record()
        # Fill new record with values of first record
        for j in range(newRecord.count()):
            newRecord.setValue(j, self.model.record(0).value(j))
        tag_ids = self.model.record(0).value('tags')

        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(newRecord.count()):
                value = record.value(j)
                if newRecord.value(j) != value or not value:
                    newRecord.setNull(j)
            tag_ids = list([tag_id for tag_id in tag_ids if tag_id in record.value('tags')])
        newRecord.setValue('tags', tag_ids)

        self.model.addCoin(newRecord, self)

        self.model.setFilter(storedFilter)

    def _multiEdit(self):
        self.changingEnabled = False
        storedFilter = self.model.intFilter
        self.model.setFilter('')
        self.changingEnabled = True

        multiRecord, usedFields = self.model.multiRecord()

        # TODO: Make identical with ListView._multiEdit
        dialog = EditCoinDialog(self.model, multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.model.setMultiRecord(multiRecord, dialog.getUsedFields(), parent=self)

        dialog.deleteLater()
        self.model.setFilter(storedFilter)

    def clearSelection(self):
        super().clearSelection()
        self.setCurrentItem(None)
