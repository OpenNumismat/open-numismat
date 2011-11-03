from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from Collection.CollectionFields import CollectionFields
from Collection.ListPageParam import ColumnListParam

class SelectColumnsDialog(QtGui.QDialog):
    DataRole = 16
    
    def __init__(self, listParam, parent=None):
        super(SelectColumnsDialog, self).__init__(parent)
        
        self.listParam = listParam
        
        self.listWidget = QtGui.QListWidget(self)
        # TODO: Disable resizing
        self.listWidget.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.listWidget.setDropIndicatorShown(True) 
        self.listWidget.setWrapping(True)
        
        allFields = CollectionFields(listParam.db)
        collectionFields = allFields.userFields
        for param in listParam.columns:
            field = allFields.field(param.fieldid)
            if field in allFields.disabledFields:
                continue
            item = QtGui.QListWidgetItem(field.title, self.listWidget)
            item.setData(SelectColumnsDialog.DataRole, param)
            checked = Qt.Unchecked
            if param.enabled:
                checked = Qt.Checked
            item.setCheckState(checked)
            self.listWidget.addItem(item)
            
            collectionFields.remove(field)   # mark field as processed

        # Process missed columns
        for field in collectionFields:
            item = QtGui.QListWidgetItem(field.title, self.listWidget)
            item.setData(SelectColumnsDialog.DataRole, ColumnListParam(field.id, False))
            item.setCheckState(Qt.Unchecked)
            self.listWidget.addItem(item)

        # TODO: Add buttons SelectAll, ClearAll, EnabledToTop
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        self.listParam.columns = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            param = item.data(SelectColumnsDialog.DataRole)
            param.enabled = (item.checkState() == Qt.Checked)
            self.listParam.columns.append(param)
        
        self.accept()
