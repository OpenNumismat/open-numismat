#!/usr/bin/python

import operator, pickle

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtSql import QSqlQuery

from EditCoinDialog.EditCoinDialog import EditCoinDialog
from Collection.CollectionFields import CollectionFields
from Collection.CollectionFields import FieldTypes as Type
from SelectColumnsDialog import SelectColumnsDialog
from Collection.HeaderFilterMenu import FilterMenuButton

def textToClipboard(text):
    for c in '\t\n\r':
        if c in text:
            return '"' + text.replace('"', '""') + '"'

    return text

def clipboardToText(text):
    for c in '\t\n\r':
        if c in text:
            return text[1:-1].replace('""', '"')

    return text

class ImageDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        if not index.data().isNull():
            image = QtGui.QImage()
            image.loadFromData(index.data())
            scaledImage = image.scaled(option.rect.width(), option.rect.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QtGui.QPixmap.fromImage(scaledImage)
            rect = option.rect
            # Set rect at center of item
            rect.translate((rect.width()-pixmap.width())/2, (rect.height()-pixmap.height())/2)
            rect.setSize(pixmap.size())
            painter.drawPixmap(rect, pixmap)

class SortFilterProxyModel(QtGui.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SortFilterProxyModel, self).__init__(parent)
        self.setDynamicSortFilter(True)
    
    def lessThan(self, left, right):
        role = Qt.DisplayRole
        if self.sourceModel().columnType(left.column()) in [Type.Date, Type.DateTime]:
            # For date columns use ISO format for sorting
            role = Qt.UserRole

        if self.sortOrder() == Qt.AscendingOrder:
            if left.data(role) == '' or isinstance(left.data(role), QtCore.QPyNullVariant):
                return False
            elif right.data(role) == '' or isinstance(right.data(role), QtCore.QPyNullVariant):
                return True
        else:
            if right.data(role) == '' or isinstance(right.data(role), QtCore.QPyNullVariant):
                return False
            elif left.data(role) == '' or isinstance(left.data(role), QtCore.QPyNullVariant):
                return True

        return left.data(role) < right.data(role)

class ListView(QtGui.QTableView):
    rowChanged = pyqtSignal(object)
    # TODO: Changes mime type
    MimeType = 'num/data'
    
    def __init__(self, listParam, parent=None):
        super(ListView, self).__init__(parent)
        
        self.listParam = listParam
        
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.itemDClicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
        self.setSortingEnabled(True)
        self.horizontalHeader().setMovable(True)
        self.horizontalHeader().sectionDoubleClicked.connect(self.sectionDoubleClicked)
        self.horizontalHeader().sectionResized.connect(self.columnResized)
        self.horizontalHeader().sectionMoved.connect(self.columnMoved)
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self.headerContextMenuEvent)
        self.horizontalScrollBar().valueChanged.connect(self.scrolled)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        # Make header font always bold
        font = self.horizontalHeader().font()
        font.setBold(True)
        self.horizontalHeader().setFont(font)
        
        self.verticalHeader().setVisible(False)
        self.verticalHeader().sectionCountChanged.connect(self.rowCountChanged)
        self.defaultHeight = self.verticalHeader().defaultSectionSize()
        
        self.listCountLabel = QtGui.QLabel()
        self.listSelectedLabel = QtGui.QLabel(self.tr("0 coin(s) selected"))
        
        # Show image data as images
        for field in CollectionFields(listParam.db):
            if field.type == Type.Image or field.type == Type.EdgeImage:
                self.setItemDelegateForColumn(field.id, ImageDelegate(self))
    
    def rowCountChanged(self, oldCount, newCount):
        if self.model():
            sql = "SELECT count(*) FROM coins"
            query = QSqlQuery(sql, self.model().database())
            query.first()
            totalCount = query.record().value(0)
            
            self.listCountLabel.setText(self.tr("%d/%d coins") % (newCount, totalCount))
    
    def columnMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        column = self.listParam.columns[oldVisualIndex]
        self.listParam.columns.remove(column)
        self.listParam.columns.insert(newVisualIndex, column)
        self.listParam.save()

        self._updateHeaderButtons()
    
    def headerContextMenuEvent(self, pos):
        self.pos = pos  # store pos for action
        menu = QtGui.QMenu(self)
        menu.addAction(self.tr("Select columns..."), self._selectColumns)
        menu.addSeparator()
        menu.addAction(self.tr("Adjust size"), self._adjustColumn)
        menu.exec_(self.mapToGlobal(pos))
        self.pos = None
    
    def _adjustColumn(self):
        index = self.horizontalHeader().logicalIndexAt(self.pos)
        self.resizeColumnToContents(index)
    
    def _selectColumns(self):
        dialog = SelectColumnsDialog(self.listParam, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            self.listParam.save()

            self._moveColumns()
            
            for param in self.listParam.columns:
                self.setColumnHidden(param.fieldid, not param.enabled)
    
    def sectionDoubleClicked(self, index):
        # NOTE: When section double-clicked it also clicked => sorting is activated
        self.resizeColumnToContents(index)

    def columnResized(self, index, oldSize, newSize):
        if newSize > 0:
            column = self.horizontalHeader().visualIndex(index)
            self.listParam.columns[column].width = newSize
            # TODO: Saving columns parameters in this slot make resizing too slow
            # self.listParam.save()

        self._updateHeaderButtons()
    
    def model(self):
        if not super(ListView, self).model():
            return None
        return self.proxyModel.sourceModel()
    
    def rowInserted(self, index):
        insertedRowIndex = self.proxyModel.mapFromSource(index)
        self.selectRow(insertedRowIndex.row())
        self.scrollTo(insertedRowIndex)
    
    def setModel(self, model):
        model.rowInserted.connect(self.rowInserted)
        
        self.proxyModel = SortFilterProxyModel(self)
        self.proxyModel.setSourceModel(model)
        super(ListView, self).setModel(self.proxyModel)
        model.proxy = self.proxyModel
        
        self.headerButtons = []
        for param in self.listParam.columns:
            btn = FilterMenuButton(param, self.listParam, self.model(), self.horizontalHeader())
            self.headerButtons.append(btn)
        
        filtersSql = FilterMenuButton.filtersToSql(self.listParam.filters.values())
        self.model().setFilter(filtersSql)

        self.horizontalHeader().sectionResized.disconnect(self.columnResized)

        self._moveColumns()

        for i in range(model.columnCount()):
            self.hideColumn(i)
        
        for param in self.listParam.columns:
            if param.enabled:
                self.showColumn(param.fieldid)
        
        for param in self.listParam.columns:
            if param.width:
                self.horizontalHeader().resizeSection(param.fieldid, param.width)

        self.horizontalHeader().sectionResized.connect(self.columnResized)

        self._updateHeaderButtons()
    
    def scrolled(self, value):
        self._updateHeaderButtons()
    
    def _updateHeaderButtons(self):
        for btn in self.headerButtons:
            index = btn.fieldid
            if self.isColumnHidden(index):
                btn.hide()
            else:
                btn.move(self.columnViewportPosition(index)+self.columnWidth(index)-btn.width()-1, 0)
                btn.show()
    
    def _moveColumns(self):
        self.horizontalHeader().sectionMoved.disconnect(self.columnMoved)

        # Revert to base state
        for pos in range(self.model().columnCount()):
            index = self.horizontalHeader().visualIndex(pos)
            self.horizontalHeader().moveSection(index, pos)

        col = []
        for i in range(self.model().columnCount()):
            col.append(i)
        
        # Move columns
        self.verticalHeader().setDefaultSectionSize(self.defaultHeight)
        for pos, param in enumerate(self.listParam.columns):
            if not param.enabled:
                continue
            index = col.index(param.fieldid)
            col.remove(param.fieldid)
            col.insert(pos, param.fieldid)
            self.horizontalHeader().moveSection(index, pos)
            
            if self.model().fields.field(param.fieldid).type in [Type.Image, Type.EdgeImage]:
                self.verticalHeader().setDefaultSectionSize(self.defaultHeight*1.5)

        self.horizontalHeader().sectionMoved.connect(self.columnMoved)

        self._updateHeaderButtons()
    
    def itemDClicked(self, index):
        self._edit(self.currentIndex())
    
    def keyPressEvent(self, event):
        key = event.key()
        if (key == Qt.Key_Return) or (key == Qt.Key_Enter):
            self._edit(self.currentIndex())
        elif event.matches(QtGui.QKeySequence.Copy):
            self._copy(self.selectedRows())
        elif event.matches(QtGui.QKeySequence.Paste):
            self._paste()
        elif event.matches(QtGui.QKeySequence.Delete):
            self._delete(self.selectedRows())
        else:
            return super(ListView, self).keyPressEvent(event)
    
    def contextMenuEvent(self, pos):
        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)
        
        menu = QtGui.QMenu(self)
        act = menu.addAction(QtGui.QIcon('icons/pencil.png'), self.tr("Edit..."), self._edit)
        act.setShortcut('Enter')
        # Disable Edit when more than one record selected
        act.setEnabled(len(self.selectedRows()) == 1)
        menu.setDefaultAction(act)
        
        menu.addAction(QtGui.QIcon('icons/page_copy.png'), self.tr("Copy"), self._copy, QtGui.QKeySequence.Copy)
        menu.addAction(QtGui.QIcon('icons/page_paste.png'), self.tr("Paste"), self._paste, QtGui.QKeySequence.Paste)
        menu.addSeparator()
        act = menu.addAction(self.tr("Clone"), self._clone)
        # Disable Clone when more than one record selected
        act.setEnabled(len(self.selectedRows()) == 1)
        act = menu.addAction(self.tr("Multi edit..."), self._multiEdit)
        # Disable Multi edit when only one record selected
        act.setEnabled(len(self.selectedRows()) > 1)
        menu.addSeparator()
        menu.addAction(icon, self.tr("Delete"), self._delete, QtGui.QKeySequence.Delete)
        menu.exec_(self.mapToGlobal(pos))
    
    def currentChanged(self, current, previous):
        if current.row() != previous.row():
            self.rowChanged.emit(self.currentIndex())

        return super(ListView, self).currentChanged(current, previous)
    
    def selectionChanged(self, selected, deselected):
        self.listSelectedLabel.setText(self.tr("%d coin(s) selected") % len(self.selectedRows()))
        return super(ListView, self).selectionChanged(selected, deselected)

    def __mapToSource(self, index):
        return self.proxyModel.mapToSource(index)

    def currentIndex(self):
        index = super(ListView, self).currentIndex()
        return self.__mapToSource(index)
    
    def selectedRows(self):
        indexes = self.selectedIndexes()
        if len(indexes) == 0:
            if self.currentIndex().row() >= 0:
                indexes.append(self.currentIndex())
                self.selectRow(self.currentIndex().row())
        else:
            rowsIndexes = {}
            for index in indexes:
                rowsIndexes[index.row()] = self.__mapToSource(index)
            indexes = list(rowsIndexes.values())
        
        return indexes

    def _edit(self, index=None):
        if not index:
            index = self.currentIndex()
        
        record = self.model().record(index.row())
        dialog = EditCoinDialog(self.model().reference, record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            rowCount = self.model().rowCount()

            updatedRecord = dialog.getRecord()
            self.model().setRecord(index.row(), updatedRecord)
            self.model().submitAll()
            
            if rowCount == self.model().rowCount():  # inserted row visible in current model
                updatedRowIndex = self.proxyModel.mapFromSource(index)
                self.selectRow(updatedRowIndex.row())
    
    def _multiEdit(self, indexes=None):
        if not indexes:
            indexes = self.selectedRows()

        # Fill multi record for editing
        multiRecord = self.model().record(indexes[0].row())
        usedFields = [Qt.Checked] * multiRecord.count()
        for index in indexes:
            record = self.model().record(index.row())
            for i in range(multiRecord.count()):
                if multiRecord.value(i) != record.value(i) or not record.value(i):
                    multiRecord.setNull(i)
                    usedFields[i] = Qt.Unchecked

        dialog = EditCoinDialog(self.model().reference, multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            progressDlg = QtGui.QProgressDialog(self.tr("Updating records"), self.tr("Cancel"), 0, len(indexes), self)
            progressDlg.setWindowModality(QtCore.Qt.WindowModal)
            progressDlg.setMinimumDuration(250)
            
            # Fill records by used fields in multi record
            multiRecord = dialog.getRecord()
            usedFields = dialog.getUsedFields()

            # Sort and reverse indexes for updating records that out
            # filtered after updating
            rindexes = sorted(indexes, key=operator.methodcaller('row'), reverse=True)
            for progress, index in enumerate(rindexes):
                progressDlg.setValue(progress)
                if progressDlg.wasCanceled():
                    break

                record = self.model().record(index.row())
                for i in range(multiRecord.count()):
                    if usedFields[i] == Qt.Checked:
                        record.setValue(i, multiRecord.value(i))
                self.model().setRecord(index.row(), record)
            
                self.model().submitAll()

            progressDlg.setValue(len(indexes))
    
    def _copy(self, indexes=None):
        if not indexes:
            indexes = self.selectedRows()

        textData = []
        pickleData = []
        for index in indexes:
            record = self.model().record(index.row())
            if record.isEmpty():
                continue
            
            textRecordData = []
            pickleRecordData = []
            for i in range(self.model().columnCount()):
                if record.isNull(i):
                    textRecordData.append('')
                    pickleRecordData.append(None)
                elif isinstance(record.value(i), QtCore.QByteArray):
                    textRecordData.append('')
                    pickleRecordData.append(record.value(i).data())
                else:
                    textRecordData.append(textToClipboard(str(record.value(i))))
                    pickleRecordData.append(record.value(i))
            
            textData.append('\t'.join(textRecordData))
            pickleData.append(pickleRecordData)

        mime = QtCore.QMimeData()
        mime.setText('\n'.join(textData))
        mime.setData(ListView.MimeType, pickle.dumps(pickleData))

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setMimeData(mime)

    def _paste(self):
        clipboard = QtGui.QApplication.clipboard()
        mime = clipboard.mimeData()
        
        if mime.hasFormat(ListView.MimeType):
            # Load data stored by application
            pickleData = pickle.loads(mime.data(ListView.MimeType))
            for recordData in pickleData:
                record = self.model().record()
                for i in range(self.model().columnCount()):
                    record.setValue(i, recordData[i])
                
                self.model().addCoin(record, self)
        elif mime.hasText():
            # Load data stored by another application (Excel)
            # TODO: Process fields with \n and \t
            textData = clipboard.text().split('\n')
            for recordData in textData:
                data = recordData.split('\t')
                # Skip very short (must contain ID and NAME) and too large data
                if len(data) < 2 or len(data) > self.model().columnCount():
                    return
                
                record = self.model().record()
                for i in range(len(data)):
                    record.setValue(i, clipboardToText(data[i]))
                
                self.model().addCoin(record, self)
    
    def _delete(self, indexes=None):
        if not indexes:
            indexes = self.selectedRows()

        result = QtGui.QMessageBox.information(self, self.tr("Delete"),
                                      self.tr("Are you sure to remove a %d coin(s)?") % len(indexes),
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
        if result == QtGui.QMessageBox.Yes:
            for index in indexes:
                self.model().removeRow(index.row())
            self.model().submitAll()
    
    def _clone(self, index=None):
        if not index:
            index = self.currentIndex()

        record = self.model().record(index.row())
        self.model().addCoin(record, self)
