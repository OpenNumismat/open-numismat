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
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.itemDClicked)
    
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
            self._copy(self.currentIndex())
        elif event.matches(QtGui.QKeySequence.Paste):
            self._paste()
                
    def _edit(self, index):
        record = self.model().record(index.row())
        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            updatedRecord = dialog.getRecord()
            self.model().setRecord(index.row(), updatedRecord)
            self.model().submitAll()
    
    def _copy(self, index):
        record = self.model().record(index.row())
        if not record.isEmpty():
            mime = QtCore.QMimeData()

            textData = []
            pickleData = []
            for i in range(self.model().columnCount()):
                if record.isNull(i):
                    textData.append('')
                    pickleData.append(None)
                elif isinstance(record.value(i), QtCore.QByteArray):
                    textData.append('')
                    pickleData.append(record.value(i).data())
                else:
                    textData.append(textToClipboard(str(record.value(i))))
                    pickleData.append(record.value(i))
            
            mime.setText('\t'.join(textData))
            mime.setData(TableView.MimeType, pickle.dumps(pickleData))

            clipboard = QtGui.QApplication.clipboard()
            clipboard.setMimeData(mime)

    def _paste(self):
        clipboard = QtGui.QApplication.clipboard()
        mime = clipboard.mimeData()
        record = self.model().record()
        if mime.hasFormat(TableView.MimeType):
            # Load data stored by application
            pickleData = pickle.loads(mime.data(TableView.MimeType))
            for i in range(self.model().columnCount()):
                record.setValue(i, pickleData[i])
        else:
            # Load data stored by another application (Excel)
            textData = clipboard.text().split('\t')
            if len(textData) != self.model().columnCount():
                return
        
            for i in range(self.model().columnCount()):
                record.setValue(i, clipboardToText(textData[i]))

        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            rec = dialog.getRecord()
            self.model().insertRecord(-1, rec)
            self.model().submitAll()
    
if __name__ == '__main__':
    from main import run
    run()
