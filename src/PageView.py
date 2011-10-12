from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from ListView import ListView
from EditCoinDialog.ImageLabel import ImageLabel
from Collection.CollectionFields import FieldTypes as Type

class ImageView(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ImageView, self).__init__(parent)

        self.resize(120, 0)
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
            if field.type == Type.Image:
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
    
    def rowChanged(self, current):
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

        self.resize(100, 0)
        
        self.setHeaderHidden(True)
        
    def setModel(self, model):
        self.db = model.database()
        self.model = model

        # TODO: Root element should contain collection name
        item = QtGui.QTreeWidgetItem(self, [self.tr("Collection"),])
        self.addTopLevelItem(item)
        
        items = self.fillChilds(item, 'type')
        for item in items:
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
            filtersSql = filtersSql + filters
        sql = "SELECT DISTINCT %s FROM coins WHERE %s" % (','.join(fields), filtersSql)
        query = QtSql.QSqlQuery(sql, self.db)

        items = []
        while query.next():
            label = []
            for i in range(len(fields)):
                label.append(str(query.record().value(i)))
            subItem = QtGui.QTreeWidgetItem([' '.join(label),])
            for i, field in enumerate(fields):
                newFilters = filters+" AND %s='%s'"%(field, label[i])
            subItem.setData(0, self.DataRole, newFilters)
            items.append(subItem)
            parentItem.addChild(subItem)
        
        return items

class PageView(QtGui.QSplitter):
    def __init__(self, listParam, parent=None):
        super(PageView, self).__init__(parent)
        
        self.treeView = TreeView(self)
        self.addWidget(self.treeView)
        
        self.listView = ListView(listParam, self)
        self.addWidget(self.listView)
        
        self.imageView = ImageView(self)
        self.addWidget(self.imageView)
        
        self.listView.rowChanged.connect(self.imageView.rowChanged)
        self.splitterMoved.connect(self.splitterPosChanged)

    def setModel(self, model):
        self.listView.setModel(model)
        self.imageView.setModel(model)
        self.treeView.setModel(model)
    
    def model(self):
        return self.listView.model()
    
    def splitterPosChanged(self, pos, index):
        settings = QtCore.QSettings()
        settings.setValue('pageview/splittersizes', self.sizes())

    def showEvent(self, e):
        settings = QtCore.QSettings()
        sizes = settings.value('pageview/splittersizes')
        if sizes:
            for i in range(len(sizes)):
                sizes[i] = int(sizes[i])

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)
