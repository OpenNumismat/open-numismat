from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication


def storeDlgSizeDecorator(original_class):
    # Make a copy of original methods
    orig_init = original_class.__init__
    orig_done = original_class.done

    def __init__(self, *args, **kws):
        orig_init(self, *args, **kws)  # call the original __init__

        settings = QSettings()
        orig_class_name = self.__class__.__name__
        size = settings.value('%s/size' % orig_class_name)
        if size:
            self.resize(size)
        if settings.value('%s/maximized' % orig_class_name, False, type=bool):
            self.showMaximized()

    def done(self, r):
        settings = QSettings()
        orig_class_name = self.__class__.__name__
        settings.setValue('%s/maximized' % orig_class_name, self.isMaximized())
        if not self.isMaximized():
            settings.setValue('%s/size' % orig_class_name, self.size())

        orig_done(self, r)  # call the original done

    # Set the class' methods to the new one
    original_class.__init__ = __init__
    original_class.done = done
    return original_class


def storeDlgPositionDecorator(original_class):
    # Make a copy of original methods
    orig_init = original_class.__init__
    orig_done = original_class.done

    def __init__(self, *args, **kws):
        orig_init(self, *args, **kws)  # call the original __init__

        settings = QSettings()
        orig_class_name = self.__class__.__name__
        position = settings.value('%s/position' % orig_class_name)
        if position:
            screen = QApplication.desktop().screenGeometry()
            if screen.contains(self.rect().center() + position):
                self.move(position)

    def done(self, r):
        settings = QSettings()
        orig_class_name = self.__class__.__name__
        settings.setValue('%s/position' % orig_class_name, self.pos())

        orig_done(self, r)  # call the original done

    # Set the class' methods to the new one
    original_class.__init__ = __init__
    original_class.done = done
    return original_class
