# -*- coding: utf-8 -*-

import os
import urllib.request

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QDialogButtonBox, QComboBox
from PyQt5.QtGui import QPixmap, QImage

from OpenNumismat.Collection.Import import _Import2
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat import version

available = True

try:
    import xlrd
except ImportError:
    print('xlrd module missed. Importing from Excel not available')
    available = False

try:
    from dateutil import parser
except ImportError:
    print('dateutil module missed. Importing from Excel not available')
    available = False


@storeDlgSizeDecorator
class TableDialog(QDialog):

    def __init__(self, parent, path, datemode):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.path = path
        self.datemode = datemode

        self.setWindowTitle(self.tr("Select columns"))

        self.hlayout = QHBoxLayout()

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        self.table = QTableWidget(self)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addLayout(self.hlayout)
        layout.addWidget(self.table)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def comboChanged(self, _index):
        labels = []
        for i in range(self.hlayout.count()):
            combo = self.hlayout.itemAt(i).widget()
            labels.append(combo.currentText())
        self.table.setHorizontalHeaderLabels(labels)

        for i in range(self.hlayout.count()):
            combo = self.hlayout.itemAt(i).widget()
            field = combo.currentData()
            if not field:
                continue

            if field.type == Type.Date:
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, i)
                    val = item.text()
                    try:
                        y, m, d, _h, _m, _s = xlrd.xldate_as_tuple(float(val),
                                                                   self.datemode)
                        date = "%d-%02d-%02d" % (y, m, d)
                        item.setText(date)
                    except ValueError:
                        pass
            elif field.type in Type.ImageTypes:
                for row in range(self.table.rowCount()):
                    item = self.table.item(row, i)
                    fileName = item.text()
                    image = QImage()
                    if fileName.startswith('http'):
                        try:
                            # Wikipedia require any header
                            req = urllib.request.Request(fileName,
                                    headers={'User-Agent': version.AppName})
                            data = urllib.request.urlopen(req).read()
                            result = image.loadFromData(data)
                            if result:
                                pixmap = QPixmap.fromImage(image)
                                item.setData(Qt.DecorationRole, pixmap)
                        except:
                            pass
                    else:
                        if not os.path.isabs(fileName):
                            fileName = os.path.join(self.path, fileName)

                        result = image.load(fileName)
                        if result:
                            pixmap = QPixmap.fromImage(image)
                            item.setData(Qt.DecorationRole, pixmap)


class ImportExcel(_Import2):

    def __init__(self, parent=None):
        super().__init__(parent)

    @staticmethod
    def isAvailable():
        return available

    def defaultField(self, col, _combo):
        if col < 10:
            return col + 1

        return 0

    def defaultStatus(self):
        return 'owned'

    def _connect(self, src):
        book = xlrd.open_workbook(src)
        self.datemode = book.datemode
        self.sheet = book.sheet_by_index(0)

        self.src_path = os.path.dirname(src)
        dialog = TableDialog(self.parent(), self.src_path, self.datemode)

        rows = self.sheet.nrows
        if rows > 10:
            rows = 10
        dialog.table.setRowCount(rows)
        dialog.table.setColumnCount(self.sheet.ncols)

        self.comboBoxes = []
        for col in range(self.sheet.ncols):
            combo = QComboBox()
            combo.addItem(self.tr("<Ignore>"))
            for f in self.fields.userFields:
                if f not in self.fields.systemFields:
                    combo.addItem(f.title, f)
            combo.setCurrentIndex(self.defaultField(col, combo))
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLength)
            combo.currentIndexChanged.connect(dialog.comboChanged)
            dialog.hlayout.addWidget(combo)

            self.comboBoxes.append(combo)
        dialog.comboChanged(0)

        for row in range(rows):
            for col in range(self.sheet.ncols):
                val = self.sheet.cell(row, col).value
                item = QTableWidgetItem(str(val))
                dialog.table.setItem(row, col, item)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.selected_fields = []
            self.has_title = False
            self.has_status = False
            for i in range(dialog.hlayout.count()):
                combo = dialog.hlayout.itemAt(i).widget()
                field = combo.currentData()
                self.selected_fields.append(field)

                if field:
                    if field.name == 'title':
                        self.has_title = True
                    elif field.name == 'status':
                        self.has_status = True

            return book

        return None

    def _getRowsCount(self, book):
        return self.sheet.nrows

    def _setRecord(self, record, row):
        for i, field in enumerate(self.selected_fields):
            if not field:
                continue

            val = self.sheet.cell(row, i).value
            if field.type == Type.Date:
                try:
                    y, m, d, _h, _m, _s = xlrd.xldate_as_tuple(float(val),
                                                               self.datemode)
                    val = "%d-%02d-%02d" % (y, m, d)
                except ValueError:
                    pass

                try:
                    val = parser.parse(val).date().isoformat()
                except ValueError:
                    val = None
            elif field.type in Type.ImageTypes:
                image = QImage()
                if val.startswith('http'):
                    try:
                        # Wikipedia require any header
                        req = urllib.request.Request(val,
                                headers={'User-Agent': version.AppName})
                        data = urllib.request.urlopen(req).read()
                        if image.loadFromData(data):
                            val = image
                        else:
                            val = None
                    except:
                        val = None
                else:
                    if os.path.isabs(val):
                        fileName = val
                    else:
                        fileName = os.path.join(self.src_path, val)

                    if image.load(fileName):
                        val = image
                    else:
                        val = None

            record.setValue(field.name, val)

        if not self.has_title:
            record.setValue('title', self.__generateTitle(record))

        if not self.has_status:
            record.setValue('status', self.defaultStatus())

    def __generateTitle(self, record):
        title = ""
        if record.value('country'):
            title += str(record.value('country')) + ' '
        if record.value('value'):
            title += str(record.value('value')) + ' '
        if record.value('unit'):
            title += str(record.value('unit')) + ' '
        if record.value('year'):
            title += str(record.value('year')) + ' '
        if record.value('subjectshort'):
            title += '(' + str(record.value('subjectshort')) + ') '

        return title.strip()
