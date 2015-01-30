# -*- coding: utf-8 -*-

import csv
import sys

from PyQt5.QtCore import QStandardPaths

from OpenNumismat.Collection.Import import _Import


class ImportUcoin(_Import):
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
        return src

    def _getRows(self, srcFile):
        csv.field_size_limit(sys.maxsize)

        rows = []
        with open(srcFile, 'r', encoding='utf-8') as f:
            first_line = True
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                if first_line:
                    first_line = False
                else:
                    rows.append(row)

        return rows

    def _setRecord(self, record, row):
        record.setValue('country', row[0])
        value, unit = row[1].split(' ', 1)
        record.setValue('value', value)
        record.setValue('unit', unit)
        record.setValue('year', row[2])
        record.setValue('subjectshort', row[3])
        record.setValue('variety', row[4])
        record.setValue('grade', row[5])
        record.setValue('payprice', row[6])
        record.setValue('features', row[7])
        record.setValue('status', 'owned')
        record.setValue('status', 'owned')

        record.setValue('title', self.__generateTitle(record))

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
