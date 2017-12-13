#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import shutil
import sys

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication

from OpenNumismat.Reference.Reference import Reference
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase


def convertImage(fileName):
    ba = QtCore.QByteArray()
    buffer = QtCore.QBuffer(ba)
    buffer.open(QtCore.QIODevice.WriteOnly)

    image = QtGui.QImage(fileName)
    image.save(buffer, 'png')

    return ba


sys.path.append('..')

app = QApplication(sys.argv)
fields = CollectionFieldsBase()
ref = Reference(fields)

f = open('langs')
langs = [x.strip('\n') for x in f.readlines()]

for lang in langs:
    print(lang)

    src_file = "ref/reference_%s.ref" % lang
    if not os.path.isfile(src_file):
        src_file = "ref/reference_en.ref"

    dst_file = "../OpenNumismat/db/reference_%s.ref" % lang
    shutil.copy(src_file, dst_file)

    ref.open(dst_file)
    ref.load()

    src_ref_file = "reference_%s.json" % lang
    if not os.path.isfile(src_ref_file):
        src_ref_file = "reference_en.json"
    json_data = codecs.open(src_ref_file, "r", "utf-8").read()
    data = json.loads(json_data)

    ref.db.transaction()

    for section_name, values in data.items():
        section = ref.section(section_name)
        for value in values:
            section.addItem(value)

    grade = ref.section('grade')
    grade.addItem('Unc')
    grade.addItem('AU')
    grade.addItem('XF')
    grade.addItem('VF')
    grade.addItem('F')
    grade.addItem('VG')
    grade.model.submitAll()

    place = ref.section('payplace')
    if lang == 'ru':
        place.addItem('newAuction', convertImage('icons/newauction.png'))
        place.addItem('Мешок', convertImage('icons/meshok.ico'))
        place.addItem('Конрос', convertImage('icons/conros.ico'))
        place.addItem('Wolmar', convertImage('icons/wolmar.ico'))
        place.addItem('aucland', convertImage('icons/aucland.ico'))
        place.addItem('АукционЪ.СПб')
    place.addItem('eBay', convertImage('icons/ebay.png'))
    place.model.submitAll()

    ref.db.commit()

print("Done")
