from PySide6.QtCore import Qt, QStandardPaths, QObject
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QProgressDialog, QMessageBox


class _InvalidDatabaseError(Exception):
    pass


class _DatabaseServerError(Exception):
    pass


class _Import(QObject):
    @staticmethod
    def isAvailable():
        return True

    @staticmethod
    def defaultDir():
        dirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
        if dirs:
            return dirs[0]
        else:
            return ''

    def __init__(self, parent=None):
        super().__init__(parent)

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
                QApplication.restoreOverrideCursor()

                self.progressDlg.setMaximum(len(rows))
                self.progressDlg.setLabelText(QApplication.translate('_Import', "Importing from %s") % src)

                for progress, row in enumerate(rows):
                    self.progressDlg.setValue(progress)
                    if self.progressDlg.wasCanceled():
                        break

                    record = model.record()
                    self._setRecord(record, row)
                    model.appendRecord(record)

                self.progressDlg.reset()
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


class _Import2(QObject):

    @staticmethod
    def isAvailable():
        return True

    @staticmethod
    def defaultDir():
        dirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
        if dirs:
            return dirs[0]
        else:
            return ''

    def __init__(self, parent=None):
        super().__init__(parent)

    def importData(self, src, model):
        self.fields = model.fields
        try:
            connection = self._connect(src)
            if not connection:
                return

            if self._check(connection):
                rows_count = self._getRowsCount(connection)

                progressDlg = QProgressDialog(self.parent(),
                                              Qt.WindowCloseButtonHint |
                                              Qt.WindowSystemMenuHint)
                progressDlg.setWindowModality(Qt.WindowModal)
                progressDlg.setCancelButtonText(QApplication.translate('_Import2', "Cancel"))
                progressDlg.setWindowTitle(QApplication.translate('_Import2', "Importing"))
                progressDlg.setMaximum(rows_count)
                progressDlg.setLabelText(QApplication.translate('_Import2', "Importing from %s") % src)

                for row in range(rows_count):
                    progressDlg.setValue(row)
                    if progressDlg.wasCanceled():
                        break

                    record = model.record()
                    self._setRecord(record, row)
                    model.appendRecord(record)

                progressDlg.reset()
            else:
                self.__invalidDbMessage(src)

            self._close(connection)

        except _InvalidDatabaseError as error:
            self.__invalidDbMessage(src, error.__str__())
        except _DatabaseServerError as error:
            self.__serverErrorMessage(error.__str__())

    def _connect(self, src):
        raise NotImplementedError

    def _check(self, connection):
        return True

    def _getRowsCount(self, connection):
        raise NotImplementedError

    def _setRecord(self, record, row):
        raise NotImplementedError

    def _close(self, connection):
        pass

    def __errorMessage(self, message, text):
        msgBox = QMessageBox(QMessageBox.Critical,
                             QApplication.translate('_Import', "Importing"),
                             message,
                             parent=self.parent())
        if text:
            msgBox.setDetailedText(text)
        msgBox.exec_()

    def __invalidDbMessage(self, src, text=''):
        self.__errorMessage(QApplication.translate('_Import', "'%s' is not a valid database") % src, text)

    def __serverErrorMessage(self, text=''):
        self.__errorMessage(QApplication.translate('_Import', "DB server connection problem. Check additional software."), text)


from OpenNumismat.Collection.Import.CoinManage import ImportCoinManage
from OpenNumismat.Collection.Import.CoinManagePredefined import ImportCoinManagePredefined
from OpenNumismat.Collection.Import.CollectionStudio import ImportCollectionStudio
from OpenNumismat.Collection.Import.Ucoin import ImportUcoin, ImportUcoin2
from OpenNumismat.Collection.Import.Tellico import ImportTellico
from OpenNumismat.Collection.Import.Excel import ImportExcel
from OpenNumismat.Collection.Import.Colnect import ImportColnect
from OpenNumismat.Collection.Import.Numista import ImportNumista
from OpenNumismat.Collection.Import.CoinSnap import ImportCoinSnap

__all__ = ("ImportCoinManage", "ImportCoinManagePredefined",
           "ImportCollectionStudio", "ImportUcoin", "ImportUcoin2",
           "ImportTellico", "ImportExcel", "ImportColnect", "ImportNumista",
           "ImportCoinSnap")
