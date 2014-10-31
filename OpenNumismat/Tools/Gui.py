import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QProgressDialog

import OpenNumismat


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
        super(ProgressDialog, self).setLabelText(text)
        self.setMaximum(self.maximum() + 1)
        self.step()


def createIcon(fileTitle=None):
    if fileTitle:
        fileName = os.path.join(OpenNumismat.PRJ_PATH, "icons", fileTitle)
        return QIcon(fileName)
    else:
        return QIcon()
