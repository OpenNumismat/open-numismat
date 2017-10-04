from PyQt5.QtCore import Qt, QByteArray, QFileInfo, QIODevice, QBuffer
from PyQt5.QtGui import QImage, QKeySequence
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


class ListView(QListView):
    latestDir = OpenNumismat.IMAGE_PATH

    def __init__(self, widget, parent=None):
        super().__init__(parent)

        self.widget = widget

    def commitData(self, editor):
        text = editor.text().strip()
        if len(text) > 0:
            super().commitData(editor)

    def closeEditor(self, editor, hint):
        row = self.currentIndex().row()
        super().closeEditor(editor, hint)

        valid = True
        text = editor.text().strip()
        if len(text) == 0:
            valid = False
        elif text == self.defaultValue():
            if hint == QAbstractItemDelegate.RevertModelCache:
                valid = False

        if valid:
            self.model().submit()
        else:
            self.model().removeRow(row)

    def defaultValue(self):
        return self.tr("Enter value")

    def selectedIndex(self):
        index = self.currentIndex()
        if index.isValid() and index in self.selectedIndexes():
            return index

        return None

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        act = menu.addAction(self.tr("Add"), self.addItem)
        if not self.widget.isEnabled():
            act.setDisabled(True)

        act = menu.addAction(self.tr("Delete"), self.deleteItem)
        act.setShortcut(QKeySequence.Delete)
        if not self.selectedIndex() or not self.widget.isEnabled():
            act.setDisabled(True)

        menu.addSeparator()

        if self.selectedIndex() and self.selectedIndex().data(Qt.DecorationRole):
            act = menu.addAction(self.tr("Change icon..."), self._addIcon)
        else:
            act = menu.addAction(self.tr("Add icon..."), self._addIcon)
        if not self.selectedIndex() or not self.widget.isEnabled():
            act.setDisabled(True)

        act = menu.addAction(self.tr("Clear icon"), self._clearIcon)
        if not self.selectedIndex() or not self.widget.isEnabled() or \
                not self.selectedIndex().data(Qt.DecorationRole):
            act.setDisabled(True)

        menu.exec_(self.mapToGlobal(event.pos()))

    def addItem(self):
        self.widget.addItem()

    def deleteItem(self):
        self.widget.deleteItem()

    def _addIcon(self):
        filter_ = self.tr("Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif *.ico);;"
                          "All files (*.*)")
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                self.tr("Open File"), self.latestDir,
                filter_)
        if fileName:
            file_info = QFileInfo(fileName)
            self.latestDir = file_info.absolutePath()

            image = QImage()
            if image.load(fileName):
                maxWidth = 22
                maxHeight = 15
                if image.width() > maxWidth or image.height() > maxHeight:
                    scaledImage = image.scaled(maxWidth, maxHeight,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                else:
                    scaledImage = image

                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QIODevice.WriteOnly)
                scaledImage.save(buffer, 'png')

                model = self.model()
                index = model.index(self.selectedIndex().row(), model.fieldIndex('icon'))
                model.setData(index, ba)

    def _clearIcon(self):
        model = self.model()
        index = model.index(self.selectedIndex().row(), model.fieldIndex('icon'))
        model.setData(index, '')


class ReferenceWidget(QWidget):
    def __init__(self, section, text, parent=None):
        super().__init__(parent)

        self.model = section.model

        self.listWidget = ListView(self, parent)
        self.listWidget.setSelectionMode(
                                    QAbstractItemView.SingleSelection)
        self.listWidget.setModel(self.model)
        self.listWidget.setModelColumn(self.model.fieldIndex('value'))

        startIndex = self.model.index(0, self.model.fieldIndex('value'))
        indexes = self.model.match(startIndex, 0, text,
                                   flags=Qt.MatchFixedString)
        if indexes:
            self.listWidget.setCurrentIndex(indexes[0])

        # TODO: Customize edit buttons
        self.editButtonBox = QDialogButtonBox(Qt.Horizontal)
        self.addButton = QPushButton(
                            QApplication.translate('ReferenceWidget', "Add"))
        self.editButtonBox.addButton(self.addButton,
                                QDialogButtonBox.ActionRole)
        self.delButton = QPushButton(
                            QApplication.translate('ReferenceWidget', "Del"))
        self.delButton.setShortcut(QKeySequence.Delete)
        self.editButtonBox.addButton(self.delButton,
                                QDialogButtonBox.ActionRole)
        self.editButtonBox.clicked.connect(self.clicked)

        self.sortButton = QCheckBox(
                            QApplication.translate('ReferenceWidget', "Sort"))
        self.sortButton.setChecked(section.sort)
        self.sortButton.stateChanged.connect(self.sortChanged)

        hlayout = QHBoxLayout(self)
        hlayout.addWidget(self.sortButton)
        hlayout.addWidget(self.editButtonBox)
        hlayout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(hlayout)

        layout = QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(widget)
        self.setLayout(layout)

    def sortChanged(self, state):
        if state == Qt.Checked:
            self.model.setSort(self.model.fieldIndex('value'), Qt.AscendingOrder)
        else:
            self.model.setSort(0, Qt.AscendingOrder)
        self.model.select()

    def selectedIndex(self):
        return self.listWidget.selectedIndex()

    def clicked(self, button):
        if button == self.addButton:
            self.addItem()
        elif button == self.delButton:
            self.deleteItem()

    def addItem(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        index = self.model.index(row, self.model.fieldIndex('value'))
        self.model.setData(index, self.listWidget.defaultValue())
        self.listWidget.setCurrentIndex(index)
        self.listWidget.edit(index)

    def deleteItem(self):
        index = self.selectedIndex()
        if index:
            if self.model.removeRow(index.row()):
                self.model.select()

    def isEnabled(self):
        return True


class CrossReferenceWidget(ReferenceWidget):
    def __init__(self, section, parentIndex, text, parent=None):
        super().__init__(section, text, parent)

        self.rel = self.model.relationModel(1)

        self.comboBox = QComboBox(parent)
        self.comboBox.setModel(self.rel)
        self.comboBox.setModelColumn(self.rel.fieldIndex('value'))
        if parentIndex:
            row = parentIndex.row()
        else:
            row = -1
        self.comboBox.setCurrentIndex(row)
        self.currentIndexChanged(row)
        self.comboBox.setDisabled(True)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)

        self.layout().insertWidget(0, self.comboBox)

    def currentIndexChanged(self, index):
        if index >= 0:
            idIndex = self.rel.fieldIndex('id')
            parentId = self.rel.data(self.rel.index(index, idIndex))
            self.model.setFilter('parentid=%d' % parentId)
        else:
            self.model.setFilter('')

        self.editButtonBox.setEnabled(index >= 0)

    def addItem(self):
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

    def deleteItem(self):
        index = self.selectedIndex()
        if index:
            if self.model.removeRow(index.row()):
                self.model.select()

    def isEnabled(self):
        return self.comboBox.currentIndex() >= 0


class ReferenceDialog(QDialog):
    def __init__(self, section, text='', parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.section = section
        self.db = section.db
        self.db.transaction()

        self.setWindowTitle(section.title)

        self.referenceWidget = self._referenceWidget(section, text)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.referenceWidget)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        self.__selectedIndex = self.referenceWidget.selectedIndex()

    def setWindowTitle(self, title=None):
        windowTitle = QApplication.translate('ReferenceDialog',
                                                   "Reference")
        if title:
            windowTitle = ' - '.join([windowTitle, title])
        super().setWindowTitle(windowTitle)

    def _referenceWidget(self, section, text):
        return ReferenceWidget(section, text, self)

    def accept(self):
        self.section.saveSort(self.referenceWidget.sortButton.isChecked())
        if not self.db.commit():
            self.db.rollback()

        self.__selectedIndex = self.referenceWidget.selectedIndex()
        super().accept()

    def reject(self):
        self.db.rollback()

        super().reject()

    def selectedIndex(self):
        return self.__selectedIndex


class CrossReferenceDialog(ReferenceDialog):
    def __init__(self, section, parentIndex, text='', parent=None):
        self.parentIndex = parentIndex
        super().__init__(section, text, parent)

    def _referenceWidget(self, section, text):
        return CrossReferenceWidget(section, self.parentIndex, text, self)


from functools import WRAPPER_ASSIGNMENTS


def class_wraps(cls):
    """Update a wrapper class `cls` to look like the wrapped."""

    class Wrapper(cls):
        """New wrapper that will extend the wrapper `cls` to make it look like `wrapped`.

        wrapped: Original function or class that is beign decorated.
        assigned: A list of attribute to assign to the the wrapper, by default they are:
             ['__doc__', '__name__', '__module__', '__annotations__'].

        """

        def __init__(self, wrapped, assigned=WRAPPER_ASSIGNMENTS):
            self.__wrapped = wrapped
            for attr in assigned:
                setattr(self, attr, getattr(wrapped, attr))

            super().__init__(wrapped)

        def __repr__(self):
            return repr(self.__wrapped)

    return Wrapper


@storeDlgSizeDecorator
class AllReferenceDialog(QDialog):
    def __init__(self, reference, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.db = reference.db
        self.db.transaction()

        self.setWindowTitle(self.tr("Reference"))

        self.sections = reference.sections

        tab = QTabWidget(self)
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

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def accept(self):
        for section in self.sections:
            widget = self.widgets[section.name]
            section.saveSort(widget.sortButton.isChecked())
        if not self.db.commit():
            QMessageBox.critical(self.parent(),
                            self.tr("Save reference"),
                            self.tr("Something went wrong when saving. Please restart"))
            self.db.rollback()

        super().accept()

    def reject(self):
        # Make select for close all SQL request
        for section in self.sections:
            section.model.select()

        if not self.db.rollback():
            QMessageBox.critical(self.parent(),
                            self.tr("Save reference"),
                            self.tr("Something went wrong when canceling. Please restart"))

        for section in self.sections:
            section.setSort()
            section.model.select()

        super().reject()
