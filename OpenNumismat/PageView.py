from PyQt5 import QtCore
from PyQt5 import QtSql
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from OpenNumismat.ListView import ListView
from OpenNumismat.EditCoinDialog.ImageLabel import ImageLabel
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.EditCoinDialog import EditCoinDialog
from OpenNumismat.CustomizeTreeDialog import CustomizeTreeDialog
from OpenNumismat.Tools import Gui
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.EditCoinDialog.DetailsTabWidget import DetailsTabWidget
from OpenNumismat.Settings import Settings


class ImageView(QWidget):
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)

        self.currentIndex = None

        layout = QVBoxLayout(self)

        self.imageLayout = QVBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QSizePolicy.Preferred,
                             QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.setLayout(layout)

    def setModel(self, model):
        self.model = model

        self.imageFields = []
        for field in self.model.fields.userFields:
            if field.type in [Type.Image, Type.EdgeImage]:
                self.imageFields.append(field)

        # By default show only first 2 images
        self.showedCount = 2

        self.imageButtons = []
        for field in self.imageFields:
            button = QCheckBox(self)
            button.setToolTip(field.title)
            button.setDisabled(True)
            button.stateChanged.connect(self.buttonClicked)
            self.imageButtons.append(button)
            self.buttonLayout.addWidget(button)

    def clear(self):
        for _ in range(self.imageLayout.count()):
            item = self.imageLayout.itemAt(0)
            item.widget().clear()
            self.imageLayout.removeItem(item)

    def buttonClicked(self, state):
        self.clear()

        current = self.currentIndex
        self.showedCount = 0
        for i, field in enumerate(self.imageFields):
            if self.imageButtons[i].checkState() == Qt.Checked:
                image = ImageLabel(self)
                index = self.model.index(current.row(), field.id)
                image.loadFromData(index.data())
                self.imageLayout.addWidget(image)

                self.showedCount = self.showedCount + 1

    def rowChangedEvent(self, current):
        self.currentIndex = current
        self.clear()

        images = []
        for i, field in enumerate(self.imageFields):
            self.imageButtons[i].stateChanged.disconnect(self.buttonClicked)
            self.imageButtons[i].setCheckState(Qt.Unchecked)
            self.imageButtons[i].setDisabled(True)

            index = self.model.index(current.row(), field.id)
            if index.data() and not index.data().isNull():
                if len(images) < self.showedCount:
                    images.append(index.data())
                    self.imageButtons[i].setCheckState(Qt.Checked)
                self.imageButtons[i].setDisabled(False)

            self.imageButtons[i].stateChanged.connect(self.buttonClicked)

        for imageData in images:
            image = ImageLabel(self)
            image.loadFromData(imageData)
            self.imageLayout.addWidget(image)

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget


class TreeView(QTreeWidget):
    FiltersRole = Qt.UserRole
    FieldsRole = FiltersRole + 1
    ParamRole = FieldsRole + 1

    def __init__(self, treeParam, parent=None):
        super(TreeView, self).__init__(parent)

        self.settings = Settings()

        self.setHeaderHidden(True)
        self.setAutoScroll(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

        self.currentItemChanged.connect(self.itemActivatedEvent)
        self.itemExpanded.connect(self.expandedEvent)
        self.collapsed.connect(self.collapsedEvent)

        self.treeParam = treeParam

        # Changing of TreeView is enabled (by signals from model or ListView)
        self.changingEnabled = True

    def setModel(self, model):
        self.db = model.database()
        self.model = model

        self.treeParam.rootTitle = model.title
        rootItem = QTreeWidgetItem(self, [model.title, ])
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

    def collapsedEvent(self, parentItem):
        self.resizeColumnToContents(0)

    def __updateChilds(self, item, paramIndex=0, filters=''):
        fields = self.treeParam.fieldNames(paramIndex)
        if not fields:
            return

        sql = "SELECT DISTINCT %s FROM coins" % ','.join(fields)
        if filters:
            sql += " WHERE " + filters
        if self.settings['sort_tree']:
            sql += " ORDER BY "
            sql += ','.join([f + ' ASC' for f in reversed(fields)])
        query = QtSql.QSqlQuery(sql, self.db)
        hasEmpty = False
        while query.next():
            record = query.record()
            data = []
            filterSql = []
            for i in range(record.count()):
                if record.isNull(i):
                    hasEmpty = True
                    continue

                text = str(record.value(i))
                if text:
                    if fields[i] == 'status':
                        data.append(Statuses[text])
                    elif fields[i] == 'value':
                        label, _ = numberWithFraction(text, self.settings['convert_fraction'])
                        data.append(label)
                    else:
                        data.append(text)
                    escapedText = text.replace("'", "''")
                    filterSql.append("%s='%s'" % (fields[i], escapedText))
                else:
                    hasEmpty = True

            if data:
                text = ' '.join(data)
                newFilters = ' AND '.join(filterSql)
                if filters:
                    newFilters = filters + ' AND ' + newFilters

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

        if hasEmpty and len(fields) == 1 and item.childCount() > 0:
            text = self.tr("Other")
            newFilters = "ifnull(%s,'')=''" % fields[0]
            if filters:
                newFilters = filters + ' AND ' + newFilters

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
                if field == 'status':
                    textPart.append(str(index.data()))
                else:
                    textPart.append(str(index.data(Qt.UserRole)))
            text2 = ' '.join(textPart)
            if text1 == text2 or (not text2 and text1 == self.tr("Other")):
                self.expandItem(parent)
                self.scrollToItem(subItem)
                self.scrollToIndex(index, subItem)
                break

    def scrollToItem(self, item, hint=QTreeWidget.EnsureVisible):
        super(TreeView, self).scrollToItem(item, hint)

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

    def itemActivatedEvent(self, current, previous):
        self.scrollToItem(current)
        self.resizeColumnToContents(0)

        self.changingEnabled = False
        filter_ = current.data(0, self.FiltersRole)
        self.model.setAdditionalFilter(filter_)
        self.changingEnabled = True

    def contextMenuEvent(self, pos):
        menu = QMenu(self)
        act = menu.addAction(self.tr("Add new coin..."), self._addCoin)
        if not (self.model.rowCount() and self.selectedItems()):
            act.setDisabled(True)
        act = menu.addAction(self.tr("Edit coins..."), self._multiEdit)
        if not (self.model.rowCount() and self.selectedItems()):
            act.setDisabled(True)
        menu.addSeparator()
        menu.addAction(self.tr("Customize tree..."), self._customizeTree)
        menu.exec_(self.mapToGlobal(pos))

    def _customizeTree(self):
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

        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(newRecord.count()):
                value = record.value(j)
                if newRecord.value(j) != value or not value:
                    newRecord.setNull(j)

        self.model.addCoin(newRecord, self)

        self.model.setFilter(storedFilter)

    def _multiEdit(self):
        self.changingEnabled = False
        storedFilter = self.model.intFilter
        self.model.setFilter('')
        self.changingEnabled = True

        # Fill multi record for editing
        multiRecord = self.model.record(0)
        usedFields = [Qt.Checked] * multiRecord.count()
        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(multiRecord.count()):
                value = record.value(j)
                if multiRecord.value(j) != value or not value:
                    multiRecord.setNull(j)
                    usedFields[j] = Qt.Unchecked

        # TODO: Make identical with ListView._multiEdit
        dialog = EditCoinDialog(self.model, multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            progressDlg = Gui.ProgressDialog(self.tr("Updating records"),
                                self.tr("Cancel"), self.model.rowCount(), self)

            # Fill records by used fields in multi record
            multiRecord = dialog.getRecord()
            usedFields = dialog.getUsedFields()
            for i in range(self.model.rowCount()):
                progressDlg.setValue(i)
                if progressDlg.wasCanceled():
                    break

                record = self.model.record(i)
                for j in range(multiRecord.count()):
                    if usedFields[j] == Qt.Checked:
                        record.setValue(j, multiRecord.value(j))
                self.model.setRecord(i, record)

            self.model.submitAll()
            progressDlg.reset()

        self.model.setFilter(storedFilter)


class DetailsView(QWidget):
    def __init__(self, parent=None):
        super(DetailsView, self).__init__(parent)

        self.resize(0, 120)

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

    def setModel(self, model):
        self.model = model

        self.widget = DetailsTabWidget(model)
        self.layout.addWidget(self.widget)

    def rowChangedEvent(self, current):
        if current.isValid():
            record = self.model.record(current.row())
            self.widget.fillItems(record)
        else:
            self.widget.clear()


class Splitter(QSplitter):
    def __init__(self, title, orientation=Qt.Horizontal, parent=None):
        super(Splitter, self).__init__(orientation, parent)

        self.title = title
        self.splitterMoved.connect(self.splitterPosChanged)

    def splitterPosChanged(self, pos, index):
        settings = QtCore.QSettings()
        settings.setValue('pageview/splittersizes' + self.title, self.sizes())

    def showEvent(self, e):
        settings = QtCore.QSettings()
        sizes = settings.value('pageview/splittersizes' + self.title)
        if sizes:
            for i in range(len(sizes)):
                sizes[i] = int(sizes[i])

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)


class PageView(Splitter):
    def __init__(self, pageParam, parent=None):
        super(PageView, self).__init__('0', parent=parent)

        self._model = None
        self.param = pageParam
        self.id = pageParam.id
        self.treeView = TreeView(pageParam.treeParam, self)
        self.listView = ListView(pageParam.listParam, self)
        self.imageView = ImageView(self)
        self.detailsView = DetailsView(self)

        splitter1 = Splitter('1', Qt.Vertical, self)
        splitter2 = Splitter('2', parent=splitter1)
        splitter2.addWidget(self.treeView)
        splitter2.addWidget(self.listView)
        splitter1.addWidget(splitter2)
        splitter1.addWidget(self.detailsView)
        self.addWidget(splitter1)
        self.addWidget(self.imageView)

        self.listView.rowChanged.connect(self.imageView.rowChangedEvent)
        self.listView.rowChanged.connect(self.treeView.rowChangedEvent)
        self.listView.rowChanged.connect(self.detailsView.rowChangedEvent)
        self.splitterMoved.connect(self.splitterPosChanged)

    def setModel(self, model):
        self._model = model

        self._model.modelChanged.connect(self.modelChanged)

        self.treeView.setModel(model)
        self.listView.setModel(model)
        self.imageView.setModel(model)
        self.detailsView.setModel(model)

    def model(self):
        return self._model

    def modelChanged(self):
        self.treeView.modelChanged()
        self.listView.modelChanged()
