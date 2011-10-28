#!/usr/bin/python

import os
import PyQt4

pyqtDir = os.path.dirname(PyQt4.__file__)
lupdatePath = os.path.join(pyqtDir, 'pylupdate4.exe')
linguistPath = os.path.join(pyqtDir, 'linguist.exe')
lreleasePath = os.path.join(pyqtDir, 'lrelease.exe')
    
srcFiles = []
for dirname, dirnames, filenames in os.walk('../src'):
    for filename in filenames:
        fileName, fileExtension = os.path.splitext(filename)
        if fileExtension == '.py':
            srcFiles.append(os.path.join(dirname, filename))
    
outputfile = 'lang_ru.ts'
os.system(' '.join([lupdatePath, ' '.join(srcFiles), '-ts', outputfile]))
os.system(' '.join([linguistPath, outputfile]))
dstfile = 'lang_ru.qm'
os.system(' '.join([lreleasePath, outputfile, '-qm', dstfile]))
