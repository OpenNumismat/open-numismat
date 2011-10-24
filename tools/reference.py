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
place.addItem('Молоток.Ру', convertImage('icons/molotok.ico'))
place.addItem('Конрос', convertImage('icons/conros.ico'))
place.addItem('Wolmar', convertImage('icons/wolmar.ico'))
place.addItem('АукционЪ.СПб')
place.model.submitAll()

rarity = ref.section('rarity')
rarity.addItem('Рядовая')
rarity.addItem('Нечастая')
rarity.addItem('Редкая')
rarity.addItem('Очень редкая')
rarity.addItem('Уникальная')
rarity.addItem('Только в наборах')
rarity.model.submitAll()

defect = ref.section('defect')
defect.addItem('Непрочекан, низкая рельефность изображения')
defect.addItem('Двойной удар')
defect.addItem('Поворот')
defect.addItem('Смещение')
defect.addItem('Соударение штемпелей, холостой удар')
defect.addItem('Односторонний чекан')
defect.addItem('Залипуха, инкузный брак')
defect.addItem('Перепутка, мул')
defect.addItem('Раскол, трещина штемпеля')
defect.addItem('Выкрошка, скол штемпеля')
defect.addItem('Выкус, луна')
defect.model.submitAll()
