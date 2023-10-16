# -*- coding: utf-8 -*-

import csv
import sys

from PySide6.QtCore import QStandardPaths

from OpenNumismat.Collection.Import import _Import
from OpenNumismat.Collection.Import.Excel import ImportExcel


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
            record.setValue('country', row[0])
            if ' ' in row[1]:
                value, unit = row[1].split(' ', 1)
            else:
                value = ''
                unit = row[1]
            if '.' in value:
                value = value.replace('.', '')
            record.setValue('value', value)
            record.setValue('unit', unit)
            year = row[2].split(' ', 1)[0]
            record.setValue('year', year)
            record.setValue('mintmark', row[3])
            record.setValue('subjectshort', row[5])
            record.setValue('grade', row[6])
            record.setValue('price3', row[7])
            record.setValue('catalognum1', row[8])
            record.setValue('features', row[9])
            record.setValue('payinfo', row[10])
        except IndexError:
            pass

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


class ImportUcoin2(ImportExcel):

    def defaultField(self, col, combo):
        res = 0

        if self.sheet.max_column == 12:  # Swap-List
            if col == 0:
                res = combo.findText(self.fields.country.title)
            elif col == 1:
                res = combo.findText(self.fields.unit.title)
            elif col == 2:
                res = combo.findText(self.fields.year.title)
            elif col == 3:
                res = combo.findText(self.fields.mintmark.title)
            elif col == 4:
                res = combo.findText(self.fields.subjectshort.title)
            elif col == 5:
                res = combo.findText(self.fields.grade.title)
            elif col == 6:
                res = combo.findText(self.fields.saleprice.title)
            elif col == 7:
                res = combo.findText(self.fields.quantity.title)
            elif col == 8:
                res = combo.findText(self.fields.catalognum1.title)
            elif col == 10:
                res = combo.findText(self.fields.features.title)
        elif self.sheet.max_column == 17:
            if col == 0:
                res = combo.findText(self.fields.country.title)
            elif col == 1:
                res = combo.findText(self.fields.unit.title)
            elif col == 2:
                res = combo.findText(self.fields.year.title)
            elif col == 3:
                res = combo.findText(self.fields.mintmark.title)
            elif col == 4:
                res = combo.findText(self.fields.subjectshort.title)
            elif col == 5:
                res = combo.findText(self.fields.grade.title)
            elif col == 6:
                res = combo.findText(self.fields.price3.title)
            elif col == 7:
                res = combo.findText(self.fields.catalognum1.title)
            elif col == 12:
                res = combo.findText(self.fields.paydate.title)
            elif col == 13:
                res = combo.findText(self.fields.payprice.title)
            elif col == 16:
                res = combo.findText(self.fields.features.title)
        else:
            if col == 0:
                res = combo.findText(self.fields.country.title)
            elif col == 1:
                res = combo.findText(self.fields.unit.title)
            elif col == 2:
                res = combo.findText(self.fields.year.title)
            elif col == 3:
                res = combo.findText(self.fields.mintmark.title)
            elif col == 4:
                res = combo.findText(self.fields.subjectshort.title)
            elif col == 5:
                res = combo.findText(self.fields.grade.title)
            elif col == 6:
                res = combo.findText(self.fields.price3.title)
            elif col == 7:
                res = combo.findText(self.fields.catalognum1.title)
            elif col == 9:
                res = combo.findText(self.fields.paydate.title)
            elif col == 11:
                res = combo.findText(self.fields.payprice.title)
            elif col == 14:
                res = combo.findText(self.fields.features.title)

        if res < 0:
            res = 0

        return res

    def defaultStatus(self):
        if self.sheet.max_column == 12:
            return 'sale'
        else:
            return 'owned'
