# -*- coding: utf-8 -*-

try:
    import pyodbc
except ImportError:
    print('pyodbc module missed. Importing not available')

from PyQt4 import QtCore, QtGui

class ImportNumizmat(QtCore.QObject):
    Columns = {
        'title': 'name',
        'value': 'nominal',
        'unit': 'unit',
        'country': 'country',
        'year': 'age',
        'period': 'period',
        'mint': 'mint',
        'mintmark': 'mintmark',
        'issuedate': None,
        'type': 'types',
        'series': 'series',
        'subjectshort': None,
        'status': 'status',
        'metal': 'metal',
        'fineness': 'probe',
        'form': 'forma',
        'diameter': 'diametr',
        'thick': 'thick',
        'mass': 'mass',
        'grade': 'safety',
        'edge': 'gurt',
        'edgelabel': 'gurtlabel',
        'obvrev': 'avrev',
        'quality': None,
        'mintage': 'circ',
        'dateemis': 'dateemis',
        'catalognum1': 'numcatalog',
        'catalognum2': None,
        'catalognum3': None,
        'catalognum4': None,
        'rarity': None,
        'price1': 'fine',
        'price2': 'vf',
        'price3': 'xf',
        'price4': 'unc',
        'paydate': 'datapay',
        'payprice': 'pricepay',
        'totalpayprice': 'pricepay',
        'saller': None,
        'payplace': None,
        'payinfo': None,
        'saledate': None,
        'saleprice': 'price',
        'totalsaleprice': 'price',
        'buyer': None,
        'saleplace': None,
        'saleinfo': None,
        'note': 'difference',
        'obverseimg': 'avers',
        'obversedesign': None,
        'obversedesigner': None,
        'reverseimg': 'revers',
        'reversedesign': None,
        'reversedesigner': None,
        'edgeimg': None,
        'subject': 'note'
    }

    def __init__(self, parent=None):
        super(ImportNumizmat, self).__init__(parent)
    
    def importData(self, dbname, model):
        res = False
        
        try:
            cnxn = pyodbc.connect(driver='{Firebird/InterBase(r) driver}', dbname=dbname, uid='SYSDBA', pwd='masterkey')
        except pyodbc.Error:
            return res
        cursor = cnxn.cursor()
        
        if self._check(cursor):
            columns = self._getColumns(cursor)
            
            rows = cursor.execute("SELECT * FROM coins").fetchall()
            
            progressDlg = QtGui.QProgressDialog(self.tr("Importing"), self.tr("Cancel"), 0, len(rows), self.parent())
            progressDlg.setWindowModality(QtCore.Qt.WindowModal)
            progressDlg.setMinimumDuration(250)
            
            for progress, row in enumerate(rows):
                progressDlg.setValue(progress)
                if progressDlg.wasCanceled():
                    break
                
                record = model.record()
                for dstColumn, srcColumn in self.Columns.items():
                    if srcColumn in columns:
                        index = columns.index(srcColumn)
                        if isinstance(row[index], bytearray):
                            record.setValue(dstColumn, QtCore.QByteArray(row[index]))
                        elif isinstance(row[index], str):
                            record.setValue(dstColumn, row[index].strip())
                        else:
                            record.setValue(dstColumn, row[index])
                        
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
        if not cursor.tables('coins').fetchone():
            return False
        
        columns = self._getColumns(cursor)
        for requiredColumn in ['name', 'nominal', 'unit', 'country']:
            if requiredColumn not in columns:
                return False
        
        return True
    
    def _getColumns(self, cursor):
        columns = [row.column_name.lower() for row in cursor.columns('coins')]
        return columns
