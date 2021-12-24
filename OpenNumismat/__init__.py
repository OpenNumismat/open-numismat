import os
import sys

from PyQt5.QtCore import QStandardPaths

from OpenNumismat import version

# Getting default path for storing user data
HOME_PATH = ''
if sys.platform in ('win32', 'darwin'):
    __location = QStandardPaths.DocumentsLocation
else:
    __location = QStandardPaths.HomeLocation

__docDirs = QStandardPaths.standardLocations(__location)
if __docDirs:
    HOME_PATH = os.path.join(__docDirs[0], version.AppName)
    if not os.path.exists(HOME_PATH):
        HOME_PATH = __docDirs[0]

__imgDirs = QStandardPaths.standardLocations(QStandardPaths.PicturesLocation)
if __imgDirs:
    IMAGE_PATH = __imgDirs[0]
else:
    IMAGE_PATH = HOME_PATH

# Getting path where stored application data (icons, templates, etc)
PRJ_PATH = os.path.abspath(os.path.dirname(__file__))
# sys.frozen is True when running from cx_Freeze executable
if getattr(sys, 'frozen', False):
    PRJ_PATH = os.path.dirname(sys.executable)

from OpenNumismat.main import main
