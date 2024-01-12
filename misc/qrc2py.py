#!/usr/bin/env python3

import os
from PySide6.QtCore import QLibraryInfo

pyqt_path = QLibraryInfo.path(QLibraryInfo.LibraryExecutablesPath)
rcc_path = os.path.join(pyqt_path, 'rcc')
src_file = os.path.join(os.path.dirname(__file__), "../OpenNumismat/resources/resources.qrc")
dst_file = os.path.join(os.path.dirname(__file__), "../OpenNumismat/resources/resources.py")
os.system(' '.join([rcc_path, src_file, '-no-compress', '-o', dst_file, '--generator', 'python']))
