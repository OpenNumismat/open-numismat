#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import sys

from PyQt5.QtCore import QStandardPaths, QTranslator
from PyQt5.QtWidgets import QApplication, QFileDialog
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type

sys.path.append('..')
from OpenNumismat.Collection.Collection import Collection

app = QApplication(sys.argv)

HOME_PATH = ''
__docDirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
if __docDirs:
    HOME_PATH = os.path.join(__docDirs[0], "OpenNumismat")
# Getting path where stored application data (icons, templates, etc)
PRJ_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "OpenNumismat"))

json_file_name, _selectedFilter = QFileDialog.getOpenFileName(None,
                "Open collection", HOME_PATH,
                "Collections (*.json)")
if json_file_name:
    file_name = json_file_name.replace('.json', '.db')
    json_file = codecs.open(json_file_name, "r", "utf-8")
    data = json.load(json_file)

    if 'lang' in data['description']:
        lang = data['description']['lang']
        translator = QTranslator()
        translator.load('lang_' + lang, PRJ_PATH)
        app.installTranslator(translator)

    collection = Collection(None)
    collection.create(file_name)

    image_path = file_name.replace('.db', '_images')

    desc = collection.getDescription()
    desc.author = data['description']['author']
    desc.title = data['description']['title']
    desc.description = data['description']['description']
    desc.save()

    model = collection.model()
    for coin_data in data['coins']:
        coin = model.record()
        for field, value in coin_data.items():
            if field in ('obverseimg', 'reverseimg', 'edgeimg',
                         'photo1', 'photo2', 'photo3', 'photo4'):
                img_file_name = os.path.join(image_path, value)
                img_file = open(img_file_name, 'rb')
                image = img_file.read()
                img_file.close()
                coin.setValue(field, image)
            else:
                coin.setValue(field, value)

        model.insertRecord(-1, coin)

    print("Saving...")
    model.submitAll()

    print("Processed %d coins" % model.rowCount())
