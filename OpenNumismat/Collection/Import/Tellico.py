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

import os
import shutil
import tempfile
import urllib
import zipfile

from PyQt6 import QtGui

from OpenNumismat.Collection.Import import _Import
from OpenNumismat.Tools.Converters import stringToMoney


available = True

try:
    import lxml.etree
except ImportError:
    print('lxml module missed. Importing from Tellico not available')
    available = False

NAMESPACES = {'t': 'http://periapsis.org/tellico/'}

class ImportTellico(_Import):
    Columns = {
        'title': 'title',
        'value': 'denomination',  # multiples of the units: for this denomination
        'unit': 'denomination',  # the units part: for this denomination
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
        'catalognum1': 'km',
        'catalognum2': 'y',
        'catalognum3': 'pcgs',
        'catalognum4': None,
        'rarity': None,
        'price1': None,  # Fine
        'price2': None,  # VF
        'price3': None,  # XF
        'price4': 'value',  # Unc
        'variety': 'variety',
        'paydate': 'pur_date',
        'payprice': 'pur_price',
        'totalpayprice': 'pur_price',
        'saller': 'dealer',
        'payplace': None,
        'payinfo': None,
        'saledate': 'sold',
        'saleprice': 'price',
        'totalsaleprice': 'price',
        'buyer': 'client',
        'saleplace': None,
        'saleinfo': None,
        'note': None,
        'obverseimg': None,  # obverse
        'obversedesign': None,
        'obversedesigner': None,
        'reverseimg': None,  # reverse
        'reversedesign': None,
        'reversedesigner': None,
        'edgeimg': None,  # edge
        'subject': None,
        'photo1': None,  # display
        'photo2': None,  # display2
        'photo3': None,  # detail
        'photo4': None,  # detail2
        'storage': 'location',
        'features': 'comments',
        'quantity': 'quantity',
        'url': None,
        'barcode': 'certification',
        'defect': 'defects',
    }

    def __init__(self, parent=None):
        super(ImportTellico, self).__init__(parent)

    @staticmethod
    def isAvailable():
        return available

    def _connect(self, src):
        self.unzippedDir = tempfile.mkdtemp(prefix='Tellico')

        zf = zipfile.ZipFile(src)
        zf.extractall(self.unzippedDir)

        return self.unzippedDir

    def _check(self, unzippedDir):
        return os.path.isfile(os.path.join(unzippedDir, 'tellico.xml'))

    def _close(self, unzippedDir):
        shutil.rmtree(unzippedDir, True)

    def _getRows(self, unzippedDir):
        tree = lxml.etree.parse(os.path.join(unzippedDir, 'tellico.xml'))
        rows = tree.xpath("/t:tellico/t:collection/t:entry", namespaces=NAMESPACES)
        return rows

    def _setRecord(self, record, row):
        # put these fields is ON's note field
        featuresFields = ['replica', 'set', 'security', 'gradenote', 'grader', 'gradecasual', 'Authenticator', 'obversesample', 'reversesample', 'edgesample', 'displaysample', 'display2sample', 'detailsample', 'detail2sample', 'detail3', 'detail3sample', 'valuedate', 'valuesource', 'gift', 'conserved', 'restricted', 'currency', 'ebay', 'atributor', 'needsupdate', 'yearalt', 'soldfor']

        for dstColumn, srcColumn in self.Columns.items():
            #
            # assumed field values
            #
            if dstColumn == 'shape':
                if row.find("./t:currency", namespaces=NAMESPACES) is None:
                    value = 'Round'  # good for most coins
                else:
                    value = None
                record.setValue(dstColumn, value)
            elif dstColumn == 'obvrev':
                if row.find("./t:currency", namespaces=NAMESPACES) is None:
                    value = 'Coin (180' + u'\u00b0' + ')'  # good for US coins +
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
                    if row.find("./t:rangestart/t:year", namespaces=NAMESPACES) is not None:
                        value1 = row.find("./t:rangestart/t:year", namespaces=NAMESPACES).text
                    else:
                        value1 = '~'

                    if row.find("./t:rangeend/t:year", namespaces=NAMESPACES) is not None:
                        value2 = row.find("./t:rangeend/t:year", namespaces=NAMESPACES).text
                    else:
                        value2 = '~'

                    if value1 != '~' or value2 != '~':
                        record.setValue(dstColumn, value1+"-"+value2)
                #
                # status of coin
                #
                elif dstColumn == 'status':
                    if row.find("./t:want", namespaces=NAMESPACES) is not None:
                        if (row.find("./t:want", namespaces=NAMESPACES).text) == "true":
                            value = 'wish'
                        else:
                            value = 'owned'
                    else:
                        value = 'owned'

                    if value == 'owned':
                        # I have it but am I selling it?
                        if row.find("./t:sell", namespaces=NAMESPACES) is not None:
                            if (row.find("./t:sell", namespaces=NAMESPACES).text) == "true":
                                value = 'sale'
                        # I have/had it.  Was it sold?
                        # the status can 'sold' wether or not sell was set. so don't use an elif below
                        if row.find("./t:sold", namespaces=NAMESPACES) is not None:
                            rawData = row.find("./t:sold", namespaces=NAMESPACES).text
                            value = 'sold'
                    record.setValue(dstColumn, value)
                ############################
                #
                # save comments and other fields
                #
                ############################
                elif dstColumn == 'features':
                    if row.find("t:"+'comments', namespaces=NAMESPACES) is not None:
                        value = row.find("t:"+'comments', namespaces=NAMESPACES).text
                        value = value + '\nADDITIONAL FIELDS:\n'
                    else:
                        value = ''
                    for featuresAdd in featuresFields:
                        if row.find("./t:" + featuresAdd, namespaces=NAMESPACES) is not None:
                            value2 = row.find("./t:" + featuresAdd, namespaces=NAMESPACES).text
                            value = value + featuresAdd + "=" + value2 + ';\n'
                    record.setValue(dstColumn, value)
                ############################
                #
                # single souce processing
                #
                ############################
                elif srcColumn and row.find("t:"+srcColumn, namespaces=NAMESPACES) is not None:
                    rawData = row.find("t:"+srcColumn, namespaces=NAMESPACES).text

                    ############################
                    #
                    # has child nodes
                    #
                    ############################
                    if srcColumn == 'countrys':
                        value = row.find("./t:countrys/t:country", namespaces=NAMESPACES).text
                        record.setValue(dstColumn, value)

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
                                if row.find("./t:bc", namespaces=NAMESPACES).text:
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
                        elif srcColumn in ['cost', 'price', 'value']:
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
                            if row.find("./t:error", namespaces=NAMESPACES) is not None:
                                rawData2 = row.find("./t:error", namespaces=NAMESPACES).text                            
                                value = rawData + 'error=' + rawData2
                        elif dstColumn == 'mintage':
                            if rawData == '':
                                value = row.find("./t:proofs", namespaces=NAMESPACES).text
                            else:
                                if row.find("./t:X10e", namespaces=NAMESPACES):
                                    rawData2 = row.find("./t:X10e", namespaces=NAMESPACES).text
                                    value = int(rawData) * int(rawData2) * 10
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

        imageSuffixes = ['.png', '.jpg', '.bmp', '.gif', '.jpeg', '.tiff']
        imageNo = 0
        for srcImg in tellicoImages:
            if row.find("./t:"+srcImg, namespaces=NAMESPACES) is not None:
                element = row.find("./t:"+srcImg, namespaces=NAMESPACES).text
                if element:
                    element = urllib.parse.unquote(element)
                    extension = os.path.splitext(element)[1]
                    image = QtGui.QImage()
                    if element[:7] == 'file://':
                        image.load(element[7:])
                    elif extension in imageSuffixes:
                        imagePath = os.path.join(self.unzippedDir, 'images', element)

                        if not os.path.exists(imagePath):  # if not in sub dir look in same dir as .tc
                            imagePath = os.path.join(self.unzippedDir, element)

                        image.load(imagePath)
                    else:
                        image.loadImageData(element)

                    record.setValue(ONimgFields[imageNo], image)

                imageNo = imageNo + 1
