import os

from PyQt4 import QtCore, QtGui

import OpenNumismat


class ProgressDialog(QtGui.QProgressDialog):
    def __init__(self, labelText, cancelButtonText, maximum, parent=None):
        super(ProgressDialog, self).__init__(labelText, cancelButtonText, 0,
                            maximum, parent, QtCore.Qt.WindowSystemMenuHint)
        self.setWindowModality(QtCore.Qt.WindowModal)
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
        return QtGui.QIcon(fileName)
    else:
        return QtGui.QIcon()
