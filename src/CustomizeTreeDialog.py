from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from Collection.CollectionFields import FieldTypes as Type

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
    
    def dragMoveEvent(self, event):
        if event.source() == self:
            event.ignore()
            return
        
        return QtGui.QTreeWidget.dragMoveEvent(self, event)
    
    def dropEvent(self, event):
        self.event = event
        if event.dropAction() & Qt.CopyAction:
            event.setDropAction(Qt.MoveAction)
        QtGui.QTreeWidget.dropEvent(self, event)
    
    def dropMimeData(self, parent, index, data, action):
        res = QtGui.QTreeWidget.dropMimeData(self, parent, index, data, action)
        if res:
            if self.event.proposedAction() & Qt.CopyAction:
                item = parent.takeChild(0)
                text = ' + '.join([parent.text(0), item.text(0)])
                parent.setText(0, text)
                data = parent.data(0, Qt.UserRole)
                if not isinstance(data, list):
                    data = [data,]
                data.append(item.data(0, Qt.UserRole))
                parent.setData(0, Qt.UserRole, data)
            
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
        
        rootItem = QtGui.QTreeWidgetItem(self.treeWidget, [self.treeParam.rootTitle,])
        self.treeWidget.addTopLevelItem(rootItem)
        topItem = rootItem
        for param in self.treeParam:
            if isinstance(param, list):
                titleParts = [field.title for field in param]
                title = ' + '.join(titleParts)
                data = [field for field in param]
            else:
                title = param.title
                data = param
            item = QtGui.QTreeWidgetItem([title,])
            item.setData(0, Qt.UserRole, data)
            topItem.addChild(item)
            topItem = item
        
        self.treeWidget.updateFlags()
        self.treeWidget.expandAll()
        
        for field in allFields.userFields:
            if field.type in [Type.String, Type.Money, Type.Number, Type.ShortString]:
                if field not in self.treeParam.usedFields():
                    item = QtGui.QListWidgetItem(field.title)
                    item.setData(Qt.UserRole, field)
                    self.listWidget.addItem(item)
    
    def save(self):
        self.treeParam.clear()
        
        rootItem = self.treeWidget.topLevelItem(0)
        topItem = rootItem.child(0)
        while topItem:
            self.treeParam.append(topItem.data(0, Qt.UserRole))
            topItem = topItem.child(0)
        
        self.accept()
