from PyQt4 import QtGui
from PyQt4.QtCore import Qt

class ListView(QtGui.QListView):
    def __init__(self, parent=None):
        super(ListView, self).__init__(parent)
    
    def closeEditor(self, editor, hint):
        super(ListView, self).closeEditor(editor, hint)
        
        text = editor.text().strip()
        if len(text) == 0:
            self.setRowHidden(self.currentIndex().row(), True)
            self.model().removeRow(self.currentIndex().row())
        elif text == self.tr("Enter value"):
            if hint == QtGui.QAbstractItemDelegate.RevertModelCache:
                self.setRowHidden(self.currentIndex().row(), True)
                self.model().removeRow(self.currentIndex().row())

class ReferenceLayout(QtGui.QVBoxLayout):
    def __init__(self, model, text, parent=None):
        super(ReferenceLayout, self).__init__(parent)
        
        self.model = model
        
        self.listWidget = ListView(parent)
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.listWidget.setModel(self.model)
        self.listWidget.setModelColumn(self.model.fieldIndex('value'))
        
        startIndex = self.model.index(0, self.model.fieldIndex('value'))
        indexes = self.model.match(startIndex, 0, text, flags=Qt.MatchFixedString)
        if indexes:
            self.listWidget.setCurrentIndex(indexes[0])
        
        # TODO: Customize edit buttons
        editButtonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        self.addButton = QtGui.QPushButton(self.tr("Add"))
        editButtonBox.addButton(self.addButton, QtGui.QDialogButtonBox.ActionRole)
        self.delButton = QtGui.QPushButton(self.tr("Del"))
        editButtonBox.addButton(self.delButton, QtGui.QDialogButtonBox.ActionRole)
        editButtonBox.clicked.connect(self.clicked)
        
        self.addWidget(self.listWidget)
        self.addWidget(editButtonBox)
    
    def selectedIndex(self):
        index = self.listWidget.currentIndex()
        if index in self.listWidget.selectedIndexes():
            return index
        
        return None
    
    def clicked(self, button):
        if button == self.addButton:
            row = self.model.rowCount()
            self.model.insertRow(row)
            index = self.model.index(row, self.model.fieldIndex('value'))
            self.model.setData(index, self.tr("Enter value"))
            self.listWidget.setCurrentIndex(index)
            self.listWidget.edit(index)
        elif button == self.delButton:
            index = self.listWidget.currentIndex()
            if index.isValid() and index in self.listWidget.selectedIndexes():
                self.model.removeRow(index.row())
                self.listWidget.setRowHidden(index.row(), True)

class CrossReferenceLayout(ReferenceLayout):
    def __init__(self, model, parentIndex, text, parent=None):
        super(CrossReferenceLayout, self).__init__(model, text, parent)
        
        self.rel = self.model.relationModel(1)
        
        self.comboBox = QtGui.QComboBox(parent)
        self.comboBox.setModel(self.rel)
        self.comboBox.setModelColumn(self.rel.fieldIndex('value'))
        if parentIndex:
            row = parentIndex.row()
        else:
            row = -1
        self.comboBox.setCurrentIndex(row)
        self.comboBox.setDisabled(True)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)
        
        self.insertWidget(0, self.comboBox)
    
    def currentIndexChanged(self, index):
        idIndex = self.rel.fieldIndex('id')
        self.model.setFilter('parentid=%d' % self.rel.data(self.rel.index(index, idIndex)))
    
    def clicked(self, button):
        if button == self.addButton:
            idIndex = self.rel.fieldIndex('id')
            parentId = self.rel.data(self.rel.index(self.comboBox.currentIndex(), idIndex))

            row = self.model.rowCount()
            self.model.insertRow(row)
            index = self.model.index(row, 1)
            self.model.setData(index, parentId)
            index = self.model.index(row, self.model.fieldIndex('value'))
            self.model.setData(index, self.tr("Enter value"))
            self.listWidget.setCurrentIndex(index)
            self.listWidget.edit(index)
        elif button == self.delButton:
            super(CrossReferenceDialog, self).clicked(button)

class ReferenceDialog(QtGui.QDialog):
    def __init__(self, model, text='', parent=None):
        super(ReferenceDialog, self).__init__(parent, Qt.WindowSystemMenuHint)
        
        self.setWindowTitle()
        
        self.listLayout = self._mainLayout(model, text)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addLayout(self.listLayout)
        layout.addWidget(buttonBox)
        
        self.setLayout(layout)
    
    def setWindowTitle(self, title=None):
        windowTitle = QtGui.QApplication.translate('ReferenceDialog', "Reference")
        if title:
            windowTitle = ' - '.join([windowTitle, title])
        super(ReferenceDialog, self).setWindowTitle(windowTitle)
    
    def _mainLayout(self, model, text):
        return ReferenceLayout(model, text)

class CrossReferenceDialog(ReferenceDialog):
    def __init__(self, model, parentIndex, text='', parent=None):
        self.parentIndex = parentIndex
        super(CrossReferenceDialog, self).__init__(model, text, parent)
    
    def _mainLayout(self, model, text):
        return CrossReferenceLayout(model, self.parentIndex, text)
