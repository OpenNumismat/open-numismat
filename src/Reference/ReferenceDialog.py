from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication


class ListView(QtGui.QListView):
    def __init__(self, parent=None):
        super(ListView, self).__init__(parent)

    def closeEditor(self, editor, hint):
        super(ListView, self).closeEditor(editor, hint)

        text = editor.text().strip()
        if len(text) == 0:
            self.setRowHidden(self.currentIndex().row(), True)
            self.model().removeRow(self.currentIndex().row())
        elif text == self.defaultValue():
            if hint == QtGui.QAbstractItemDelegate.RevertModelCache:
                self.setRowHidden(self.currentIndex().row(), True)
                self.model().removeRow(self.currentIndex().row())

    def defaultValue(self):
        return self.tr("Enter value")


class ReferenceWidget(QtGui.QWidget):
    def __init__(self, model, text, parent=None):
        super(ReferenceWidget, self).__init__(parent)

        self.model = model

        self.listWidget = ListView(parent)
        self.listWidget.setSelectionMode(
                                    QtGui.QAbstractItemView.SingleSelection)
        self.listWidget.setModel(self.model)
        self.listWidget.setModelColumn(self.model.fieldIndex('value'))

        startIndex = self.model.index(0, self.model.fieldIndex('value'))
        indexes = self.model.match(startIndex, 0, text,
                                   flags=Qt.MatchFixedString)
        if indexes:
            self.listWidget.setCurrentIndex(indexes[0])

        # TODO: Customize edit buttons
        self.editButtonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        self.addButton = QtGui.QPushButton(
                            QApplication.translate('ReferenceWidget', "Add"))
        self.editButtonBox.addButton(self.addButton,
                                QtGui.QDialogButtonBox.ActionRole)
        self.delButton = QtGui.QPushButton(
                            QApplication.translate('ReferenceWidget', "Del"))
        self.editButtonBox.addButton(self.delButton,
                                QtGui.QDialogButtonBox.ActionRole)
        self.editButtonBox.clicked.connect(self.clicked)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.editButtonBox)
        self.setLayout(layout)

    def selectedIndex(self):
        index = self.listWidget.currentIndex()
        if index.isValid() and index in self.listWidget.selectedIndexes():
            return index

        return None

    def clicked(self, button):
        if button == self.addButton:
            self._addClicked()
        elif button == self.delButton:
            self._delClicked()

    def _addClicked(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        index = self.model.index(row, self.model.fieldIndex('value'))
        self.model.setData(index, self.listWidget.defaultValue())
        self.listWidget.setCurrentIndex(index)
        self.listWidget.edit(index)

    def _delClicked(self):
        index = self.selectedIndex()
        if index:
            self.model.removeRow(index.row())
            self.listWidget.setRowHidden(index.row(), True)


class CrossReferenceWidget(ReferenceWidget):
    def __init__(self, model, parentIndex, text, parent=None):
        super(CrossReferenceWidget, self).__init__(model, text, parent)

        self.rel = self.model.relationModel(1)

        self.comboBox = QtGui.QComboBox(parent)
        self.comboBox.setModel(self.rel)
        self.comboBox.setModelColumn(self.rel.fieldIndex('value'))
        if parentIndex:
            row = parentIndex.row()
        else:
            row = -1
            self.editButtonBox.setEnabled(False)
        self.comboBox.setCurrentIndex(row)
        self.comboBox.setDisabled(True)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)

        self.layout().insertWidget(0, self.comboBox)

    def currentIndexChanged(self, index):
        idIndex = self.rel.fieldIndex('id')
        parentId = self.rel.data(self.rel.index(index, idIndex))
        self.model.setFilter('parentid=%d' % parentId)

        self.editButtonBox.setEnabled(True)

    def _addClicked(self):
        idIndex = self.rel.fieldIndex('id')
        index = self.rel.index(self.comboBox.currentIndex(), idIndex)
        parentId = self.rel.data(index)

        row = self.model.rowCount()
        self.model.insertRow(row)
        index = self.model.index(row, 1)
        self.model.setData(index, parentId)
        index = self.model.index(row, self.model.fieldIndex('value'))
        self.model.setData(index, self.listWidget.defaultValue())
        self.listWidget.setCurrentIndex(index)
        self.listWidget.edit(index)


class ReferenceDialog(QtGui.QDialog):
    def __init__(self, model, text='', parent=None):
        super(ReferenceDialog, self).__init__(parent, Qt.WindowSystemMenuHint)

        self.setWindowTitle()

        self.referenceWidget = self._referenceWidget(model, text)

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.referenceWidget)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def setWindowTitle(self, title=None):
        windowTitle = QtGui.QApplication.translate('ReferenceDialog',
                                                   "Reference")
        if title:
            windowTitle = ' - '.join([windowTitle, title])
        super(ReferenceDialog, self).setWindowTitle(windowTitle)

    def _referenceWidget(self, model, text):
        return ReferenceWidget(model, text, self)


class CrossReferenceDialog(ReferenceDialog):
    def __init__(self, model, parentIndex, text='', parent=None):
        self.parentIndex = parentIndex
        super(CrossReferenceDialog, self).__init__(model, text, parent)

    def _referenceWidget(self, model, text):
        return CrossReferenceWidget(model, self.parentIndex, text, self)


class AllReferenceDialog(QtGui.QDialog):
    def __init__(self, reference, parent=None):
        super(AllReferenceDialog, self).__init__(parent,
                                                 Qt.WindowSystemMenuHint)

        self.setWindowTitle(self.tr("Reference"))

        self.sections = [reference.section(name) for name in reference.allSections()]

        tab = QtGui.QTabWidget(self)
        for section in self.sections:
            if section.parentName:
                widget = CrossReferenceWidget(section.model, None, '', self)
                widget.comboBox.setEnabled(True)
            else:
                widget = ReferenceWidget(section.model, '', self)
            tab.addTab(widget, section.title)

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def accept(self):
        for section in self.sections:
            section.model.submitAll()
        super(AllReferenceDialog, self).accept()

    def reject(self):
        for section in self.sections:
            section.model.revertAll()
        super(AllReferenceDialog, self).reject()
