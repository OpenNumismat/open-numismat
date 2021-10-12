#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import sys

from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5.QtWidgets import QApplication, QFileDialog

sys.path.append('..')
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase
from OpenNumismat.Settings import Settings

app = QApplication(sys.argv)

HOME_PATH = ''
__docDirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
if __docDirs:
    HOME_PATH = os.path.join(__docDirs[0], "OpenNumismat")

file_name, _selectedFilter = QFileDialog.getOpenFileName(None,
                "Open collection", HOME_PATH,
                "Collections (*.db)")
if file_name:
    collection = Collection()
    collection.open(file_name)
    collection.loadReference(Settings()['reference'])

    json_file_name = file_name.replace('.db', '.json')
    json_file = codecs.open(json_file_name, "w", "utf-8")

    image_path = file_name.replace('.db', '_images')
    os.makedirs(image_path, exist_ok=True)

    desc = collection.getDescription()
    data = {'title': desc.title, 'description': desc.description,
            'author': desc.author, 'type': "OpenNumismat"}
    json_file.write('{"description": ')

    model = collection.model()

    sort_column_id = model.fields.sort_id.id
    model.sort(sort_column_id, Qt.AscendingOrder)

    while model.canFetchMore():
        model.fetchMore()

    count = model.rowCount()

    data['count'] = count
    json.dump(data, json_file, indent=2, sort_keys=True, ensure_ascii=False)
    json_file.write(',\n"coins": [\n')

    fields = CollectionFieldsBase()
    for i in range(count):
        data = {}
        coin = model.record(i)
        for field in fields:
            val = coin.value(field.name)
            if val is None or val == '':
                continue

            if field.name in ('id', 'createdat', 'updatedat', 'sort_id') or field.type == Type.PreviewImage:
                continue
            if field.name in ('saledate', 'paydate', 'issuedate') and val == '2000-01-01':
                continue

            if field.type == Type.Image:
                img_file_title = "%d_%s.jpg" % (i + 1, field.name)
                img_file_name = os.path.join(image_path, img_file_title)
                img_file = open(img_file_name, 'wb')
                img_file.write(val)
                img_file.close()
                data[field.name] = img_file_title
            else:
                data[field.name] = val

        json.dump(data, json_file, indent=2, sort_keys=True, ensure_ascii=False)
        if i < count - 1:
            json_file.write(',\n')

    json_file.write(']\n}')
    json_file.close()

    print("Processed %d coins" % model.rowCount())
