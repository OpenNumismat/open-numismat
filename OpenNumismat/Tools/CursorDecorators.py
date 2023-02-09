from functools import wraps
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication


def waitCursorDecorator(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        res = f(*args, **kwds)
        QApplication.restoreOverrideCursor()
        return res

    return wrapper
