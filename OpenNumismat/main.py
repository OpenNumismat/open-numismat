import locale
import os
import platform
import shutil
import sys
import traceback

from PyQt4 import QtGui, QtCore

import OpenNumismat
from OpenNumismat.Settings import Settings
from OpenNumismat.MainWindow import MainWindow
from OpenNumismat.Tools import TemporaryDir
from OpenNumismat import version


def main():
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        # Work around system locale not specified (under Linux or Mac OS)
        pass

    app = QtGui.QApplication(sys.argv)

    QtCore.QCoreApplication.setOrganizationName(version.Company)
    QtCore.QCoreApplication.setApplicationName(version.AppName)

    settings = Settings()
    if settings['error']:
        sys.excepthook = exceptHook

    if not os.path.exists(settings['reference']):
        # Create default dirs and files if not exists
        try:
            ref_path = os.path.dirname(settings['reference'])
            dst_ref = os.path.join(ref_path, 'reference.ref')
            if not os.path.exists(dst_ref):
                os.makedirs(ref_path, exist_ok=True)
                src_ref = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                   'reference_%s.ref' % settings['locale'])
                shutil.copy(src_ref, dst_ref)

            dst_demo_db = os.path.join(OpenNumismat.HOME_PATH, 'demo.db')
            if not os.path.exists(dst_demo_db):
                os.makedirs(OpenNumismat.HOME_PATH, exist_ok=True)
                src_demo_db = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                           'demo_%s.db' % settings['locale'])
                shutil.copy(src_demo_db, dst_demo_db)
        except:
            pass

    TemporaryDir.init(version.AppName)

    lang = settings['locale']

    translator = QtCore.QTranslator()
    translator.load('lang_' + lang, OpenNumismat.PRJ_PATH)
    app.installTranslator(translator)

    translatorQt = QtCore.QTranslator()
    translatorQt.load('qt_' + lang, OpenNumismat.PRJ_PATH)
    app.installTranslator(translatorQt)

    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.raise_()  # this will raise the window on Mac OS X
    status = app.exec_()

    # Clear temporary files
    TemporaryDir.remove()

    sys.exit(status)


def exceptHook(type_, value, tback):
    stack = ''.join(traceback.format_exception(type_, value, tback))

    title = QtGui.QApplication.translate("ExcpHook", "System error")
    text = QtGui.QApplication.translate("ExcpHook",
                        "A system error occurred.\n"
                        "Do you want to send an error message to the author\n"
                        "(Google account required)?")
    msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, title, text)
    msgBox.setDetailedText(stack)
    msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    if msgBox.exec_() == QtGui.QMessageBox.Yes:
        line = traceback.extract_tb(tback, 1)[0]
        subject = "[v%s] %s - %s:%d" % (version.Version, type_.__name__,
                                        line[0], line[1])

        errorMessage = []
        errorMessage.append("%s: %s" % (version.AppName, version.Version))
        errorMessage.append("OS: %s %s %s (%s)" % (platform.system(),
                                                   platform.release(),
                                                   platform.architecture()[0],
                                                   platform.version()))
        errorMessage.append("Python: %s" % platform.python_version())
        errorMessage.append("Qt: %s" % QtCore.PYQT_VERSION_STR)
        errorMessage.append('')
        errorMessage.append(stack)

        url = QtCore.QUrl(version.Web + 'issues/entry')
        url.setQueryItems([('summary', subject),
                           ('comment', '\n'.join(errorMessage))])

        executor = QtGui.QDesktopServices()
        executor.openUrl(url)

    # Call the default handler
    sys.__excepthook__(type_, value, tback)

if __name__ == '__main__':
    main()
