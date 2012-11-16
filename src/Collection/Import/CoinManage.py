# -*- coding: utf-8 -*-

import datetime, decimal

try:
    import winreg
    import pyodbc
except ImportError:
    print('pyodbc or winreg module missed. Importing not available')

from PyQt4 import QtCore, QtGui

from Collection.Import import _Import, _DatabaseServerError

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
    }

    def __init__(self, parent=None):
        super(ImportCoinManage, self).__init__(parent)
    
    @staticmethod
    def defaultDir():
        # Search for default default dir in default location on disk
        dir_ = QtCore.QDir(QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))
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
            except WindowsError:
                continue
        
        return dir_.absolutePath()
    
    def _connect(self, src):
        try:
            self.cnxn = pyodbc.connect(driver='{Microsoft Access Driver (*.mdb)}', DBQ=src)
        except pyodbc.Error as error:
            raise _DatabaseServerError(error.__str__())
        
        # Check images folder
        self.imgDir = QtCore.QDir(src)
        if not self.imgDir.cd('../../CoinImages'):
            directory = QtGui.QFileDialog.getExistingDirectory(self.parent(),
                            self.tr("Select directory with images"),
                            QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))
            if directory:
                self.imgDir = QtCore.QDir(directory)
            else:
                return False
        
        return self.cnxn.cursor()
    
    def _check(self, cursor):
        tables = [row.table_name.lower() for row in cursor.tables()]
        for requiredTables in ['coinattributes', 'cointypes', 'cm2001maincollection']:
            if requiredTables not in tables:
                return False
        
        return True
    
    def _getRows(self, cursor):
        cursor.execute("""
            SELECT cm2001maincollection.*,
                coinattributes.*, cointypes.* FROM (cm2001maincollection
            LEFT JOIN coinattributes ON cm2001maincollection.[type id] = coinattributes.[type id])
            LEFT JOIN cointypes ON cm2001maincollection.[coin id] = cointypes.[coin id]
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
                elif isinstance(rawData, decimal.Decimal):
                    value = float(rawData)
                else:
                    value = rawData
                
                record.setValue(dstColumn, value)
            
            if dstColumn == 'status':
                record.setValue(dstColumn, 'owned')
                if getattr(row, 'Sold To') or getattr(row, 'Date Sold'):
                    record.setValue(dstColumn, 'sold')
                elif getattr(row, 'Sell'):
                    record.setValue(dstColumn, 'sale')
                elif getattr(row, 'Want'):
                    record.setValue(dstColumn, 'wish')
        
            if dstColumn == 'features':
                features = []
                additionalFields = {
                    'Comments': None,
                    'Error': self.tr("Error: %s"),
                    'UDF1': self.tr("Field 1: %s"),
                    'UDF2': self.tr("Field 2: %s"),
                    'Defects': self.tr("Defect: %s"),
                    'BarCode': self.tr("BarCode: %s"),
                }
                for column, string in additionalFields.items():
                    value = getattr(row, column)
                    if value:
                        if string:
                            features.append(string % value)
                        else:
                            features.append(value.strip())
                
                if features:
                    record.setValue(dstColumn, '\n'.join(features))
        
        if not record.value('title'):
            # Make a coin title (1673 Charles II Farthing - Brittania)
            year = record.value('year')
            period = record.value('period')
            unit = record.value('unit')
            variety = record.value('variety')
            mainTitle = ' '.join(filter(None, [year, period, unit]))
            title = ' - '.join(filter(None, [mainTitle, variety]))
            record.setValue('title', title)
        
        # Processing images
        image = QtGui.QImage()
        rowId = getattr(row, 'ID')
        if image.load(self.imgDir.absoluteFilePath('Coin%d(1)' % rowId)):
            record.setValue('obverseimg', image)
        if image.load(self.imgDir.absoluteFilePath('Coin%d(2)' % rowId)):
            record.setValue('reverseimg', image)
        if image.load(self.imgDir.absoluteFilePath('Coin%d(3)' % rowId)):
            record.setValue('photo1', image)
        if image.load(self.imgDir.absoluteFilePath('Coin%d(4)' % rowId)):
            record.setValue('photo2', image)
        # TODO: Add pre-defined image
    
    def _close(self, connection):
        self.cnxn.close()
    
    def __getColumns(self, cursor):
        columns = [row.column_name for row in cursor.columns('coins')]
        return columns
