# -*- coding: utf-8 -*-

import datetime, decimal

try:
    import firebirdsql
except ImportError:
    print('firebirdsql module missed. Importing from Numizmat 2.1 not available')

from PyQt4 import QtCore, QtGui

class ImportNumizmat(QtCore.QObject):
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
    
    def importData(self, file, model):
        res = False
        
        try:
            cnxn = firebirdsql.connect(database=file, host='localhost', user='SYSDBA', password='masterkey', charset='WIN1251')
        except firebirdsql.Error:
            return res
        cursor = cnxn.cursor()
        
        if self._check(cursor):
            rows = cursor.execute("SELECT * FROM coins")
            rows = cursor.fetchallmap()
            
            progressDlg = QtGui.QProgressDialog(self.tr("Importing"), self.tr("Cancel"), 0, len(rows), self.parent())
            progressDlg.setWindowModality(QtCore.Qt.WindowModal)
            progressDlg.setMinimumDuration(250)
            
            for progress, row in enumerate(rows):
                progressDlg.setValue(progress)
                if progressDlg.wasCanceled():
                    break
                
                record = model.record()
                for dstColumn, srcColumn in self.Columns.items():
                    if srcColumn and srcColumn in row.keys():
                        value = row[srcColumn]
                        if isinstance(value, bytearray) or isinstance(value, bytes):
                            record.setValue(dstColumn, QtCore.QByteArray(value))
                        elif isinstance(value, str):
                            record.setValue(dstColumn, value.strip())
                        elif isinstance(value, decimal.Decimal):
                            record.setValue(dstColumn, int(value))
                        elif isinstance(value, datetime.date):
                            record.setValue(dstColumn, QtCore.QDate.fromString(value.isoformat(), QtCore.Qt.ISODate))
                        else:
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
                model.appendRecord(record)
            
            progressDlg.setValue(len(rows))
            res = True
        else:
            res = False
        
        cnxn.close()
        return res
    
    def _check(self, cursor):
        return True
