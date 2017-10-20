#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import sys

from PyQt5.QtCore import QByteArray, QIODevice, QBuffer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import QImage

from OpenNumismat.Reference.Reference import Reference
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase


app = QApplication(sys.argv)

src_file = "ref/countries.json"
json_data = codecs.open(src_file, "r", "utf-8").read()
countries = json.loads(json_data)

en_file = "ref/countries_en.json"
en_json_data = codecs.open(en_file, "r", "utf-8").read()
en_translations = json.loads(en_json_data)

for lang in ['en', 'de', 'es', 'fr', 'it', 'nl', 'pt', 'ru']:
    print(lang)

    tr_file = "ref/countries_%s.json" % lang
    tr_json_data = codecs.open(tr_file, "r", "utf-8").read()
    translations = json.loads(tr_json_data)

    ref_file = "ref/reference_%s.ref" % lang
    try:
        os.remove(ref_file)
    except FileNotFoundError:
        pass
    fields = CollectionFieldsBase()
    ref = Reference(fields)
    ref.open(ref_file)

    region_section = ref.section('region')
    country_section = ref.section('country')
    unit_section = ref.section('unit')

    for i, region in enumerate(countries['regions'], 1):
        pos = en_translations['region'].index(region['name'])
        region_name = translations['region'][pos]

        region_section.addItem(region_name)

        for country in region['countries']:
            pos = en_translations['country'].index(country['name'])
            country_name = translations['country'][pos]

            query = QSqlQuery(country_section.db)
            query.prepare("INSERT INTO country (value, parentid, icon) VALUES (?, ?, ?)")
            query.addBindValue(country_name)
            query.addBindValue(i)
            code = country['code']
            image = QImage()
            if image.load("ref/flags/%s.png" % code.lower()):
                ba = QByteArray()
                buffer = QBuffer(ba)
                buffer.open(QIODevice.WriteOnly)
                image.save(buffer, 'png')

                query.addBindValue(ba)
            else:
                query.addBindValue(None)
            query.exec_()
            country_id = query.lastInsertId()

            for unit in country['units']:
                pos = en_translations['unit'].index(unit)
                unit_name = translations['unit'][pos]

                query = QSqlQuery(country_section.db)
                query.prepare("INSERT INTO unit (value, parentid) VALUES (?, ?)")
                query.addBindValue(unit_name)
                query.addBindValue(country_id)
                query.exec_()

print('Done')
