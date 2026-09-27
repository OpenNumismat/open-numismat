import datetime
import openpyxl
import os

from dateutil import parser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QDialogButtonBox, QComboBox
from PySide6.QtGui import QPixmap, QImage, QPainter

from OpenNumismat.Collection.Import import _Import2, _InvalidDatabaseError
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CachedPoolManager import CachedPoolManager

IMAGE_CONNECTION_TIMEOUT = 30


@storeDlgSizeDecorator
class TableDialog(QDialog):

    def __init__(self, parent, path):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.http = CachedPoolManager(self)

        self.path = path

        self.setWindowTitle(self.tr("Select columns"))

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        self.table = QTableWidget(self)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def comboChanged(self, _index):
        for col in range(self.table.columnCount()):
            combo = self.table.cellWidget(0, col)
            if combo is None:
                continue

            field = combo.currentData()
            if not field:
                continue

            if field.type == Type.Date:
                for row in range(1, self.table.rowCount()):
                    item = self.table.item(row, col)
                    if item is None:
                        continue

                    val = item.text()
                    try:
                        val = parser.parse(val).date().isoformat()
                        item.setText(val)
                    except (ValueError, TypeError):
                        pass
            elif field.type in Type.ImageTypes:
                for row in range(1, self.table.rowCount()):
                    item = self.table.item(row, col)
                    if item is None:
                        continue

                    fileName = item.text()
                    image = QImage()
                    loaded = False
                    if fileName.startswith('http'):
                        data = self.http.get(fileName, timeout=IMAGE_CONNECTION_TIMEOUT)
                        if data:
                            loaded = image.loadFromData(data)
                    else:
                        if not os.path.isabs(fileName):
                            fileName = os.path.join(self.path, fileName)

                        if fileName:
                            loaded = image.load(fileName)

                    if not loaded and item.data(Qt.UserRole) is not None:
                        image = item.data(Qt.UserRole)
                        loaded = True

                    if loaded:
                        pixmap = QPixmap.fromImage(image)
                        item.setData(Qt.DecorationRole, pixmap)
                        item.setText('')


class ImportExcel(_Import2):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.http = CachedPoolManager(parent)

    @staticmethod
    def isAvailable():
        return True

    def defaultField(self, col, _combo):
        if col < 10:
            return col + 1

        return 0

    def defaultStatus(self):
        return 'owned'

    def _connect(self, src):
        try:
            book = openpyxl.load_workbook(src)
        except openpyxl.utils.exceptions.InvalidFileException as e:
            raise _InvalidDatabaseError(str(e))

        self.sheet = book.active

        MAX_COLUMN_COUNT = 50  # len(self.fields.fields)
        sheet_max_column = min(self.sheet.max_column, MAX_COLUMN_COUNT)

        self.images = {}
        for image in self.sheet._images:
            img = QImage()
            if img.loadFromData(image._data()):
                _from = image.anchor._from
                col = openpyxl.utils.get_column_letter(_from.col + 1)
                coordinate = f"{col}{_from.row + 1}"
                self.images[coordinate] = img

        self.src_path = os.path.dirname(src)
        dialog = TableDialog(self.parent(), self.src_path)

        rows = min(max(self.sheet.max_row - 1, 0), 10)

        dialog.table.setRowCount(rows + 1)
        dialog.table.setColumnCount(sheet_max_column)

        header_labels = []
        for col in range(sheet_max_column):
            title = self.sheet.cell(1, col + 1).value
            if title is None:
                title = ''
            elif isinstance(title, datetime.datetime):
                title = title.date().isoformat()
            elif isinstance(title, datetime.time):
                title = ''
            header_labels.append(str(title))

        dialog.table.setHorizontalHeaderLabels(header_labels)

        vertical_labels = ['']
        for row in range(1, rows + 1):
            vertical_labels.append(str(row))
        dialog.table.setVerticalHeaderLabels(vertical_labels)

        for row in range(rows):
            for col in range(sheet_max_column):
                cell = self.sheet.cell(row + 2, col + 1)
                val = cell.value

                if val is None:
                    val = ''
                elif isinstance(val, datetime.time):
                    val = ''
                elif isinstance(val, datetime.datetime):
                    val = val.date()
                if cell.hyperlink:
                    val = cell.hyperlink.target

                item = QTableWidgetItem(str(val))

                if cell.coordinate in self.images:
                    item.setData(Qt.UserRole, self.images[cell.coordinate])

                dialog.table.setItem(row + 1, col, item)

        self.comboBoxes = []
        for col in range(sheet_max_column):
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.lineEdit().setReadOnly(True)
            combo.lineEdit().setAlignment(Qt.AlignCenter)
            combo.addItem(self.tr("<Ignore>"))
            for f in self.fields.userFields:
                if f not in self.fields.systemFields:
                    combo.addItem(f.title, f)
            combo.setCurrentIndex(self.defaultField(col, combo))
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setStyleSheet("QComboBox { font-weight: 700; }")
            combo.currentIndexChanged.connect(dialog.comboChanged)
            dialog.table.setCellWidget(0, col, combo)

            self.comboBoxes.append(combo)
        dialog.comboChanged(0)

        result = dialog.exec()
        if result == QDialog.Accepted:
            self.selected_fields = []
            self.has_title = False
            self.has_status = False
            for i in range(dialog.table.columnCount()):
                combo = dialog.table.cellWidget(0, i)
                field = combo.currentData() if combo is not None else None
                self.selected_fields.append(field)

                if field:
                    if field.name == 'title':
                        self.has_title = True
                    elif field.name == 'status':
                        self.has_status = True

            return book

        return None

    def _getRowsCount(self, book):
        # Row 1 holds the headers, not a record
        return max(self.sheet.max_row - 1, 0)

    def _setRecord(self, record, row):
        for i, field in enumerate(self.selected_fields):
            if not field:
                continue

            cell = self.sheet.cell(row + 2, i + 1)
            val = cell.value
            if isinstance(val, datetime.time):
                val = ''
            elif isinstance(val, datetime.datetime):
                val = val.date()
            if isinstance(val, datetime.date):
                val = val.isoformat()
            if cell.hyperlink:
                val = cell.hyperlink.target

            if field.type == Type.Date:
                try:
                    val = parser.parse(val).date().isoformat()
                except (ValueError, TypeError):
                    val = None
            elif field.type in Type.ImageTypes:
                image = QImage()
                loaded = False
                if val:
                    if isinstance(val, str) and val.startswith('http'):
                        url = val
                        data = self.http.get(url, timeout=IMAGE_CONNECTION_TIMEOUT)
                        if data:
                            loaded = image.loadFromData(data)
                    elif isinstance(val, str):
                        if os.path.isabs(val):
                            fileName = val
                        else:
                            fileName = os.path.join(self.src_path, val)

                        loaded = image.load(fileName)

                if loaded:
                    val = self.__fixTransparentImage(image)
                elif cell.coordinate in self.images:
                    val = self.__fixTransparentImage(self.images[cell.coordinate])
                else:
                    val = None

            record.setValue(field.name, val)

        if not self.has_title:
            record.setValue('title', self.__generateTitle(record))

        if not self.has_status:
            record.setValue('status', self.defaultStatus())

    def __fixTransparentImage(self, image):
        if image.hasAlphaChannel() and not Settings()['transparent_store']:
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
