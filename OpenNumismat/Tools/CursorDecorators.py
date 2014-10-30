from functools import wraps
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication


def waitCursorDecorator(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        res = f(*args, **kwds)
        QApplication.restoreOverrideCursor()
        return res

    return wrapper
