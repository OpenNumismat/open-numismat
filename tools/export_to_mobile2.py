#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import QStandardPaths, Qt
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtSql import QSqlTableModel, QSqlDatabase, QSqlQuery, QSqlField

sys.path.append('..')
from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.Export import ExportDialog
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Tools import Gui

IMAGE_OBVERSE = 0
IMAGE_REVERSE = 1
IMAGE_BOTH = 2

def exportToMobile(model, params):
    IMAGE_FORMAT = 'jpg'
    IMAGE_COMPRESS = 50
    USED_FIELDS = ('title', 'unit', 'country', 'year', 'mint', 'mintmark',
        'issuedate', 'type', 'series', 'subjectshort', 'material', 'fineness',
        'diameter', 'thickness', 'weight', 'mintage', 'rarity',
        'obverseimg', 'reverseimg', 'subject', 'price1', 'price2', 'price3', 'price4')

    if os.path.isfile(params['file']):
        os.remove(params['file'])

    db = QSqlDatabase.addDatabase('QSQLITE', 'mobile')
    db.setDatabaseName(params['file'])
    if not db.open():
        print(db.lastError().text())
        QMessageBox.critical(None, "Create mobile collection", "Can't open collection")
        return

    sql = """CREATE TABLE "android_metadata" ("locale" TEXT DEFAULT 'en_US')"""
    QSqlQuery(sql, db)
    sql = """INSERT INTO "android_metadata" VALUES ('en_US')"""
    QSqlQuery(sql, db)

    mobile_settings = {'Version': 1, 'Type': 'MobilePro', 'Filter': params['filter']}

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

    sql = """CREATE TABLE updates (
        title CHAR NOT NULL UNIQUE,
        value CHAR)"""
    QSqlQuery(sql, db)

    sql = """INSERT INTO updates (title, value)
                VALUES ('160203', '2016-02-03T10:19:00')"""
    QSqlQuery(sql, db)

    sql = """CREATE TABLE photos (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        image BLOB)"""
    QSqlQuery(sql, db)

    sql = """CREATE TABLE coins (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        description_id INTEGER,
        grade INTEGER,
        createdat STRING)"""
    QSqlQuery(sql, db)

    sql = """CREATE INDEX coins_descriptions ON coins(description_id)"""
    QSqlQuery(sql, db)

    sqlFields = []
    fields = CollectionFieldsBase()
    for field in fields:
        if field.name == 'id':
            sqlFields.append('id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT')
        elif field.name == 'image':
            sqlFields.append('image INTEGER')
        elif field.name in USED_FIELDS:
            sqlFields.append("%s %s" % (field.name, Type.toSql(field.type)))

    sql = "CREATE TABLE descriptions (" + ", ".join(sqlFields) + ")"
    QSqlQuery(sql, db)

    while model.canFetchMore():
        model.fetchMore()

    dest_model = QSqlTableModel(None, db)
    dest_model.setEditStrategy(QSqlTableModel.OnManualSubmit)
    dest_model.setTable('descriptions')
    dest_model.select()

    height = 64
    if params['density'] == 'HDPI':
        height *= 1.5
    elif params['density'] == 'XHDPI':
        height *= 2
    elif params['density'] == 'XXHDPI':
        height *= 3
    elif params['density'] == 'XXXHDPI':
        height *= 4
    maxHeight = height * 4

    is_obverse_enabled = params['image'] in (ExportDialog.IMAGE_OBVERSE, ExportDialog.IMAGE_BOTH)
    is_reverse_enabled = params['image'] in (ExportDialog.IMAGE_REVERSE, ExportDialog.IMAGE_BOTH)

    fields = CollectionFieldsBase()
    count = model.rowCount()
    progressDlg = Gui.ProgressDialog("Exporting records",
                                    "Cancel", count, None)

    for i in range(count):
        progressDlg.step()
        if progressDlg.wasCanceled():
            break

        coin = model.record(i)
        if coin.value('status') in ('pass', 'sold'):
            continue

        dest_record = dest_model.record()

        for field in fields:
            if field.name in ('id', 'image', 'obverseimg', 'reverseimg'):
                continue
            if field.name in USED_FIELDS:
                val = coin.value(field.name)
                if val is None or val == '':
                    continue

                dest_record.setValue(field.name, val)

        # Process images
        is_obverse_present = not coin.isNull('obverseimg')
        is_reverse_present = not coin.isNull('reverseimg')
        if is_obverse_present or is_reverse_present:
            obverseImage = QImage()
            reverseImage = QImage()

            if is_obverse_present:
                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)
                buffer.open(QtCore.QIODevice.WriteOnly)

                obverseImage.loadFromData(coin.value('obverseimg'))
                if not obverseImage.isNull() and not params['fullimage'] and obverseImage.height() > maxHeight:
                    scaledImage = obverseImage.scaled(maxHeight, maxHeight,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    scaledImage.save(buffer, IMAGE_FORMAT, IMAGE_COMPRESS)
                    save_data = ba
                else:
                    if not obverseImage.isNull():
                        obverseImage.save(buffer, IMAGE_FORMAT, IMAGE_COMPRESS)
                        save_data = ba
                    else:
                        save_data = coin.value('obverseimg')

                query = QSqlQuery(db)
                query.prepare("""INSERT INTO photos (image)
                        VALUES (?)""")
                query.addBindValue(save_data)
                query.exec_()
                img_id = query.lastInsertId()
                dest_record.setValue('obverseimg', img_id)
            if not obverseImage.isNull():
                obverseImage = obverseImage.scaledToHeight(height,
                                                        Qt.SmoothTransformation)

            if is_reverse_present:
                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)
                buffer.open(QtCore.QIODevice.WriteOnly)

                reverseImage.loadFromData(coin.value('reverseimg'))
                if not reverseImage.isNull() and not params['fullimage'] and reverseImage.height() > maxHeight:
                    scaledImage = reverseImage.scaled(maxHeight, maxHeight,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    scaledImage.save(buffer, IMAGE_FORMAT, IMAGE_COMPRESS)
                    save_data = ba
                else:
                    if not reverseImage.isNull():
                        reverseImage.save(buffer, IMAGE_FORMAT, IMAGE_COMPRESS)
                        save_data = ba
                    else:
                        save_data = coin.value('reverseimg')

                query = QSqlQuery(db)
                query.prepare("""INSERT INTO photos (image)
                        VALUES (?)""")
                query.addBindValue(save_data)
                query.exec_()
                img_id = query.lastInsertId()
                dest_record.setValue('reverseimg', img_id)
            if not reverseImage.isNull():
                reverseImage = reverseImage.scaledToHeight(height,
                                                    Qt.SmoothTransformation)

            if not is_obverse_enabled:
                obverseImage = QImage()
            if not is_reverse_enabled:
                reverseImage = QImage()

            image = QImage(obverseImage.width() + reverseImage.width(),
                                 height, QImage.Format_RGB32)
            image.fill(QColor(Qt.white).rgb())

            paint = QPainter(image)
            if is_obverse_present and is_obverse_enabled:
                paint.drawImage(QtCore.QRectF(0, 0, obverseImage.width(), height), obverseImage,
                                QtCore.QRectF(0, 0, obverseImage.width(), height))
            if is_reverse_present and is_reverse_enabled:
                paint.drawImage(QtCore.QRectF(obverseImage.width(), 0, reverseImage.width(), height), reverseImage,
                                QtCore.QRectF(0, 0, reverseImage.width(), height))
            paint.end()

            ba = QtCore.QByteArray()
            buffer = QtCore.QBuffer(ba)
            buffer.open(QtCore.QIODevice.WriteOnly)
            image.save(buffer, IMAGE_FORMAT, 75)

            query = QSqlQuery(db)
            query.prepare("""INSERT INTO photos (image)
                    VALUES (?)""")
            query.addBindValue(ba)
            query.exec_()
            img_id = query.lastInsertId()
            dest_record.setValue('image', img_id)

        dest_model.insertRecord(-1, dest_record)

    progressDlg.setLabelText("Saving...")
    dest_model.submitAll()

    progressDlg.setLabelText("Compact...")
    QSqlQuery("""UPDATE descriptions
SET
reverseimg = (select t2.id from descriptions t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.reverseimg = t1.id where t1.id <> t2.id and t3.id = descriptions.id)
WHERE descriptions.id in (select t3.id from descriptions t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.reverseimg = t1.id where t1.id <> t2.id)
""", db)
    QSqlQuery("""UPDATE descriptions
SET
obverseimg = (select t2.id from descriptions t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.obverseimg = t1.id where t1.id <> t2.id and t3.id = descriptions.id)
WHERE descriptions.id in (select t3.id from descriptions t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.obverseimg = t1.id where t1.id <> t2.id)
""", db)
    QSqlQuery("""UPDATE descriptions
SET
image = (select t2.id from descriptions t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.image = t1.id where t1.id <> t2.id and t3.id = descriptions.id)
WHERE descriptions.id in (select t3.id from descriptions t3 join (select id, image from photos group by image having count(*) > 1) t2 on t1.image = t2.image join photos t1 on t3.image = t1.id where t1.id <> t2.id)
""", db)

    QSqlQuery("""DELETE FROM photos
        WHERE id NOT IN (SELECT id FROM photos GROUP BY image)""", db)

    db.close()

    progressDlg.setLabelText("Vacuum...")
    db = QSqlDatabase.addDatabase('QSQLITE', 'mobile')
    db.setDatabaseName(params['file'])
    if not db.open():
        print(db.lastError().text())
        QMessageBox.critical(None, "Create mobile collection", "Can't open collection")
        return
    QSqlQuery("VACUUM", db)
    db.close()

    progressDlg.reset()



app = QApplication(sys.argv)

HOME_PATH = ''
__docDirs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)
if __docDirs:
    HOME_PATH = os.path.join(__docDirs[0], "OpenNumismat")

dialog = ExportDialog(None)
res = dialog.exec_()
if res == QDialog.Accepted:
    collection = Collection(None)
    collection.open(dialog.params['file'])
    model = collection.model()

    for density in ('MDPI', 'HDPI', 'XHDPI', 'XXHDPI'):
        params = {'filter': dialog.params['filter'], 'image': dialog.params['image'],
            'density': density,
            'file': collection.getCollectionName() + '_' + density.lower() + '.db',
            'fullimage': False}
        exportToMobile(model, params)

        print(density, 'done')
