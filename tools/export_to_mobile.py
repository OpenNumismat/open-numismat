#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QStandardPaths
from PyQt5.QtWidgets import QApplication, QFileDialog, QDialog

sys.path.append('..')
from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.Export import ExportDialog

IMAGE_OBVERSE = 0
IMAGE_REVERSE = 1
IMAGE_BOTH = 2

app = QApplication(sys.argv)

HOME_PATH = ''
__docDirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
if __docDirs:
    HOME_PATH = os.path.join(__docDirs[0], "OpenNumismat")

dialog = ExportDialog(None)
res = dialog.exec_()
if res == QDialog.Accepted:
    collection = Collection(None)
    collection.open(dialog.params['file'])

    for fullimage in (True, False):
        fullimage_part = ''
        if not fullimage:
            fullimage_part = '_lite'
        for density in ('MDPI', 'HDPI', 'XHDPI', 'XXHDPI', 'XXXHDPI'):
            params = {'filter': dialog.params['filter'], 'image': dialog.params['image'],
                'density': density,
                'file': collection.getCollectionName() + '_' + density.lower() + fullimage_part + '.db',
                'fullimage': fullimage}
            collection.exportToMobile(params)

            print(density, 'done')
