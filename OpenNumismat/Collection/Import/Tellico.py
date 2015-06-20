# -*- coding: utf-8 -*-

#############################################
#
# for the Open Numismat project
#
# Contributed by Kurt R. Rahlfs
# kurtRR at affinityCM dot com
# Gnu public license V3
#
#############################################
import base64

available = True

try:
    import lxml.etree
except ImportError:
    print('lxml module missed. Importing from Tellico not available')
    available = False

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt

from OpenNumismat.Collection.Import import _Import
from OpenNumismat.Tools.Converters import stringToMoney


class ImportTellico(_Import):
    Columns = {
        'title': 'title',
        'value': 'denomination', #multiples of the units: for this denomination
        'unit': 'denomination', #the units part: for this denomination
        'country': 'countrys',
        'year': 'year',
        'period': 'rangestart',
        'mint': None,
        'mintmark': 'mintmark',
        'issuedate': None,
        'type': 'type',
        'series': 'type',
        'subjectshort': 'type',
        'status': 'want',
        'material': 'precious',
        'fineness': None,
        'shape': None,
        'diameter': None,
        'thickness': None,
        'weight': None,
        'grade': 'grade',
        'edge': None,
        'edgelabel': None,
        'obvrev': None,
        'quality': None,
        'mintage': 'mintage',
        'dateemis': None,
        'catalognum1': 'km',
        'catalognum2': 'y',
        'catalognum3': 'pcgs',
        'catalognum4': None,
        'rarity': None,
        'price1': None, # Fine
        'price2': None, # VF
        'price3': None, # XF
        'price4': 'value', # Unc
        'variety': 'variety',
        'paydate': 'purchased',
        'payprice': 'cost',
        'totalpayprice': 'cost',
        'saller': 'dealer',
        'payplace': None,
        'payinfo': None,
        'saledate': 'sold',
        'saleprice': 'price',
        'totalsaleprice': 'price',
        'buyer': 'client',
        'saleplace': None,
        'saleinfo': None,
        'note': 'comments',
        'obverseimg': None, #obverse
        'obversedesign': None,
        'obversedesigner': None,
        'reverseimg': None, #reverse
        'reversedesign': None,
        'reversedesigner': None,
        'edgeimg': None, #edge
        'subject': None,
        'photo1': None, #display
        'photo2': None, #display2
        'photo3': None, #detail
        'photo4': None, #detail2
        'storage': 'location',
        'features': None,
        'quantity': 'quantity',
        'url': None,
        'barcode': 'certification',
        #krr: added below
        'defect': 'defects',
        'id': 'id',              #use this only when DB is empty
        'createdat': 'cdate',
        'updatedat': 'mdate',
    }

    def __init__(self, parent=None):
        super(ImportTellico, self).__init__(parent)

    @staticmethod
    def isAvailable():
        return available

    def _connect(self, src):
        return src

    def _getRows(self, srcFile):
        tree = lxml.etree.parse(srcFile)
        rows = tree.xpath("/t:tellico/t:collection/t:entry", namespaces={'t': 'http://periapsis.org/tellico/'})
        return rows
        
    def _setRecord(self, record, row):
#        print ("\n1***add coin\nkrr: row: "+ str(row))
        for dstColumn, srcColumn in self.Columns.items():
          #
          # assumptions
          #
          if dstColumn == 'shape':
              value = 'Circle'
              record.setValue(dstColumn, value)
          elif dstColumn == 'obvrev':
              value = 'Coin'
              record.setValue(dstColumn, value)
          if srcColumn is not None:
#            print ("krr: "+str(dstColumn)+":"+ str(srcColumn))
            #############################
            #
            # multiple source processing
            #
            #############################
            #
            # period of production
            #
            if dstColumn == 'period':
                if row.find("./t:rangestart/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                    value1 = row.find("./t:rangestart/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                else: value1 = '~'
                if row.find("./t:rangeend/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                    value2 = row.find("./t:rangeend/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                else: value2 = '~'
                if value1 != '~' or value2 != '~':
                    record.setValue(dstColumn, value1+"-"+value2)
#                print('')
            #
            # status of coin
            #
            elif dstColumn == 'status':
                if row.find("./t:want", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                    if (row.find("./t:want", namespaces={'t': 'http://periapsis.org/tellico/'}).text) == "true":
                        value = 'wish'
                    else:
                        value = 'owned'
                else:
                    value = 'owned'
#                print ("  krr: status(want) =", value)

                if value == 'owned':
                    #I have it but am I selling it?
                    if row.find("./t:sell", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                        if (row.find("./t:sell", namespaces={'t': 'http://periapsis.org/tellico/'}).text) == "true":
                            value = 'sale'
#                    print ("  krr: status(sell) =", value)
                    # I have/had it.  Was it sold?
                    # the status can 'sold' wether or not sell was set. so don't use an elif below
                    if row.find("./t:sold", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                        rawData = row.find("./t:sold", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                        value = 'sold'
#                            print ("  krr: status(sold-raw) =", rawData)
#                        else:    print ("  krr: status(sold) is absent") #keep it the same as it was
#                    print ("    krr: status result:", dstColumn, value)
                record.setValue(dstColumn, value)
            ############################
            #
            # single souce processing
            #
            ############################
            elif srcColumn and row.find("t:"+srcColumn, namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                rawData = row.find("t:"+srcColumn, namespaces={'t': 'http://periapsis.org/tellico/'}).text
#                print ("  krr: processing: "+srcColumn+" raw data: "+ str(rawData))
                ############################
                #
                # has child nodes
                #
                ############################
                if srcColumn == 'countrys':
                    value = row.find("./t:countrys/t:country", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                    record.setValue(dstColumn, value)
#                    print('')

                elif srcColumn in ['cdate', 'mdate']:
                    valueY = int(row.find("./t:"+srcColumn+"/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                    valueM = int(row.find("./t:"+srcColumn+"/t:month", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                    valueD = int(row.find("./t:"+srcColumn+"/t:day", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                    recordedDate = QtCore.QDateTime.fromString('{:04}{:02}{:02}'.format(valueY, valueM, valueM),'yyyyMMdd')
                    record.setValue(dstColumn, recordedDate.toString(Qt.ISODate))
#                    print ("krr: date=", recordedDate)

                elif rawData:
                    ############################
                    #
                    # sources w/o parent
                    #
                    ############################
#                    print ("    krr: no child values: "+srcColumn+" raw data: "+ str(rawData))
                    #
                    # year
                    #
                    if srcColumn == 'Year' and rawData == '00-00-00':
                        value = None
                    #
                    # quantity
                    #
                    elif srcColumn == 'quantity':
                        if rawData == '0':
                            value = None
                        else:
                            value = int(rawData)
                    #
                    # money fields
                    #
                    elif srcColumn in ['cost','price', 'value']:
                        if rawData == '0':
                            value = None
                        else:
                            try:
                                value = stringToMoney(rawData)
                            except ValueError:
                                value = None
                                
                    #
                    # denomination processing (value, unit)
                    #
                    elif dstColumn == 'value':
                        if len(rawData.split()) == 1:
                            if rawData in ['Tokens', 'Low', 'Medium', 'High']:
                                value = None
                            else:
                                value = 1
                        else:
                            value = rawData.split()[0]

                    elif dstColumn == 'unit':
                        if len(rawData.split()) == 1:
                            value = rawData
                        else:
                            value = ' '.join(rawData.split()[1:])
                        
                    else:
                        value = rawData

#                    print ("krr: setvalue is " + str(dstColumn)+":"+str(srcColumn)+"=", value)
                    record.setValue(dstColumn, value)
#                    print('')
                    
# Obverse obverseimg
# Reverse reverseimg
# Edge edgeimg
#*Edge2
#*Edge3
#*Edge4
# Display photo1
# Display2 photo2
# Detail photo3
# Detail2 photo4
#*Detail3 
        tellicoImages = ['obverse', 'reverse',
                     'edge',
                     'display', 'display2'
                     'detail', 'detail2']

        ONimgFields = ['obverseimg', 'reverseimg', 'edgeimg',
                     'photo1', 'photo2', 'photo3', 'photo4']

        imageNo = 0
        for srcImg in tellicoImages:
            if row.find("./t:"+srcImg, namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                element = row.find("./t:"+srcImg, namespaces={'t': 'http://periapsis.org/tellico/'}).text[7:]
                if element:
                    image = QtGui.QImage()
                    image.load(element)
                    record.setValue(ONimgFields[imageNo], image)
                    imageNo = imageNo + 1

#krr        record.setValue('title', self.__generateTitle(record))

    def __generateTitle(self, record):
        title = ""
        if record.value('country'):
            title = title+"-"+str(record.value('country'))
        else:
            title = title+"-"
        if record.value('value') or record.value('unit'):
            title = title+"-"
            if record.value('value'):
                title = title+str(record.value('value'))
            if record.value('value') and record.value('unit'):
                title = title+"-"
            if record.value('unit'):
                title = title+str(record.value('unit'))
        else:
            title = title+"-"
        if record.value('type'):
            title = title+"-"+str(record.value('type'))
        else:
            title = title+"-"
        if record.value('year'):
            title = title+"-"+str(record.value('year'))
        else:
            title = title+"-"
        if record.value('mintmark'):
            title = title+"-"+str(record.value('mintmark'))
        else:
            title = title+"-"
        if record.value('variety'):
            title = title+"-"+str(record.value('variety'))
        return title
