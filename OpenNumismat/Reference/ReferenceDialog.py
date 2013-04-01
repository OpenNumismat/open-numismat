from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication


class ListView(QtGui.QListView):
    def __init__(self, parent=None):
        super(ListView, self).__init__(parent)

    def commitData(self, editor):
        text = editor.text().strip()
        if len(text) > 0:
            super(ListView, self).commitData(editor)

    def closeEditor(self, editor, hint):
        row = self.currentIndex().row()
        super(ListView, self).closeEditor(editor, hint)

        valid = True
        text = editor.text().strip()
        if len(text) == 0:
            valid = False
        elif text == self.defaultValue():
            if hint == QtGui.QAbstractItemDelegate.RevertModelCache:
                valid = False

        if valid:
            self.model().submit()
        else:
            self.model().removeRow(row)

    def defaultValue(self):
        return self.tr("Enter value")


class ReferenceWidget(QtGui.QWidget):
    def __init__(self, section, text, parent=None):
        super(ReferenceWidget, self).__init__(parent)

        self.model = section.model

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

        self.sortButton = QtGui.QCheckBox(
                            QApplication.translate('ReferenceWidget', "Sort"))
        self.sortButton.setChecked(section.sort)
        self.sortButton.stateChanged.connect(self.sortChanged)

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.sortButton)
        hlayout.addWidget(self.editButtonBox)
        hlayout.setContentsMargins(0, 0, 0, 0)
        widget = QtGui.QWidget(self)
        widget.setLayout(hlayout)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(widget)
        self.setLayout(layout)

    def sortChanged(self, state):
        if self.sortButton.isChecked():
            self.model.setSort(self.model.fieldIndex('value'), Qt.AscendingOrder)
        else:
            self.model.setSort(0, Qt.AscendingOrder)
        self.model.select()

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


class CrossReferenceWidget(ReferenceWidget):
    def __init__(self, section, parentIndex, text, parent=None):
        super(CrossReferenceWidget, self).__init__(section, text, parent)

        self.rel = self.model.relationModel(1)

        self.comboBox = QtGui.QComboBox(parent)
        self.comboBox.setModel(self.rel)
        self.comboBox.setModelColumn(self.rel.fieldIndex('value'))
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)
        if parentIndex:
            row = parentIndex.row()
        else:
            row = -1
        self.comboBox.setCurrentIndex(row)
        self.comboBox.setDisabled(True)

        self.layout().insertWidget(0, self.comboBox)

    def currentIndexChanged(self, index):
        if index >= 0:
            idIndex = self.rel.fieldIndex('id')
            parentId = self.rel.data(self.rel.index(index, idIndex))
            self.model.setFilter('parentid=%d' % parentId)
        else:
            self.model.setFilter('')

        self.editButtonBox.setEnabled(index >= 0)

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
    def __init__(self, section, text='', parent=None):
        super(ReferenceDialog, self).__init__(parent, Qt.WindowSystemMenuHint)

        self.section = section
        self.db = section.db
        self.db.transaction()

        self.setWindowTitle(section.title)

        self.referenceWidget = self._referenceWidget(section, text)

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.referenceWidget)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        self.__selectedIndex = self.referenceWidget.selectedIndex()

    def setWindowTitle(self, title=None):
        windowTitle = QtGui.QApplication.translate('ReferenceDialog',
                                                   "Reference")
        if title:
            windowTitle = ' - '.join([windowTitle, title])
        super(ReferenceDialog, self).setWindowTitle(windowTitle)

    def _referenceWidget(self, section, text):
        return ReferenceWidget(section, text, self)

    def accept(self):
        self.section.saveSort(self.referenceWidget.sortButton.isChecked())
        if not self.db.commit():
            self.db.rollback()

        self.__selectedIndex = self.referenceWidget.selectedIndex()
        super(ReferenceDialog, self).accept()

    def reject(self):
        self.db.rollback()

        super(ReferenceDialog, self).reject()

    def selectedIndex(self):
        return self.__selectedIndex


class CrossReferenceDialog(ReferenceDialog):
    def __init__(self, section, parentIndex, text='', parent=None):
        self.parentIndex = parentIndex
        super(CrossReferenceDialog, self).__init__(section, text, parent)

    def _referenceWidget(self, section, text):
        return CrossReferenceWidget(section, self.parentIndex, text, self)


class AllReferenceDialog(QtGui.QDialog):
    def __init__(self, reference, parent=None):
        super(AllReferenceDialog, self).__init__(parent,
                                                 Qt.WindowSystemMenuHint)

        self.db = reference.db
        self.db.transaction()

        self.setWindowTitle(self.tr("Reference"))

        self.sections = reference.sections

        tab = QtGui.QTabWidget(self)
        self.widgets = {}
        for section in self.sections:
            if section.parentName:
                widget = CrossReferenceWidget(section, None, '', self)
                widget.comboBox.setEnabled(True)
            else:
                widget = ReferenceWidget(section, '', self)

            widget.sortButton.setChecked(section.sort)
            self.widgets[section.name] = widget
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
            widget = self.widgets[section.name]
            section.saveSort(widget.sortButton.isChecked())
        if not self.db.commit():
            QtGui.QMessageBox.critical(self.parent(),
                            self.tr("Save reference"),
                            self.tr("Something went wrong when saving. Please restart"))
            self.db.rollback()

        super(AllReferenceDialog, self).accept()

    def reject(self):
        # Make select for close all SQL request
        for section in self.sections:
            section.model.select()

        if not self.db.rollback():
            QtGui.QMessageBox.critical(self.parent(),
                            self.tr("Save reference"),
                            self.tr("Something went wrong when canceling. Please restart"))

        for section in self.sections:
            section.setSort()
            section.model.select()

        super(AllReferenceDialog, self).reject()
