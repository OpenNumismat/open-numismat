import os
import sys

from PyQt4.QtGui import QDesktopServices

from OpenNumismat import version


# Getting default path for storing user data
if sys.platform in ['win32', 'darwin']:
    __docDir = QDesktopServices.storageLocation(QDesktopServices.DocumentsLocation)
    HOME_PATH = os.path.join(__docDir, version.AppName)
else:
    __homeDir = QDesktopServices.storageLocation(QDesktopServices.HomeLocation)
    HOME_PATH = os.path.join(__homeDir, version.AppName)


# Getting path where stored application data (icons, templates, etc)
PRJ_PATH = os.path.abspath(os.path.dirname(__file__))
# sys.frozen is True when running from cx_Freeze executable
if getattr(sys, 'frozen', False):
    PRJ_PATH = os.path.dirname(sys.executable)


from OpenNumismat.main import main

__all__ = ["main"]
