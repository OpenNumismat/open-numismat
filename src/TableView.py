#!/usr/bin/python

from PyQt4 import QtGui

from EditCoinDialog import EditCoinDialog

class TableView(QtGui.QTableView):
    def __init__(self, parent=None):
        super(TableView, self).__init__(parent)
        
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.itemDClicked)
        
    def itemDClicked(self, index):
        record = self.model().record(index.row())
        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            updatedRecord = dialog.getRecord()
            self.model().setRecord(index.row(), updatedRecord)
            self.model().submitAll()
    
if __name__ == '__main__':
    from main import run
    run()
