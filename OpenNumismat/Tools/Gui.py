import os

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QColor, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QDialog,
    QFileDialog,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSplitter,
)


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


class Splitter(QSplitter):

    def __init__(self, title, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)

        self.title = title
        self.splitterMoved.connect(self.splitterPosChanged)

    def splitterPosChanged(self, _pos, _index):
        settings = QSettings()
        settings.setValue('pageview/splittersizes' + self.title, self.sizes())

    def showEvent(self, _e):
        settings = QSettings()
        sizes = settings.value('pageview/splittersizes' + self.title)
        if sizes:
            for i, size in enumerate(sizes):
                sizes[i] = int(size)

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)


class ColorButton(QPushButton):

    def __init__(self, color, parent=None):
        super().__init__(parent)

        self._color = color

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.updateColorButton(self._color)
        self.clicked.connect(self.colorButtonClicked)

    def color(self):
        return self._color

    def colorButtonClicked(self):
        dlg = QColorDialog(self._color, self)
        if dlg.exec() == QDialog.Accepted:
            self._color = dlg.currentColor()
            self.updateColorButton(self._color)

    def updateColorButton(self, color):
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        icon = QIcon(pixmap)
        self.setIcon(icon)


def statusIcon(status):
    return QIcon(f":/{status}.png")


def statusColor(status):
    if status == 'demo':
        return QColor(174, 170, 170, 127)
    if status == 'bidding':
        return QColor(174, 117, 104, 127)
    if status == 'ordered':
        return QColor(169, 208, 142, 127)
    if status == 'owned':
        return QColor(112, 173, 71, 127)
    if status == 'duplicate':
        return QColor(45, 200, 138, 127)
    if status == 'replacement':
        return QColor(189, 180, 64, 127)
    if status == 'sold':
        return QColor(192, 0, 0, 127, 127)
    if status == 'wish':
        return QColor(255, 192, 0, 127)
    if status == 'sale':
        return QColor(237, 125, 49, 127)
    if status == 'missing':
        return QColor(154, 104, 174, 127)
    if status == 'pass':
        return QColor(91, 155, 213, 127)

    palette = QPalette()
    return palette.color(QPalette.Midlight)


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
        selectedFilter=defaultFilter)
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
        msg_box.exec()
        if cb.isChecked():
            settings.setValue(key, False)
