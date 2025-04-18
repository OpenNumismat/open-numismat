import pickle
import os.path

from PySide6.QtCore import (
    QAbstractProxyModel,
    QByteArray,
    QCollator,
    QItemSelectionModel,
    QLocale,
    QMargins,
    QMimeData,
    QModelIndex,
    QRect,
    QRectF,
    QSortFilterProxyModel,
    QUrl,
)
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import (
    Qt,
    QAction,
    QDesktopServices,
    QIcon,
    QImage,
    QKeySequence,
    QPalette,
    QPixmap,
    QTextOption,
)
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QMessageBox,
    QStyle,
    QStyledItemDelegate,
    QTableView,
)

import OpenNumismat
from OpenNumismat.EditCoinDialog.EditCoinDialog import EditCoinDialog
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.SelectColumnsDialog import SelectColumnsDialog
from OpenNumismat.Collection.HeaderFilterMenu import FilterMenuButton
from OpenNumismat.Tools import Gui, TemporaryDir
from OpenNumismat.Tools.Converters import compareYears
from OpenNumismat.Reports.Report import Report
from OpenNumismat.Reports.Preview import PreviewDialog
from OpenNumismat.Settings import Settings
from OpenNumismat.Reports.ExportList import ExportToExcel, ExportToHtml, ExportToCsv, ExportToCsvUtf8
from OpenNumismat.Tools.Gui import getSaveFileName, statusColor
from OpenNumismat.Collection.HeaderFilterMenu import ColumnFilters, ValueFilter, DataFilter, BlankFilter


def textToClipboard(text):
    for c in '\t\n\r':
        if c in text:
            return '"' + text.replace('"', '""') + '"'

    return text


def clipboardToText(text):
    for c in '\t\n\r':
        if c in text:
            return text[1:-1].replace('""', '"')

    return text


class BaseTableView(QTableView):
    rowChanged = pyqtSignal(object)
    # TODO: Changes mime type
    MimeType = 'num/data'

    def __init__(self, listParam, parent=None):
        super().__init__(parent)

        self.proxyModel = None

        self.sortingChanged = False
        self.searchText = ''
        self.listParam = listParam

        self.selectedId = None

        self.listCountLabel = QLabel()
        self.listSelectedLabel = QLabel(QApplication.translate('BaseTableView', "0 records selected"))

    def _sortChangedMessage(self):
        return QMessageBox.information(
            self, QApplication.translate('BaseTableView', "Custom sorting"),
            QApplication.translate('BaseTableView',
                    "Default sort order changed.\n"
                    "Changing item position avalaible only on default "
                    "sort order. Clear sort order now?"),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel)

    def tryDragMode(self):
        if self.sortingChanged:
            result = self._sortChangedMessage()
            if result == QMessageBox.Yes:
                self.clearSorting()
            else:
                return False

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)

        return True

    def selectMode(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(False)
        self.setAcceptDrops(False)

    def isDragMode(self):
        return self.dragDropMode() == QAbstractItemView.InternalMove

    def modelChanged(self):
        # Fetch all selected records
        while self.model().canFetchMore():
            self.model().fetchMore()
        newCount = self.model().rowCount()

        # Show updated coins count
        sql = "SELECT count(*) FROM coins"
        query = QSqlQuery(sql, self.model().database())
        query.first()
        totalCount = query.record().value(0)

        labelText = QApplication.translate('BaseTableView', "%d/%d records") % (newCount, totalCount)
        self.listCountLabel.setText(labelText)

    def itemDClicked(self, _index):
        selected_count = len(self.selectedCoins())
        if not selected_count:
            return

        self._edit(self.currentIndex())

    def keyPressEvent(self, event):
        key = event.key()
        if (key == Qt.Key_Return) or (key == Qt.Key_Enter):
            indexes = self.selectedCoins()
            if len(indexes) == 1:
                self._edit(indexes[0])
            elif len(indexes) > 1:
                self._multiEdit(indexes)
        elif event.matches(QKeySequence.Copy):
            self._copy(self.selectedCoins())
        elif event.matches(QKeySequence.Paste):
            self._paste()
        elif event.matches(QKeySequence.Delete):
            self._delete(self.selectedCoins())
        elif event.matches(QKeySequence.MoveToStartOfDocument):
            index = self.model().index(0, 0)
            self.scrollToIndex(index)
            self.clearSelection()
        elif event.matches(QKeySequence.MoveToEndOfDocument):
            index = self.model().index(self.model().rowCount() - 1, 0)
            self.scrollToIndex(index)
            self.clearSelection()
        else:
            return super().keyPressEvent(event)

    def currentChanged(self, current, previous):
        index = self.currentIndex()
        if index.isValid():
            id_col = self.model().fieldIndex('id')
            id_index = self.model().index(index.row(), id_col)
            self.selectedId = self.model().dataDisplayRole(id_index)

        return super().currentChanged(current, previous)

    def selectionChanged(self, selected, deselected):
        count = len(self.selectedCoins())
        label = QApplication.translate('BaseTableView', "%d record(s) selected") % count
        self.listSelectedLabel.setText(label)
        return super().selectionChanged(selected, deselected)

    def _mapToSource(self, index):
        return self.proxyModel.mapToSource(index)

    def currentIndex(self):
        index = super().currentIndex()
        return self._mapToSource(index)

    def selectedCoins(self):
        raise NotImplementedError

    def clearSorting(self):
        sort_column_id = self.model().fields.sort_id.id
        self.sortByColumn(sort_column_id, Qt.AscendingOrder)
        self.sortingChanged = False

    def saveSorting(self):
        pass

    def report(self):
        indexes = []
        for i in range(self.model().rowCount()):
            index = self.proxyModel.index(i, 0)
            real_index = self.proxyModel.mapToSource(index)
            indexes.append(real_index)

        if indexes:
            preview = PreviewDialog(self.model(), indexes, self)
            preview.exec()
            preview.deleteLater()
        else:
            QMessageBox.information(
                self, QApplication.translate('BaseTableView', "Report preview"),
                QApplication.translate('BaseTableView', "Nothing selected"))

    def viewInBrowser(self, template=None):
        if not template:
            template = Settings()['template']
        template_name = os.path.basename(template)
        dstPath = os.path.join(TemporaryDir.path(), template_name + '.htm')
        report = Report(self.model(), template, dstPath, self)

        indexes = []
        for i in range(self.model().rowCount()):
            index = self.proxyModel.index(i, 0)
            real_index = self.proxyModel.mapToSource(index)
            indexes.append(real_index)

        if indexes:
            fileName = report.generate(indexes)
            if fileName:
                executor = QDesktopServices()
                executor.openUrl(QUrl.fromLocalFile(fileName))
        else:
            QMessageBox.information(
                self, QApplication.translate('BaseTableView', "Report preview"),
                QApplication.translate('BaseTableView', "Nothing selected"))

        report.deleteLater()

    def saveTable(self):
        filters = (QApplication.translate('BaseTableView', "Excel document (*.xlsx)"),
                   QApplication.translate('BaseTableView', "Web page (*.htm *.html)"),
                   QApplication.translate('BaseTableView', "Text file (*.csv)"),
                   QApplication.translate('BaseTableView', "Text file UTF-8 (*.csv)"))

        defaultFileName = self.listParam.page.title
        fileName, selectedFilter = getSaveFileName(
            self, 'export_table', defaultFileName,
            OpenNumismat.HOME_PATH, filters)
        if fileName:
            model = self.model()
            progressDlg = Gui.ProgressDialog(
                QApplication.translate('BaseTableView', "Saving list"),
                QApplication.translate('BaseTableView', "Cancel"),
                model.rowCount(), self)

            if filters.index(selectedFilter) == 0:  # Excel documents
                export = ExportToExcel(fileName, self.listParam.page.title)
            elif filters.index(selectedFilter) == 1:  # Web page
                export = ExportToHtml(fileName, self.listParam.page.title)
            elif filters.index(selectedFilter) == 2:  # Text file
                export = ExportToCsv(fileName, self.listParam.page.title)
            elif filters.index(selectedFilter) == 3:  # Text file UTF-8
                export = ExportToCsvUtf8(fileName, self.listParam.page.title)
            else:
                raise ValueError

            export.open()

            parts = []
            for param in self.listParam.columns:
                if not param.enabled:
                    continue

                field = model.fields.field(param.fieldid)
                if not export.acceptImages() and field.type in Type.ImageTypes:
                    continue

                parts.append(field.title)

            export.writeHeader(parts)

            for i in range(model.rowCount()):
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                parts = []
                for param in self.listParam.columns:
                    if not param.enabled:
                        continue

                    field = model.fields.field(param.fieldid)
                    if not export.acceptImages() and field.type in Type.ImageTypes:
                        continue

                    field_index = model.index(i, model.fieldIndex(field.name))
                    value = model.data(field_index, Qt.DisplayRole)

                    if value is None:
                        parts.append('')
                    else:
                        parts.append(value)

                export.writeRow(parts)

            while True:
                try:
                    export.close()
                    break
                except PermissionError:
                    progressDlg.close()
                    btn = QMessageBox.warning(self, self.tr("Saving list"),
                                        self.tr("File is open in another program or permission required.\nClose the file and try again."),
                                        QMessageBox.Retry | QMessageBox.Cancel,
                                        QMessageBox.Retry)
                    if btn != QMessageBox.Retry:
                        break

            progressDlg.reset()

    def _edit(self, index=None):
        if not index:
            index = self.currentIndex()

        record = self.model().record(index.row())
        record_id = record.value('id')
        dialog = EditCoinDialog(self.model(), record, self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.model().setRecord(index.row(), record)
            self.model().submitAll()

            if record_id == self.model().record(index.row()).value('id'):
                self.scrollToIndex(index)
        dialog.deleteLater()

    def _multiEdit(self, indexes=None):
        if not indexes:
            indexes = self.selectedCoins()

        rows = []
        for index in indexes:
            rows.append(index.row())

        multiRecord, usedFields = self.model().multiRecord(rows)

        dialog = EditCoinDialog(self.model(), multiRecord, self, usedFields)
        result = dialog.exec()
        if result == QDialog.Accepted:
            # Sort and reverse indexes for updating records that out
            # filtered after updating
            rows.sort(reverse=True)
            self.model().setMultiRecord(multiRecord, dialog.getUsedFields(), rows, parent=self)

        dialog.deleteLater()

    def _copy(self, indexes=None):
        if not indexes:
            indexes = self.selectedCoins()

        textData = []
        pickleData = []
        for index in indexes:
            record = self.model().record(index.row())
            if record.isEmpty():
                continue

            textRecordData = []
            pickleRecordData = []
            for i in range(self.model().columnCount()):
                value = record.value(i)
                if record.isNull(i):
                    textRecordData.append('')
                    pickleRecordData.append(None)
                elif isinstance(value, QByteArray):
                    textRecordData.append('')
                    pickleRecordData.append(value.data())
                else:
                    textRecordData.append(textToClipboard(str(value)))
                    pickleRecordData.append(value)

            textData.append('\t'.join(textRecordData))
            pickleData.append(pickleRecordData)

        mime = QMimeData()
        mime.setText('\n'.join(textData))
        mime.setData(ListView.MimeType, pickle.dumps(pickleData))

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime)

    def _paste(self):
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()
        progressDlg = None

        if mime.hasFormat(ListView.MimeType):
            # Load data stored by application
            pickleData = pickle.loads(mime.data(ListView.MimeType))
            for progress, recordData in enumerate(pickleData):
                if progressDlg:
                    progressDlg.setValue(progress)
                    if progressDlg.wasCanceled():
                        break

                record = self.model().record()
                for i in range(self.model().columnCount()):
                    if isinstance(recordData[i], bytes):
                        # Note: Qt::QVariant convert Python bytes type to
                        # str type
                        record.setValue(i, QByteArray(recordData[i]))
                    else:
                        record.setValue(i, recordData[i])

                if progressDlg:
                    self.model().appendRecord(record)
                else:
                    btn = self.model().addCoins(record, len(pickleData) - progress)
                    if btn == QDialogButtonBox.Abort:
                        break
                    if btn == QDialogButtonBox.SaveAll:
                        progressDlg = Gui.ProgressDialog(
                            QApplication.translate('BaseTableView', "Inserting records"),
                            QApplication.translate('BaseTableView', "Cancel"),
                            len(pickleData), self)

            if progressDlg:
                progressDlg.reset()

        elif mime.hasText():
            # Load data stored by another application (Excel)
            # TODO: Process fields with \n and \t
            # https://docs.python.org/3.2/library/csv.html#csv.excel_tab
            textData = clipboard.text().split('\n')
            for progress, recordData in enumerate(textData):
                if progressDlg:
                    progressDlg.setValue(progress)
                    if progressDlg.wasCanceled():
                        break

                data = recordData.split('\t')
                # Skip very short (must contain ID and NAME) and too large data
                if len(data) < 2 or len(data) > self.model().columnCount():
                    return

                record = self.model().record()
                for i, val in enumerate(data):
                    record.setValue(i, clipboardToText(val))

                if progressDlg:
                    self.model().appendRecord(record)
                else:
                    btn = self.model().addCoins(record, len(textData) - progress)
                    if btn == QDialogButtonBox.Abort:
                        break
                    if btn == QDialogButtonBox.SaveAll:
                        progressDlg = Gui.ProgressDialog(
                            QApplication.translate('BaseTableView', "Inserting records"),
                            QApplication.translate('BaseTableView', "Cancel"),
                            len(pickleData), self)

            if progressDlg:
                progressDlg.reset()

    def _delete(self, indexes=None):
        if not indexes:
            indexes = self.selectedCoins()

        result = QMessageBox.information(
            self, QApplication.translate('BaseTableView', "Delete"),
            QApplication.translate('BaseTableView', "Are you sure to remove a %d coin(s)?") % len(indexes),
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel)
        if result == QMessageBox.Yes:
            progressDlg = Gui.ProgressDialog(
                QApplication.translate('BaseTableView', "Deleting records"),
                QApplication.translate('BaseTableView', "Cancel"),
                len(indexes), self)

            model = self.model()
            for index in indexes:
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                model.removeRow(index.row())

            progressDlg.setLabelText(
                QApplication.translate('BaseTableView', "Saving..."))
            model.submitAll()

            progressDlg.reset()

    def _clone(self, index=None):
        if not index:
            index = self.currentIndex()

        record = self.model().record(index.row())
        self.model().addCoin(record, self)


class ImageDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        data = index.data()
        if data and not data.isNull():
            image = QImage()
            image.loadFromData(data)
            rect = option.rect
            scaledImage = image.scaled(rect.width(), rect.height(),
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap = QPixmap.fromImage(scaledImage)
            # Set rect at center of item
            rect.translate((rect.width() - pixmap.width()) // 2,
                           (rect.height() - pixmap.height()) // 2)
            rect.setSize(pixmap.size())
            painter.drawPixmap(rect, pixmap)


class SortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, model, parent=None):
        super().__init__(parent)

        self.model = model
        self.setSourceModel(model)
        self.status_id = model.fields.status.id
        self.year_id = model.fields.year.id

        self.setDynamicSortFilter(True)

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

    def lessThan(self, left, right):
        leftData = self.model.dataDisplayRole(left)
        rightData = self.model.dataDisplayRole(right)

        if left.column() == self.status_id:
            return Statuses.compare(leftData, rightData) < 0
        elif left.column() == self.year_id:
            return compareYears(leftData, rightData) < 0
        else:
            if isinstance(leftData, str):
                rightData = str(rightData)
                return self.collator.compare(leftData, rightData) < 0
            elif isinstance(rightData, str):
                leftData = str(leftData)
                return self.collator.compare(leftData, rightData) < 0

            return leftData < rightData

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled


class ListView(BaseTableView):

    def __init__(self, listParam, parent=None):
        super().__init__(listParam, parent)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.itemDClicked)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionsMovable(True)
        self.horizontalHeader().sectionDoubleClicked.connect(
                                                self.sectionDoubleClicked)
        self.horizontalHeader().sectionResized.connect(self.columnResized)
        self.horizontalHeader().sectionMoved.connect(self.columnMoved)
        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(
                                                self.headerContextMenuEvent)
        self.horizontalHeader().sortIndicatorChanged.connect(
                                                self.sortChangedEvent)
        self.horizontalScrollBar().valueChanged.connect(self.scrolled)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        # Make header font always bold
        font = self.horizontalHeader().font()
        font.setBold(True)
        self.horizontalHeader().setFont(font)

        self.verticalHeader().setVisible(False)
        self.defaultHeight = self.verticalHeader().defaultSectionSize()

        # Show image data as images
        for field in listParam.fields:
            if field.type in Type.ImageTypes:
                self.setItemDelegateForColumn(field.id, ImageDelegate(self))

        self.upAct = QAction(QIcon(':/bullet_arrow_up.png'), self.tr("Move up"),
                          self, shortcut=Qt.ALT | Qt.Key_Up, triggered=self._moveUp)
        self.downAct = QAction(QIcon(':/bullet_arrow_down.png'), self.tr("Move down"),
                          self, shortcut=Qt.ALT | Qt.Key_Down, triggered=self._moveDown)
        self.addActions([self.upAct, self.downAct, ])

    def sortChangedEvent(self, logicalIndex, order):
        sort_column_id = self.model().fields.sort_id.id
        if logicalIndex == sort_column_id and order == Qt.AscendingOrder:
            self.sortingChanged = False
        else:
            self.sortingChanged = True

    def columnMoved(self, logicalIndex, oldVisualIndex, newVisualIndex):
        column = self.listParam.columns[oldVisualIndex]
        self.listParam.columns.remove(column)
        self.listParam.columns.insert(newVisualIndex, column)
        self.listParam.save_lists()

        self._updateHeaderButtons()

    def headerContextMenuEvent(self, pos):
        self.pos = pos  # store pos for action
        menu = QMenu(self)
        menu.addAction(self.tr("Select columns..."), self.selectColumns)
        menu.addAction(self.tr("Hide"), self._hideColumn)
        menu.addSeparator()
        menu.addAction(self.tr("Adjust size"), self._adjustColumn)
        menu.exec(self.mapToGlobal(pos))
        self.pos = None

    def _adjustColumn(self):
        index = self.horizontalHeader().logicalIndexAt(self.pos)
        self.resizeColumnToContents(index)

    def _hideColumn(self):
        index = self.horizontalHeader().logicalIndexAt(self.pos)
        column = self.horizontalHeader().visualIndex(index)
        self.listParam.columns[column].enabled = False
        self.listParam.save_lists()
        self.setColumnHidden(index, True)

    def selectColumns(self):
        dialog = SelectColumnsDialog(self.listParam, self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.listParam.save_lists()

            self._moveColumns()

            for param in self.listParam.columns:
                self.setColumnHidden(param.fieldid, not param.enabled)
        dialog.deleteLater()

    def sectionDoubleClicked(self, index):
        # NOTE: When section double-clicked it also clicked => sorting is
        # activated
        self.resizeColumnToContents(index)

    def columnResized(self, index, oldSize, newSize):
        if newSize > 0:
            column = self.horizontalHeader().visualIndex(index)
            self.listParam.columns[column].width = newSize
            # Saving columns parameters in this slot make resizing very slow
            # self.listParam.save_lists()
            self.listParam.mark_lists_changed()

        self._updateHeaderButtons()

    def scrollToIndex(self, index):
        realRowIndex = self.proxyModel.mapFromSource(index)
        self.selectRow(realRowIndex.row())
        self.scrollTo(realRowIndex)

    def clearAllFilters(self):
        for btn in self.headerButtons:
            btn.clear()

        self.listParam.filters.clear()
        self.listParam.save_filters()
        self.searchText = ''
        self.model().clearFilters()

    def model(self):
        if not super().model():
            return None
        return self.proxyModel.sourceModel()

    def setModel(self, model):
        model.rowInserted.connect(self.scrollToIndex)

        self.proxyModel = SortFilterProxyModel(model, self)
        super().setModel(self.proxyModel)
        model.proxy = self.proxyModel

        self.headerButtons = []
        for param in self.listParam.columns:
            btn = FilterMenuButton(param, self.listParam, self.model(),
                                   self.horizontalHeader())
            self.headerButtons.append(btn)

        filtersSql = FilterMenuButton.filtersToSql(
                                            self.listParam.filters.values())
        self.model().setFilter(filtersSql)

        self.horizontalHeader().sectionResized.disconnect(self.columnResized)
        self.horizontalHeader().sortIndicatorChanged.disconnect(
                                                self.sortChangedEvent)

        self._moveColumns()

        for i in range(model.columnCount()):
            self.hideColumn(i)

        self.clearSorting()

        for param in self.listParam.columns:
            if param.enabled:
                self.showColumn(param.fieldid)

            if param.width:
                self.horizontalHeader().resizeSection(param.fieldid,
                                                      param.width)

        self.horizontalHeader().sortIndicatorChanged.connect(
                                                self.sortChangedEvent)
        self.horizontalHeader().sectionResized.connect(self.columnResized)

        self._updateHeaderButtons()

    def modelChanged(self):
        super().modelChanged()

        # Restore selected row
        if self.selectedId is not None:
            idIndex = self.model().fieldIndex('id')
            startIndex = self.model().index(0, idIndex)

            indexes = self.proxyModel.match(startIndex, Qt.UserRole,
                                        self.selectedId, 1, Qt.MatchExactly)
            if indexes:
                index = self.proxyModel.index(indexes[0].row(), 1)
                self.selectRow(index.row())
                self.scrollTo(index)
            else:
                self.selectedId = None

    def scrolled(self, value):
        self._updateHeaderButtons()

    def _updateHeaderButtons(self):
        for btn in self.headerButtons:
            index = btn.fieldid
            if self.isColumnHidden(index):
                btn.hide()
            else:
                x = self.columnViewportPosition(index) + \
                            self.columnWidth(index) - btn.width() - 1
                btn.move(x, 0)
                btn.show()

    def _moveColumns(self):
        self.horizontalHeader().sectionMoved.disconnect(self.columnMoved)

        # Revert to base state
        for pos in range(self.model().columnCount()):
            index = self.horizontalHeader().visualIndex(pos)
            self.horizontalHeader().moveSection(index, pos)

        col = list(range(self.model().columnCount()))

        # Move columns
        height = self.defaultHeight
        for pos, param in enumerate(self.listParam.columns):
            if not param.enabled:
                continue
            index = col.index(param.fieldid)
            col.remove(param.fieldid)
            col.insert(pos, param.fieldid)
            self.horizontalHeader().moveSection(index, pos)

            type_ = self.model().fields.field(param.fieldid).type
            if type_ in Type.ImageTypes:
                height_multiplex = self.model().settings['image_height']
                height = int(self.defaultHeight * height_multiplex)

        self.verticalHeader().setDefaultSectionSize(height)

        self.horizontalHeader().sectionMoved.connect(self.columnMoved)

        self._updateHeaderButtons()

    def contextMenuEvent(self, event):
        selected_count = len(self.selectedCoins())
        if not selected_count:
            return

        menu = QMenu(self)
        act = menu.addAction(QIcon(':/pencil.png'),
                             self.tr("Edit..."), self._edit)
        act.setShortcut(Qt.Key_Enter)
        # Disable Edit when more than one record selected
        act.setEnabled(selected_count == 1)
        menu.setDefaultAction(act)

        menu.addAction(QIcon(':/page_copy.png'),
                       self.tr("Copy"), self._copy, QKeySequence.Copy)
        menu.addAction(QIcon(':/page_paste.png'),
                       self.tr("Paste"), self._paste, QKeySequence.Paste)

        menu.addSeparator()
        act = menu.addAction(self.tr("Clone"), self._clone)
        # Disable Clone when more than one record selected
        act.setEnabled(selected_count == 1)
        act = menu.addAction(self.tr("Multi edit..."), self._multiEdit)
        # Disable Multi edit when only one record selected
        act.setEnabled(selected_count > 1)

        menu.addSeparator()
        act = menu.addAction(QIcon(':/funnel.png'),
                             self.tr("Filter in"), self._filter)
        act.setEnabled(selected_count == 1)

        menu.addSeparator()
        index = QTableView.currentIndex(self)
        row = index.row()
        menu.addAction(self.upAct)
        if (selected_count > 1) or (row == 0):
            self.upAct.setEnabled(False)
        menu.addAction(self.downAct)
        if (selected_count > 1) or (row == self.model().rowCount() - 1):
            self.downAct.setEnabled(False)

        menu.addSeparator()
        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        menu.addAction(icon, self.tr("Delete"),
                       self._delete, QKeySequence.Delete)
        menu.exec(self.mapToGlobal(event.pos()))

        self.upAct.setEnabled(True)
        self.downAct.setEnabled(True)

    def currentChanged(self, current, previous):
        if current.row() != previous.row():
            self.rowChanged.emit(self.currentIndex())

        return super().currentChanged(current, previous)

    def selectedCoins(self):
        indexes = self.selectedIndexes()
        if not indexes:
            current_index = self.currentIndex()
            if current_index.row() >= 0:
                self.selectRow(current_index.row())
                return [current_index, ]
            else:
                return []
        else:
            indexes = self.selectionModel().selectedRows()
            return [self._mapToSource(index) for index in indexes]

    def _filter(self, index=None):
        if not index:
            index = self.currentIndex()

        model = self.model()

        column = index.column()
        column_name = model.columnName(column)
        column_type = model.columnType(column)
        data = index.data(Qt.UserRole)
        if column_type == Type.Text or column_type in Type.ImageTypes:
            if data:
                filter_ = DataFilter(column_name)
            else:
                filter_ = BlankFilter(column_name)
        else:
            value = str(data)
            if value:
                filter_ = ValueFilter(column_name, value)
            else:
                filter_ = BlankFilter(column_name)
        filter_.revert = True

        filters = ColumnFilters(column_name)
        filters.addFilter(filter_)
        for btn in self.headerButtons:
            if btn.fieldid == column:
                btn.applyFilters(filters)
                break

    def dropEvent(self, e):
        if self.sortingChanged:
            result = self._sortChangedMessage()
            if result == QMessageBox.Yes:
                self.clearSorting()

            return

        if e.source() == self:
            if self.viewport().rect().contains(e.pos()):
                index = self.indexAt(e.pos())
                if index.isValid():
                    index1 = QTableView.currentIndex(self)
                    self.model().moveRows(index1.row(), index.row())
                    return

        super().dropEvent(e)

    def _moveUp(self):
        selected_count = len(self.selectedCoins())
        if selected_count != 1:
            return

        if self.sortingChanged:
            result = self._sortChangedMessage()
            if result == QMessageBox.Yes:
                self.clearSorting()

            return

        index1 = QTableView.currentIndex(self)
        if index1.row() == 0:
            return

        index2 = self.proxyModel.index(index1.row() - 1, 0)

        self.model().moveRows(index1.row(), index2.row())

    def _moveDown(self):
        selected_count = len(self.selectedCoins())
        if selected_count != 1:
            return

        if self.sortingChanged:
            result = self._sortChangedMessage()
            if result == QMessageBox.Yes:
                self.clearSorting()

            return

        index1 = QTableView.currentIndex(self)
        if index1.row() == self.model().rowCount() - 1:
            return

        index2 = self.proxyModel.index(index1.row() + 1, 0)

        self.model().moveRows(index1.row(), index2.row())

    def search(self, text):
        self.searchText = text
        model = self.model()

        if text:
            val = "'%%%s%%'" % text.replace("'", "''")
            values = []
            val_lower = val.lower()
            values.append(val_lower)
            val_upper = val.upper()
            if val_lower != val_upper:
                values.append(val_upper)
                values.append(val.title())
            if val not in values:
                values.append(val)

            parts = []
            for param in self.listParam.columns:
                if not param.enabled:
                    continue

                field = model.fields.field(param.fieldid)
                if field.type in Type.ImageTypes:
                    continue

                parts.append(field.name)

            sql = []
            for part in parts:
                for val in values:
                    sql.append("%s LIKE %s" % (part, val))
            model.setSearchFilter('(' + ' OR '.join(sql) + ')')
        else:
            model.setSearchFilter('')

    def saveSorting(self):
        sort_column_id = self.model().fields.sort_id.id
        indexes = []
        for i in range(self.model().rowCount()):
            index = self.proxyModel.index(i, sort_column_id)
            real_index = self.proxyModel.mapToSource(index)
            indexes.append(real_index)

        if indexes:
            self.model().setRowsPos(indexes)
            self.clearSorting()


class IconDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        model = index.model().model
        orig_index = index.model().mapToSource(index)
        if orig_index.isValid():
            image_index = model.index(orig_index.row(), model.fields.image.id)
            image_data = image_index.data()
            title_index = model.index(orig_index.row(), model.fields.title.id)
            title = title_index.data()

            palette = QPalette()
            if option.state & QStyle.State_HasFocus or option.state & QStyle.State_Selected:
                color = palette.color(QPalette.HighlightedText)
                back_color = palette.color(QPalette.Highlight)
            else:
                color = palette.color(QPalette.Text)

                status_index = model.index(orig_index.row(), model.fields.status.id)
                status = status_index.data(Qt.UserRole)
                back_color = statusColor(status)

            painter.setPen(back_color)
            rect = option.rect.marginsRemoved(QMargins(1, 1, 1, 1))
            painter.drawRect(rect)

            text_rect = QRect(rect)
            text_rect.setHeight(30 + 4)
            painter.fillRect(text_rect, back_color)

            text_rect = rect.marginsRemoved(QMargins(3, 2, 2, 2))
            text_rect.setHeight(30)

            painter.setPen(color)
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            painter.drawText(QRectF(text_rect), title, text_option)

            image = QImage()
            image.loadFromData(image_data)
            if rect.width() - 1 < image.width():
                scaledImage = image.scaledToWidth(rect.width() - 2,
                                                  Qt.SmoothTransformation)
            else:
                scaledImage = image
            pixmap = QPixmap.fromImage(scaledImage)
            # Set rect at center of item
            rect.translate((rect.width() - pixmap.width()) // 2,
                           (rect.height() + 35 - pixmap.height()) // 2)
            rect.setSize(pixmap.size())
            painter.drawPixmap(rect, pixmap)


class CardDelegate(QStyledItemDelegate):

    def paint(self, painter, option, index):
        model = index.model().model
        orig_index = index.model().mapToSource(index)
        if orig_index.isValid():
            obverse_index = model.index(orig_index.row(), model.fields.obverseimg.id)
            obverse_data = obverse_index.data()
            reverse_index = model.index(orig_index.row(), model.fields.reverseimg.id)
            reverse_data = reverse_index.data()
            title_index = model.index(orig_index.row(), model.fields.title.id)
            title = title_index.data()

            palette = QPalette()
            if option.state & QStyle.State_HasFocus or option.state & QStyle.State_Selected:
                color = palette.color(QPalette.HighlightedText)
                back_color = palette.color(QPalette.Highlight)
            else:
                color = palette.color(QPalette.Text)

                status_index = model.index(orig_index.row(), model.fields.status.id)
                status = status_index.data(Qt.UserRole)
                back_color = statusColor(status)

            painter.setPen(back_color)
            rect = option.rect.marginsRemoved(QMargins(1, 1, 1, 1))
            painter.drawRect(rect)

            text_rect = QRect(rect)
            text_rect.setHeight(30 + 4)
            painter.fillRect(text_rect, back_color)

            text_rect = rect.marginsRemoved(QMargins(3, 2, 2, 2))
            text_rect.setHeight(30)

            painter.setPen(color)
            text_option = QTextOption()
            text_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            painter.drawText(QRectF(text_rect), title, text_option)

            rect.setY(rect.y() + 30 + 4 + 1)
            rect.setHeight(rect.height() - 1)
            obverse_rect = QRect(rect.x(), rect.y(),
                                 rect.width(), rect.height() // 2)

            maxWidth = obverse_rect.width() - 4
            maxHeight = obverse_rect.height() - 4

            image = QImage()
            image.loadFromData(obverse_data)
            if image.width() > maxWidth or image.height() > maxHeight:
                scaledImage = image.scaled(maxWidth, maxHeight,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                scaledImage = image
            pixmap = QPixmap.fromImage(scaledImage)
            # Set rect at center of item
            obverse_rect.translate((obverse_rect.width() - pixmap.width()) // 2,
                                   (obverse_rect.height() - pixmap.height()) // 2)
            obverse_rect.setSize(pixmap.size())
            painter.drawPixmap(obverse_rect, pixmap)

            reverse_rect = QRect(rect.x(), rect.y() + rect.height() // 2,
                                 rect.width(), rect.height() // 2)

            image = QImage()
            image.loadFromData(reverse_data)
            if image.width() > maxWidth or image.height() > maxHeight:
                scaledImage = image.scaled(maxWidth, maxHeight,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                scaledImage = image
            pixmap = QPixmap.fromImage(scaledImage)
            # Set rect at center of item
            reverse_rect.translate((reverse_rect.width() - pixmap.width()) // 2,
                                   (reverse_rect.height() - pixmap.height()) // 2)
            reverse_rect.setSize(pixmap.size())
            painter.drawPixmap(reverse_rect, pixmap)


class CardModel(QAbstractProxyModel):

    def __init__(self, model, parent):
        super().__init__(parent)

        self.parent_widget = parent

        self.columns = 1

        self.model = model
        self.setSourceModel(model)

    def parent(self, index):
        return QModelIndex()

    def flags(self, index):
        count = self.model.rowCount()
        num = index.row() * self.columns + index.column()
        if num >= count:
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    def index(self, row, column, parent=QModelIndex()):
        return self.createIndex(row, column)

    def rowCount(self, parent=QModelIndex()):
        count = self.model.rowCount()
        return (count + (self.columns - 1)) // self.columns

    def columnCount(self, parent=QModelIndex()):
        return self.columns

    def mapToSource(self, index):
        num = index.row() * self.columns + index.column()
        return self.model.index(num, 0)

    def mapFromSource(self, index):
        return self.model.index(index.row() // self.columns,
                                index.row() % self.columns)

    def repaint(self, immediately=False):
        width = self.parent_widget.width()
        vertical_bar = self.parent_widget.verticalScrollBar()
        if vertical_bar.isVisible():
            width -= vertical_bar.width() + 2
        col_width = self.parent_widget.columnWidth(0)
        old = self.columns
        new = width // col_width
        if new == 0:
            new = 1
        if old != new or immediately:
            self.beginResetModel()
            self.columns = new
            self.endResetModel()


class IconView(BaseTableView):
    def __init__(self, listParam, parent=None):
        super().__init__(listParam, parent)

        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.doubleClicked.connect(self.itemDClicked)

        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)

        self.setItemDelegate(IconDelegate(self))

    def resizeEvent(self, e):
        if self.proxyModel:
            self.proxyModel.repaint()

    def model(self):
        if not super().model():
            return None
        return self.proxyModel.sourceModel()

    def _updateSizes(self):
        defaultHeight = self.verticalHeader().defaultSectionSize()
        height_multiplex = self.model().settings['image_height']
        height = defaultHeight * height_multiplex
        self.verticalHeader().setDefaultSectionSize(int(height + 41))
        self.horizontalHeader().setDefaultSectionSize(int(height * 2 + 10 * height_multiplex))

    def setModel(self, model):
        model.rowInserted.connect(self.scrollToIndex)

        self.proxyModel = CardModel(model, self)
        super().setModel(self.proxyModel)
        # model.proxy = self.proxyModel
        model.proxy = None

        self.clearSorting()

        self._updateSizes()

    def modelChanged(self):
        super().modelChanged()

        # Restore selected coin
        if self.selectedId is not None:
            idIndex = self.model().fieldIndex('id')
            startIndex = self.model().index(0, idIndex)

            indexes = self.proxyModel.model.match(startIndex, Qt.UserRole,
                                        self.selectedId, 1, Qt.MatchExactly)
            if indexes:
                self.scrollToIndex(indexes[0])
            else:
                self.selectedId = None

        self.proxyModel.repaint(True)

    def scrollToIndex(self, index):
        realRowIndex = self.proxyModel.mapFromSource(index)
        self.selectionModel().setCurrentIndex(realRowIndex,
                                              QItemSelectionModel.ClearAndSelect)
        self.scrollTo(realRowIndex)

    def clearAllFilters(self):
        self.searchText = ''
        self.model().clearFilters()

    def contextMenuEvent(self, event):
        selected_count = len(self.selectedCoins())
        if not selected_count:
            return

        menu = QMenu(self)
        act = menu.addAction(QIcon(':/pencil.png'),
                             QApplication.translate('IconView', "Edit..."),
                             self._edit)
        act.setShortcut(Qt.Key_Enter)
        # Disable Edit when more than one record selected
        act.setEnabled(selected_count == 1)
        menu.setDefaultAction(act)

        menu.addAction(QIcon(':/page_copy.png'),
                       QApplication.translate('IconView', "Copy"),
                       self._copy, QKeySequence.Copy)
        menu.addAction(QIcon(':/page_paste.png'),
                       QApplication.translate('IconView', "Paste"),
                       self._paste, QKeySequence.Paste)

        menu.addSeparator()
        act = menu.addAction(QApplication.translate('IconView', "Clone"),
                             self._clone)
        # Disable Clone when more than one record selected
        act.setEnabled(selected_count == 1)
        act = menu.addAction(QApplication.translate('IconView', "Multi edit..."),
                             self._multiEdit)
        # Disable Multi edit when only one record selected
        act.setEnabled(selected_count > 1)

        menu.addSeparator()
        index = self.currentIndex()
        row = index.row()
        act = menu.addAction(QIcon(':/bullet_arrow_up.png'),
                             self.tr("Move up"), self._moveUp)
        if (selected_count > 1) or (row == 0):
            act.setEnabled(False)

        act = menu.addAction(QIcon(':/bullet_arrow_down.png'),
                             self.tr("Move down"), self._moveDown)
        if (selected_count > 1) or (row == self.model().rowCount() - 1):
            act.setEnabled(False)

        menu.addSeparator()
        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        menu.addAction(icon, QApplication.translate('IconView', "Delete"),
                       self._delete, QKeySequence.Delete)
        menu.exec(self.mapToGlobal(event.pos()))

    def currentChanged(self, current, previous):
        if (current.row() != previous.row()) or (current.column() != previous.column()):
            self.rowChanged.emit(self.currentIndex())

        return super().currentChanged(current, previous)

    def selectedCoins(self):
        indexes = self.selectedIndexes()
        if not indexes:
            if self.currentIndex().isValid():
                indexes.append(self.currentIndex())
                index = super().currentIndex()
                self.selectionModel().select(index, QItemSelectionModel.Select)
        else:
            indexes = list(self._mapToSource(index) for index in indexes)

        return indexes

    def dropEvent(self, e):
        if e.source() == self:
            if self.viewport().rect().contains(e.pos()):
                index = self.indexAt(e.pos())
                if index.isValid():
                    index1 = self.currentIndex()
                    index2 = self._mapToSource(index)
                    self.model().moveRows(index1.row(), index2.row())
                    return

        super().dropEvent(e)

    def _moveUp(self):
        index1 = self.currentIndex()
        if index1.row() == 0:
            return

        index2 = self.proxyModel.index(index1.row() - 1, 0)

        self.model().moveRows(index1.row(), index2.row())

    def _moveDown(self):
        index1 = self.currentIndex()
        if index1.row() == self.model().rowCount() - 1:
            return

        index2 = self.proxyModel.index(index1.row() + 1, 0)

        self.model().moveRows(index1.row(), index2.row())

    def search(self, text):
        self.searchText = text
        model = self.model()

        if text:
            val = "'%%%s%%'" % text.replace("'", "''")
            values = []
            val_lower = val.lower()
            values.append(val_lower)
            val_upper = val.upper()
            if val_lower != val_upper:
                values.append(val_upper)
                values.append(val.title())
            if val not in values:
                values.append(val)

            parts = ('title',)
            sql = []
            for part in parts:
                for val in values:
                    sql.append("%s LIKE %s" % (part, val))
            model.setSearchFilter('(' + ' OR '.join(sql) + ')')
        else:
            model.setSearchFilter('')


class CardView(IconView):

    def __init__(self, listParam, parent=None):
        super().__init__(listParam, parent)

        self.setItemDelegate(CardDelegate(self))

    def _updateSizes(self):
        defaultHeight = self.verticalHeader().defaultSectionSize()
        height_multiplex = self.model().settings['image_height']
        height = defaultHeight * height_multiplex * 2
        self.verticalHeader().setDefaultSectionSize(int(height * 2 + 42))
        self.horizontalHeader().setDefaultSectionSize(int(height + 10 * height_multiplex))
