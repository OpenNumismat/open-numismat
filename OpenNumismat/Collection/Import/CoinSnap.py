# -*- coding: utf-8 -*-

import csv
import sys
import urllib.request
import urllib3

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QMessageBox

from OpenNumismat.Collection.Import import _Import
from OpenNumismat.Settings import Settings
from OpenNumismat import version

CONNECTION_TIMEOUT = 30


class ImportCoinSnap(_Import):
    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def isAvailable():
        return True

    @staticmethod
    def defaultDir():
        dirs = QStandardPaths.standardLocations(QStandardPaths.DownloadLocation)
        if dirs:
            return dirs[0]
        else:
            return ''

    def _connect(self, src):
        urllib3.disable_warnings()
        timeout = urllib3.Timeout(connect=CONNECTION_TIMEOUT / 2,
                                  read=CONNECTION_TIMEOUT)
        self.http = urllib3.PoolManager(num_pools=1,
                                        headers={'User-Agent': version.AppName},
                                        timeout=timeout,
                                        cert_reqs="CERT_NONE")

        return src

    def _getRows(self, srcFile):
        maxInt = sys.maxsize
        while True:
            # decrease the maxInt value by factor 10
            # as long as the OverflowError occurs.
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = maxInt // 10

        rows = []
        with open(srcFile, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = True
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    rows.append(row)

        return rows

    def _setRecord(self, record, row):
        record.setValue('status', 'owned')
        try:
            record.setValue('country', row[1])
            if ' ' in row[2]:
                value, unit = row[2].split(' ', 1)
            else:
                value = ''
                unit = row[2]
#            if '.' in value:
#                value = value.replace('.', '')
            record.setValue('value', value)
            record.setValue('unit', unit)
            record.setValue('year', row[3])
            mintmark = row[4]
            if mintmark in (self.tr("No mint mark"), "No mint mark", "Sem marca da casa da moeda"):
                mintmark = None
            record.setValue('mintmark', mintmark)
            subjectshort = row[5]
            if subjectshort in (self.tr("Common series"), "Common series", "Séries comuns"):
                subjectshort = None
            record.setValue('subjectshort', subjectshort)
            record.setValue('price3', row[6])
            record.setValue('catalognum1', row[7])
            record.setValue('payprice', row[8])
            record.setValue('features', row[10])

            record.setValue('obverseimg', self.__getImage(row[11]))
            record.setValue('reverseimg', self.__getImage(row[12]))
        except IndexError:
            pass

        record.setValue('title', self.__generateTitle(record))

    def __getImage(self, url):
        if url:
            try:
                resp = self.http.request("GET", url)
                data = resp.data
            except urllib3.exceptions.MaxRetryError:
                QMessageBox.warning(self.parent(), "CoinSnap",
                                    self.tr("CoinSnap not response"))
                return None
            except:
                return None

            image = QImage()
            if image.loadFromData(data):
                return self.__fixTransparentImage(image)

        return None

    def __fixTransparentImage(self, image):
        if image.hasAlphaChannel():
            # Fill transparent color if present
            color = Settings()['transparent_color']
            fixedImage = QImage(image.size(), QImage.Format_RGB32)
            fixedImage.fill(color)
            painter = QPainter(fixedImage)
            painter.drawImage(0, 0, image)
            painter.end()
        else:
            fixedImage = image

        return fixedImage

    def __generateTitle(self, record):
        title = ""
        if record.value('country'):
            title += record.value('country') + ' '
        if record.value('value'):
            title += record.value('value') + ' '
        if record.value('unit'):
            title += record.value('unit') + ' '
        if record.value('year'):
            title += record.value('year') + ' '
        if record.value('subjectshort'):
            title += '(' + record.value('subjectshort') + ') '
        if record.value('variety'):
            title += '/' + record.value('variety') + '/'

        return title.strip()
