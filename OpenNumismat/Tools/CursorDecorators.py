from functools import wraps
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication, QCursor


def waitCursorDecorator(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        res = f(*args, **kwds)
        QApplication.restoreOverrideCursor()
        return res

    return wrapper
