import os

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QProgressDialog, QFileDialog, QApplication, QCheckBox, QMessageBox


class ProgressDialog(QProgressDialog):
    def __init__(self, labelText, cancelButtonText, maximum, parent=None):
        super().__init__(labelText, cancelButtonText, 0, maximum, parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)
        self.setWindowModality(Qt.WindowModal)
        self.setMinimumDuration(250)

    def step(self):
        self.setValue(self.value() + 1)

    # Reimplementing default method for showing updated label immediately
    def setLabelText(self, text):
        super().setLabelText(text)
        self.setMaximum(self.maximum() + 1)
        self.step()


def statusIcon(status):
    return QIcon(":/%s.png" % status)


def getSaveFileName(parent, name, filename, dir_, filters):
    if isinstance(filters, str):
        filters = (filters,)
    settings = QSettings()
    keyDir = name + '/last_dir'
    keyFilter = name + '/last_filter'
    lastExportDir = settings.value(keyDir, dir_)
    defaultFileName = os.path.join(lastExportDir, filename)
    defaultFilter = settings.value(keyFilter)
    caption = QApplication.translate("GetSaveFileName", "Save as")

    fileName, selectedFilter = QFileDialog.getSaveFileName(
        parent, caption, defaultFileName, filter=';;'.join(filters),
        initialFilter=defaultFilter)
    if fileName:
        lastExportDir = os.path.dirname(fileName)
        settings.setValue(keyDir, lastExportDir)
        settings.setValue(keyFilter, selectedFilter)

    return fileName, selectedFilter


def infoMessageBox(key, title, text, parent=None):
    settings = QSettings()
    key = 'show_info/' + key
    show = settings.value(key, True, type=bool)
    if show:
        cb = QCheckBox(QApplication.translate("InfoMessageBox", "Don't show this again"))
        msg_box = QMessageBox(QMessageBox.Information, title, text, parent=parent)
        msg_box.setCheckBox(cb)
        msg_box.exec_()
        if cb.isChecked():
            settings.setValue(key, False)
