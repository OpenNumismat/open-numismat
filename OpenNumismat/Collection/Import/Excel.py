from typing import Optional
import datetime
import openpyxl
import os

from dateutil import parser

from PySide6.QtCore import (Qt, QSize, QEvent, QSortFilterProxyModel, QPointF)
from PySide6.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QDialogButtonBox, QComboBox, QCheckBox, QLabel,
                               QStyledItemDelegate, QStyle, QStyleOptionViewItem,
                               QApplication)
from PySide6.QtGui import (QPixmap, QImage, QPainter, QColor, QTextLayout,
                           QTextCharFormat, QTextOption)

from OpenNumismat.Collection.Import import _Import2, _InvalidDatabaseError
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.CachedPoolManager import CachedPoolManager

IMAGE_CONNECTION_TIMEOUT = 30
IMAGE_PREVIEW_SIZE = 64
IMAGE_SOURCE_ROLE = Qt.UserRole + 1
IMAGE_PREVIEW_ROLE = Qt.UserRole + 2


def _blendColors(color1, color2):
    return QColor((color1.red() + color2.red()) // 2,
                  (color1.green() + color2.green()) // 2,
                  (color1.blue() + color2.blue()) // 2)


def _errorColor(palette):
    if palette.window().color().lightness() < 128:
        return QColor(255, 110, 110)   # dark theme
    return QColor(190, 45, 45)         # light theme


class FilterHighlightDelegate(QStyledItemDelegate):
    """Mark filter matches in item labels, keeping the native item rendering."""

    MARK_COLOR = QColor(220, 120, 20)

    def __init__(self, combo):
        """Create the delegate for the combo holding the active filter."""
        super().__init__(combo)
        self._combo = combo

    def paint(self, painter, option, index):
        # The style draws the row and its label as everywhere else in the
        # application; the matched letters are underlined using the same text
        # layout the style draws the label with (see
        # QCommonStylePrivate::viewItemDrawText), so the marks always sit
        # under the right letters on any style and color scheme
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        widget = opt.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, widget)

        query = self._combo.filterQuery()
        if not query or not isinstance(opt.text, str) or not opt.text:
            return

        rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, widget)
        margin = style.pixelMetric(QStyle.PM_FocusFrameHMargin, opt, widget) + 1
        rect = rect.adjusted(margin, 0, -margin, 0)
        shown = opt.fontMetrics.elidedText(opt.text, opt.textElideMode,
                                           rect.width())

        marks = self._findMatches(shown, query)
        if not marks:
            return

        layout, line = self._labelLayout(opt, shown, rect.width(),
                                         self._markFormats(marks))
        origin = QPointF(rect.x(),
                         rect.y() + (rect.height() - round(line.height())) // 2)

        painter.save()
        painter.setClipRect(opt.rect)
        painter.setPen(Qt.transparent)   # the label itself stays native
        layout.draw(painter, origin)
        painter.restore()

    @staticmethod
    def _labelLayout(opt, text, width, formats):
        # Same text layout as the style draws the label with; the formats
        # must be set before the layout starts or they are ignored
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.ManualWrap)
        text_option.setTextDirection(opt.direction)
        text_option.setAlignment(
            QStyle.visualAlignment(opt.direction, opt.displayAlignment))
        layout = QTextLayout(text, opt.font)
        layout.setTextOption(text_option)
        layout.setFormats(formats)
        layout.beginLayout()
        line = layout.createLine()
        line.setLineWidth(width)
        layout.endLayout()
        return layout, line

    @classmethod
    def _markFormats(cls, marks):
        formats = []
        for begin, end in marks:
            mark = QTextCharFormat()
            mark.setUnderlineStyle(QTextCharFormat.SingleUnderline)
            mark.setUnderlineColor(cls.MARK_COLOR)
            run = QTextLayout.FormatRange()
            run.start = begin
            run.length = end - begin
            run.format = mark
            formats.append(run)
        return formats

    @staticmethod
    def _findMatches(text, query):
        matches = []
        if not query:
            return matches
        start = 0
        lower_text = text.lower()
        lower_query = query.lower()
        while True:
            pos = lower_text.find(lower_query, start)
            if pos < 0:
                return matches
            matches.append((pos, pos + len(query)))
            start = pos + len(query)


class FilterComboBox(QComboBox):

    def __init__(self, parent=None):
        """Create the combo and install filtering support via enableFilter."""
        super().__init__(parent)
        self._filter_query = ''
        self._filtering = False
        self._selected_row = 0
        self._source_model = None
        self._filter_model = None
        self._count_label = None

    def enableFilter(self):
        self._source_model = self.model()
        self._filter_model = QSortFilterProxyModel(self)
        self._filter_model.setSourceModel(self._source_model)
        self._source_model.setParent(self._filter_model)
        self._filter_model.setFilterKeyColumn(0)
        self._filter_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setModel(self._filter_model)
        self.view().installEventFilter(self)
        self.view().viewport().installEventFilter(self)
        if self.lineEdit() is not None:
            self.lineEdit().installEventFilter(self)
            self._count_label = QLabel(self.lineEdit())
            font = self._count_label.font()
            font.setPointSizeF(font.pointSizeF() * 0.85)
            self._count_label.setFont(font)
            self._count_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            self._count_label.hide()
        self.setItemDelegate(FilterHighlightDelegate(self))
        self.currentIndexChanged.connect(self._rememberSelection)
        self.currentTextChanged.connect(self._showFromStart)

    def filterQuery(self):
        return self._filter_query

    def _updateFilterFeedback(self):
        count = self._filter_model.rowCount() if self._filter_query else 0
        self._showQuery(self._filter_query, count)

    def _showQuery(self, query, count):
        line_edit = self.lineEdit()
        if line_edit is None:
            return

        if query:
            # Show the typed letters instead of the current item
            error = not count
            line_edit.setText(query)
            if error:
                color = _errorColor(self.palette())
            else:
                color = _blendColors(self.palette().text().color(),
                                     self.palette().base().color())
            line_edit.setStyleSheet(
                'color: %s; font-style: italic; font-weight: 400;' % color.name())
            self._updateCountLabel(count, error)
        else:
            if self._count_label is not None:
                self._count_label.hide()
            line_edit.setTextMargins(0, 0, 0, 0)
            line_edit.setStyleSheet('')
            line_edit.setText(self.currentText())
        # A read-only line edit scrolls to the cursor after setText; show
        # the text from its beginning instead of from its end
        line_edit.setCursorPosition(0)

    def _showFromStart(self):
        line_edit = self.lineEdit()
        if line_edit is not None and not self._filter_query:
            line_edit.setCursorPosition(0)

    def _updateCountLabel(self, count, error=False):
        label = self._count_label
        label.setText('(%d)' % count)
        # Keep the widget font in sync with the painted weight so the
        # size hint (and thus the label box) fits the text
        font = label.font()
        font.setBold(error)
        label.setFont(font)
        if error:
            # Match the error color of the query and stand out
            color = _errorColor(self.palette()).name()
            weight = 700
        else:
            color = self.palette().placeholderText().color().name()
            weight = 400
        label.setStyleSheet(
            'color: %s; font-style: normal; font-weight: %d;' % (color, weight))
        label.show()
        label.raise_()
        self._positionCountLabel()

    def _positionCountLabel(self):
        line_edit = self.lineEdit()
        label = self._count_label
        if line_edit is None or label is None:
            return
        label.adjustSize()
        label.move(line_edit.width() - label.width() - 6,
                   (line_edit.height() - label.height()) // 2)
        line_edit.setTextMargins(0, 0, label.width() + 12, 0)

    def _rememberSelection(self, index):
        if not self._filtering and index >= 0:
            source_index = self._filter_model.mapToSource(
                self._filter_model.index(index, 0))
            self._selected_row = source_index.row()

    def rememberCurrentSelection(self):
        self._rememberSelection(self.currentIndex())

    def selectedData(self):
        if self._source_model is None:
            return self.currentData()
        return self._source_model.index(
            self._selected_row, 0).data(Qt.UserRole)

    def _applyFilter(self, query):
        self._filter_query = query
        self._filtering = True
        self._filter_model.setFilterFixedString(query)
        source_index = self._source_model.index(self._selected_row, 0)
        proxy_index = self._filter_model.mapFromSource(source_index)
        self.setCurrentIndex(proxy_index.row() if proxy_index.isValid() else -1)
        if proxy_index.isValid():
            self.view().setCurrentIndex(proxy_index)
        else:
            self.view().selectionModel().clearCurrentIndex()
        self._filtering = False
        # Rows surviving the filter change must repaint to update the marks
        self.view().viewport().update()
        self._updateFilterFeedback()

    def showPopup(self):
        self._applyFilter('')
        super().showPopup()

    def hidePopup(self):
        super().hidePopup()
        if self._filter_query:
            self._applyFilter('')

    def _moveHighlight(self, key):
        if not self.count():
            return
        step = 1 if key == Qt.Key_Down else -1
        row = self.view().currentIndex().row()
        if row < 0:
            row = self.currentIndex()
        if row < 0:
            row = 0 if step > 0 else self.count() - 1
        else:
            row = max(0, min(self.count() - 1, row + step))

        index = self._filter_model.index(row, 0)
        self.view().setCurrentIndex(index)
        self.view().scrollTo(index)
        self.setCurrentIndex(row)
        self._updateFilterFeedback()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Resize and watched is self.lineEdit():
            self._positionCountLabel()
            self._showFromStart()
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(watched, event)

        if watched is self.lineEdit():
            handled = self._lineEditKey(event)
        elif watched in (self.view(), self.view().viewport()):
            handled = self._viewKey(event)
        else:
            handled = False
        if handled:
            return True
        return super().eventFilter(watched, event)

    def _lineEditKey(self, event):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if not self.view().isVisible():
                self.showPopup()
                return True
        elif self._isFilterChar(event) and not self.view().isVisible():
            # Start filtering even before the popup is opened
            self.showPopup()
            self._applyFilter(self._filter_query + event.text())
            return True
        return False

    def _viewKey(self, event):
        key = event.key()
        if key in (Qt.Key_Up, Qt.Key_Down):
            self._moveHighlight(key)
            return True
        if key == Qt.Key_Escape and self._filter_query:
            self._applyFilter('')
            return True
        if key == Qt.Key_Backspace and self._filter_query:
            self._applyFilter(self._filter_query[:-1])
            return True
        if self._isFilterChar(event):
            self._applyFilter(self._filter_query + event.text())
            return True
        return False

    @staticmethod
    def _isFilterChar(event):
        text = event.text()
        return (text and text.isprintable() and
                not (event.modifiers() &
                     (Qt.ControlModifier | Qt.AltModifier)))

    def keyPressEvent(self, event):
        if (event.key() in (Qt.Key_Return, Qt.Key_Enter) and
                not self.view().isVisible()):
            self.showPopup()
            event.accept()
            return
        if (self.view().isVisible() and
                event.key() in (Qt.Key_Up, Qt.Key_Down)):
            self._moveHighlight(event.key())
            event.accept()
            return
        super().keyPressEvent(event)


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
                self._updateColumnPreview(col, combo.selectedData())

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

        # See Collection.exportToExcel, do not count 'id', 'createdat', 'updatedat', 'sort_id'.
        # And 'image' of Type.PreviewImage. So in total 5 "internal" fields/columns.
        MAX_COLUMN_COUNT = len(self.fields.fields) - 5
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
            combo = FilterComboBox()
            combo.setEditable(True)
            combo.setInsertPolicy(QComboBox.NoInsert)
            combo.lineEdit().setReadOnly(True)
            combo.lineEdit().setAlignment(Qt.AlignCenter)
            combo.addItem(self.tr("<Ignore>"))
            for f in self.fields.userFields:
                if f not in self.fields.systemFields:
                    combo.addItem(f.title, f)
            combo.enableFilter()
            combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            combo.setStyleSheet("QComboBox { font-weight: 700; }")
            combo.setToolTip(self.tr("Type to filter fields; press Esc to show all fields"))
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
                field = combo.selectedData() if combo is not None else None
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
        for col, combo in enumerate(self.comboBoxes):
            combo.blockSignals(True)
            combo.setCurrentIndex(self.defaultField(col, combo, has_header))
            combo.blockSignals(False)
            combo.rememberCurrentSelection()

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
