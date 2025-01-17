from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication


def storeDlgSizeDecorator(original_class):
    # Make a copy of original methods
    orig_init = original_class.__init__
    orig_done = original_class.done

    def __init__(self, *args, **kws):
        orig_init(self, *args, **kws)  # call the original __init__

        settings = QSettings()
        orig_class_name = self.__class__.__name__
        geometry = settings.value(f"{orig_class_name}/geometry")
        if geometry:
            if QApplication.screenAt(geometry.center()):
                self.setGeometry(geometry)
        if settings.value(f"{orig_class_name}/maximized", False, type=bool):
            # NOTE: Uses setWindowState(Qt.WindowMaximized) instead showMaximized()
            # for workaround Qt 6.8
            self.setWindowState(Qt.WindowMaximized)

    def done(self, r):
        settings = QSettings()
        orig_class_name = self.__class__.__name__
        settings.setValue(f"{orig_class_name}/maximized", self.isMaximized())
        if not self.isMaximized():
            settings.setValue(f"{orig_class_name}/geometry", self.geometry())

        orig_done(self, r)  # call the original done

    # Set the class' methods to the new one
    original_class.__init__ = __init__
    original_class.done = done
    return original_class


def storeDlgPositionDecorator(original_class):
    # Make a copy of original methods
    orig_done = original_class.done
    orig_show = original_class.show

    def show(self):
        orig_show(self)

        settings = QSettings()
        orig_class_name = self.__class__.__name__
        position = settings.value(f"{orig_class_name}/position")
        if position:
            if QApplication.screenAt(self.rect().center() + position):
                self.move(position)

    def done(self, r):
        settings = QSettings()
        orig_class_name = self.__class__.__name__
        settings.setValue(f"{orig_class_name}/position", self.pos())

        orig_done(self, r)  # call the original done

    # Set the class' methods to the new one
    original_class.done = done
    original_class.show = show
    return original_class
