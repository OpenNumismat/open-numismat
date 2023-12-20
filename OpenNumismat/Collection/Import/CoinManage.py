# -*- coding: utf-8 -*-

try:
    import winreg
except ImportError:
    pass

from PySide6 import QtCore, QtGui
from PySide6.QtSql import QSqlDatabase, QSqlQuery
from PySide6.QtWidgets import QFileDialog

import OpenNumismat
from OpenNumismat.Collection.Import import _Import, _DatabaseServerError


class ImportCoinManage(_Import):
    Columns = {
        'title': 'ShortDesc',
        'value': None,
        'unit': 'Denomination',
        'country': 'Country',
        'year': 'Year',
        'period': 'Type',
        'mint': 'Mints',
        'mintmark': 'Mint',
        'issuedate': None,
        'type': None,
        'series': None,
        'subjectshort': None,
        'status': None,
        'material': 'Composition',
        'fineness': None,
        'shape': None,
        'diameter': 'Diameter',
        'thickness': 'Thickness',
        'weight': 'Weight',
        'grade': 'Grade',
        'edge': 'Edge',
        'edgelabel': None,
        'obvrev': None,
        'quality': None,
        'mintage': 'Mintage',
        'dateemis': 'Type Years',
        'catalognum1': 'CatNumber1',
        'catalognum2': 'CatNumber2',
        'catalognum3': 'CatNumber3',
        'catalognum4': None,
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': None,
        'variety': 'Variety',
        'paydate': 'Date Purchased',
        'payprice': 'Amount Paid',
        'totalpayprice': 'Amount Paid',
        'saller': 'Dealer',
        'payplace': None,
        'payinfo': None,
        'saledate': 'Date Sold',
        'saleprice': 'Sold For',
        'totalsaleprice': 'Sold For',
        'buyer': 'Sold To',
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': None,
        'obversedesign': None,
        'obversedesigner': 'Designer',
        'reverseimg': None,
        'reversedesign': None,
        'reversedesigner': 'Designer',
        'edgeimg': None,
        'subject': None,
        'photo1': None,
        'photo2': None,
        'photo3': None,
        'photo4': None,
        'storage': 'Location',
        'features': None,
        'quantity': 'Quantity',
        'url': None,
        'barcode': 'BarCode',
        'grader': 'GradingServiceName',
    }

    def __init__(self, parent=None):
        super(ImportCoinManage, self).__init__(parent)

    @staticmethod
    def isAvailable():
        return 'QODBC' in QSqlDatabase.drivers()

    @staticmethod
    def defaultDir():
        # Search for default default dir in default location on disk
        dir_ = QtCore.QDir(OpenNumismat.HOME_PATH)
        dirNames = ["CoinManage/Data", "CoinManage UK/Data", "CoinManage Canada/Data"]
        for dirName in dirNames:
            if dir_.cd(dirName):
                break

        # Search for default dir in windows registry
        subkeys = ['CoinManage', 'CoinManage UK', 'CoinManage Canada']
        for key in [r'Software\Liberty Street Software\%s' % subkey for subkey in subkeys]:
            try:
                hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key)
                value = winreg.QueryValueEx(hkey, 'DataDirectory')[0]
                winreg.CloseKey(hkey)
                if dir_.cd(value):
                    break
            except (OSError, NameError):
                continue

        return dir_.absolutePath()

    def _connect(self, src):
        db = QSqlDatabase.addDatabase('QODBC', 'CoinManage')
        db.setDatabaseName("DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s" % src)
        if not db.open():
            db.setDatabaseName("DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s" % src)
            if not db.open():
                raise _DatabaseServerError(db.lastError().text())

        # Check images folder
        self.imgDir = QtCore.QDir(src)
        if not self.imgDir.cd('../../CoinImages'):
            directory = QFileDialog.getExistingDirectory(self.parent(),
                            self.tr("Select directory with images"),
                            OpenNumismat.HOME_PATH)
            if directory:
                self.imgDir = QtCore.QDir(directory)
            else:
                return False

        # Check predefined images folder
        self.defImgDir = QtCore.QDir(src)
        if not self.defImgDir.cd('../../Images'):
            directory = QFileDialog.getExistingDirectory(self.parent(),
                            self.tr("Select directory with pre-defined images"),
                            OpenNumismat.HOME_PATH)
            if directory:
                self.defImgDir = QtCore.QDir(directory)
            else:
                return False

        return db

    def _check(self, db):
        tables = [row.lower() for row in db.tables()]
        for requiredTables in ('coinattributes', 'cointypes', 'cm2001maincollection', 'collections', 'gradingservices'):
            if requiredTables not in tables:
                return False

        for table in tables:
            if table[:6] == 'cmval~':
                self.priceTable = table

        if not self.priceTable:
            # Prices not found
            return False

        return True

    def _getRows(self, db):
        priceFields = ['F-12', 'F-16', 'VF-20', 'VF-30', 'XF-40', 'XF-45',
                       'AU-50', 'AU-55', 'AU-57', 'AU-58', 'AU-59', 'MS-60',
                       'MS-61', 'MS-62', 'MS-63', 'MS-64', 'MS-65', 'MS-66',
                       'MS-67', 'MS-68', 'MS-69', 'MS-70', 'F', 'VF', 'EF',
                       'AU', 'Unc', 'BU']
        priceSql = []
        for field in priceFields:
            priceSql.append("[%s].[%s]" % (self.priceTable, field))

        sql = "SELECT cm2001maincollection.*, \
                coinattributes.*, cointypes.*, collections.CollectionName, gradingservices.GradingServiceName,\
                %s FROM ((((cm2001maincollection \
            LEFT JOIN coinattributes ON cm2001maincollection.[type id] = coinattributes.[type id]) \
            LEFT JOIN cointypes ON cm2001maincollection.[coin id] = cointypes.[coin id]) \
            LEFT JOIN gradingservices ON cm2001maincollection.GradingServiceId = gradingservices.GradingServiceId) \
            LEFT JOIN collections ON cm2001maincollection.CollectionId = collections.CollectionId2) \
            LEFT JOIN [%s] ON cm2001maincollection.[coin id] = [%s].[coin id]" % (','.join(priceSql), self.priceTable, self.priceTable)

        query = QSqlQuery(sql, db)
        records = []
        while query.next():
            records.append(query.record())

        return records

    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn:
                rawData = row.value(srcColumn)
                if isinstance(rawData, str):
                    if srcColumn == 'Mintage':
                        rawData = rawData.replace(',', '').replace('(', '').replace(')', '')
                    value = rawData.strip()
                else:
                    value = rawData

                record.setValue(dstColumn, value)

        if row.value('Sold To') or row.value('Date Sold') or row.value('CollectionName') == 'Sold Coins':
            record.setValue('status', 'sold')
        elif row.value('Sell'):
            record.setValue('status', 'sale')
        elif row.value('Want') or row.value('CollectionName') == 'Want List':
            record.setValue('status', 'wish')
        else:
            record.setValue('status', 'owned')

        if not record.value('title'):
            # Make a coin title (1673 Charles II Farthing - Brittania)
            year = record.value('year')
            period = record.value('period')
            unit = record.value('unit')
            variety = record.value('variety')
            mainTitle = ' '.join(filter(None, [year, period, unit]))
            title = ' - '.join(filter(None, [mainTitle, variety]))
            record.setValue('title', title)

        # Process features
        features = []
        additionalFields = {
            'Comments': None,
            'Error': self.tr("Error: %s"),
            'UDF1': self.tr("Field 1: %s"),
            'UDF2': self.tr("Field 2: %s"),
            'Defects': self.tr("Defect: %s"),
        }
        for column, string in additionalFields.items():
            value = row.value(column)
            if value:
                if string:
                    features.append(string % value)
                else:
                    features.append(value.strip())

        if features:
            record.setValue('features', '\n'.join(features))

        # Process prices
        fineFields = ['F-16', 'F-12', 'F']
        self.__processPrices(row, record, fineFields, 'price1')
        vfFields = ['VF-30', 'VF-20', 'VF']
        self.__processPrices(row, record, vfFields, 'price2')
        xfFields = ['XF-45', 'XF-40', 'AU-50', 'AU-55', 'AU-57', 'AU-58', 'AU-59', 'EF', 'AU']
        self.__processPrices(row, record, xfFields, 'price3')
        uncFields = ['MS-64', 'MS-63', 'MS-62', 'MS-61', 'MS-60', 'MS-65',
                     'MS-66', 'MS-67', 'MS-68', 'MS-69', 'MS-70', 'Unc', 'BU']
        self.__processPrices(row, record, uncFields, 'price4')

        # Processing images
        image = QtGui.QImage()
        rowId = row.value('ID')
        if image.load(self.imgDir.absoluteFilePath('Coin%d(1)' % rowId)):
            record.setValue('obverseimg', image)
        if image.load(self.imgDir.absoluteFilePath('Coin%d(2)' % rowId)):
            record.setValue('reverseimg', image)
        if image.load(self.imgDir.absoluteFilePath('Coin%d(3)' % rowId)):
            record.setValue('photo1', image)
        if image.load(self.imgDir.absoluteFilePath('Coin%d(4)' % rowId)):
            record.setValue('photo2', image)

        # Processing pre-defined images
        value = row.value('UseGraphic')
        country = row.value('Country')
        typeId = row.value('Type ID')
        if country:
            dir_ = QtCore.QDir(self.defImgDir)
            dir_.cd(country)
        if value and country:
            image = QtGui.QImage()
            if image.load(dir_.absoluteFilePath(value)):
                if record.isNull('obverseimg'):
                    record.setValue('obverseimg', image)
                else:
                    record.setValue('photo3', image)
        if typeId and country:
            image = QtGui.QImage()
            if image.load(dir_.absoluteFilePath(str(typeId))):
                if record.isNull('obverseimg'):
                    record.setValue('obverseimg', image)
                else:
                    record.setValue('photo4', image)

    def _close(self, connection):
        connection.close()
        QSqlDatabase.removeDatabase('CoinManage')

    def __processPrices(self, row, record, srcFields, dstField):
        for field in srcFields:
            value = row.value(field)
            if isinstance(value, float) and value > 0:
                record.setValue(dstField, value)
                break
