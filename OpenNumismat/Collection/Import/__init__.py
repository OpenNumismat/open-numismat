from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import *


class _InvalidDatabaseError(Exception):
    pass


class _DatabaseServerError(Exception):
    pass


class _Import(QtCore.QObject):
    @staticmethod
    def isAvailable():
        return True

    @staticmethod
    def defaultDir():
        return QStandardPaths.displayName(QStandardPaths.DocumentsLocation)

    def __init__(self, parent=None):
        super(_Import, self).__init__(parent)

        self.progressDlg = QProgressDialog(self.parent(),
                                           Qt.WindowCloseButtonHint |
                                           Qt.WindowSystemMenuHint)
        self.progressDlg.setWindowModality(Qt.WindowModal)
        self.progressDlg.setMinimumDuration(250)
        self.progressDlg.setCancelButtonText(QApplication.translate('_Import', "Cancel"))
        self.progressDlg.setWindowTitle(QApplication.translate('_Import', "Importing"))

    def importData(self, src, model):
        try:
            connection = self._connect(src)
            if not connection:
                return False

            if self._check(connection):
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                rows = self._getRows(connection)
                QApplication.restoreOverrideCursor();

                self.progressDlg.setMaximum(len(rows))
                self.progressDlg.setLabelText(QApplication.translate('_Import', "Importing from %s") % src)

                for progress, row in enumerate(rows):
                    self.progressDlg.setValue(progress)
                    if self.progressDlg.wasCanceled():
                        break

                    record = model.record()
                    self._setRecord(record, row)
                    model.appendRecord(record)

                self.progressDlg.setValue(len(rows))
            else:
                self.__invalidDbMessage(src)

            self._close(connection)

            return not self.progressDlg.wasCanceled()

        except _InvalidDatabaseError as error:
            self.__invalidDbMessage(src, error.__str__())
        except _DatabaseServerError as error:
            self.__serverErrorMessage(error.__str__())

        return False

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

    def __errorMessage(self, message, text):
        msgBox = QMessageBox(QMessageBox.Critical, QApplication.translate('_Import', "Importing"),
                                   message,
                                   parent=self.parent())
        if text:
            msgBox.setDetailedText(text)
        msgBox.exec_()

    def __invalidDbMessage(self, src, text=''):
        self.__errorMessage(QApplication.translate('_Import', "'%s' is not a valid database") % src, text)

    def __serverErrorMessage(self, text=''):
        self.__errorMessage(QApplication.translate('_Import', "DB server connection problem. Check additional software."), text)

from OpenNumismat.Collection.Import.Numizmat import ImportNumizmat
from OpenNumismat.Collection.Import.Cabinet import ImportCabinet
from OpenNumismat.Collection.Import.CoinsCollector import ImportCoinsCollector
from OpenNumismat.Collection.Import.CoinManage import ImportCoinManage
from OpenNumismat.Collection.Import.CoinManagePredefined import ImportCoinManagePredefined
from OpenNumismat.Collection.Import.CollectionStudio import ImportCollectionStudio
from OpenNumismat.Collection.Import.Numizmatik_Ru import ImportNumizmatik_Ru
from OpenNumismat.Collection.Import.Numizmatik_RuPredefined import ImportNumizmatik_RuPredefined

__all__ = ["ImportNumizmat", "ImportCabinet", "ImportCoinsCollector",
           "ImportCoinManage", "ImportCoinManagePredefined",
           "ImportCollectionStudio", "ImportNumizmatik_Ru",
           "ImportNumizmatik_RuPredefined"]
