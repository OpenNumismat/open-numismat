from typing import Optional
import datetime
import openpyxl
import os

from dateutil import parser

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QDialogButtonBox, QComboBox, QCheckBox
from PySide6.QtGui import QPixmap, QImage, QPainter

from OpenNumismat.Collection.Import import _Import2, _InvalidDatabaseError
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Collection.CollectionFields import CollectionFieldsBase, FieldTypes as Type
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CachedPoolManager import CachedPoolManager

IMAGE_CONNECTION_TIMEOUT = 30
IMAGE_PREVIEW_SIZE = 64
IMAGE_SOURCE_ROLE = Qt.UserRole + 1
IMAGE_PREVIEW_ROLE = Qt.UserRole + 2


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

        self.headerCheckBox = QCheckBox(self.tr("First row is header (column names)"))
        self.headerCheckBox.setChecked(True)

        layout = QVBoxLayout()
        layout.addWidget(self.headerCheckBox)
        layout.addWidget(self.table)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def comboChanged(self, _index):
        self._resetRowHeights()

        for col in range(self.table.columnCount()):
            combo = self.table.cellWidget(0, col)
            if combo is not None:
                self._updateColumnPreview(col, combo.currentData())

    def _resetRowHeights(self):
        for row in range(1, self.table.rowCount()):
            self.table.setRowHeight(
                row, self.table.verticalHeader().defaultSectionSize())

    def _updateColumnPreview(self, col, field):
        image_field = field is not None and field.type in Type.ImageTypes
        if image_field:
            self.table.setColumnWidth(
                col, max(self.table.columnWidth(col), IMAGE_PREVIEW_SIZE + 8))

        for row in range(1, self.table.rowCount()):
            item = self.table.item(row, col)
            if item is not None:
                self._updateItemPreview(row, item, field, image_field)

    def _updateItemPreview(self, row, item, field, image_field):
        source_text = item.data(IMAGE_SOURCE_ROLE)
        if source_text is None:
            source_text = item.text()
        item.setData(Qt.DecorationRole, None)
        item.setText(source_text)

        if field is not None and field.type == Type.Date:
            try:
                item.setText(parser.parse(source_text).date().isoformat())
            except (ValueError, TypeError):
                pass

        image = item.data(Qt.UserRole)
        loaded = image is not None and not image.isNull()
        if not loaded and image_field:
            image = self._loadImagePreview(item, source_text)
            loaded = not image.isNull()

        if loaded:
            self._showImagePreview(row, item, image)

    def _loadImagePreview(self, item, source_text):
        image = item.data(IMAGE_PREVIEW_ROLE)
        if image is not None:
            return image

        image = QImage()
        fileName = str(source_text)
        if fileName.startswith('http'):
            data = self.http.get(fileName, timeout=IMAGE_CONNECTION_TIMEOUT)
            if data:
                image.loadFromData(data)
        else:
            if not os.path.isabs(fileName):
                fileName = os.path.join(self.path, fileName)

            if fileName:
                image.load(fileName)

        item.setData(IMAGE_PREVIEW_ROLE, image)
        return image

    def _showImagePreview(self, row, item, image):
        self.table.setRowHeight(row, IMAGE_PREVIEW_SIZE + 8)
        preview = image.scaled(
            QSize(IMAGE_PREVIEW_SIZE, IMAGE_PREVIEW_SIZE),
            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        item.setData(Qt.DecorationRole, QPixmap.fromImage(preview))
        item.setText('')


class ImportExcel(_Import2):
    sheet: Optional[openpyxl.worksheet.worksheet.Worksheet]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.http = CachedPoolManager(parent)
        self.sheet = None
        self.sheetImages = {}
        self.images = {}
        self.allSheetImagesIndexed = False
        self.has_header = True
        self.export_fields = []
        self.export_headers = []

    @staticmethod
    def isAvailable():
        return True

    def defaultField(self, col, combo, has_header=True):
        if not has_header:
            # No header row to match, map first columns to first fields
            if col < 10:
                return col + 1
            return 0

        title = self.sheet.cell(1, col + 1).value
        if title is None:
            return 0
        if isinstance(title, datetime.datetime):
            title = title.date().isoformat()
        elif isinstance(title, datetime.time):
            title = ''

        title = str(title)
        if not title:
            return 0

        matches = [index for index in range(1, combo.count())
                   if combo.itemText(index) == title]
        return matches[0] if len(matches) == 1 else 0

    def defaultStatus(self):
        return 'owned'

    @staticmethod
    def _getSheetImages(sheet, max_row=None):
        """Index embedded images without decoding them; openpyxl exposes them privately."""
        images = {}
        for image in sheet._images:
            anchor = image.anchor._from
            if max_row is not None and anchor.row + 1 > max_row:
                continue
            coordinate = sheet.cell(
                row=anchor.row + 1, column=anchor.col + 1).coordinate
            images[coordinate] = image
        return images

    def _getEmbeddedImage(self, coordinate, include_all=False):
        if coordinate in self.images:
            return self.images[coordinate]

        source = self.sheetImages.get(coordinate)
        if source is None and include_all and not self.allSheetImagesIndexed:
            self.sheetImages = self._getSheetImages(self.sheet)
            self.allSheetImagesIndexed = True
            source = self.sheetImages.get(coordinate)

        if source is None:
            return None

        image = QImage()
        try:
            data = source._data()
        except (ValueError, OSError):
            # openpyxl closes the image stream after the first read
            data = None
        if data and image.loadFromData(data):
            self.images[coordinate] = image
            return image

        self.images[coordinate] = None
        return None

    def _connect(self, src):
        try:
            book = openpyxl.load_workbook(src)
        except openpyxl.utils.exceptions.InvalidFileException as e:
            raise _InvalidDatabaseError(str(e))

        self.sheet = book.active

        # Keep the import mapping in sync with Collection.exportToExcel, which
        # exports all fields except internal fields and the preview image.
        exported_fields = [field for field in CollectionFieldsBase()
                           if field.name not in ('id', 'createdat', 'updatedat', 'sort_id')
                           and field.type != Type.PreviewImage]
        self.export_fields = [self.fields.field(field.id) for field in exported_fields]
        self.export_headers = [field.title for field in exported_fields]
        MAX_COLUMN_COUNT = len(self.export_fields)
        self.sheet_max_column = min(self.sheet.max_column, MAX_COLUMN_COUNT)

        self.sheetImages = {}
        self.images = {}
        self.allSheetImagesIndexed = False

        self.src_path = os.path.dirname(src)
        dialog = TableDialog(self.parent(), self.src_path)

        dialog.table.setRowCount(1)
        dialog.table.setColumnCount(self.sheet_max_column)

        self.comboBoxes = []
        for col in range(self.sheet_max_column):
            combo = QComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.lineEdit().setReadOnly(True)
            combo.lineEdit().setAlignment(Qt.AlignCenter)
            combo.addItem(self.tr("<Ignore>"))
            for f in self.export_fields:
                combo.addItem(f.title, f)
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setStyleSheet("QComboBox { font-weight: 700; }")
            combo.currentIndexChanged.connect(dialog.comboChanged)
            dialog.table.setCellWidget(0, col, combo)

            self.comboBoxes.append(combo)

        dialog.headerCheckBox.toggled.connect(
            lambda checked: self._fillPreview(dialog, checked))
        self._fillPreview(dialog, dialog.headerCheckBox.isChecked())

        result = dialog.exec()
        if result == QDialog.Accepted:
            self.has_header = dialog.headerCheckBox.isChecked()
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

        self.sheet = None
        self.sheetImages.clear()
        self.images.clear()
        return None

    def _fillPreview(self, dialog, has_header):
        rows = self._getPreviewRowCount(has_header)

        self.sheetImages = self._getSheetImages(
            self.sheet, max_row=rows + (1 if has_header else 0))
        # Keep decoded self.images cache: coordinates don't change on mode
        # switch and openpyxl image streams can be read only once
        self.allSheetImagesIndexed = False

        dialog.table.setRowCount(rows + 1)
        self._setPreviewHeaders(dialog, rows, has_header)
        self._fillPreviewRows(dialog.table, rows, has_header)
        self._setDefaultFieldSelections(has_header)
        dialog.comboChanged(0)

    def _getPreviewRowCount(self, has_header):
        data_rows = self.sheet.max_row - (1 if has_header else 0)
        return min(max(data_rows, 0), 10)

    def _setPreviewHeaders(self, dialog, rows, has_header):
        if has_header:
            header_labels = []
            for col in range(self.sheet_max_column):
                title = self.sheet.cell(1, col + 1).value
                if title is None:
                    title = ''
                elif isinstance(title, datetime.datetime):
                    title = title.date().isoformat()
                elif isinstance(title, datetime.time):
                    title = ''
                header_labels.append(str(title))
        else:
            # No header row, just number the columns
            header_labels = [str(col + 1) for col in range(self.sheet_max_column)]

        dialog.table.setHorizontalHeaderLabels(header_labels)

        vertical_labels = ['']
        for row in range(1, rows + 1):
            vertical_labels.append(str(row))
        dialog.table.setVerticalHeaderLabels(vertical_labels)

    def _fillPreviewRows(self, table, rows, has_header):
        for row in range(rows):
            for col in range(self.sheet_max_column):
                cell = self.sheet.cell(row + (2 if has_header else 1), col + 1)
                table.setItem(row + 1, col, self._makePreviewItem(cell))

    def _makePreviewItem(self, cell):
        value = cell.value
        if value is None or isinstance(value, datetime.time):
            value = ''
        elif isinstance(value, datetime.datetime):
            value = value.date()
        if cell.hyperlink:
            value = cell.hyperlink.target

        item = QTableWidgetItem(str(value))
        item.setData(IMAGE_SOURCE_ROLE, str(value))

        image = self._getEmbeddedImage(cell.coordinate)
        if image is not None:
            item.setData(Qt.UserRole, image)
        return item

    def _setDefaultFieldSelections(self, has_header):
        is_export_format = self._isExportFormat(has_header)
        for col, combo in enumerate(self.comboBoxes):
            combo.blockSignals(True)
            if is_export_format:
                index = combo.findData(self.export_fields[col])
            else:
                index = self.defaultField(col, combo, has_header)
            combo.setCurrentIndex(index)
            combo.blockSignals(False)

    def _isExportFormat(self, has_header):
        if not has_header or self.sheet.max_column != len(self.export_fields):
            return False

        headers = []
        for col in range(self.sheet.max_column):
            title = self.sheet.cell(1, col + 1).value
            if title is None:
                title = ''
            elif isinstance(title, datetime.datetime):
                title = title.date().isoformat()
            elif isinstance(title, datetime.time):
                title = ''
            headers.append(str(title))

        return headers == self.export_headers

    def _getRowsCount(self, book):
        if self.has_header:
            # Row 1 holds the headers, not a record
            return max(self.sheet.max_row - 1, 0)
        return self.sheet.max_row

    def _setRecord(self, record, row):
        for i, field in enumerate(self.selected_fields):
            if not field:
                continue

            cell = self.sheet.cell(row + (2 if self.has_header else 1), i + 1)
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
                else:
                    embedded_image = self._getEmbeddedImage(
                        cell.coordinate, include_all=True)
                    if embedded_image is not None:
                        val = self.__fixTransparentImage(embedded_image)
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
