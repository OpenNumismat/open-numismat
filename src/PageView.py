from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from ListView import ListView
from EditCoinDialog.ImageLabel import ImageLabel
from Collection.CollectionFields import FieldTypes as Type
from EditCoinDialog.EditCoinDialog import EditCoinDialog

class ImageView(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)

        self.currentIndex = None

        layout = QtGui.QVBoxLayout(self)
        
        self.imageLayout = QtGui.QVBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))
        
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.setLayout(layout)

    def setModel(self, model):
        self.model = model
        self.imageButtons = []
        self.imageFields = []
        for field in model.fields:
            if field.type in [Type.Image, Type.EdgeImage]:
                self.imageFields.append(field.name)
                button = QtGui.QCheckBox(self)
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
        for i, field in enumerate(self.imageFields):
            if self.imageButtons[i].checkState() == Qt.Checked:
                image = ImageLabel(self)
                index = self.model.index(current.row(), self.model.fieldIndex(field))
                image.loadFromData(index.data())
                self.imageLayout.addWidget(image)
    
    def rowChangedEvent(self, current):
        self.currentIndex = current
        self.clear()
        
        images = []
        for i, field in enumerate(self.imageFields):
            self.imageButtons[i].stateChanged.disconnect(self.buttonClicked)
            self.imageButtons[i].setCheckState(Qt.Unchecked)
            self.imageButtons[i].setDisabled(True)

            index = self.model.index(current.row(), self.model.fieldIndex(field))
            if index.data() and not index.data().isNull():
                # By default show only first 2 images
                if len(images) < 2:
                    images.append(index.data())
                    self.imageButtons[i].setCheckState(Qt.Checked)
                self.imageButtons[i].setDisabled(False)

            self.imageButtons[i].stateChanged.connect(self.buttonClicked)

        for imageData in images:
            image = ImageLabel(self)
            image.loadFromData(imageData)
            self.imageLayout.addWidget(image)

    def __layoutToWidget(self, layout):
        widget = QtGui.QWidget(self)
        widget.setLayout(layout)
        return widget

from PyQt4 import QtSql

class TreeView(QtGui.QTreeWidget):
    DataRole = 16
    
    def __init__(self, parent=None):
        super(TreeView, self).__init__(parent)

        self.setHeaderHidden(True)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

        self.currentItemChanged.connect(self.itemActivatedEvent)
        self.expanded.connect(self.expandedEvent)
        
    def setModel(self, model):
        self.db = model.database()
        self.model = model

        item = QtGui.QTreeWidgetItem(self, [model.title,])
        item.setData(0, self.DataRole, '')
        self.addTopLevelItem(item)
        self.expandItem(item)
        
        for item in self.processChilds(item, 'type'):
            for item in self.processChilds(item, 'country'):
                for item in self.processChilds(item, 'period'):
                    for item in self.processChilds(item, ['value', 'unit']):
                        for item in self.processChilds(item, 'series'):
                            for item in self.processChilds(item, 'year'):
                                self.processChilds(item, 'mintmark')
    
    def processChilds(self, parentItem, field):
        items = self.fillChilds(parentItem, field, parentItem.data(0, self.DataRole))
        if not items:
            items = [parentItem,]
        return items
    
    def fillChilds(self, parentItem, fields, filters=''):
        if not isinstance(fields, list):
            fields = [fields,]
        filterSql = []
        for field in fields:
            filterSql.append("%s<>'' AND %s IS NOT NULL" % (field, field))
        filtersSql = " AND ".join(filterSql)
        if filters:
            filtersSql = filtersSql + " AND " + filters
        sql = "SELECT DISTINCT %s FROM coins WHERE %s" % (','.join(fields), filtersSql)
        query = QtSql.QSqlQuery(sql, self.db)

        items = []
        while query.next():
            label = []
            for i in range(len(fields)):
                label.append(str(query.record().value(i)))
            subItem = QtGui.QTreeWidgetItem([' '.join(label),])
            filterSql = []
            for i, field in enumerate(fields):
                filterSql.append("%s='%s'"%(field, label[i]))
            newFilters = " AND ".join(filterSql)
            if filters:
                newFilters = filters + " AND " + newFilters
            subItem.setData(0, self.DataRole, newFilters)
            subItem.setData(0, self.DataRole+1, fields)
            items.append(subItem)
            parentItem.addChild(subItem)
        
        return items
    
    def rowChangedEvent(self, current):
        if current.isValid():
            self.collapseAll()
            item = self.topLevelItem(0)
            self.findSubitem(current, item)
    
    def findSubitem(self, index, item):
        for i in range(item.childCount()):
            subItem = item.child(i)
            fields = subItem.data(0, self.DataRole+1)
            text1 = subItem.text(0)
            textPart = []
            for field in fields:
                index = self.model.index(index.row(), self.model.fieldIndex(field))
                textPart.append(str(index.data()))
            text2 = ' '.join(textPart)
            if text1 == text2:
                self.expandItem(item)
                self.findSubitem(index, subItem)
                return

    def itemActivatedEvent(self, current, previous):
        self.resizeColumnToContents(0)
        filter_ = current.data(0, self.DataRole)
        self.model.setAdditionalFilter(filter_)

    def expandedEvent(self, index):
        self.resizeColumnToContents(0)
    
    def contextMenuEvent(self, pos):
        menu = QtGui.QMenu(self)
        act = menu.addAction(self.tr("Add new coin..."), self._addCoin)
        act.setEnabled(self.model.rowCount())
        act = menu.addAction(self.tr("Edit coins..."), self._multiEdit)
        act.setEnabled(self.model.rowCount())
        menu.exec_(self.mapToGlobal(pos))
    
    def _addCoin(self):
        storedFilter = self.model.intFilter
        self.model.setFilter('')

        newRecord = self.model.record()
        # Fill new record with values of first record
        for j in range(newRecord.count()):
            newRecord.setValue(j, self.model.record(0).value(j))

        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(newRecord.count()):
                if newRecord.value(j) != record.value(j) or not record.value(j):
                    newRecord.setNull(j)
        
        newRecord.setNull('id')  # remove ID value from record
        self.model.addCoin(newRecord, self)
        
        self.model.setFilter(storedFilter)

    def _multiEdit(self):
        storedFilter = self.model.intFilter
        self.model.setFilter('')

        # Fill multi record for editing
        multiRecord = self.model.record(0)
        usedFields = [Qt.Checked] * multiRecord.count()
        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(multiRecord.count()):
                if multiRecord.value(j) != record.value(j) or not record.value(j):
                    multiRecord.setNull(j)
                    usedFields[j] = Qt.Unchecked

        dialog = EditCoinDialog(self.model.reference, multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            # Fill records by used fields in multi record
            multiRecord = dialog.getRecord()
            usedFields = dialog.getUsedFields()
            for i in range(self.model.rowCount()):
                record = self.model.record(i)
                for j in range(multiRecord.count()):
                    if usedFields[j] == Qt.Checked:
                        record.setValue(j, multiRecord.value(j))
                self.model.setRecord(i, record)
            
            self.model.submitAll()
        
        self.model.setFilter(storedFilter)

from EditCoinDialog.DetailsTabWidget import DetailsTabWidget

class DetailsView(DetailsTabWidget):
    def __init__(self, parent=None):
        super(DetailsView, self).__init__(parent)

        self.resize(0, 120)

    def rowChangedEvent(self, current):
        if current.isValid():
            model = current.model()
            record = model.record(current.row())
            self.fillItems(record)
        else:
            self.clear()

class Splitter(QtGui.QSplitter):
    def __init__(self, title, orientation=Qt.Horizontal, parent=None):
        super(Splitter, self).__init__(orientation, parent)

        self.title = title
        self.splitterMoved.connect(self.splitterPosChanged)

    def splitterPosChanged(self, pos, index):
        settings = QtCore.QSettings()
        settings.setValue('pageview/splittersizes'+self.title, self.sizes())

    def showEvent(self, e):
        settings = QtCore.QSettings()
        sizes = settings.value('pageview/splittersizes'+self.title)
        if sizes:
            for i in range(len(sizes)):
                sizes[i] = int(sizes[i])

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)

class PageView(Splitter):
    def __init__(self, listParam, parent=None):
        super(PageView, self).__init__('0', parent=parent)
        
        self.treeView = TreeView(self)
        self.listView = ListView(listParam, self)
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
        self.listView.setModel(model)
        self.imageView.setModel(model)
        self.treeView.setModel(model)
    
    def model(self):
        return self.listView.model()
