#!/usr/bin/env python3

import os
from PySide6.QtCore import QLibraryInfo

i18n_path = os.path.join(os.path.dirname(__file__), "../OpenNumismat/resources/i18n")
dst_path = os.path.join(os.path.dirname(__file__), "../OpenNumismat/resources/i18n")

pyqt_path = QLibraryInfo.path(QLibraryInfo.LibraryExecutablesPath)
lrelease_path = os.path.join(pyqt_path, 'lrelease')

for filename in os.listdir(i18n_path):
    _, file_extension = os.path.splitext(filename)
    if file_extension == ".ts" and filename != "lang.ts":
        os.system(' '.join([lrelease_path, os.path.join(dst_path, filename)]))
