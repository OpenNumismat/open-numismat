#!/usr/bin/python

from PyQt4 import QtGui, QtCore

from Settings import Settings
from MainWindow import MainWindow
import version

def main():
    import os, sys, locale
    
    locale.setlocale(locale.LC_ALL, '')
    
    if not os.path.exists(version.AppDir):
        # Create default dirs if not exists
        try:
            os.makedirs(version.AppDir)
        except:
            pass
    
    app = QtGui.QApplication(sys.argv)

    QtCore.QCoreApplication.setOrganizationName(version.Company)
    QtCore.QCoreApplication.setApplicationName(version.AppName)

    settings = Settings()
    if settings.sendError:
        sys.excepthook = exceptHook
    
    lang = settings.language

    translator = QtCore.QTranslator()
    translator.load('lang_'+lang)
    app.installTranslator(translator)

    translatorQt = QtCore.QTranslator()
    translatorQt.load('qt_'+lang)
    app.installTranslator(translatorQt)

    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

def exceptHook(type_, value, tback):
    import platform, sys, traceback
    
    stack = ''.join(traceback.format_exception(type_, value, tback))

    title = QtGui.QApplication.translate("ExcpHook", "System error")
    text = QtGui.QApplication.translate("ExcpHook", "A system error occurred.\nDo you want to send an error message to the author\n(Google account required)?")
    msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, title, text)
    msgBox.setDetailedText(stack)
    msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    if msgBox.exec_() == QtGui.QMessageBox.Yes:
        line = traceback.extract_tb(tback, 1)[0]
        subject = "[v%s] %s - %s:%d" % (version.Version, type_.__name__, line[0], line[1])
        
        errorMessage = []
        errorMessage.append("%s: %s" % (version.AppName, version.Version))
        errorMessage.append("OS: %s %s %s (%s)" % (platform.system(), platform.release(), platform.architecture()[0], platform.version()))
        errorMessage.append("Python: %s" % platform.python_version())
        errorMessage.append("Qt: %s" % QtCore.PYQT_VERSION_STR)
        errorMessage.append('')
        errorMessage.append(stack)

        url = QtCore.QUrl(version.Web + 'issues/entry')
        url.setQueryItems([('summary', subject), ('comment', '\n'.join(errorMessage))])

        executor = QtGui.QDesktopServices()
        executor.openUrl(url)
    
    # Call the default handler
    sys.__excepthook__(type_, value, tback) 

if __name__ == '__main__':
    main()
