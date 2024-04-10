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
from OpenNumismat.Tools import Gui
from OpenNumismat.Tools.Gui import statusIcon
from OpenNumismat.Tools.Converters import numberWithFraction, compareYears
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Settings import Settings


class YearTreeWidgetItem(QTreeWidgetItem):

    def __lt__(self, other):
        left = self.data(0, Qt.UserRole + 3)
        right = other.data(0, Qt.UserRole + 3)

        if not left or not right:
            return super().__lt__(other)

        return compareYears(left[0], right[0]) < 0


class TreeWidgetItem(QTreeWidgetItem):

    def __lt__(self, other):
        left = self.data(0, Qt.UserRole + 3)
        right = other.data(0, Qt.UserRole + 3)

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
    SortDataRole = Qt.UserRole + 3

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
        rootItem.setData(0, self.FiltersRole, '')

        self.addTopLevelItem(rootItem)

    def expandedEvent(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            if child.childCount() == 0:
                paramIndex = child.data(0, self.ParamRole) + 1
                filters = child.data(0, self.FiltersRole)
                self.__updateChilds(child, paramIndex, filters)

        self.resizeColumnToContents(0)

    def collapsedEvent(self, _parentItem):
        self.resizeColumnToContents(0)

    def __updateChilds(self, item, paramIndex=0, filters=''):
        fields = self.treeParam.fieldNames(paramIndex)
        if not fields:
            return

        sql = f"SELECT DISTINCT {','.join(fields)} FROM coins"
        if filters:
            sql += f" WHERE {filters}"
        query = QSqlQuery(sql, self.db)
        hasEmpty = False
        while query.next():
            record = query.record()
            data = []
            orig_data = []
            filterSql = []
            for i in range(record.count()):
                if record.isNull(i):
                    hasEmpty = True
                    continue

                orig_data.append(record.value(i))
                text = str(record.value(i))
                if text:
                    if fields[i] == 'status':
                        data.append(Statuses[text])
                    elif fields[i] == 'year':
                        label = text
                        if text[0] == '-':
                            label = f"{text[1:]} BC"
                        data.append(label)
                    elif fields[i] == 'value':
                        label, _ = numberWithFraction(text, self.convert_fraction)
                        data.append(label)
                    else:
                        data.append(text)
                    escapedText = text.replace("'", "''")
                    filterSql.append(f"{fields[i]}='{escapedText}'")
                else:
                    hasEmpty = True

            if data:
                if len(data) > 1:
                    newFilters = ' AND '.join(filterSql)
                    text = ' '.join(data)
                    child = TreeWidgetItem([text, ])
                    child.setData(0, self.SortDataRole, orig_data)
                else:
                    newFilters = filterSql[0]
                    if fields[0] == 'year':
                        child = YearTreeWidgetItem(data)
                    else:
                        child = TreeWidgetItem(data)
                    child.setData(0, self.SortDataRole, orig_data)

                if filters:
                    newFilters = f"{filters} AND {newFilters}"

                child.setData(0, self.ParamRole, paramIndex)
                child.setData(0, self.FiltersRole, newFilters)
                child.setData(0, self.FieldsRole, fields)

                if fields[0] == 'status':
                    icon = statusIcon(orig_data[0])
                else:
                    icon = self.reference.getIcon(fields[0], data[0])
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
            if filters:
                newFilters = f"{filters} AND {newFilters}"

            child = QTreeWidgetItem([text, ])
            child.setData(0, self.ParamRole, paramIndex)
            child.setData(0, self.FiltersRole, newFilters)
            child.setData(0, self.FieldsRole, fields)
            item.addChild(child)

            # Restore selection
            if newFilters == self.model.extFilter:
                self.currentItemChanged.disconnect(self.itemActivatedEvent)
                self.setCurrentItem(child)
                self.currentItemChanged.connect(self.itemActivatedEvent)

        # Recursion for next field if nothing selected
        if item.childCount() == 0:
            self.__updateChilds(item, paramIndex + 1, filters)

    def modelChanged(self):
        if self.changingEnabled:
            self.collapseAll()
            rootItem = self.topLevelItem(0)

            self.currentItemChanged.disconnect(self.itemActivatedEvent)
            rootItem.takeChildren()  # remove all children
            self.currentItemChanged.connect(self.itemActivatedEvent)

            self.__updateChilds(rootItem)
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

        # Fill multi record for editing
        multiRecord = self.model.record(0)
        tags = {}
        for tag_id in multiRecord.value('tags'):
            tags[tag_id] = Qt.Checked
        usedFields = [Qt.Checked] * multiRecord.count()
        for i in range(self.model.rowCount()):
            record = self.model.record(i)

            tags_diff = set(tags).symmetric_difference(record.value('tags'))
            for tag_id in tags_diff:
                tags[tag_id] = Qt.PartiallyChecked

            for j in range(multiRecord.count()):
                field = record.field(j)
                if field.name() == 'tags':
                    usedFields[j] = Qt.Unchecked
                else:
                    value = field.value()
                    if multiRecord.value(j) != value or not value:
                        multiRecord.setNull(j)
                        usedFields[j] = Qt.Unchecked
        multiRecord.setValue('tags', tags)

        # TODO: Make identical with ListView._multiEdit
        dialog = EditCoinDialog(self.model, multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            progressDlg = Gui.ProgressDialog(self.tr("Updating records"),
                                self.tr("Cancel"), self.model.rowCount(), self)

            # Fill records by used fields in multi record
            multiRecord = dialog.record
            usedFields = dialog.getUsedFields()
            new_tags = multiRecord.value('tags')
            for i in range(self.model.rowCount()):
                progressDlg.setValue(i)
                if progressDlg.wasCanceled():
                    break

                record = self.model.record(i)
                for j in range(multiRecord.count()):
                    if usedFields[j] == Qt.Checked:
                        record.setValue(j, multiRecord.value(j))
                cur_tags = record.value('tags')
                for tag_id, state in new_tags.items():
                    if state == Qt.Checked:
                        if tag_id not in cur_tags:
                            cur_tags.append(tag_id)
                    elif state == Qt.Unchecked:
                        if tag_id in cur_tags:
                            cur_tags.remove(tag_id)
                record.setValue('tags', cur_tags)
                self.model.setRecord(i, record)

            self.model.submitAll()
            progressDlg.reset()

        self.model.setFilter(storedFilter)

    def clearSelection(self):
        super().clearSelection()
        self.setCurrentItem(None)
