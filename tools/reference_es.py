#!/usr/bin/python
# -*- coding: utf-8 -*-

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
ref.open('reference_es.ref')

place = ref.section('payplace')
place.addItem('eBay', convertImage('icons/ebay.png'))
place.model.submitAll()

rarity = ref.section('rarity')
rarity.addItem('Común')
rarity.addItem('Normal')
rarity.addItem('Limitada')
rarity.addItem('Rara')
rarity.addItem('Única')
rarity.addItem('Sólo en sets')
rarity.model.submitAll()

quality = ref.section('quality')
quality.addItem('Sin circular')
quality.addItem('Brillante sin circular')
quality.addItem('Prueba')
quality.addItem('Similar a prueba')
quality.addItem('Reverso escarchado')
quality.model.submitAll()

type = ref.section('type')
type.addItem('Emisión regular')
type.addItem('Conmemorativa')
type.addItem('Metal precioso')
type.addItem('Reacuñación')
type.addItem('Patrón')
type.addItem('Set')
type.model.submitAll()

grade = ref.section('grade')
grade.addItem('Unc')
grade.addItem('AU')
grade.addItem('XF')
grade.addItem('VF')
grade.addItem('F')
grade.addItem('VG')
grade.model.submitAll()

edge = ref.section('edge')
edge.addItem('Estriado')
edge.addItem('Liso')
edge.addItem('Estriado segmentado')
edge.model.submitAll()

form = ref.section('form')
form.addItem('Círculo')
form.model.submitAll()

metal = ref.section('metal')
metal.addItem('Aluminio')
metal.addItem('Antimonio')
metal.addItem('Caróon')
metal.addItem('Cromo')
metal.addItem('Cobalto')
metal.addItem('Cobre')
metal.addItem('Oro')
metal.addItem('Hierro')
metal.addItem('Plomo')
metal.addItem('Magnesio')
metal.addItem('Manganeso')
metal.addItem('Níquel')
metal.addItem('Niobio')
metal.addItem('Oro nórdico')
metal.addItem('Paladio')
metal.addItem('Platino')
metal.addItem('Plata')
metal.addItem('Tantalio')
metal.addItem('Telurio')
metal.addItem('Estaño')
metal.addItem('Zinc')
metal.addItem('Bimetálica')
metal.model.submitAll()
