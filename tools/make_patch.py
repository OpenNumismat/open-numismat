#!/usr/bin/python
# -*- coding: utf-8 -*-

import codecs
import json
import os
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QStandardPaths, Qt, QDateTime
from PyQt5.QtGui import QImage
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery
from PyQt5.QtWidgets import QApplication, QFileDialog
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type

sys.path.append('..')
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase

PATCH = [
    {'action': 'add'},
    {'action': 'add'},
    {'action': 'add'},
    {'action': 'add'},
]

SKIPPED_FIELDS = ('edgeimg', 'photo1', 'photo2', 'photo3', 'photo4',
    'obversedesigner', 'reversedesigner', 'catalognum2', 'catalognum3', 'catalognum4',
    'saledate', 'saleprice', 'totalsaleprice', 'buyer', 'saleplace', 'saleinfo',
    'paydate', 'payprice', 'totalpayprice', 'saller', 'payplace', 'payinfo',
    'url', 'obversedesigner', 'reversedesigner', 'barcode', 'quantity',
    'features', 'storage', 'defect', 'note', 'status', 'createdat')

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
    image_path = json_file_name.replace('.json', '_images')
    json_file = codecs.open(json_file_name, "r", "utf-8")
    data = json.load(json_file)

    is_obverse_enabled = False
    is_reverse_enabled = True

    for density in ('MDPI', 'HDPI', 'XHDPI', 'XXHDPI', 'XXXHDPI'):
        print(density, "started")

        db = QSqlDatabase.addDatabase('QSQLITE', 'patch_' + density.lower())
        file_name = json_file_name.replace('.json', '_patch_' + density.lower() + '.db')
        db.setDatabaseName(file_name)
        if not db.open():
            print(db.lastError().text())
            print("Can't open collection")
            exit()

        mobile_settings = {'Version': 1, 'Type': 'Patch'}

        sql = """CREATE TABLE settings (
            title CHAR NOT NULL UNIQUE,
            value CHAR)"""
        QSqlQuery(sql, db)
        for key, value in mobile_settings.items():
            query = QSqlQuery(db)
            query.prepare("""INSERT INTO settings (title, value)
                    VALUES (?, ?)""")
            query.addBindValue(key)
            query.addBindValue(str(value))
            query.exec_()

        sql = """CREATE TABLE patches (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            action CHAR,
            src_id INTEGER,
            dst_id INTEGER)"""
        QSqlQuery(sql, db)

        sql = """CREATE TABLE photos (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            image BLOB)"""
        QSqlQuery(sql, db)

        sqlFields = []
        fields = CollectionFieldsBase()
        for field in fields:
            if field.name == 'id':
                sqlFields.append('id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT')
            elif field.name == 'image':
                sqlFields.append('image INTEGER')
            elif field.name in SKIPPED_FIELDS:
                continue
            else:
                sqlFields.append("%s %s" % (field.name, Type.toSql(field.type)))

        sql = "CREATE TABLE coins (" + ", ".join(sqlFields) + ")"
        QSqlQuery(sql, db)

        dest_model = QSqlTableModel(None, db)
        dest_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        dest_model.setTable('coins')
        dest_model.select()

        height = 64
        if density == 'HDPI':
            height *= 1.5
        elif density == 'XHDPI':
            height *= 2
        elif density == 'XXHDPI':
            height *= 3
        elif density == 'XXXHDPI':
            height *= 4

        coin_id = 0

        for coin_data in data['coins']:
            action = coin_data['action']
            coin = dest_model.record()

            for field in fields:
                if field.name in ('id', 'image', 'obverseimg', 'reverseimg'):
                    continue
                if field.name in SKIPPED_FIELDS:
                    continue
                if field.name == 'updatedat':
                    currentTime = QDateTime.currentDateTimeUtc()
                    coin.setValue('updatedat', currentTime.toString(Qt.ISODate))
                    continue

                if field.name in coin_data:
                    coin.setValue(field.name, coin_data[field.name])

            image = QImage()
            for field_name in ('obverseimg', 'reverseimg'):
                if field_name in coin_data:
                    img_file_name = os.path.join(image_path, coin_data[field_name])
                    img_file = open(img_file_name, 'rb')
                    img_data = img_file.read()
                    img_file.close()

                    query = QSqlQuery(db)
                    query.prepare("""INSERT INTO photos (image)
                            VALUES (?)""")
                    ba = QtCore.QByteArray(img_data)
                    query.addBindValue(ba)
                    query.exec_()
                    img_id = query.lastInsertId()
                    coin.setValue(field_name, img_id)

                    if (field_name == 'obverseimg' and is_obverse_enabled) or \
                       (field_name == 'reverseimg' and is_reverse_enabled):
                        image.loadFromData(img_data)
                        image = image.scaledToHeight(height,
                                                    Qt.SmoothTransformation)

            if not image.isNull():
                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)
                buffer.open(QtCore.QIODevice.WriteOnly)
                # Store as PNG for better view
                image.save(buffer, 'png')
                coin.setValue('image', ba)

            if action == 'update_desc':
                dest_model.insertRecord(-1, coin)
                coin_id += 1
                for i in range(coin.count()):
                    if coin.fieldName(i) not in ('id', 'title', 'subjectshort', 'series', 'obversevar'):
                        coin.setNull(i)
                dest_model.insertRecord(-1, coin)
                coin_id += 1
            elif action == 'update_img':
                for i in range(coin.count()):
                    if coin.fieldName(i) not in ('id', 'title', 'subjectshort', 'series', 'obversevar',
                                             'image', 'obverseimg', 'reverseimg'):
                        coin.setNull(i)
                dest_model.insertRecord(-1, coin)
                coin_id += 1
            elif action == 'add':
                dest_model.insertRecord(-1, coin)
                coin_id += 1
            elif action == 'delete':
                for i in range(coin.count()):
                    if coin.fieldName(i) not in ('id', 'title', 'subjectshort', 'series', 'obversevar'):
                        coin.setNull(i)
                dest_model.insertRecord(-1, coin)
                coin_id += 1

            if action in ('add', 'update_img'):
                query = QSqlQuery(db)
                query.prepare("""INSERT INTO patches (action, src_id)
                        VALUES (?, ?)""")
                query.addBindValue(action)
                query.addBindValue(coin_id)
                query.exec_()
            else:
                query = QSqlQuery(db)
                query.prepare("""INSERT INTO patches (action, src_id, dst_id)
                        VALUES (?, ?, ?)""")
                query.addBindValue(action)
                query.addBindValue(coin_id)
                query.addBindValue(coin_id - 1)
                query.exec_()

        dest_model.submitAll()
        db.close()
        print(density, "done")

    print("Processed %d coins" % dest_model.rowCount())
