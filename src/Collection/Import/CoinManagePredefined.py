# -*- coding: utf-8 -*-

import datetime, decimal

try:
    import pyodbc
except ImportError:
    print('pyodbc module missed. Importing not available')

from PyQt4 import QtCore, QtGui

from Collection.Import import _Import, _DatabaseServerError

class ImportCoinManagePredefined(_Import):
    Columns = {
        'title': None,
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
        'grade': None,
        'edge': 'Edge',
        'edgelabel': None,
        'obvrev': None,
        'quality': None,
        'mintage': 'Mintage',
        'dateemis': 'Type Years',
        'catalognum1': None,
        'catalognum2': None,
        'catalognum3': None,
        'catalognum4': None,
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': None,
        'variety': 'Variety',
        'paydate': None,
        'payprice': None,
        'totalpayprice': None,
        'saller': None,
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
        'storage': None,
        'features': None
    }

    def __init__(self, parent=None):
        super(ImportCoinManagePredefined, self).__init__(parent)
    
    def _connect(self, src):
        try:
            self.cnxn = pyodbc.connect(driver='{Microsoft Access Driver (*.mdb)}', DBQ=src)
        except pyodbc.Error as error:
            raise _DatabaseServerError(error.__str__())
        
        # Check images folder
        self.imgDir = QtCore.QDir(src)
        if not self.imgDir.cd('../../Images'):
            directory = QtGui.QFileDialog.getExistingDirectory(self.parent(),
                            self.tr("Select directory with pre-defined images"),
                            QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))
            if directory:
                self.imgDir = QtCore.QDir(directory)
            else:
                return False
        
        return self.cnxn.cursor()
    
    def _check(self, cursor):
        self.priceTable = None
        tables = [row.table_name.lower() for row in cursor.tables()]
        
        for requiredTables in ['coinattributes', 'cointypes']:
            if requiredTables not in tables:
                return False
        
        for table in tables:
            if table[:6] == 'cmval~':
                self.priceTable = table
        
        if not self.priceTable:
            # Prices not found
            return False
        
        return True
    
    def _getRows(self, cursor):
        priceFields = ['F-12', 'F-16', 'VF-20', 'VF-30', 'XF-40', 'XF-45',
                       'AU-50', 'AU-55', 'AU-57', 'AU-58', 'AU-59', 'MS-60',
                       'MS-61', 'MS-62', 'MS-63', 'MS-64', 'MS-65', 'MS-66',
                       'MS-67', 'MS-68', 'MS-69', 'MS-70', 'F', 'VF', 'EF',
                       'AU', 'Unc', 'BU']
        priceSql = []
        for field in priceFields:
            priceSql.append("[%s].[%s]" % (self.priceTable, field))            
        
        sql = "SELECT cointypes.*, \
                coinattributes.*, %s FROM (cointypes \
            LEFT JOIN coinattributes ON cointypes.[type id] = coinattributes.[type id]) \
            LEFT JOIN [%s] ON cointypes.[coin id] = [%s].[coin id]" % (','.join(priceSql), self.priceTable, self.priceTable)
        
        cursor.execute(sql)
        return cursor.fetchall()
    
    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and hasattr(row, srcColumn):
                rawData = getattr(row, srcColumn)
                if isinstance(rawData, bytearray):
                    value = QtCore.QByteArray(rawData)
                elif isinstance(rawData, str):
                    if srcColumn == 'Mintage':
                        rawData = rawData.replace(',', '').replace('(', '').replace(')', '')
                    value = rawData.strip()
                elif isinstance(rawData, datetime.date):
                    value = QtCore.QDate.fromString(rawData.isoformat(), QtCore.Qt.ISODate)
                else:
                    value = rawData
                
                record.setValue(dstColumn, value)
        
        # Process Status field
        record.setValue('status', 'demo')
        
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
        
        if hasattr(row, 'UseGraphic') and hasattr(row, 'Country') and hasattr(row, 'Type ID'):
            value = getattr(row, 'UseGraphic')
            country = getattr(row, 'Country')
            typeId = getattr(row, 'Type ID')
            if value and country:
                dir_ = QtCore.QDir(self.imgDir)
                dir_.cd(country)
                image = QtGui.QImage()
                if image.load(dir_.absoluteFilePath(value)):
                    record.setValue('obverseimg', image)
            if typeId and country:
                dir_ = QtCore.QDir(self.imgDir)
                dir_.cd(country)
                image = QtGui.QImage()
                if image.load(dir_.absoluteFilePath(str(typeId))):
                    if record.isNull('obverseimg'):
                        record.setValue('obverseimg', image)
                    else:
                        record.setValue('photo1', image)
        
        # Make a coin title (1673 Charles II Farthing - Brittania)
        year = record.value('year')
        period = record.value('period')
        unit = record.value('unit')
        variety = record.value('variety')
        mainTitle = ' '.join(filter(None, [year, period, unit]))
        title = ' - '.join(filter(None, [mainTitle, variety]))
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
