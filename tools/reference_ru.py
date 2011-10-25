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
ref.open('reference_ru.db')

for sec in ref.allSections():
    ref.section(sec)

place = ref.section('payplace')
place.addItem('Молоток.Ру', convertImage('icons/molotok.ico'))
place.addItem('Конрос', convertImage('icons/conros.ico'))
place.addItem('Wolmar', convertImage('icons/wolmar.ico'))
place.addItem('eBay', convertImage('icons/ebay.png'))
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

quality = ref.section('quality')
quality.addItem('Unc')
quality.addItem('BU')
quality.addItem('Proof')
quality.addItem('Proof like')
quality.addItem('Reverse frosted')
quality.model.submitAll()

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

type = ref.section('type')
type.addItem('Курсовая (регулярная)')
type.addItem('Памятная (юбилейная)')
type.addItem('Инвестиционная')
type.addItem('Новодел')
type.addItem('Пробная')
type.addItem('Набор')
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
obvrev.addItem('Медальное (0°)')
obvrev.model.submitAll()

edge = ref.section('edge')
edge.addItem('Гладкий')
edge.addItem('Рубчатый')
edge.addItem('Прерывисто-рубчатый')
edge.addItem('Шнуровидный')
edge.addItem('Пунктирный')
edge.addItem('Надпись')
edge.addItem('Сетчатый')
edge.addItem('Узорный')
edge.model.submitAll()

form = ref.section('form')
form.addItem('Круг')
form.model.submitAll()

metal = ref.section('metal')
metal.addItem('Акмонитал')
metal.addItem('Алюминиевая бронза')
metal.addItem('Алюминий')
metal.addItem('Биллон')
metal.addItem('Биметалл')
metal.addItem('Бронза')
metal.addItem('Железо')
metal.addItem('Золото')
metal.addItem('Латунь')
metal.addItem('Медно-никелевый сплав')
metal.addItem('Медно-цинковый сплав')
metal.addItem('Медь')
metal.addItem('Мельхиор')
metal.addItem('Нейзильбер')
metal.addItem('Никель')
metal.addItem('Палладий')
metal.addItem('Платина')
metal.addItem('Северное золото')
metal.addItem('Серебро')
metal.addItem('Сталь')
metal.addItem('Томпак')
metal.addItem('Цинк')
metal.model.submitAll()
