#!/usr/bin/env python3

import os
import shutil
import PyQt5

pyqtPath = PyQt5.__path__[0]
translationsPath = os.path.join(pyqtPath, "translations")
lupdatePath = os.path.join(pyqtPath, 'pylupdate5.exe')
linguistPath = os.path.join(pyqtPath, 'linguist.exe')
lreleasePath = os.path.join(pyqtPath, 'lrelease.exe')

srcFiles = []
for dirname, dirnames, filenames in os.walk('../OpenNumismat'):
    for filename in filenames:
        fileName, fileExtension = os.path.splitext(filename)
        if fileExtension in ('.py', '.ui'):
            srcFiles.append(os.path.join(dirname, filename))

outputfile = 'lang_en.ts'
os.system(' '.join([lupdatePath, ' '.join(srcFiles), '-ts', outputfile]))

f = open('langs')
langs = [x.strip('\n') for x in f.readlines()]

for lang in langs:
    if lang == 'en':
        continue

    outputfile = 'lang_%s.ts' % lang
    if os.path.isfile(outputfile):
        dst_file = '../OpenNumismat/translations/lang_%s.qm' % lang
        os.system(' '.join([lreleasePath, outputfile, '-qm', dst_file]))

    src_file = os.path.join(translationsPath, "qtbase_%s.qm" % lang)
    if os.path.isfile(src_file):
        shutil.copy(src_file, "../OpenNumismat/translations")
