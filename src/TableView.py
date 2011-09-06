#!/usr/bin/python

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from EditCoinDialog.EditCoinDialog import EditCoinDialog

class TableView(QtGui.QTableView):
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
            data = []
            for i in range(self.model().columnCount()):
                if record.isNull(i):
                    data.append('')
                elif isinstance(record.value(i), QtCore.QByteArray):
                    data.append('')
                else:
                    data.append(str(record.value(i)))
                
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText('\t'.join(data))

    def _paste(self):
        clipboard = QtGui.QApplication.clipboard()
        data = clipboard.text().split('\t')
        if len(data) != self.model().columnCount():
            return
        
        record = self.model().record()
        for i in range(self.model().columnCount()):
            record.setValue(i, data[i])

        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            rec = dialog.getRecord()
            self.model().insertRecord(-1, rec)
            self.model().submitAll()

if __name__ == '__main__':
    from main import run
    run()
