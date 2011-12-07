# -*- coding: utf-8 -*-

import datetime

try:
    import pyodbc
except ImportError:
    print('pyodbc module missed. Importing not available')

from PyQt4 import QtCore, QtGui

class ImportCabinet(QtCore.QObject):
    Columns = {
        'title': None,
        'value': 'Nominal',
        'unit': 'Currency',
        'country': 'Country',
        'year': 'Date',
        'period': None,
        'mint': None,
        'mintmark': 'MintMark',
        'issuedate': None,
        'type': 'Type',
        'series': None,
        'subjectshort': None,
        'status': None,
        'metal': 'Material',
        'fineness': None,
        'form': 'Form',
        'diameter': 'Diameter',
        'thick': 'Thickness',
        'mass': 'Weight',
        'grade': 'Sostojanie',
        'edge': 'RandType',
        'edgelabel': 'Text_Rand',
        'obvrev': None,
        'quality': None,
        'mintage': 'Mintage',
        'dateemis': None,
        'catalognum1': 'Catalog',
        'catalognum2': 'Catalog_s1',
        'catalognum3': 'Catalog_s2',
        'catalognum4': 'Catalog_s3',
        'rarity': None,
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': None,
        'paydate': 'Purchased',
        'payprice': 'Price',
        'totalpayprice': 'Price',
        'saller': None,
        'payplace': 'PurchasedIn',
        'payinfo': 'PurchasedInfo',
        'saledate': 'Sold',
        'saleprice': 'PriceSold',
        'totalsaleprice': 'PriceSold',
        'buyer': None,
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': 'Picture',
        'obversedesign': 'Text_Avers',
        'obversedesigner': None,
        'reverseimg': 'Picture2',
        'reversedesign': 'Text_Revers',
        'reversedesigner': None,
        'edgeimg': None,
        'subject': 'HyperLinkCaption',
        'photo1': 'Picture3',
        'photo2': 'Picture4',
        'photo3': 'Picture5',
        'photo4': 'Picture6',
        'storage': 'Location',
        'features': None
    }

    def __init__(self, parent=None):
        super(ImportCabinet, self).__init__(parent)
    
    def importData(self, directory, model):
        res = False
        
        try:
            cnxn = pyodbc.connect(driver='{DBISAM 4 ODBC Driver}', connectionType='Local', catalogName=directory)
        except pyodbc.Error:
            return res
        cursor = cnxn.cursor()
        
        if self._check(cursor):
            rows = cursor.execute("""
            SELECT coins.*, country.Name AS Country, kl_nominal.Name AS Currency,
                kl_metal.Name AS Material, kl_form.Name AS Form,
                kl_cond.Name AS Sostojanie, kl_rand.Name AS RandType,
                kl_album.Name AS Location FROM coins
            LEFT OUTER JOIN country ON coins.idcountry = country.inc
            LEFT OUTER JOIN kl_nominal ON coins.idcurrency = kl_nominal.id
            LEFT OUTER JOIN kl_metal ON coins.idmaterial = kl_metal.id
            LEFT OUTER JOIN kl_form ON coins.idform = kl_form.id
            LEFT OUTER JOIN kl_cond ON coins.idsostojanie1 = kl_cond.id
            LEFT OUTER JOIN kl_rand ON coins.idrand = kl_rand.id
            LEFT OUTER JOIN kl_album ON CAST(coins.CoinLocation AS INTEGER) = kl_album.id
            """).fetchall()
            
            progressDlg = QtGui.QProgressDialog(self.tr("Importing"), self.tr("Cancel"), 0, len(rows), self.parent())
            progressDlg.setWindowModality(QtCore.Qt.WindowModal)
            progressDlg.setMinimumDuration(250)
            for progress, row in enumerate(rows):
                progressDlg.setValue(progress)
                if progressDlg.wasCanceled():
                    break
                
                record = model.record()
                for dstColumn, srcColumn in self.Columns.items():
                    if srcColumn and hasattr(row, srcColumn):
                        value = getattr(row, srcColumn)
                        if isinstance(value, bytearray):
                            record.setValue(dstColumn, QtCore.QByteArray(value))
                        elif isinstance(value, str):
                            record.setValue(dstColumn, value.strip())
                        elif isinstance(value, datetime.date):
                            record.setValue(dstColumn, QtCore.QDate.fromString(value.isoformat(), QtCore.Qt.ISODate))
                        else:
                            record.setValue(dstColumn, value)
                    
                    if dstColumn == 'status':
                        record.setValue(dstColumn, 'demo')
                        if getattr(row, 'Sold') or getattr(row, 'PriceSold'):
                            record.setValue(dstColumn, 'sold')
                        elif getattr(row, 'Present') == 1 or getattr(row, 'Purchased') or getattr(row, 'Price') or getattr(row, 'PurchasedInfo'):
                            record.setValue(dstColumn, 'owned')
                    
                    if dstColumn == 'saller':
                        sallerRow = cursor.execute("""
                            SELECT Name FROM person WHERE id=?
                        """, row.SellerID).fetchone()
                        if sallerRow:
                            record.setValue(dstColumn, sallerRow.Name)
                    
                    if dstColumn == 'buyer':
                        buyerRow = cursor.execute("""
                            SELECT Name FROM person WHERE id=?
                        """, row.BuyerID).fetchone()
                        if buyerRow:
                            record.setValue(dstColumn, buyerRow.Name)
                    
                    if dstColumn == 'features':
                        features = []
                        value = getattr(row, 'CoinInfo')
                        if value:
                            features.append(value.strip())
                        inCapsule = getattr(row, 'Capsule')
                        if inCapsule:
                            features.append(self.tr("In capsule"))
                        value = getattr(row, 'Sertified')
                        if value:
                            features.append(value.strip())
                        value = getattr(row, 'Extra s1.')
                        if value:
                            features.append(self.tr("Extra s1: %s") % value.strip())
                        value = getattr(row, 'Extra s2.')
                        if value:
                            features.append(self.tr("Extra s2: %s") % value.strip())
                        value = getattr(row, 'Extra n.')
                        if value:
                            features.append(self.tr("Extra n: %d") % value)
                        
                        if features:
                            record.setValue(dstColumn, '\n'.join(features))
                
                model.appendRecord(record)
            
            progressDlg.setValue(len(rows))
            res = True
        else:
            res = False
        
        cnxn.close()
        return res
    
    def _check(self, cursor):
        tables = [row.table_name.lower() for row in cursor.tables()]
        for requiredTables in ['coins', 'country']:
            if requiredTables not in tables:
                return False
        
        columns = self._getColumns(cursor)
        for requiredColumn in ['Nominal', 'idCurrency', 'idCountry']:
            if requiredColumn not in columns:
                return False
        
        return True
    
    def _getColumns(self, cursor):
        columns = [row.column_name for row in cursor.columns('coins')]
        return columns
