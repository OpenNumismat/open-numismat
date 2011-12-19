# -*- coding: utf-8 -*-

import datetime, decimal

try:
    import pyodbc
except ImportError:
    print('pyodbc module missed. Importing not available')

from PyQt4 import QtCore

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
        'metal': 'Composition',
        'fineness': None,
        'form': None,
        'diameter': 'Diameter',
        'thick': 'Thickness',
        'mass': 'Weight',
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
        'obverseimg': 'Picture',
        'obversedesign': None,
        'obversedesigner': 'Designer',
        'reverseimg': None,
        'reversedesign': None,
        'reversedesigner': 'Designer',
        'edgeimg': None,
        'subject': None,
        'photo1': 'Bitmap',
        'photo2': None,
        'photo3': None,
        'photo4': None,
        'storage': 'Location',
        'features': 'Comments',
    }

    def __init__(self, parent=None):
        super(ImportCoinManage, self).__init__(parent)
    
    def _connect(self, src):
        try:
            self.cnxn = pyodbc.connect(driver='{Microsoft Access Driver (*.mdb)}', DBQ=src)
        except pyodbc.Error as error:
            raise _DatabaseServerError(error.__str__())
        
        return self.cnxn.cursor()
    
    def _check(self, cursor):
        tables = [row.table_name.lower() for row in cursor.tables()]
        for requiredTables in ['coinattributes', 'cm2001maincollection', 'cm2001maincollection']:
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
                value = getattr(row, srcColumn)
                if isinstance(value, bytearray):
                    record.setValue(dstColumn, QtCore.QByteArray(value))
                elif isinstance(value, str):
                    if srcColumn == 'Mintage':
                        value = value.replace(',', '').replace('(', '').replace(')', '')
                    record.setValue(dstColumn, value.strip())
                elif isinstance(value, datetime.date):
                    record.setValue(dstColumn, QtCore.QDate.fromString(value.isoformat(), QtCore.Qt.ISODate))
                elif isinstance(value, decimal.Decimal):
                    record.setValue(dstColumn, float(value))
                else:
                    record.setValue(dstColumn, value)
            
            if dstColumn == 'status':
                record.setValue(dstColumn, 'owned')
                if getattr(row, 'Sold To') or getattr(row, 'Date Sold'):
                    record.setValue(dstColumn, 'sold')
                elif getattr(row, 'Sell'):
                    record.setValue(dstColumn, 'sale')
                elif getattr(row, 'Want'):
                    record.setValue(dstColumn, 'wish')
        
        if not record.value('title'):
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
