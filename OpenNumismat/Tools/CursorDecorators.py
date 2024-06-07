from functools import wraps
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication


def waitCursorDecorator(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            res = f(*args, **kwds)

        except Exception as e:
            QApplication.restoreOverrideCursor()
            raise e

        QApplication.restoreOverrideCursor()
        return res

    return wrapper
