# -*- coding: utf-8 -*-

#############################################
#
# for the Open Numismat project
#
# Contributed by Kurt R. Rahlfs
# kurtRR (at) affinityCM (dot) com
# Gnu public license V3
#
#############################################

import pdb
from  PyQt5.QtCore import pyqtRemoveInputHook

import os
import zipfile
import urllib
from OpenNumismat.Settings import Settings
from pytz import timezone
import pytz, datetime

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
    srcDB = ''
    unzippedName = ''
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
        'defect': 'defects',
        'id': 'id',              #this filled in only when DB is empty
        'createdat': 'cdate',    #this filled in only when DB is empty
        'updatedat': 'mdate',    #this filled in only when DB is empty
    }

    def __init__(self, parent=None):
        super(ImportTellico, self).__init__(parent)
        
        self.settings = Settings()

    @staticmethod
    def isAvailable():
        return available

    def _connect(self, src):
        self.srcDB = src # initally assume a .xml file
        if src[-3:] == '.tc':  #if a .tc file we need to unzip to /tmp
            zf = zipfile.ZipFile(self.srcDB)
            zName = zf.namelist()[0]
            self.unzippedName = "/tmp/" + zName
            targetF = open(self.unzippedName, 'wb')
            targetF.write(zf.read(zName))
            targetF.flush()
            targetF.close()
            return self.unzippedName
        return self.srcDB

    def _getRows(self, srcFile):
        tree = lxml.etree.parse(srcFile)
        rows = tree.xpath("/t:tellico/t:collection/t:entry", namespaces={'t': 'http://periapsis.org/tellico/'})
        if self.unzippedName:
            os.remove(self.unzippedName)
        return rows
        
    def _setRecord(self, record, row):
        for dstColumn, srcColumn in self.Columns.items():
          #
          # assumed field values
          #
          if dstColumn == 'shape':
              value = 'Circle' #good for most modern coins
              record.setValue(dstColumn, value)
          elif dstColumn == 'obvrev':
              value = 'Coin' # good for US coins
              record.setValue(dstColumn, value)
          if srcColumn is not None:

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

                if value == 'owned':
                    #I have it but am I selling it?
                    if row.find("./t:sell", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                        if (row.find("./t:sell", namespaces={'t': 'http://periapsis.org/tellico/'}).text) == "true":
                            value = 'sale'
                    # I have/had it.  Was it sold?
                    # the status can 'sold' wether or not sell was set. so don't use an elif below
                    if row.find("./t:sold", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                        rawData = row.find("./t:sold", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                        value = 'sold'

                record.setValue(dstColumn, value)
            ############################
            #
            # single souce processing
            #
            ############################
            elif srcColumn and row.find("t:"+srcColumn, namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                rawData = row.find("t:"+srcColumn, namespaces={'t': 'http://periapsis.org/tellico/'}).text

                ############################
                #
                # has child nodes
                #
                ############################
                if srcColumn == 'countrys':
                    value = row.find("./t:countrys/t:country", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                    record.setValue(dstColumn, value)

#                elif self.settings['id_dates'] and srcColumn in ['cdate', 'mdate']:
                elif srcColumn in ['cdate', 'mdate']:
                    #extract date elements from xml    
                    tsYear = int(row.find("./t:"+srcColumn+"/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                    tsMonth = int(row.find("./t:"+srcColumn+"/t:month", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                    tsDay = int(row.find("./t:"+srcColumn+"/t:day", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                    recordedDate = '{:04}{:02}{:02}'.format(tsYear, tsMonth, tsDay)
                    myTZ = "America/Chicago"  #krr:todo: prompt for this
                    local = pytz.timezone(myTZ)
                    naive = datetime.datetime.strptime(recordedDate, "%Y%m%d")
                    local_dt = local.localize(naive)
                    utc_dt = local_dt.astimezone (pytz.utc)
                    record.setValue(dstColumn, str(utc_dt))
                elif rawData:
                    ############################
                    #
                    # correction to sources w/o parent
                    #
                    ############################

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

                    record.setValue(dstColumn, value)
                    
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

        image3Suffixes = ['.png','.jpg', '.bmp']  #krr:todo: .gif hangs
        image4Suffixes = ['.jpeg', '.tiff']
        imageNo = 0
        for srcImg in tellicoImages:
            if row.find("./t:"+srcImg, namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                element = row.find("./t:"+srcImg, namespaces={'t': 'http://periapsis.org/tellico/'}).text
                if element:
                    element = urllib.parse.unquote(element)
                    image = QtGui.QImage()
                    if element[:7] == 'file://':
                        if self.settings['image_name']:
                            image = element
                        else:
                            image.load(element[7:])
                    elif element[-4:] in image3Suffixes or element[-5:] in image4Suffixes:
                        if self.unzippedName: #was unzipped so is a .tc file
                            imagePath = "file://" + self.srcDB[:-3] + "_files" + "/" + element
                        else: #rm .xml
                            imagePath = "file://" + self.srcDB[:-4] + "_files" + "/" + element
                        if not os.path.exists(imagePath[7:]): #if not in sub dir look in same dir as .tc or .xml
                            imagePath = "file://" + os.path.dirname(self.srcDB) + "/" + element
                        if self.settings['image_name']:
                            image = imagePath
                        else:
                            image.load(imagePath[7:])
                    else:
                        image.loadImageData(element)

                    record.setValue(ONimgFields[imageNo], image)
                    
                    imageNo = imageNo + 1
