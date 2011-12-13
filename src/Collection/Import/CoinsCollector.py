# -*- coding: utf-8 -*-

import base64
from encodings.cp1251 import Codec

try:
    import lxml.etree
except ImportError:
    print('lxml module missed. Importing from CoinsCollector not available')

from PyQt4 import QtCore, QtGui

def encodeXml(data):
    if data:
        codec = Codec()
        decodedData = codec.decode(bytes(data, 'latin-1'))
        return decodedData[0].strip()
    else:
        return ''

class Reference(dict):
    def __init__(self, fileName=''):
        if fileName:
            self.load(fileName)
    
    def load(self, fileName):
        tree = lxml.etree.parse(fileName)
        rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
        for row in rows:
            dict.__setitem__(self, row.get("ID"), encodeXml(row.get("NAME")))
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return None

class MintReference(Reference):
    def __init__(self, fileName=''):
        super(MintReference, self).__init__(fileName)
        
        self.mintMarks = {}
        self.mintDescriptions = {}
    
    def load(self, fileName):
        tree = lxml.etree.parse(fileName)
        rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
        for row in rows:
            dict.__setitem__(self, row.get("ID"), encodeXml(row.get("NAME")))
            self.mintMarks[row.get("ID")] = encodeXml(row.get("MARK"))
            self.mintDescriptions[row.get("ID")] = encodeXml(row.get("DESCRIPTION"))
    
    def mark(self, key):
        return self.mintMarks[key]
    
    def description(self, key):
        return self.mintDescriptions[key]

class PictureReference(Reference):
    def __init__(self, fileName=''):
        super(PictureReference, self).__init__(fileName)
    
    def load(self, fileName):
        tree = lxml.etree.parse(fileName)
        rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
        for row in rows:
            id_ = row.get("MAIN_CODE")
            if id_ in self.keys():
                pictures = self.__getitem__(id_)
            else:
                pictures = [None]*4
            type_ = int(row.get("TYPE")) - 1
            data = bytes(row.get("PICTURE"), 'latin-1')
            pictures[type_] = base64.b64decode(data)
            
            dict.__setitem__(self, id_, pictures)

class ImportCoinsCollector(QtCore.QObject):
    Columns = {
        'title': 'TITLE',
        'value': 'DENOMINATION',
        'unit': 'UNIT_CODE',
        'country': 'COUNTRY_CODE',
        'year': 'M_YEAR',
        'period': None,
        'mint': 'MINT_CODE',
        'mintmark': None,
        'issuedate': 'ENTRY_DATE',
        'type': 'TYPE_CODE',
        'series': 'VARIETY_CODE',
        'subjectshort': None,
        'status': 'STATUS_CODE',
        'metal': 'MATERIAL_CODE',
        'fineness': None,
        'form': 'FORMA_CODE',
        'diameter': 'DIAMETER',
        'thick': 'EDGE',
        'mass': 'WEIGHT',
        'grade': 'CONDITION_CODE',
        'edge': 'GURT_CODE',
        'edgelabel': 'GURT_DESC_CODE',
        'obvrev': 'OBREV_CODE',
        'quality': None,
        'mintage': 'MINTAGE',
        'dateemis': 'M_DATES',
        'catalognum1': None,
        'catalognum2': 'KRAUZENUM',
        'catalognum3': None,
        'catalognum4': None,
        'rarity': 'RARITY_CODE',
        'price1': None,
        'price2': None,
        'price3': None,
        'price4': 'M_VALUE',
        'variety': None,
        'paydate': 'PURCHASED',
        'payprice': 'COST',
        'totalpayprice': 'COST',
        'saller': 'PURCHFROM_CODE',
        'payplace': None,
        'payinfo': 'CUSTOM2',
        'saledate': 'SOLD',
        'saleprice': 'SELLPRISE',
        'totalsaleprice': 'SELLPRISE',
        'buyer': 'PURCHTO_CODE',
        'saleplace': None,
        'saleinfo': 'PURCHSELL',
        'note': 'DESCRIPTION',
        'obverseimg': None,
        'obversedesign': 'OBVERSE',
        'obversedesigner': 'DESIGNER_CODE',
        'reverseimg': None,
        'reversedesign': 'REVERSE',
        'reversedesigner': 'DESIGNER_CODE',
        'edgeimg': None,
        'subject': 'CUSTOM1',
        'photo1': None,
        'photo2': None,
        'photo3': None,
        'photo4': None,
        'storage': 'LOCATION_CODE',
        'features': None,
    }
    
    referenceFiles = {
        'COUNTRY_CODE': 'Country.XML',
        'UNIT_CODE': 'Unit.XML',
        'CONDITION_CODE': 'Condition.XML',
        'MATERIAL_CODE': 'Material.XML',
        'CATALOG_CODE': 'Catalog.XML',
        'TYPE_CODE': 'Type.XML',
        'STATUS_CODE': 'Status.XML',
        'LOCATION_CODE': 'Location.XML',
        'FORMA_CODE': 'FORMA.XML',
        'GURT_CODE': 'Gurt.XML',
        'MINT_CODE': 'Mint.XML',
        'OBREV_CODE': 'ObRev.XML',
        'RARITY_CODE': 'Rarity.XML',
        'VARIETY_CODE': 'Variety.XML',
        'GURT_DESC_CODE': 'GurtDesc.XML',
        'DESIGNER_CODE': 'Designer.XML',
        'PURCHFROM_CODE': 'Seller.XML',
        'PURCHTO_CODE': 'Buyer.XML',
    }
    
    def __init__(self, parent=None):
        super(ImportCoinsCollector, self).__init__(parent)
    
    def getFields(self, tree):
        fields = {}
        rows = tree.xpath("/DATAPACKET/METADATA/FIELDS/FIELD")
        for row in rows:
            field = row.get("attrname")
            if field in self.referenceFiles:
                ref = self.__loadReference(self.referenceFiles[field])
                fields[field] = ref
            else:
                if "SUBTYPE" in row.keys():
                    fields[field] = row.get("SUBTYPE").lower()
                else:
                    fields[field] = row.get("fieldtype").lower()
        
        fields["PICTURES"] = self.__loadReference("Pictures.XML")
        
        return fields
    
    def __loadReference(self, fileTitle):
        if fileTitle == "Mint.XML":
            ref = MintReference()
        elif fileTitle == "Pictures.XML":
            ref = PictureReference()
        else:
            ref = Reference()
        
        if self.dir_.exists(fileTitle):
            fileName = self.dir_.absoluteFilePath(fileTitle)
            ref.load(fileName)
        
        return ref
    
    def importData(self, directory, model):
        res = False
        if self._check(directory):
            self.dir_ = QtCore.QDir(directory)
            file = self.dir_.absoluteFilePath("MainTable.XML")
            tree = lxml.etree.parse(file)
            fields = self.getFields(tree)
            rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
            
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
                        value = row.get(srcColumn)
                        if isinstance(fields[srcColumn], Reference):
                            ref = fields[srcColumn]
                            value = ref[value]
                        elif fields[srcColumn] == 'date':
                            value = QtCore.QDate.fromString(value, 'yyyyMMdd')
                        elif srcColumn in ['COST', 'SELLPRISE']:
                            try:
                                # TODO: Use converter from auction parser
                                value = float(value)
                            except ValueError:
                                value = None
                        else:
                            value = encodeXml(value)
                        
                        record.setValue(dstColumn, value)
                    
                    if dstColumn == 'status':
                        # Process Status fields that contain translated text
                        value = record.value(dstColumn) or ''
                        if value.lower() in ['имеется', 'приобретена', 'есть', 'в наличии']:
                            record.setValue(dstColumn, 'owned')
                        elif value.lower() in ['нужна', 'нуждаюсь']:
                            record.setValue(dstColumn, 'wish')
                        else:
                            record.setValue(dstColumn, 'demo')
                        
                        if row.get('SELLPRISE') or row.get('PURCHTO_CODE'):
                            record.setValue(dstColumn, 'sold')
                        elif row.get('COST') or row.get('PURCHFROM_CODE'):
                            record.setValue(dstColumn, 'owned')
                    
                    if dstColumn == 'mintmark':
                        mintId = row.get("MINT_CODE")
                        if mintId:
                            ref = fields["MINT_CODE"]
                            mark = ref.mark(mintId)
                            record.setValue(dstColumn, mark)
                    
                    if dstColumn == 'catalognum1':
                        catalogParts = []
                        ref = fields["CATALOG_CODE"]
                        catalog = ref[row.get("CATALOG_CODE")]
                        if catalog:
                            catalogParts.append(catalog)
                        catalogNum = encodeXml(row.get("CATALOG_NUMBER"))
                        if catalogNum:
                            catalogParts.append(catalogNum)
                        record.setValue(dstColumn, ' '.join(catalogParts))
                    
                    imgFields = ['obverseimg', 'reverseimg', 'photo1', 'photo2']
                    if dstColumn in imgFields:
                        ref = fields["PICTURES"]
                        pictures = ref[row.get("ID")]
                        if pictures:
                            type_ = imgFields.index(dstColumn)
                            value = pictures[type_]
                            if value:
                                record.setValue(dstColumn, QtCore.QByteArray(value))
                    
                    if dstColumn == 'features':
                        features = []
                        value = encodeXml(row.get('NOTE'))
                        if value:
                            features.append(value)
                        value = encodeXml(row.get('CERTIFIEDBY'))
                        if value:
                            features.append(self.tr("Certified by: %s") % value)
                        value = encodeXml(row.get('VALUENOTE'))
                        if value:
                            features.append(self.tr("Price note: %s") % value)
                        
                        if features:
                            record.setValue(dstColumn, '\n'.join(features))
                
                model.appendRecord(record)
            
            progressDlg.setValue(len(rows))
            res = True
        
        return res
    
    def _check(self, directory):
        dir_ = QtCore.QDir(directory)
        if not dir_.exists("MainTable.XML"):
            return False
        
        return True
