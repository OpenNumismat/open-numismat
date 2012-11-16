# -*- coding: utf-8 -*-

import base64, ctypes, shutil, tempfile

try:
    import winreg
    import lxml.etree
except ImportError:
    print('lxml or winreg module missed. Importing from CoinsCollector not available')

from PyQt4 import QtCore, QtGui

from Collection.Import import _Import
from Tools.Converters import stringToMoney

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

class ImportCoinsCollector(_Import):
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
        'material': 'MATERIAL_CODE',
        'fineness': None,
        'shape': 'FORMA_CODE',
        'diameter': 'DIAMETER',
        'thickness': 'EDGE',
        'weight': 'WEIGHT',
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
    
    @staticmethod
    def defaultDir():
        dir_ = QtCore.QDir(_Import.defaultDir())
        dirNames = ["C:/Program Files/Coins Collector 2/Collections", "C:/Program Files (x86)/Coins Collector 2/Collections"]
        for dirName in dirNames:
            if dir_.cd(dirName):
                break
        
        try:
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\SerFox Soft\Coins Collector\2.0')
            value = winreg.QueryValueEx(hkey, 'LocalBase')[0]
            winreg.CloseKey(hkey)
            dir_.cd(value)
        except WindowsError:
            pass
        
        return dir_.absolutePath()
    
    def _connect(self, src):
        self.dir_ = None
        return QtCore.QDir(src)
    
    def _check(self, srcDir):
        if not srcDir.exists("MainTable.cds"):
            return False
        
        return True
    
    def _getRows(self, srcDir):
        self.dir_ = self.__convert(srcDir)
        
        file = self.dir_.absoluteFilePath("MainTable.xml")
        tree = lxml.etree.parse(file)
        self.fields = self.__getFields(tree)
        rows = tree.xpath("/DATAPACKET/ROWDATA/ROW")
        return rows
    
    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
            if srcColumn and srcColumn in row.keys():
                rawData = row.get(srcColumn)
                if isinstance(self.fields[srcColumn], Reference):
                    ref = self.fields[srcColumn]
                    value = ref[rawData]
                elif self.fields[srcColumn] == 'date':
                    value = QtCore.QDate.fromString(rawData, 'yyyyMMdd')
                elif srcColumn in ['COST', 'SELLPRISE']:
                    try:
                        value = stringToMoney(rawData)
                    except ValueError:
                        value = None
                else:
                    value = rawData
                
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
                    ref = self.fields["MINT_CODE"]
                    mark = ref.mark(mintId)
                    record.setValue(dstColumn, mark)
            
            if dstColumn == 'catalognum1':
                catalogParts = []
                ref = self.fields["CATALOG_CODE"]
                catalog = ref[row.get("CATALOG_CODE")]
                if catalog:
                    catalogParts.append(catalog)
                catalogNum = row.get("CATALOG_NUMBER")
                if catalogNum:
                    catalogParts.append(catalogNum)
                record.setValue(dstColumn, ' '.join(catalogParts))
            
            imgFields = ['obverseimg', 'reverseimg', 'photo1', 'photo2']
            if dstColumn in imgFields:
                ref = self.fields["PICTURES"]
                pictures = ref[row.get("ID")]
                if pictures:
                    type_ = imgFields.index(dstColumn)
                    value = pictures[type_]
                    if value:
                        image = QtGui.QImage()
                        image.loadFromData(value)
                        record.setValue(dstColumn, image)
            
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
    
    def _close(self, connection):
        if self.dir_:
            shutil.rmtree(self.dir_.absolutePath(), True)
    
    def __convert(self, directory):
        dfBinary, dfXML, dfXMLUTF8 = range(3)
        
        srcDir = QtCore.QDir(directory)
        dstDir = QtCore.QDir(tempfile.mkdtemp())
        
        converter = ctypes.windll.LoadLibrary("Cdr2Xml.dll")
        for fn in self.referenceFiles.values():
            src = srcDir.absoluteFilePath('.'.join([fn, 'cds']))
            dst = dstDir.absoluteFilePath('.'.join([fn, 'xml']))
            converter.CdrToXml(src, dst, dfXMLUTF8)
        
        return dstDir
    
    def __getFields(self, tree):
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
