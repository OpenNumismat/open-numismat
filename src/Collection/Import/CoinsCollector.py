# -*- coding: utf-8 -*-

import base64, ctypes, tempfile

try:
    import lxml.etree
except ImportError:
    print('lxml module missed. Importing from CoinsCollector not available')

from PyQt4 import QtCore, QtGui

class Reference(dict):
    def __init__(self, fileName=''):
        if fileName:
            self.load(fileName)
    
    def load(self, fileName):
        tree = lxml.etree.parse(fileName)
        rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
        for row in rows:
            dict.__setitem__(self, row.get("ID"), row.get("NAME"))
    
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
            dict.__setitem__(self, row.get("ID"), row.get("NAME"))
            self.mintMarks[row.get("ID")] = row.get("MARK")
            self.mintDescriptions[row.get("ID")] = row.get("DESCRIPTION")
    
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
        '__dummy1__': 'MainTable',
        '__dummy2__': 'Pictures',
        'COUNTRY_CODE': 'Country',
        'UNIT_CODE': 'Unit',
        'CONDITION_CODE': 'Condition',
        'MATERIAL_CODE': 'Material',
        'CATALOG_CODE': 'Catalog',
        'TYPE_CODE': 'Type',
        'STATUS_CODE': 'Status',
        'LOCATION_CODE': 'Location',
        'FORMA_CODE': 'FORMA',
        'GURT_CODE': 'Gurt',
        'MINT_CODE': 'Mint',
        'OBREV_CODE': 'ObRev',
        'RARITY_CODE': 'Rarity',
        'VARIETY_CODE': 'Variety',
        'GURT_DESC_CODE': 'GurtDesc',
        'DESIGNER_CODE': 'Designer',
        'PURCHFROM_CODE': 'Seller',
        'PURCHTO_CODE': 'Buyer',
    }
    
    def __init__(self, parent=None):
        super(ImportCoinsCollector, self).__init__(parent)
    
    def getFields(self, tree):
        fields = {}
        rows = tree.xpath("/DATAPACKET/METADATA/FIELDS/FIELD")
        for row in rows:
            field = row.get("attrname")
            if field in self.referenceFiles:
                ref = self.__loadReference('.'.join([self.referenceFiles[field], 'xml']))
                fields[field] = ref
            else:
                if "SUBTYPE" in row.keys():
                    fields[field] = row.get("SUBTYPE").lower()
                else:
                    fields[field] = row.get("fieldtype").lower()
        
        fields["PICTURES"] = self.__loadReference("Pictures.xml")
        
        return fields
    
    def __loadReference(self, fileTitle):
        if fileTitle == "Mint.xml":
            ref = MintReference()
        elif fileTitle == "Pictures.xml":
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
            progressDlg = QtGui.QProgressDialog(self.tr("Importing"), self.tr("Cancel"), 0, 1, self.parent())
            progressDlg.setWindowModality(QtCore.Qt.WindowModal)
            progressDlg.setMinimumDuration(250)
            progressDlg.setValue(0)
            
            self.dir_ = self.convert(directory)
            
            file = self.dir_.absoluteFilePath("MainTable.xml")
            tree = lxml.etree.parse(file)
            fields = self.getFields(tree)
            rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
            
            progressDlg.setMaximum(len(rows))
            
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
                            value = value
                        
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
                        catalogNum = row.get("CATALOG_NUMBER")
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
                        value = row.get('NOTE')
                        if value:
                            features.append(value)
                        value = row.get('CERTIFIEDBY')
                        if value:
                            features.append(self.tr("Certified by: %s") % value)
                        value = row.get('VALUENOTE')
                        if value:
                            features.append(self.tr("Price note: %s") % value)
                        
                        if features:
                            record.setValue(dstColumn, '\n'.join(features))
                
                model.appendRecord(record)
            
            progressDlg.setValue(len(rows))
            res = True
        
        return res
    
    def convert(self, directory):
        dfBinary, dfXML, dfXMLUTF8 = range(3)
        
        srcDir = QtCore.QDir(directory)
        dstDir = QtCore.QDir(tempfile.mkdtemp())
        
        converter = ctypes.windll.LoadLibrary("Cdr2Xml.dll")
        for fn in self.referenceFiles.values():
            src = srcDir.absoluteFilePath('.'.join([fn, 'cds']))
            dst = dstDir.absoluteFilePath('.'.join([fn, 'xml']))
            converter.CdrToXml(src, dst, dfXMLUTF8)
        
        return dstDir
    
    def _check(self, directory):
        dir_ = QtCore.QDir(directory)
        if not dir_.exists("MainTable.cds"):
            return False
        
        return True
