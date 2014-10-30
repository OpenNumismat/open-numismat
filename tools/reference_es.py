#!/usr/bin/python
# -*- coding: utf-8 -*-

import shutil

from PyQt5 import QtCore, QtGui

def convertImage(fileName):
    ba = QtCore.QByteArray()
    buffer = QtCore.QBuffer(ba)
    buffer.open(QtCore.QIODevice.WriteOnly)

    image = QtGui.QImage(fileName)
    image.save(buffer, 'png')

    return ba

import sys
sys.path.append('..')
from OpenNumismat.Reference.Reference import Reference

shutil.copy("../OpenNumismat/db/reference_es.ref", ".")

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

shape = ref.section('shape')
shape.addItem('Círculo')
shape.model.submitAll()

material = ref.section('material')
material.addItem('Aluminio')
material.addItem('Antimonio')
material.addItem('Caróon')
material.addItem('Cromo')
material.addItem('Cobalto')
material.addItem('Cobre')
material.addItem('Oro')
material.addItem('Hierro')
material.addItem('Plomo')
material.addItem('Magnesio')
material.addItem('Manganeso')
material.addItem('Níquel')
material.addItem('Niobio')
material.addItem('Oro nórdico')
material.addItem('Paladio')
material.addItem('Platino')
material.addItem('Plata')
material.addItem('Tantalio')
material.addItem('Telurio')
material.addItem('Estaño')
material.addItem('Zinc')
material.addItem('Bimetálica')
material.model.submitAll()
