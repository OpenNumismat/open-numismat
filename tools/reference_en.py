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

shutil.copy("../OpenNumismat/db/reference_en.ref", ".")

app = QtGui.QApplication(sys.argv)

ref = Reference()
ref.open('reference_en.ref')

place = ref.section('payplace')
place.addItem('eBay', convertImage('icons/ebay.png'))
place.model.submitAll()

rarity = ref.section('rarity')
rarity.addItem('Common')
rarity.addItem('Normal')
rarity.addItem('Scarce')
rarity.addItem('Rare')
rarity.addItem('Unique')
rarity.addItem('In sets only')
rarity.model.submitAll()

quality = ref.section('quality')
quality.addItem('Uncirculated')
quality.addItem('Brilliant uncirculated')
quality.addItem('Proof')
quality.addItem('Proof like')
quality.addItem('Reverse frosted')
quality.model.submitAll()

defect = ref.section('defect')
defect.addItem('Clipped planchet')
defect.addItem('Lamination')
defect.addItem('Off center strike')
defect.addItem('Broadstrike')
defect.addItem('Mule')
defect.addItem('Doubled die')
defect.addItem('Brockage')
defect.model.submitAll()

type = ref.section('type')
type.addItem('Regular issue')
type.addItem('Commemorative')
type.addItem('Bullion')
type.addItem('Restrike')
type.addItem('Pattern')
type.addItem('Set')
type.addItem('Roll')
type.model.submitAll()

grade = ref.section('grade')
grade.addItem('Unc')
grade.addItem('AU')
grade.addItem('XF')
grade.addItem('VF')
grade.addItem('F')
grade.addItem('VG')
grade.model.submitAll()

obvrev = ref.section('obvrev')
obvrev.addItem('Medallic (0°)')
obvrev.addItem('Coin (180°)')
obvrev.model.submitAll()

edge = ref.section('edge')
edge.addItem('Plain')
edge.addItem('Grooved')
edge.addItem('Reeded')
edge.addItem('Decorated')
edge.addItem('Interrupted reeded')
edge.addItem('Indented')
edge.addItem('Smooth')
edge.model.submitAll()

shape = ref.section('shape')
shape.addItem('Round')
shape.addItem('Square')
shape.addItem('Polygon')
shape.model.submitAll()

material = ref.section('material')
material.addItem('Aluminium')
material.addItem('Antimony')
material.addItem('Carbon')
material.addItem('Chromium')
material.addItem('Cobalt')
material.addItem('Copper')
material.addItem('Gold')
material.addItem('Iron')
material.addItem('Lead')
material.addItem('Magnesium')
material.addItem('Manganese')
material.addItem('Nickel')
material.addItem('Niobium')
material.addItem('Nordic gold')
material.addItem('Palladium')
material.addItem('Platinum')
material.addItem('Silver')
material.addItem('Tantalum')
material.addItem('Tellurium')
material.addItem('Tin')
material.addItem('Zinc')
material.addItem('Bimetal')
material.model.submitAll()
