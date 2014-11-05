#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import shutil

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication

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

app = QApplication(sys.argv)
ref = Reference()

f = open('langs')
langs = [x.strip('\n') for x in f.readlines()]

for lang in langs:
    src_file = "../OpenNumismat/db/reference_%s.ref" % lang
    if not os.path.isfile(src_file):
        src_file = "../OpenNumismat/db/reference_en.ref"

    shutil.copy(src_file, ".")

    ref.open('reference_%s.ref' % lang)

    src_ref_file = "reference_%s.json" % lang
    if not os.path.isfile(src_ref_file):
        src_ref_file = "reference_en.json"
    json_data = codecs.open(src_ref_file, "r", "utf-8").read()
    data = json.loads(json_data)

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
        place.addItem('Молоток.Ру', convertImage('icons/molotok.ico'))
        place.addItem('Конрос', convertImage('icons/conros.ico'))
        place.addItem('Wolmar', convertImage('icons/wolmar.ico'))
        place.addItem('АукционЪ.СПб')
    place.addItem('eBay', convertImage('icons/ebay.png'))
    place.model.submitAll()

print("Processed %d referenceses: %s" % (len(langs), ', '.join(langs)))
