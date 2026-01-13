import os
import platform
import shutil
import ssl
import sys
import traceback

from PySide6.QtCore import (
    Qt,
    QCoreApplication,
    QLibraryInfo,
    QLocale,
    QSettings,
    QTranslator,
    QUrl,
    QUrlQuery,
)
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QDesktopServices
from PySide6 import __version__ as PYQT_VERSION_STR

import OpenNumismat
from OpenNumismat.Settings import Settings
from OpenNumismat.LatestCollections import LatestCollections
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
                          OpenNumismat.HOME_PATH)

    settings = Settings()
    if settings['font_size'] == 1:
        app.setStyleSheet("QWidget{font-size: 11pt;}")
    elif settings['font_size'] == 2:
        app.setStyleSheet("QWidget{font-size: 13pt;}")
    # TODO: Warning: To ensure that the application's style is set correctly,
    # it is best to call this function before the QApplication constructor,
    # if possible. (https://doc.qt.io/qt-6/qapplication.html#setStyle)
    app.setStyle(settings['style'])
    styleHints = app.styleHints()
    styleHints.setColorScheme(Qt.ColorScheme(settings['color_scheme']))

    if settings['error']:
        sys.excepthook = exceptHook

    setupHomeFolder(settings)

    TemporaryDir.init(version.AppName)

    locale = QLocale(settings['locale'])

    translator = QTranslator(app)
    if translator.load(locale, 'lang', '_', ':/i18n'):
        app.installTranslator(translator)

    path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
    translator = QTranslator(app)
    if translator.load(locale, 'qtbase', '_', path):
        app.installTranslator(translator)

    # TODO: Enable SSL verification
    ssl._create_default_https_context = ssl._create_unverified_context

    mainWindow = MainWindow()
    mainWindow.show()
    mainWindow.raise_()  # this will raise the window on Mac OS X
    mainWindow.openStartCollection()

    status = app.exec()

    # Clear temporary files
    TemporaryDir.remove()

    sys.exit(status)


def setupHomeFolder(settings):
    if not os.path.exists(settings['reference']):
        # Create default dirs and files if not exists
        try:
            ref_path = os.path.dirname(settings['reference'])
            dst_ref = os.path.join(ref_path, 'reference.ref')
            if not os.path.exists(dst_ref):
                os.makedirs(ref_path, exist_ok=True)
                src_ref = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                   f"reference_{settings['locale']}.ref")
                if not os.path.exists(src_ref):
                    src_ref = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                       'reference_en.ref')

                shutil.copy(src_ref, dst_ref)

            dst_demo_db = LatestCollections.DefaultCollectionName
            if not os.path.exists(dst_demo_db):
                os.makedirs(OpenNumismat.HOME_PATH, exist_ok=True)
                src_demo_db = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                           f"demo_{settings['locale']}.db")
                if not os.path.exists(src_demo_db):
                    src_demo_db = os.path.join(OpenNumismat.PRJ_PATH, 'db',
                                       'demo_en.db')

                shutil.copy(src_demo_db, dst_demo_db)

            templates_path = os.path.join(OpenNumismat.HOME_PATH, 'templates')
            os.makedirs(templates_path, exist_ok=True)
        except ValueError:
            pass


def exceptHook(type_, value, tback):
    stack = ''.join(traceback.format_exception(type_, value, tback))

    title = QApplication.translate("ExcpHook", "System error")
    text = QApplication.translate("ExcpHook",
                        "A system error occurred.\n"
                        "Do you want to send an error message to the author?")
    msgBox = QMessageBox(QMessageBox.Information, title, text)
    msgBox.setDetailedText(stack)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    if msgBox.exec() == QMessageBox.Yes:
        line = traceback.extract_tb(tback, -1)[0]
        subject = "[v%s] %s - %s:%d" % (version.Version, type_.__name__,
                                        line[0], line[1])

        errorMessage = []
        # errorMessage.append(QApplication.translate(
        #    "ExcpHook",
        #    "PLEASE ADD A COMMENT, IT WILL HELP IN SOLVING THE PROBLEM"))
        # errorMessage.append('')
        version_str = f"{version.AppName}: {version.Version}"
        package_types = []
        if "__compiled__" in globals():
            package_types.append('nuitka')
        if version.Portable:
            package_types.append('portable')
        if package_types:
            version_str += f" ({','.join(package_types)})"
        errorMessage.append(version_str)
        errorMessage.append("OS: %s %s (%s)" % (platform.system(),
                                                platform.release(),
                                                platform.version()))
        errorMessage.append("Python: %s (%s)" % (platform.python_version(),
                                                 platform.architecture()[0]))
        errorMessage.append(f"Qt: {PYQT_VERSION_STR}")
        try:
            errorMessage.append("Locale: %s" % Settings()['locale'])
        except:
            pass

        errorMessage.append('')
        errorMessage.append(stack)

        url = QUrl('https://opennumismat.idea.informer.com/proj/')
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
