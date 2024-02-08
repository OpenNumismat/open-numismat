import os
import sys

from PySide6.QtCore import QStandardPaths

import OpenNumismat
from OpenNumismat import version

def init_pathes():
    if version.Portable:
        OpenNumismat.HOME_PATH = '.'
    else:
        # Getting default path for storing user data
        if sys.platform in ('win32', 'darwin'):
            location = QStandardPaths.DocumentsLocation
        else:
            location = QStandardPaths.HomeLocation
        
        doc_dirs = QStandardPaths.standardLocations(location)
        if doc_dirs:
            OpenNumismat.HOME_PATH = os.path.join(doc_dirs[0], version.AppName)

    img_dirs = QStandardPaths.standardLocations(QStandardPaths.PicturesLocation)
    if img_dirs:
        OpenNumismat.IMAGE_PATH = img_dirs[0]
    else:
        OpenNumismat.IMAGE_PATH = OpenNumismat.HOME_PATH

    # Getting path where stored application data (icons, templates, etc)
    # sys.frozen is True when running from cx_Freeze/pyinstaller executable
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        OpenNumismat.PRJ_PATH = sys._MEIPASS
    elif "__compiled__" in globals():  # for Nuitka
#        OpenNumismat.PRJ_PATH = __compiled__.containing_dir
        OpenNumismat.PRJ_PATH = os.path.dirname(sys.executable)
    else:
        OpenNumismat.PRJ_PATH = os.path.abspath(os.path.dirname(__file__))
