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
from OpenNumismat.Settings import Settings, BaseSettings

from pytz import timezone
import pytz, datetime
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QVBoxLayout, QGridLayout, QCheckBox, QMessageBox

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
        'period': 'countrymodififier',
        'dateemis': 'rangestart',
        'mint': None,
        'mintmark': 'mintmark',
        'issuedate': None,
        'type': 'type',
        'series': None,
        'subjectshort': None,
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
        'seller': 'dealer',
        'payplace': None,
        'payinfo': None,
        'saledate': 'sold',
        'saleprice': 'price',
        'totalsaleprice': 'price',
        'buyer': 'client',
        'saleplace': None,
        'saleinfo': None,
        'note': None,
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
        'features': 'comments',
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

        #if id_dates set then convert recorded times to UTC
        if self.settings['id_dates']: #krr:todo: gotta be a better way
            self.myTZ = TZprompt.getTZ()


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
        #put these fields is ON's note field
        featuresFields = [ 'replica', 'set', 'security', 'gradenote', 'grader', 'gradecasual', 'Authenticator', 'obversesample', 'reversesample', 'edgesample', 'displaysample', 'display2sample', 'detailsample', 'detail2sample', 'detail3', 'detail3sample', 'valuedate', 'valuesource', 'gift', 'conserved', 'restricted', 'currency', 'ebay', 'atributor', 'needsupdate', 'yearalt', 'soldfor' ]

        for dstColumn, srcColumn in self.Columns.items():
            #
            # assumed field values
            #
            if dstColumn == 'shape':
                if row.find("./t:currency", namespaces={'t': 'http://periapsis.org/tellico/'}) is None:
                    value = 'Round' #good for most coins
                else:
                    value = None
                record.setValue(dstColumn, value)
            elif dstColumn == 'obvrev':
                if row.find("./t:currency", namespaces={'t': 'http://periapsis.org/tellico/'}) is None:
                    value = 'Coin (180' + u'\u00b0' + ')' # good for US coins +
                else:
                    value = None
                record.setValue(dstColumn, value)
                    
            if srcColumn is not None:

            #############################
            #
            # multiple source processing
            #
            #############################
                #
                # Emission of production
                #
                if dstColumn == 'dateemis':
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
                # save comments and other fields
                #
                ############################
                elif dstColumn == 'features':
                    if row.find("t:"+'comments', namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                        value = row.find("t:"+'comments', namespaces={'t': 'http://periapsis.org/tellico/'}).text
                        value = value + '\nADDITIONAL FIELDS:\n'
                    else:
                        value = ''
                    for featuresAdd in featuresFields:
                        if row.find("./t:" + featuresAdd, namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                            value2 = row.find("./t:" + featuresAdd, namespaces={'t': 'http://periapsis.org/tellico/'}).text
                            value = value + featuresAdd + "=" + value2 + ';\n'
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

                    elif srcColumn in ['cdate', 'mdate']:
                        #extract date elements from xml
                        tsYear = int(row.find("./t:"+srcColumn+"/t:year", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                        tsMonth = int(row.find("./t:"+srcColumn+"/t:month", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                        tsDay = int(row.find("./t:"+srcColumn+"/t:day", namespaces={'t': 'http://periapsis.org/tellico/'}).text)
                        recordedDate = '{:04}{:02}{:02}'.format(tsYear, tsMonth, tsDay)

                        #if id_dates set then convert recorded times to UTC
                        if self.settings['id_dates']: #krr:todo: gotta be a better way
                            #convert local time in Tellico to UTC
                            localT = pytz.timezone(self.myTZ)
                            naive = datetime.datetime.strptime(recordedDate, "%Y%m%d")
                            local_dt = localT.localize(naive)
                            utc_dt = local_dt.astimezone (pytz.utc)

                            #Convert ISODate to QDate
                            [tsCal, tsTimeSpec] = str(utc_dt).split()
                            [tsYear, tsMonth, tsDay] = tsCal.split('-')
                            [tsTime, tsOffset] = tsTimeSpec.split('+')
                            [tsHour, tsMin, tsSec] = tsTime.split(':')
                            UTCDate = QtCore.QDateTime.fromString(tsYear + tsMonth + tsDay + tsHour + tsMin + tsSec, 'yyyyMMddHHmmss')

                            record.setValue(dstColumn,
                                            UTCDate.toString(Qt.ISODate))

                    elif rawData:
                        ############################
                        #
                        # correction to sources w/o parent
                        #
                        ############################

                        #
                        # year
                        #
                        if srcColumn == 'Year':
                            if rawData == '00-00-00':
                                value = None
                            else:
                                if row.find("./t:bc", namespaces={'t': 'http://periapsis.org/tellico/'}).text:
                                    value = 0 - int(rawData)
                        #
                        # quantity
                        #
                        elif srcColumn == 'quantity':
                            if rawData == '0':
                                value = None
                            else:
                                value = rawData
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

                        elif dstColumn == 'defect':
                            if row.find("./t:error", namespaces={'t': 'http://periapsis.org/tellico/'}) is not None:
                                rawData2 = row.find("./t:error", namespaces={'t': 'http://periapsis.org/tellico/'}).text                            
                                value = rawData + 'error=' + rawData2
                        elif dstColumn == 'mintage':
                            if rawData == '':
                                value == row.find("./t:proofs", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                            else:
                                if row.find("./t:X10e", namespaces={'t': 'http://periapsis.org/tellico/'}):
                                    rawData2 = row.find("./t:X10e", namespaces={'t': 'http://periapsis.org/tellico/'}).text
                                    value = longint(rawData) * int(rawData2) * 10
                                else:
                                    value = rawData
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

        image3Suffixes = ['.png','.jpg', '.bmp', '.gif']
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

class TZprompt(QDialog):
    def __init__(self, parent=None):
        super(TZprompt, self).__init__(parent)

        #self.idDates = QCheckBox("Import ID and created/modified dates")

        promptLabel = QLabel("Time Zone in which the Tellico data was entered:")

        self.zoneName = QComboBox(self)
        current = -1
        self.suppliedTZ = 'America/Chicago'
        for i, zone in enumerate (pytz.common_timezones):
            self.zoneName.addItem(zone, i)
            if self.suppliedTZ == zone:
                current = i
        self.zoneName.setCurrentIndex(current)

        self.submitButton = QPushButton("Submit")
        self.submitButton.isDefault()


        buttonLayout1 = QVBoxLayout()
        #buttonLayout1.addWidget(self.idDates)
        buttonLayout1.addWidget(promptLabel)
        buttonLayout1.addWidget(self.zoneName)
        buttonLayout1.addWidget(self.submitButton)

        self.submitButton.clicked.connect(self.TZsubmitted)

        mainLayout = QGridLayout()
        mainLayout.addLayout(buttonLayout1, 0, 1)

        self.setLayout(mainLayout)
        self.setWindowTitle("Time Zone")

    def TZsubmitted(self):
        self.suppliedTZ = self.zoneName.currentText()
        QDialog.accept(self)

    @staticmethod
    def getTZ(parent = None):
        TZdialog = TZprompt(parent)
        result = TZdialog.exec_()

        if result == QDialog.Accepted:
            return TZdialog.suppliedTZ

        return 'UTC'
