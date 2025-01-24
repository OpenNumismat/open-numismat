import sys

from PySide6.QtCore import Qt, QFileInfo, QIODevice, QBuffer, QRect, QPoint
from PySide6.QtGui import QImage, QKeySequence, QPainter, QIcon
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QListView,
    QMenu,
    QMessageBox,
    QPushButton,
    QStyle,
    QStyleOptionTab,
    QStylePainter,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import OpenNumismat
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.misc import readImageFilters


class ListView(QListView):
    latestDir = OpenNumismat.IMAGE_PATH

    def __init__(self, widget, parent=None):
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

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
        if not self.selectedIndex():
            act.setDisabled(True)

        menu.addSeparator()

        row = self.currentIndex().row()

        act = menu.addAction(QIcon(':/bullet_arrow_up.png'), self.tr("Move up"),
                             self.moveUp)
        if not self.selectedIndex() or row == 0 or self.model().parent().is_sorted:
            act.setDisabled(True)

        act = menu.addAction(QIcon(':/bullet_arrow_down.png'), self.tr("Move down"),
                             self.moveDown)
        if not self.selectedIndex() or row >= self.model().rowCount() - 1 or self.model().parent().is_sorted:
            act.setDisabled(True)

        menu.addSeparator()

        if self.selectedIndex() and self.selectedIndex().data(Qt.DecorationRole):
            act = menu.addAction(self.tr("Change icon..."), self._addIcon)
        else:
            act = menu.addAction(self.tr("Add icon..."), self._addIcon)
        if not self.selectedIndex():
            act.setDisabled(True)

        act = menu.addAction(self.tr("Paste icon"), self._pasteIcon)
        if not self.selectedIndex():
            act.setDisabled(True)

        act = menu.addAction(self.tr("Clear icon"), self._clearIcon)
        if not self.selectedIndex() or \
                not self.selectedIndex().data(Qt.DecorationRole):
            act.setDisabled(True)

        menu.exec(self.mapToGlobal(event.pos()))

    def addItem(self):
        self.widget.addItem()

    def deleteItem(self):
        self.widget.deleteItem()

    def moveUp(self):
        index1 = self.currentIndex()
        if index1.row() == 0:
            return

        index2 = self.model().index(index1.row() - 1, 0)

        self.model().parent().moveRows(index1.row(), index2.row())

        index = self.model().index(index1.row() - 1, 1)
        self.setCurrentIndex(index)

    def moveDown(self):
        index1 = self.currentIndex()
        if index1.row() >= self.model().rowCount() - 1:
            return

        index2 = self.model().index(index1.row() + 1, 0)

        self.model().parent().moveRows(index1.row(), index2.row())

        index = self.model().index(index1.row() + 1, 1)
        self.setCurrentIndex(index)

    def _addIcon(self):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                self.tr("Open File"), self.latestDir,
                ';;'.join(readImageFilters()))
        if fileName:
            file_info = QFileInfo(fileName)
            self.latestDir = file_info.absolutePath()

            self.loadFromFile(fileName)

    def _pasteIcon(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasImage():
            image = mime.imageData()
            if image.hasAlphaChannel():
                # Fill transparent color if present
                color = Settings()['transparent_color']
                fixedImage = QImage(image.size(), QImage.Format_RGB32)
                fixedImage.fill(color)
                painter = QPainter(fixedImage)
                painter.drawImage(0, 0, image)
                painter.end()
            else:
                fixedImage = image

            self._setNewImage(fixedImage)
        elif mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())

    def loadFromFile(self, fileName):
        image = QImage()
        if image.load(fileName):
            self._setNewImage(image)

    def _setNewImage(self, image):
        maxWidth = 16
        maxHeight = 16
        if image.width() > maxWidth or image.height() > maxHeight:
            scaledImage = image.scaled(maxWidth, maxHeight,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaledImage = image

        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        scaledImage.save(buffer, 'png')

        model = self.model()
        index = model.index(self.selectedIndex().row(), model.sourceModel().fieldIndex('icon'))
        model.setData(index, buffer.data())

    def _clearIcon(self):
        model = self.model()
        index = model.index(self.selectedIndex().row(), model.sourceModel().fieldIndex('icon'))
        model.setData(index, None)


class ReferenceWidget(QWidget):
    def __init__(self, section, text, parent=None):
        super().__init__(parent)

        self.model = section.model

        self.listWidget = ListView(self, parent)
        self.proxyModel = self.model.proxyModel()
        self.listWidget.setModel(self.proxyModel)
        self.listWidget.setModelColumn(self.model.fieldIndex('value'))

        startIndex = self.model.index(0, self.model.fieldIndex('value'))
        indexes = self.model.match(startIndex, 0, text,
                                   flags=Qt.MatchFixedString)
        if indexes:
            # TODO: Not work
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
        self.sortButton.checkStateChanged.connect(self.sortChanged)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.sortButton)
        hlayout.addWidget(self.editButtonBox)
        hlayout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(hlayout)

        layout = QVBoxLayout()
        layout.addWidget(self.listWidget)
        layout.addWidget(widget)
        self.setLayout(layout)

    def sortChanged(self, state):
        self.model.sort(state == Qt.Checked)

    def selectedIndex(self):
        return self.listWidget.selectedIndex()

    def clicked(self, button):
        if button == self.addButton:
            self.addItem()
        elif button == self.delButton:
            self.deleteItem()

    def addItem(self):
        self.proxyModel.setDynamicSortFilter(False)
        row = self.proxyModel.rowCount()
        self.proxyModel.insertRow(row)
        index = self.proxyModel.index(row, self.model.fieldIndex('position'))
        self.proxyModel.setData(index, self.model.nextPosition())
        index = self.proxyModel.index(row, self.model.fieldIndex('value'))
        self.proxyModel.setData(index, self.listWidget.defaultValue())
        self.listWidget.setCurrentIndex(index)
        self.listWidget.edit(index)
        self.proxyModel.setDynamicSortFilter(True)

    def deleteItem(self):
        index = self.selectedIndex()
        if index:
            if self.proxyModel.removeRow(index.row()):
                self.model.select()

    def isEnabled(self):
        return True


class CrossReferenceWidget(ReferenceWidget):
    def __init__(self, section, parentIndex, text, parent=None):
        super().__init__(section, text, parent)

        self.rel = self.model.relationModel(1)

        self.comboBox = QComboBox(parent)
        self.crossProxyModel = self.rel.proxyModel()
        self.comboBox.setModel(self.crossProxyModel)
        self.comboBox.setModelColumn(self.rel.fieldIndex('value'))

        if parentIndex:
            row = parentIndex.row()
        else:
            row = -1
        self.comboBox.setCurrentIndex(row)
        self.currentIndexChanged(row)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)

        self.layout().insertWidget(0, self.comboBox)

    def currentIndexChanged(self, index):
        if index >= 0:
            idIndex = self.rel.fieldIndex('id')
            parentId = self.crossProxyModel.data(self.crossProxyModel.index(index, idIndex))
            self.model.setFilter('%s.parentid=%d' % (self.model.tableName(), parentId))
        else:
            self.model.setFilter(None)

        self.addButton.setEnabled(index >= 0)

    def addItem(self):
        self.proxyModel.setDynamicSortFilter(False)
        idIndex = self.rel.fieldIndex('id')
        index = self.crossProxyModel.index(self.comboBox.currentIndex(), idIndex)
        parentId = self.crossProxyModel.data(index)

        row = self.proxyModel.rowCount()
        self.proxyModel.insertRow(row)
        index = self.proxyModel.index(row, self.model.parentidIndex)
        self.proxyModel.setData(index, parentId)
        index = self.proxyModel.index(row, self.model.fieldIndex('position'))
        self.proxyModel.setData(index, self.model.nextPosition())
        index = self.proxyModel.index(row, self.model.fieldIndex('value'))
        self.proxyModel.setData(index, self.listWidget.defaultValue())
        self.listWidget.setCurrentIndex(index)
        self.listWidget.edit(index)
        self.proxyModel.setDynamicSortFilter(True)

    def deleteItem(self):
        index = self.selectedIndex()
        if index:
            # TODO: Work around bug in Qt 5.5
            # if self.proxyModel.removeRow(index.row()):
            #     self.model.select()
            self.proxyModel.beginRemoveRows(index, index.row(), index.row())
            self.proxyModel.removeRow(index.row())
            self.proxyModel.endRemoveRows()
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

        layout = QVBoxLayout()
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


class VTabBar(QTabBar):

    def tabSizeHint(self, index):
        s = super().tabSizeHint(index)
        s.transpose()
        return s

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class VTabWidget(QTabWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO: Workaround macOS problem
        # https://github.com/yjg30737/pyqt-vertical-tab-widget/issues/1
        if sys.platform != "darwin":
            self.setTabBar(VTabBar())
            self.setTabPosition(QTabWidget.West)


@storeDlgSizeDecorator
class AllReferenceDialog(QDialog):
    def __init__(self, reference, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.db = reference.db
        self.db.transaction()

        self.setWindowTitle(self.tr("Reference"))

        self.sections = reference.sections

        tab = VTabWidget(self)
        self.widgets = {}
        for section in self.sections:
            if section.parent_name:
                widget = CrossReferenceWidget(section, None, '', self)
            else:
                widget = ReferenceWidget(section, '', self)

            self.widgets[section.name] = widget
            tab.addTab(widget, section.title)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
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
