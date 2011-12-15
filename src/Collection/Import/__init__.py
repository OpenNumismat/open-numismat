from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

class _Import(QtCore.QObject):
    def __init__(self, parent=None):
        super(_Import, self).__init__(parent)

        self.progressDlg = QtGui.QProgressDialog(self.parent(), Qt.WindowSystemMenuHint)
        self.progressDlg.setWindowModality(Qt.WindowModal)
        self.progressDlg.setMinimumDuration(250)
        self.progressDlg.setCancelButtonText(self.tr("Cancel"))
        self.progressDlg.setWindowTitle(self.tr("Importing"))
    
    def importData(self, src, model):
        connection = self._connect(src)
        if self._check(connection):
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            rows = self._getRows(connection)
            QtGui.QApplication.restoreOverrideCursor();
            
            self.progressDlg.setMaximum(len(rows))
            self.progressDlg.setWindowTitle(self.tr("Importing from %s") % src)
            
            for progress, row in enumerate(rows):
                self.progressDlg.setValue(progress)
                if self.progressDlg.wasCanceled():
                    break
                
                record = model.record()
                self._setRecord(record, row)
                model.appendRecord(record)
            
            self.progressDlg.setValue(len(rows))
        
        self._close(connection)
    
    def _connect(self, src):
        raise NotImplementedError
    
    def _check(self, connection):
        return True
    
    def _getRows(self, connection):
        pass
    
    def _setRecord(self, record, row):
        pass
    
    def _close(self, connection):
        pass

from Collection.Import.Numizmat import ImportNumizmat
from Collection.Import.Cabinet import ImportCabinet
from Collection.Import.CoinsCollector import ImportCoinsCollector

__all__ = ["ImportNumizmat", "ImportCabinet", "ImportCoinsCollector"]
