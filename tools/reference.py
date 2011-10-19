#!/usr/bin/python

from PyQt4 import QtCore, QtGui

def convertImage(fileName):
    ba = QtCore.QByteArray() 
    buffer = QtCore.QBuffer(ba)
    buffer.open(QtCore.QIODevice.WriteOnly)

    image = QtGui.QImage(fileName)
    image.save(buffer, 'png')

    return ba

import sys
sys.path.append('../src')
from Reference.Reference import Reference

app = QtGui.QApplication(sys.argv)

ref = Reference()
ref.open('reference.db')

for sec in ref.allSections():
    ref.section(sec)

place = ref.section('payplace')

record = place.model.record()
record.setValue('value', 'Молоток.Ру')
record.setValue('icon', convertImage('icons/molotok.ico'))
place.model.insertRecord(-1, record)

record = place.model.record()
record.setValue('value', 'Конрос')
record.setValue('icon', convertImage('icons/conros.ico'))
place.model.insertRecord(-1, record)

record = place.model.record()
record.setValue('value', 'Wolmar')
record.setValue('icon', convertImage('icons/wolmar.ico'))
place.model.insertRecord(-1, record)

record = place.model.record()
record.setValue('value', 'АукционЪ.СПб')
place.model.insertRecord(-1, record)

place.model.submitAll()
