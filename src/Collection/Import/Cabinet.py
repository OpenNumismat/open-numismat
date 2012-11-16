# -*- coding: utf-8 -*-

import datetime

try:
    import pyodbc
except ImportError:
    print('pyodbc module missed. Importing not available')

from PyQt4 import QtCore, QtGui

from Collection.Import import _Import, _DatabaseServerError

class ImportCabinet(_Import):
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
        'material': 'Material',
        'fineness': None,
        'shape': 'Form',
        'diameter': 'Diameter',
        'thickness': 'Thickness',
        'weight': 'Weight',
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
    
    def _connect(self, src):
        try:
            self.cnxn = pyodbc.connect(driver='{DBISAM 4 ODBC Driver}', connectionType='Local', catalogName=src)
        except pyodbc.Error as error:
            raise _DatabaseServerError(error.__str__())
        
        return self.cnxn.cursor()
    
    def _check(self, cursor):
        tables = [row.table_name.lower() for row in cursor.tables()]
        for requiredTables in ['coins', 'country']:
            if requiredTables not in tables:
                return False
        
        columns = self.__getColumns(cursor)
        for requiredColumn in ['Nominal', 'idCurrency', 'idCountry']:
            if requiredColumn not in columns:
                return False
        
        return True
    
    def _getRows(self, cursor):
        cursor.execute("""
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
        """)
        return cursor.fetchall()
    
    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and hasattr(row, srcColumn):
                rawData = getattr(row, srcColumn)
                if isinstance(rawData, bytearray):
                    image = QtGui.QImage()
                    image.loadFromData(rawData)
                    value = image
                elif isinstance(rawData, str):
                    value = rawData.strip()
                elif isinstance(rawData, datetime.date):
                    value = QtCore.QDate.fromString(rawData.isoformat(), QtCore.Qt.ISODate)
                else:
                    value = rawData
                
                record.setValue(dstColumn, value)
            
            if dstColumn == 'status':
                record.setValue(dstColumn, 'demo')
                if getattr(row, 'Sold') or getattr(row, 'PriceSold'):
                    record.setValue(dstColumn, 'sold')
                elif getattr(row, 'Present') == 1 or getattr(row, 'Purchased') or getattr(row, 'Price') or getattr(row, 'PurchasedInfo'):
                    record.setValue(dstColumn, 'owned')
            
            if dstColumn == 'saller':
                if row.SellerID:
                    cursor = self.cnxn.cursor()
                    sallerRow = cursor.execute("""
                        SELECT Name FROM person WHERE id=?
                    """, row.SellerID).fetchone()
                    if sallerRow:
                        record.setValue(dstColumn, sallerRow.Name)
            
            if dstColumn == 'buyer':
                if row.BuyerID:
                    cursor = self.cnxn.cursor()
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
    
    def _close(self, connection):
        self.cnxn.close()
    
    def __getColumns(self, cursor):
        columns = [row.column_name for row in cursor.columns('coins')]
        return columns
