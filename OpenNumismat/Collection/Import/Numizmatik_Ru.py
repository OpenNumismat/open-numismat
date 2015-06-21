# -*- coding: utf-8 -*-

import datetime
import decimal

available = True

try:
    import pyodbc
except ImportError:
    print('pyodbc module missed. Importing from Numizmatik_Ru not available')
    available = False

from PyQt5 import QtCore, QtGui

from OpenNumismat.Collection.Import import _Import, _DatabaseServerError


class ImportNumizmatik_Ru(_Import):
    Columns = {
        'title': None,
        'value': None,
        'unit': None,
        'country': None,
        'year': 'MONY_YEAR',
        'period': None,
        'mint': None,
        'mintmark': None,
        'issuedate': None,
        'type': None,
        'series': None,
        'subjectshort': None,
        'status': None,
        'material': None,
        'fineness': None,
        'shape': None,
        'diameter': None,
        'thickness': None,
        'weight': None,
        'grade': None,
        'edge': None,
        'edgelabel': None,
        'obvrev': None,
        'quality': None,
        'mintage': None,
        'dateemis': None,
        'catalognum1': None,
        'catalognum2': None,
        'catalognum3': None,
        'catalognum4': None,
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': None,
        'variety': None,
        'paydate': None,
        'payprice': None,
        'totalpayprice': None,
        'seller': None,
        'payplace': None,
        'payinfo': None,
        'saledate': None,
        'saleprice': None,
        'totalsaleprice': None,
        'buyer': None,
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': None,
        'obversedesign': None,
        'obversedesigner': None,
        'reverseimg': None,
        'reversedesign': None,
        'reversedesigner': None,
        'edgeimg': None,
        'subject': None,
        'photo1': None,
        'photo2': None,
        'photo3': None,
        'photo4': None,
        'storage': None,
        'features': None,
        'storage': None
    }

    def __init__(self, parent=None):
        super(ImportNumizmatik_Ru, self).__init__(parent)

    @staticmethod
    def isAvailable():
        return available

    @staticmethod
    def defaultDir():
        dir_ = QtCore.QDir(_Import.defaultDir())
        store_dir = QtCore.QDir.home()
        if store_dir.cd('AppData/Local/VirtualStore/Program Files (x86)/Numizmatik_Ru'):
            dir_ = store_dir
        elif store_dir.cd('AppData/Local/VirtualStore/Program Files/Numizmatik_Ru'):
            dir_ = store_dir
        else:
            dirNames = ["C:/Program Files/Numizmatik_Ru",
                        "C:/Program Files (x86)/Numizmatik_Ru"]
            for dirName in dirNames:
                if dir_.cd(dirName):
                    break

        return dir_.absolutePath()

    def _connect(self, src):
        try:
            self.cnxn = pyodbc.connect(driver='{Microsoft Access Driver (*.mdb)}', DBQ=src)
        except pyodbc.Error as error:
            raise _DatabaseServerError(error.__str__())

        # Check images folder
        self.imgDir = QtCore.QDir(src)
        if not self.imgDir.cd('../Images'):
            return False

        return self.cnxn.cursor()

    def _check(self, cursor):
        tables = [row.table_name.lower() for row in cursor.tables()]

        for requiredTables in ['elements', 'mony']:
            if requiredTables not in tables:
                return False

        return True

    def _getRows(self, cursor):
        sql = "SELECT * FROM mony WHERE mony_loc_id<>0"

        cursor.execute(sql)
        return cursor.fetchall()

    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and hasattr(row, srcColumn):
                rawData = getattr(row, srcColumn)
                if isinstance(rawData, bytearray):
                    value = QtCore.QByteArray(rawData)
                elif isinstance(rawData, str):
                    value = rawData.strip()
                elif isinstance(rawData, datetime.date):
                    value = QtCore.QDate.fromString(rawData.isoformat(), QtCore.Qt.ISODate)
                else:
                    value = rawData

                record.setValue(dstColumn, value)

        cursor = self.cnxn.cursor()

        srcColumn = 'MONY_PARENT_SER_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_ser_id=%d AND el_cat_id=2" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('country', _row[0])

        srcColumn = 'MONY_PARENT_LOC_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_loc_id=%d AND el_cat_id=2" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('country', _row[0])

        srcColumn = 'MONY_METAL_SER_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_ser_id=%d AND el_cat_id=10" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('material', _row[0])

        srcColumn = 'MONY_METAL_LOC_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_loc_id=%d AND el_cat_id=10" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('material', _row[0])

        srcColumn = 'MONY_QUALITY_SER_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_ser_id=%d AND el_cat_id=7" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('quality', _row[0])

        srcColumn = 'MONY_QUALITY_LOC_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_loc_id=%d AND el_cat_id=7" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('quality', _row[0])

        srcColumn = 'MONY_MONYGROUP_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_loc_id=%d AND el_cat_id=4" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('mint', _row[0])

        srcColumn = 'MONY_SALER_ID'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn) or 0
            id_ = int(rawData)
            if id_:
                sql = "SELECT el_name FROM elements \
                        WHERE el_loc_id=%d AND el_cat_id=9" % id_
                cursor.execute(sql)

                _row = cursor.fetchone()
                if _row:
                    record.setValue('seller', _row[0])

        # Process Value and Unit fields
        srcColumn = 'MONY_NAME'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn)
            parts = rawData.strip().split(' ', 1)
            if len(parts) == 2:
                record.setValue('value', parts[0])
            record.setValue('unit', parts[-1])

        # Process content
        srcColumn = 'MONY_CONTENT'
        if hasattr(row, srcColumn):
            rawData = getattr(row, srcColumn)
            rawData = rawData.replace('""', "'")

            if "image=" in rawData:
                start = rawData.find("image=") + 7
                end = rawData.find('"', start)
                image_name = rawData[start:end]
                if image_name:
                    image = QtGui.QImage()
                    if image.load(self.imgDir.absoluteFilePath(image_name)):
                        record.setValue('obverseimg', image)

            if "diameter=" in rawData:
                start = rawData.find("diameter=") + 10
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value:
                    value.replace(',', '.')
                    record.setValue('diameter', value)

            if "weight=" in rawData:
                start = rawData.find("weight=") + 8
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value:
                    value.replace(',', '.')
                    record.setValue('weight', value)

            if "height=" in rawData:
                start = rawData.find("height=") + 8
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value:
                    value.replace(',', '.')
                    record.setValue('thickness', value)

            if "gurt=" in rawData:
                start = rawData.find("gurt=") + 6
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    record.setValue('edgelabel', value)

            if "content=" in rawData:
                start = rawData.find("content=") + 9
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    record.setValue('subjectshort', value)

            if "averce legend=" in rawData:
                start = rawData.find("averce legend=") + 15
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    record.setValue('obversedesign', value)

            if "reverce legend=" in rawData:
                start = rawData.find("reverce legend=") + 16
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    record.setValue('reversedesign', value)

            if "km=" in rawData:
                start = rawData.find("km=") + 4
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    record.setValue('catalognum1', value)

            if "placenumb=" in rawData:
                start = rawData.find("placenumb=") + 11
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    record.setValue('storage', value)

            if "costbuy=" in rawData:
                start = rawData.find("costbuy=") + 9
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    value.replace(',', '.')
                    record.setValue('payprice', value)
                    record.setValue('totalpayprice', value)

            if "costnumizmat=" in rawData:
                start = rawData.find("costnumizmat=") + 14
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    value.replace(',', '.')
                    record.setValue('price1', value)

            if "datebuy=" in rawData:
                start = rawData.find("datebuy=") + 9
                end = rawData.find('"', start)
                value = rawData[start:end]
                if value and value != 'undefined':
                    time = QtCore.QDateTime()
                    time.setTime_t(int(value))
                    record.setValue('paydate', time.date())

        # Process Status field
        record.setValue('status', 'owned')

        # Make a coin title
        unit = record.value('unit')
        value = record.value('value')
        country = record.value('country')
        mainTitle = ' '.join(filter(None, [unit, value]))
        title = ', '.join(filter(None, [mainTitle, country]))
        record.setValue('title', title)

    def _close(self, connection):
        self.cnxn.close()

    def __getColumns(self, cursor):
        columns = [row.column_name for row in cursor.columns('coins')]
        return columns

    def __processPrices(self, row, record, srcFields, dstField):
        for field in srcFields:
            if hasattr(row, field):
                rawData = getattr(row, field)
                if isinstance(rawData, decimal.Decimal):
                    value = float(rawData)
                    if value > 0:
                        record.setValue(dstField, value)
                        break
