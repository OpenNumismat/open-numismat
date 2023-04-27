from PySide6 import QtCore
from PySide6.QtWidgets import QApplication
from PySide6.QtSql import QSqlQuery
from PySide6.QtCore import QSettings

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Tools import Gui


class Updater(QtCore.QObject):
    def __init__(self, collection, parent=None):
        super().__init__(parent)

        self.collection = collection
        self.currentVersion = self.collection.settings['Version']

    def check(self):
        if self.currentVersion < self.collection.settings.Default['Version']:
            return True

        return False

    def update(self):
        if self.__begin():
            if self.currentVersion < 2:
                updater = UpdaterTo2(self.collection)
                updater.update()
            if self.currentVersion < 3:
                updater = UpdaterTo3(self.collection)
                updater.update()
            if self.currentVersion < 4:
                updater = UpdaterTo4(self.collection)
                updater.update()
            if self.currentVersion < 5:
                updater = UpdaterTo5(self.collection)
                updater.update()
            if self.currentVersion < 6:
                updater = UpdaterTo6(self.collection)
                updater.update()
            if self.currentVersion < 7:
                updater = UpdaterTo7(self.collection)
                updater.update()
            if self.currentVersion < 8:
                updater = UpdaterTo8(self.collection)
                updater.update()
            if self.currentVersion < 9:
                updater = UpdaterTo9(self.collection)
                updater.update()

            self.__finalize()

            return True

        return False

    def __begin(self):
        return self.collection.backup()

    def __finalize(self):
        # TODO: Move vacuum here
        pass


class _Updater(QtCore.QObject):
    def __init__(self, collection, parent=None):
        super().__init__(parent)

        self.collection = collection
        self.db = collection.db

        self.totalCount = self.getTotalCount()

        self.progressDlg = Gui.ProgressDialog(
                    QApplication.translate('_Updater', "Updating records"),
                    None, self.totalCount,
                    collection.parent())

    def getTotalCount(self):
        raise NotImplementedError

    def update(self):
        pass

    def _begin(self):
        pass

    def _updateRecord(self):
        self.progressDlg.step()

    def _finish(self):
        self.progressDlg.reset()


class UpdaterTo2(_Updater):
    def getTotalCount(self):
        sql = "SELECT count(*) FROM coins"
        query = QSqlQuery(sql, self.db)
        query.first()
        return query.record().value(0)

    def update(self):
        self._begin()

        self.db.transaction()

        fields = ['quantity', 'url', 'barcode']
        for field in fields:
            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = True
            query = QSqlQuery(self.db)
            query.prepare("""INSERT INTO fields (id, title, enabled)
                VALUES (?, ?, ?)""")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(fieldDesc.enabled))
            query.exec_()

            self.collection.fields.userFields.append(fieldDesc)

        sql = """ALTER TABLE coins RENAME TO tmp_coins"""
        QSqlQuery(sql, self.db)

        self.collection.createCoinsTable()

        query = QSqlQuery("SELECT * FROM tmp_coins", self.db)
        while query.next():
            self._updateRecord()

            record = query.record()

            imgIds = {}
            fields = ['obverseimg', 'reverseimg', 'edgeimg',
                      'photo1', 'photo2', 'photo3', 'photo4']
            for field in fields:
                if not record.isNull(field):
                    image_query = QSqlQuery(self.db)
                    image_query.prepare("""INSERT INTO images (title, image)
                            VALUES (?, ?)""")
                    fieldDesc = getattr(self.collection.fields, field)
                    image_query.addBindValue(fieldDesc.title)
                    image_query.addBindValue(record.value(field))
                    image_query.exec_()
                    imgIds[field] = image_query.lastInsertId()
                else:
                    imgIds[field] = None

            coin_query = QSqlQuery(self.db)
            coin_query.prepare("""INSERT INTO coins (title, value, unit,
                        country, year, period, mint, mintmark, issuedate, type,
                        series, subjectshort, status, material, fineness,
                        shape, diameter, thickness, weight, grade, edge,
                        edgelabel, obvrev, quality, mintage, dateemis,
                        catalognum1, catalognum2, catalognum3, catalognum4,
                        rarity, price1, price2, price3, price4, variety,
                        obversevar, reversevar, edgevar, paydate, payprice,
                        totalpayprice, saller, payplace, payinfo, saledate,
                        saleprice, totalsaleprice, buyer, saleplace, saleinfo,
                        note, image, obverseimg, obversedesign,
                        obversedesigner, reverseimg, reversedesign,
                        reversedesigner, edgeimg, subject, photo1, photo2,
                        photo3, photo4, defect, storage, features, createdat,
                        updatedat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""")
            coin_query.addBindValue(record.value('title'))
            coin_query.addBindValue(record.value('value'))
            coin_query.addBindValue(record.value('unit'))
            coin_query.addBindValue(record.value('country'))
            coin_query.addBindValue(record.value('year'))
            coin_query.addBindValue(record.value('period'))
            coin_query.addBindValue(record.value('mint'))
            coin_query.addBindValue(record.value('mintmark'))
            coin_query.addBindValue(record.value('issuedate'))
            coin_query.addBindValue(record.value('type'))
            coin_query.addBindValue(record.value('series'))
            coin_query.addBindValue(record.value('subjectshort'))
            coin_query.addBindValue(record.value('status'))
            coin_query.addBindValue(record.value('metal'))
            coin_query.addBindValue(record.value('fineness'))
            coin_query.addBindValue(record.value('form'))
            coin_query.addBindValue(record.value('diameter'))
            coin_query.addBindValue(record.value('thick'))
            coin_query.addBindValue(record.value('mass'))
            coin_query.addBindValue(record.value('grade'))
            coin_query.addBindValue(record.value('edge'))
            coin_query.addBindValue(record.value('edgelabel'))
            coin_query.addBindValue(record.value('obvrev'))
            coin_query.addBindValue(record.value('quality'))
            coin_query.addBindValue(record.value('mintage'))
            coin_query.addBindValue(record.value('dateemis'))
            coin_query.addBindValue(record.value('catalognum1'))
            coin_query.addBindValue(record.value('catalognum2'))
            coin_query.addBindValue(record.value('catalognum3'))
            coin_query.addBindValue(record.value('catalognum4'))
            coin_query.addBindValue(record.value('rarity'))
            coin_query.addBindValue(record.value('price1'))
            coin_query.addBindValue(record.value('price2'))
            coin_query.addBindValue(record.value('price3'))
            coin_query.addBindValue(record.value('price4'))
            coin_query.addBindValue(record.value('variety'))
            coin_query.addBindValue(record.value('obversevar'))
            coin_query.addBindValue(record.value('reversevar'))
            coin_query.addBindValue(record.value('edgevar'))
            coin_query.addBindValue(record.value('paydate'))
            coin_query.addBindValue(record.value('payprice'))
            coin_query.addBindValue(record.value('totalpayprice'))
            coin_query.addBindValue(record.value('saller'))
            coin_query.addBindValue(record.value('payplace'))
            coin_query.addBindValue(record.value('payinfo'))
            coin_query.addBindValue(record.value('saledate'))
            coin_query.addBindValue(record.value('saleprice'))
            coin_query.addBindValue(record.value('totalsaleprice'))
            coin_query.addBindValue(record.value('buyer'))
            coin_query.addBindValue(record.value('saleplace'))
            coin_query.addBindValue(record.value('saleinfo'))
            coin_query.addBindValue(record.value('note'))
            coin_query.addBindValue(record.value('image'))
            coin_query.addBindValue(imgIds['obverseimg'])
            coin_query.addBindValue(record.value('obversedesign'))
            coin_query.addBindValue(record.value('obversedesigner'))
            coin_query.addBindValue(imgIds['reverseimg'])
            coin_query.addBindValue(record.value('reversedesign'))
            coin_query.addBindValue(record.value('reversedesigner'))
            coin_query.addBindValue(imgIds['edgeimg'])
            coin_query.addBindValue(record.value('subject'))
            coin_query.addBindValue(imgIds['photo1'])
            coin_query.addBindValue(imgIds['photo2'])
            coin_query.addBindValue(imgIds['photo3'])
            coin_query.addBindValue(imgIds['photo4'])
            coin_query.addBindValue(record.value('defect'))
            coin_query.addBindValue(record.value('storage'))
            coin_query.addBindValue(record.value('features'))
            coin_query.addBindValue(record.value('createdat'))
            coin_query.addBindValue(record.value('updatedat'))
            if not coin_query.exec_():
                print(coin_query.lastError().text())

        self.progressDlg.setLabelText(self.tr("Saving..."))

        sql = """DROP TABLE tmp_coins"""
        QSqlQuery(sql, self.db)

        self.collection.settings['Version'] = 2
        self.collection.settings.save()

        query = QSqlQuery(self.db)
        query.prepare("""INSERT INTO settings (title, value) VALUES (?, ?)""")
        query.addBindValue('Password')
        query.addBindValue(self.collection.settings['Password'])
        query.exec_()

        self.db.commit()

        self.progressDlg.setLabelText(self.tr("Vacuum..."))

        self.collection.vacuum()

        self._finish()


class UpdaterTo3(_Updater):
    def getTotalCount(self):
        sql = "SELECT count(*) FROM coins"
        query = QSqlQuery(sql, self.db)
        query.first()
        return query.record().value(0)

    def update(self):
        self._begin()

        self.db.transaction()

        sql = "ALTER TABLE lists ADD COLUMN sortorder INTEGER"
        QSqlQuery(sql, self.db)

        sql = "ALTER TABLE filters ADD COLUMN revert INTEGER"
        QSqlQuery(sql, self.db)

        query = QSqlQuery(self.db)
        query.prepare("""INSERT INTO settings (title, value) VALUES (?, ?)""")
        query.addBindValue('Type')
        query.addBindValue(self.collection.settings['Type'])
        query.exec_()

        sql = """ALTER TABLE images RENAME TO photos"""
        QSqlQuery(sql, self.db)

        sql = """CREATE TABLE images (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    image BLOB)"""
        QSqlQuery(sql, self.db)

        query = QSqlQuery("SELECT id, image FROM coins", self.db)
        while query.next():
            self._updateRecord()

            record = query.record()

            if not record.isNull('image'):
                insert_query = QSqlQuery(self.db)
                insert_query.prepare("INSERT INTO images (image) VALUES (?)")
                insert_query.addBindValue(record.value('image'))
                insert_query.exec_()
                img_id = insert_query.lastInsertId()
            else:
                img_id = None

            update_query = QSqlQuery(self.db)
            update_query.prepare("UPDATE coins SET image=? WHERE id=?")
            update_query.addBindValue(img_id)
            update_query.addBindValue(record.value('id'))
            update_query.exec_()

        self.collection.settings['Version'] = 3
        self.collection.settings.save()

        self.db.commit()

        self._finish()


class UpdaterTo4(_Updater):
    def __init__(self, collection):
        super().__init__(collection)
        self.progressDlg.setMinimumDuration(0)

    def getTotalCount(self):
        return 2

    def update(self):
        self._begin()

        self.db.transaction()

        fields = ['ruler', 'region']
        for field in fields:
            self._updateRecord()

            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = False
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO fields (id, title, enabled)"
                          " VALUES (?, ?, ?)")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(fieldDesc.enabled))
            query.exec_()

            sql = "ALTER TABLE coins ADD COLUMN %s TEXT" % field
            QSqlQuery(sql, self.db)

            self.collection.fields.userFields.append(fieldDesc)

        self.progressDlg.setLabelText(self.tr("Saving..."))

        sql = "UPDATE photos SET title=NULL"
        QSqlQuery(sql, self.db)

        self.collection.settings['Version'] = 4
        self.collection.settings.save()

        self.db.commit()

        self._finish()


class UpdaterTo5(_Updater):

    def __init__(self, collection):
        super().__init__(collection)
        self.progressDlg.setMinimumDuration(0)

    def getTotalCount(self):
        return 2

    def update(self):
        self._begin()

        self.db.transaction()

        fields = ('obverseengraver', 'reverseengraver', 'obversecolor',
                  'reversecolor', 'varietydesc', 'varietyimg', 'format',
                  'condition')
        for field in fields:
            self._updateRecord()

            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = False
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO fields (id, title, enabled)"
                          " VALUES (?, ?, ?)")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(fieldDesc.enabled))
            query.exec_()

            sql = "ALTER TABLE coins ADD COLUMN %s %s" % (field, Type.toSql(fieldDesc.type))
            QSqlQuery(sql, self.db)

            self.collection.fields.userFields.append(fieldDesc)

        if 'statistics' in self.db.tables():
            sql = "ALTER TABLE statistics ADD COLUMN color INTEGER"
            QSqlQuery(sql, self.db)

        self.progressDlg.setLabelText(self.tr("Saving..."))

        settings = QSettings()
        for key in ('free_numeric', 'convert_fraction'):
            default = self.collection.settings.Default[key]
            value = settings.value('mainwindow/' + key, default, type=bool)
            self.collection.settings[key] = value
        value = settings.value('mainwindow/ImageSideLen', 1024, type=int)
        self.collection.settings['ImageSideLen'] = value

        self.collection.settings['Version'] = 5
        self.collection.settings.save()

        self.db.commit()

        self._finish()


class UpdaterTo6(_Updater):

    def __init__(self, collection):
        super().__init__(collection)
        self.progressDlg.setMinimumDuration(0)

    def getTotalCount(self):
        return 3

    def update(self):
        self._begin()

        self.db.transaction()

        fields = ('category', 'sort_id')
        for field in fields:
            self._updateRecord()

            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = False
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO fields (id, title, enabled)"
                          " VALUES (?, ?, ?)")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(False))
            query.exec_()

            sql = "ALTER TABLE coins ADD COLUMN %s %s" % (field, Type.toSql(fieldDesc.type))
            QSqlQuery(sql, self.db)

            self.collection.fields.userFields.append(fieldDesc)

        self._updateRecord()

        sql = "UPDATE coins SET sort_id = id"
        QSqlQuery(sql, self.db)

        self.collection.settings['Version'] = 6
        self.collection.settings.save()

        self.db.commit()

        self._finish()


class UpdaterTo7(_Updater):

    def __init__(self, collection):
        super().__init__(collection)
        self.progressDlg.setMinimumDuration(0)

    def getTotalCount(self):
        return 8

    def update(self):
        self._begin()

        self.db.transaction()

        fields = ('emitent', 'signaturetype', 'signature', 'signatureimg',
                  'address', 'latitude', 'longitude')
        for field in fields:
            self._updateRecord()

            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = False
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO fields (id, title, enabled)"
                          " VALUES (?, ?, ?)")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(False))
            query.exec_()

            sql = "ALTER TABLE coins ADD COLUMN %s %s" % (field, Type.toSql(fieldDesc.type))
            QSqlQuery(sql, self.db)

            self.collection.fields.userFields.append(fieldDesc)

        self._updateRecord()

        self.collection.settings['Version'] = 7
        self.collection.settings.save()

        self.db.commit()

        self._finish()


class UpdaterTo8(_Updater):

    def __init__(self, collection):
        super().__init__(collection)
        self.progressDlg.setMinimumDuration(0)

    def getTotalCount(self):
        return 6

    def update(self):
        self._begin()

        self.db.transaction()

        fields = ('photo5', 'photo6', 'grader', 'seat', 'native_year')
        for field in fields:
            self._updateRecord()

            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = False
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO fields (id, title, enabled)"
                          " VALUES (?, ?, ?)")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(False))
            query.exec_()

            sql = "ALTER TABLE coins ADD COLUMN %s %s" % (field, Type.toSql(fieldDesc.type))
            QSqlQuery(sql, self.db)

            self.collection.fields.userFields.append(fieldDesc)

        self._updateRecord()

        self.collection.settings['Version'] = 8
        self.collection.settings.save()

        self.db.commit()

        self._finish()


class UpdaterTo9(_Updater):

    def __init__(self, collection):
        super().__init__(collection)
        self.progressDlg.setMinimumDuration(0)

    def getTotalCount(self):
        return 13 + 2

    def update(self):
        self._begin()

        self.db.transaction()

        fields = (
            'composition',
            'material2',
            'width',
            'height',
            'technique',
            'modification',
            'axis',
            'real_weight',
            'real_diameter',
            'rating',
            'buying_invoice',
            'sale_invoice',
        )
        for field in fields:
            self._updateRecord()

            fieldDesc = getattr(self.collection.fields, field)
            fieldDesc.enabled = False
            query = QSqlQuery(self.db)
            query.prepare("INSERT INTO fields (id, title, enabled)"
                          " VALUES (?, ?, ?)")
            query.addBindValue(fieldDesc.id)
            query.addBindValue(fieldDesc.title)
            query.addBindValue(int(False))
            query.exec_()

            sql = "ALTER TABLE coins ADD COLUMN %s %s" % (field, Type.toSql(fieldDesc.type))
            QSqlQuery(sql, self.db)

            self.collection.fields.userFields.append(fieldDesc)

        self._updateRecord()

        sql = """CREATE TABLE tags (
                    id INTEGER NOT NULL PRIMARY KEY,
                    tag TEXT,
                    parent_id INTEGER)"""
        QSqlQuery(sql, self.db)

        self._updateRecord()

        sql = """CREATE TABLE coins_tags (
                    coin_id INTEGER,
                    tag_id INTEGER)"""
        QSqlQuery(sql, self.db)

        self.collection.settings['Version'] = 9
        self.collection.settings.save()

        self.db.commit()

        self._finish()


def updateCollection(collection):
    updater = Updater(collection, collection.parent())
    if updater.check():
        return updater.update()

    return True
