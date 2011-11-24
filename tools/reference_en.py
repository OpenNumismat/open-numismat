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
ref.open('reference_en.db')

for sec in ref.allSections():
    ref.section(sec)

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

type = ref.section('type')
type.addItem('Regular issue')
type.addItem('Commemorative')
type.addItem('Bullion')
type.addItem('Restrike')
type.addItem('Pattern')
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
edge.addItem('Reeded')
edge.addItem('Smooth')
edge.addItem('Segmented reeding')
edge.model.submitAll()

form = ref.section('form')
form.addItem('Circle')
form.model.submitAll()

metal = ref.section('metal')
metal.addItem('Aluminium')
metal.addItem('Antimony')
metal.addItem('Carbon')
metal.addItem('Chromium')
metal.addItem('Cobalt')
metal.addItem('Copper')
metal.addItem('Gold')
metal.addItem('Iron')
metal.addItem('Lead')
metal.addItem('Magnesium')
metal.addItem('Manganese')
metal.addItem('Nickel')
metal.addItem('Niobium')
metal.addItem('Nordic gold')
metal.addItem('Palladium')
metal.addItem('Platinum')
metal.addItem('Silver')
metal.addItem('Tantalum')
metal.addItem('Tellurium')
metal.addItem('Tin')
metal.addItem('Zinc')
metal.addItem('Bimetal')
metal.model.submitAll()
