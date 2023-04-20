#!/usr/bin/env python3

import os
from PySide6.QtCore import QLibraryInfo

pyqtPath = QLibraryInfo.path(QLibraryInfo.LibraryExecutablesPath)

lupdatePath = os.path.join(pyqtPath, 'lupdate')
lreleasePath = os.path.join(pyqtPath, 'lrelease')
rccPath = os.path.join(pyqtPath, 'rcc')

srcFiles = []
for dirname, dirnames, filenames in os.walk('../OpenNumismat'):
    for filename in filenames:
        fileName, fileExtension = os.path.splitext(filename)
        if fileExtension in ('.py', '.ui'):
            srcFiles.append(os.path.join(dirname, filename))

outputfile = 'lang.ts'
os.system(' '.join([lupdatePath, ' '.join(srcFiles), '-ts', outputfile, '-noobsolete', '-locations', 'none']))
# os.system(' '.join([lupdatePath, '../OpenNumismat', '-ts', outputfile, '-noobsolete', '-extensions', ','.join(['py', 'ui'])]))

f = open('langs')
langs = [x.strip('\n') for x in f.readlines()]

for lang in langs:
    if lang == 'en':
        continue

    src_file = 'lang_%s.ts' % lang
    if os.path.isfile(src_file):
        dst_file = '../OpenNumismat/translations/lang_%s.qm' % lang
        os.system(' '.join([lreleasePath, src_file, '-qm', dst_file]))

src_file = '../resources.qrc'
dst_file = '../OpenNumismat/resources.py'
os.system(' '.join([rccPath, src_file, '-no-compress', '-o', dst_file, '--generator', 'python']))
