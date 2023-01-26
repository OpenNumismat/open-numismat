import os
import platform
import shutil
import ssl
import sys
import traceback

from PyQt5.QtCore import QCoreApplication, QTranslator, QUrl, QUrlQuery, PYQT_VERSION_STR, QSettings
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QDesktopServices

import OpenNumismat
from OpenNumismat.Settings import Settings
from OpenNumismat.MainWindow import MainWindow
from OpenNumismat.Tools import TemporaryDir
from OpenNumismat import resources
from OpenNumismat import version


def main():
    app = QApplication(sys.argv)

    QCoreApplication.setOrganizationName(version.Company)
    QCoreApplication.setApplicationName(version.AppName)

    if version.Portable:
        QCoreApplication.setOrganizationName('.')
        QSettings.setDefaultFormat(QSettings.IniFormat)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope,
                          OpenNumismat.PRJ_PATH)

    settings = Settings()
    if settings['font_size'] == 1:
        app.setStyleSheet("QWidget{font-size: 11pt;}")
    elif settings['font_size'] == 2:
        app.setStyleSheet("QWidget{font-size: 13pt;}")

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
                if not os.path.exists(src_ref):
                    src_ref = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                       'reference_en.ref')

                shutil.copy(src_ref, dst_ref)

            dst_demo_db = os.path.join(OpenNumismat.HOME_PATH, 'demo.db')
            if not os.path.exists(dst_demo_db):
                os.makedirs(OpenNumismat.HOME_PATH, exist_ok=True)
                src_demo_db = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                           'demo_%s.db' % settings['locale'])
                if not os.path.exists(src_demo_db):
                    src_demo_db = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                       'demo_en.ref')

                shutil.copy(src_demo_db, dst_demo_db)

            templates_path = os.path.join(OpenNumismat.HOME_PATH, 'templates')
            os.makedirs(templates_path, exist_ok=True)
        except:
            pass

    TemporaryDir.init(version.AppName)

    lang = settings['locale']

    translator = QTranslator()
    translator.load('translations/lang_' + lang, OpenNumismat.PRJ_PATH)
    app.installTranslator(translator)

    translatorQt = QTranslator()
    translatorQt.load('translations/qtbase_' + lang, OpenNumismat.PRJ_PATH)
    app.installTranslator(translatorQt)

    # TODO: Enable SSL verification
    ssl._create_default_https_context = ssl._create_unverified_context

    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.raise_()  # this will raise the window on Mac OS X
    status = app.exec_()

    # Clear temporary files
    TemporaryDir.remove()

    sys.exit(status)


def exceptHook(type_, value, tback):
    stack = ''.join(traceback.format_exception(type_, value, tback))

    title = QApplication.translate("ExcpHook", "System error")
    text = QApplication.translate("ExcpHook",
                        "A system error occurred.\n"
                        "Do you want to send an error message to the author?")
    msgBox = QMessageBox(QMessageBox.Information, title, text)
    msgBox.setDetailedText(stack)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    if msgBox.exec_() == QMessageBox.Yes:
        line = traceback.extract_tb(tback)[-1]
        subject = "[v%s] %s - %s:%d" % (version.Version, type_.__name__,
                                        line[0], line[1])

        errorMessage = []
        # errorMessage.append(QApplication.translate(
        #    "ExcpHook",
        #    "PLEASE ADD A COMMENT, IT WILL HELP IN SOLVING THE PROBLEM"))
        # errorMessage.append('')
        errorMessage.append("%s: %s" % (version.AppName, version.Version))
        errorMessage.append("OS: %s %s (%s)" % (platform.system(),
                                                platform.release(),
                                                platform.version()))
        errorMessage.append("Python: %s (%s)" % (platform.python_version(),
                                                 platform.architecture()[0]))
        errorMessage.append("Qt: %s" % PYQT_VERSION_STR)
        try:
            errorMessage.append("Locale: %s" % Settings()['locale'])
        except:
            pass

        errorMessage.append('')
        errorMessage.append(stack)

        url = QUrl('http://opennumismat.idea.informer.com/proj/')
        query = QUrlQuery()
        query.addQueryItem('mod', 'add')
        query.addQueryItem('cat', '3')
        query.addQueryItem('idea', subject)
        query.addQueryItem('descr', '\n'.join(errorMessage))
        url.setQuery(query)

        executor = QDesktopServices()
        executor.openUrl(url)

    # Call the default handler
    sys.__excepthook__(type_, value, tback)
