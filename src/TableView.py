#!/usr/bin/python

import pickle

from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtCore import Qt

from EditCoinDialog.EditCoinDialog import EditCoinDialog

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

class TableView(QtGui.QTableView):
    # TODO: Changes mime type
    MimeType = 'num/data'
    
    def __init__(self, parent=None):
        super(TableView, self).__init__(parent)
        
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.itemDClicked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
    
    def setModel(self, model):
        super(TableView, self).setModel(model)
        
        self.hideColumn(0)
        
    def itemDClicked(self, index):
        self._edit(index)
        
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

    def contextMenuEvent(self, pos):
        separator = QtGui.QAction(self)
        separator.setSeparator(True)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)

        menu = QtGui.QMenu(self)
        menu.addAction(self.tr("Clone"), self._clone)
        menu.addAction(self.tr("Copy"), self._copy)
        menu.addAction(self.tr("Paste"), self._paste)
        menu.addAction(separator)
        menu.addAction(icon, self.tr("Delete"), self._delete)
        menu.exec_(self.mapToGlobal(pos))
    
    def selectedRows(self):
        indexes = self.selectedIndexes()
        if len(indexes) == 0:
            indexes.append(self.currentIndex())
        else:
            a = {}
            for index in indexes:
                a[index.row()] = index
            indexes = a.values()
        
        return indexes

    def _edit(self, index):
        record = self.model().record(index.row())
        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            updatedRecord = dialog.getRecord()
            self.model().setRecord(index.row(), updatedRecord)
            self.model().submitAll()
    
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
        mime.setData(TableView.MimeType, pickle.dumps(pickleData))

        clipboard = QtGui.QApplication.clipboard()
        clipboard.setMimeData(mime)

    def _paste(self):
        clipboard = QtGui.QApplication.clipboard()
        mime = clipboard.mimeData()
        
        if mime.hasFormat(TableView.MimeType):
            # Load data stored by application
            pickleData = pickle.loads(mime.data(TableView.MimeType))
            for recordData in pickleData:
                record = self.model().record()
                for i in range(self.model().columnCount()):
                    record.setValue(i, recordData[i])
        
                dialog = EditCoinDialog(record, self)
                result = dialog.exec_()
                if result == QtGui.QDialog.Accepted:
                    newRecord = dialog.getRecord()
                    newRecord.setNull('id')  # remove ID value from record
                    self.model().insertRecord(-1, newRecord)
                    self.model().submitAll()
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
            
                dialog = EditCoinDialog(record, self)
                result = dialog.exec_()
                if result == QtGui.QDialog.Accepted:
                    newRecord = dialog.getRecord()
                    newRecord.setNull('id')  # remove ID value from record
                    self.model().insertRecord(-1, newRecord)
                    self.model().submitAll()
    
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
        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            newRecord = dialog.getRecord()
            newRecord.setNull('id')  # remove ID value from record
            self.model().insertRecord(-1, newRecord)
            self.model().submitAll()
    
if __name__ == '__main__':
    from main import run
    run()
