from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from Collection.CollectionFields import FieldTypes as Type
from Collection.CollectionFields import CollectionFields

class TreeWidget(QtGui.QTreeWidget):
    def __init__(self, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        
        self.setHeaderHidden(True)
        
        self.model().rowsRemoved.connect(self.rowsRemoved)
    
    def updateFlags(self):
        self.invisibleRootItem().setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        
        rootItem = self.topLevelItem(0)
        if rootItem.childCount():
            rootItem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        else:
            rootItem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsSelectable)
        
        topItem = rootItem.child(0)
        if topItem:
            while topItem.childCount():
                topItem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
                topItem = topItem.child(0)
            topItem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)
    
    def rowsRemoved(self, parent, start, end):
        self.updateFlags()
    
    def dropMimeData(self, parent, index, data, action):
        res = QtGui.QTreeWidget.dropMimeData(self, parent, index, data, action)
        if res:
            self.updateFlags()
            self.expandAll()
        return res

class ListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        QtGui.QListWidget.__init__(self, parent)
    
    def dragMoveEvent(self, event):
        if event.source() == self:
            event.ignore()
            return
        
        return QtGui.QListWidget.dragMoveEvent(self, event)

class CustomizeTreeDialog(QtGui.QDialog):
    def __init__(self, model, treeParam, parent=None):
        QtGui.QDialog.__init__(self, parent, Qt.WindowSystemMenuHint)
        
        self.setWindowTitle(self.tr("Customize tree"))
        
        self.treeWidget = TreeWidget(self)
        self.treeWidget.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.treeWidget.setDropIndicatorShown(True)
        self.treeWidget.setDefaultDropAction(Qt.MoveAction)
        
        self.listWidget = ListWidget(self)
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.listWidget.setDropIndicatorShown(True)
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        
        splitter = QtGui.QSplitter(self)
        splitter.addWidget(self.treeWidget)
        splitter.addWidget(self.listWidget)

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)
        
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(splitter)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)
        
        self.treeParam = treeParam
        allFields = model.fields
        
        rootItem = QtGui.QTreeWidgetItem(self.treeWidget, [model.title,])
        self.treeWidget.addTopLevelItem(rootItem)
        topItem = rootItem
        for field in self.treeParam:
            item = QtGui.QTreeWidgetItem([field.title,])
            item.setData(0, Qt.UserRole, field)
            topItem.addChild(item)
            topItem = item
        
        self.treeWidget.updateFlags()
        self.treeWidget.expandAll()
        
        for field in allFields.userFields:
            if field.type in [Type.String, Type.Money, Type.Number, Type.ShortString]:
                if field not in self.treeParam:
                    item = QtGui.QListWidgetItem(field.title)
                    item.setData(Qt.UserRole, field)
                    self.listWidget.addItem(item)
    
    def save(self):
        del self.treeParam[:]   # clearing list
        
        rootItem = self.treeWidget.topLevelItem(0)
        topItem = rootItem.child(0)
        while topItem:
            self.treeParam.append(topItem.data(0, Qt.UserRole))
            topItem = topItem.child(0)
        
        self.accept()
