# -*- coding: utf-8 -*-

import datetime

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
        'metal': 'Composition',
        'fineness': None,
        'form': None,
        'diameter': 'Diameter',
        'thick': 'Thickness',
        'mass': 'Weight',
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
        tables = [row.table_name.lower() for row in cursor.tables()]
        for requiredTables in ['coinattributes', 'cointypes']:
            if requiredTables not in tables:
                return False
        
        return True
    
    def _getRows(self, cursor):
        cursor.execute("""
            SELECT cointypes.*,
                coinattributes.* FROM cointypes
            LEFT JOIN coinattributes ON cointypes.[type id] = coinattributes.[type id]
        """)
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
