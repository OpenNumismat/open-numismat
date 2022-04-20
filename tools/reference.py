#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import sys

sys.path.append('..')

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlQuery

from OpenNumismat.Reference.Reference import Reference
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase


def convertImage(fileName):
    image = QtGui.QImage(fileName)
    if image.load(fileName):
        ba = QtCore.QByteArray()
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.WriteOnly)

        image.save(buffer, 'png')

        return ba
    else:
        return None


app = QApplication(sys.argv)
fields = CollectionFieldsBase()
ref = Reference(fields)

file = "ref/colors_en.json"
json_data = codecs.open(file, "r", "utf-8").read()
colors = json.loads(json_data)

file = "ref/countries.json"
json_data = codecs.open(file, "r", "utf-8").read()
countries = json.loads(json_data)

file = "ref/countries_en.json"
json_data = codecs.open(file, "r", "utf-8").read()
en_translations = json.loads(json_data)

f = open('langs')
langs = [x.strip('\n') for x in f.readlines()]

for lang in langs:
    print(lang)

    dst_file = "../OpenNumismat/db/reference_%s.ref" % lang
    try:
        os.remove(dst_file)
    except FileNotFoundError:
        pass

    file = "ref/countries_%s.json" % lang
    json_data = codecs.open(file, "r", "utf-8").read()
    translations = json.loads(json_data)

    ref.open(dst_file, interactive=False)
    ref.load()

    region_section = ref.section('region')
    country_section = ref.section('country')
    unit_section = ref.section('unit')

    ref.db.transaction()

    for i, region in enumerate(countries['regions'], 1):
        pos = en_translations['region'].index(region['name'])
        region_name = translations['region'][pos]

        region_section.addItem(region_name)

        for country in region['countries']:
            pos = en_translations['country'].index(country['name'])
            country_name = translations['country'][pos]

            query = QSqlQuery(country_section.db)
            query.prepare("INSERT INTO ref_country (value, parentid, icon) VALUES (?, ?, ?)")
            query.addBindValue(country_name)
            query.addBindValue(i)
            code = country['code']
            image = convertImage("ref/flags/%s.png" % code.lower())
            query.addBindValue(image)
            query.exec_()
            country_id = query.lastInsertId()

            for unit in country['units']:
                pos = en_translations['unit'].index(unit)
                unit_name = translations['unit'][pos]

                query = QSqlQuery(country_section.db)
                query.prepare("INSERT INTO ref_unit (value, parentid) VALUES (?, ?)")
                query.addBindValue(unit_name)
                query.addBindValue(country_id)
                query.exec_()

    ref.db.commit()

    file = "reference_%s.json" % lang
    if not os.path.isfile(file):
        file = "reference_en.json"
    json_data = codecs.open(file, "r", "utf-8").read()
    data = json.loads(json_data)

    ref.db.transaction()

    for section_name in sorted(data.keys()):
        section = ref.section(section_name)
        for value in data[section_name]:
            section.addItem(value)

    grade = ref.section('grade')
    grade.addItem('Unc')
    grade.addItem('AU')
    grade.addItem('XF')
    grade.addItem('VF')
    grade.addItem('F')
    grade.addItem('VG')
    grade.model.submitAll()

    grader = ref.section('grader')
    grader.addItem('ANACS', convertImage('icons/anacs.png'))
    grader.addItem('ICCS', convertImage('icons/iccs.png'))
    grader.addItem('ICG', convertImage('icons/icg.ico'))
    grader.addItem('NGC', convertImage('icons/ngc.png'))
    grader.addItem('PCGS', convertImage('icons/pcgs.png'))
    grader.addItem('PMG', convertImage('icons/pmg.png'))
    grader.addItem('RNGA', convertImage('icons/rnga.png'))
    if lang == 'ru':
        place.addItem('ННР', convertImage('icons/nreestr.png'))
    grader.model.submitAll()

    place = ref.section('payplace')
    if lang == 'ru':
        place.addItem('Auction.ru', convertImage('icons/newauction.png'))
        place.addItem('Мешок', convertImage('icons/meshok.ico'))
        place.addItem('Конрос', convertImage('icons/conros.ico'))
        place.addItem('Wolmar', convertImage('icons/wolmar.ico'))
        place.addItem('aucland', convertImage('icons/aucland.ico'))
        place.addItem('АукционЪ.СПб', convertImage('icons/spb.png'))
    place.addItem('eBay', convertImage('icons/ebay.png'))
    place.addItem('Heritage', convertImage('icons/heritage.png'))
    place.model.submitAll()

    color_file = "ref/colors_%s.json" % lang
    if not os.path.isfile(color_file):
        color_file = "ref/colors_en.json"
    color_json_data = codecs.open(color_file, "r", "utf-8").read()
    color_translations = json.loads(color_json_data)

    color_section = ref.section('color')

    for pos, color in enumerate(colors['colors']):
        color_name = color_translations['colors'][pos]
        icon_file = "ref/colors/%s.png" % color.lower().replace(' ', '-')
        color_section.addItem(color_name, convertImage(icon_file))

    ref.db.commit()

print("Done")
