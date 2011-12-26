# -*- coding: utf-8 -*-

import datetime, decimal, socket

try:
    import firebirdsql
except ImportError:
    print('firebirdsql module missed. Importing from Numizmat 2.1 not available')

from PyQt4 import QtCore, QtGui

from Collection.Import import _Import, _InvalidDatabaseError, _DatabaseServerError

class ImportNumizmat(_Import):
    Columns = {
        'title': 'NAME',
        'value': 'NOMINAL',
        'unit': 'UNIT',
        'country': 'COUNTRY',
        'year': 'AGE',
        'period': 'PERIOD',
        'mint': 'MINT',
        'mintmark': 'MINTMARK',
        'issuedate': None,
        'type': 'TYPES',
        'series': 'SERIES',
        'subjectshort': None,
        'status': 'STATUS',
        'metal': 'METAL',
        'fineness': 'PROBE',
        'form': 'FORMA',
        'diameter': 'DIAMETR',
        'thick': 'THICK',
        'mass': 'MASS',
        'grade': 'SAFETY',
        'edge': 'GURT',
        'edgelabel': 'GURTLABEL',
        'obvrev': 'AVREV',
        'quality': None,
        'mintage': 'CIRC',
        'dateemis': 'DATEEMIS',
        'catalognum1': 'NUMCATALOG',
        'catalognum2': None,
        'catalognum3': None,
        'catalognum4': None,
        'rarity': None,
        'price1': 'FINE',
        'price2': 'VF',
        'price3': 'XF',
        'price4': 'UNC',
        'paydate': 'DATAPAY',
        'payprice': 'PRICEPAY',
        'totalpayprice': 'PRICEPAY',
        'saller': None,
        'payplace': None,
        'payinfo': None,
        'saledate': None,
        'saleprice': 'PRICE',
        'totalsaleprice': 'PRICE',
        'buyer': None,
        'saleplace': None,
        'saleinfo': None,
        'note': 'DIFFERENCE',
        'obverseimg': 'AVERS',
        'obversedesign': None,
        'obversedesigner': None,
        'reverseimg': 'REVERS',
        'reversedesign': None,
        'reversedesigner': None,
        'edgeimg': None,
        'subject': 'NOTE'
    }

    def __init__(self, parent=None):
        super(ImportNumizmat, self).__init__(parent)
    
    def _connect(self, src):
        try:
            self.cnxn = firebirdsql.connect(database=src, host='localhost', user='SYSDBA',
                                            password='masterkey', charset='WIN1251')
        except firebirdsql.OperationalError as error:
            raise _InvalidDatabaseError(error.__str__())
        except socket.error as error:
            raise _DatabaseServerError(error.__str__())
        
        return self.cnxn.cursor()
    
    def _getRows(self, cursor):
        cursor.execute("SELECT * FROM coins")
        return cursor.fetchallmap()
    
    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and srcColumn in row.keys():
                rawData = row[srcColumn]
                if isinstance(rawData, bytearray) or isinstance(rawData, bytes):
                    image = QtGui.QImage()
                    image.loadFromData(rawData)
                    value = image
                elif isinstance(rawData, str):
                    if srcColumn == 'CIRC':
                        rawData = rawData.replace('.', '')
                    value = rawData.strip()
                elif isinstance(rawData, decimal.Decimal):
                    value = int(rawData)
                elif isinstance(rawData, datetime.date):
                    value = QtCore.QDate.fromString(rawData.isoformat(), QtCore.Qt.ISODate)
                else:
                    value = rawData
                
                record.setValue(dstColumn, value)
                
                if dstColumn == 'status':
                    # Process Status fields that contain translated text
                    if record.value(dstColumn) in ['есть', 'have', 'є', 'притежава']:
                        record.setValue(dstColumn, 'owned')
                    elif record.value(dstColumn) in ['нужна', 'need', 'потрібна', 'издирва']:
                        record.setValue(dstColumn, 'wish')
                    elif record.value(dstColumn) in ['обмен', 'exchange', 'обмін', 'обмен']:
                        record.setValue(dstColumn, 'sale')
                    else:
                        record.setValue(dstColumn, 'demo')
    
    def _close(self, connection):
        self.cnxn.close()
