import operator
import pickle
import os.path

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtCore import QCollator, QLocale
from PyQt5.QtCore import QAbstractProxyModel, QModelIndex, QItemSelectionModel
from PyQt5.QtCore import QRectF, QRect
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import QMargins

import OpenNumismat
from OpenNumismat.EditCoinDialog.EditCoinDialog import EditCoinDialog
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.SelectColumnsDialog import SelectColumnsDialog
from OpenNumismat.Collection.HeaderFilterMenu import FilterMenuButton
from OpenNumismat.Tools import Gui, TemporaryDir
from OpenNumismat.Reports.Report import Report
from OpenNumismat.Reports.Preview import PreviewDialog
from OpenNumismat.Settings import Settings
from OpenNumismat.Reports.ExportList import ExportToExcel, ExportToHtml, ExportToCsv, ExportToCsvUtf8
from OpenNumismat.Tools.Gui import createIcon, getSaveFileName
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
        self.listSelectedLabel = QLabel(QApplication.translate('BaseTableView', "0 coins selected"))

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

        labelText = QApplication.translate('BaseTableView', "%d/%d coins") % (newCount, totalCount)
        self.listCountLabel.setText(labelText)

    def itemDClicked(self, _index):
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
            self.selectRow(0)
            self.clearSelection()
        elif event.matches(QKeySequence.MoveToEndOfDocument):
            self.selectRow(self.model().rowCount() - 1)
            self.clearSelection()
        else:
            return super().keyPressEvent(event)

    def contextMenuEvent(self, pos):
        raise NotImplementedError

    def currentChanged(self, current, previous):
        index = self.currentIndex()
        if index.isValid():
            id_col = self.model().fieldIndex('id')
            id_index = self.model().index(index.row(), id_col)
            self.selectedId = self.model().dataDisplayRole(id_index)

        return super().currentChanged(current, previous)

    def selectionChanged(self, selected, deselected):
        count = len(self.selectedCoins())
        label = QApplication.translate('BaseTableView', "%n coin(s) selected",
                                       '', count)
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

    def report(self):
        indexes = self.selectedCoins()
        if indexes:
            preview = PreviewDialog(self.model(), indexes, self)
            preview.exec_()
        else:
            QMessageBox.information(
                self, QApplication.translate('BaseTableView', "Report preview"),
                QApplication.translate('BaseTableView',
                        "Nothing selected.\nSelect required coins by clicking "
                        "with Ctrl or Shift, or Ctrl+A for select all coins."))

    def viewInBrowser(self, template=None):
        if not template:
            template = Settings()['template']
        template_name = os.path.basename(template)
        dstPath = os.path.join(TemporaryDir.path(), template_name + '.htm')
        report = Report(self.model(), template, dstPath, self)
        indexes = self.selectedCoins()
        if indexes:
            fileName = report.generate(indexes)
            if fileName:
                executor = QDesktopServices()
                executor.openUrl(QtCore.QUrl.fromLocalFile(fileName))
        else:
            QMessageBox.information(
                self, QApplication.translate('BaseTableView', "Report preview"),
                QApplication.translate('BaseTableView',
                        "Nothing selected.\nSelect required coins by clicking "
                        "with Ctrl or Shift, or Ctrl+A for select all coins."))

    def saveTable(self):
        filters = (QApplication.translate('BaseTableView', "Excel document (*.xls)"),
                   QApplication.translate('BaseTableView', "Web page (*.htm *.html)"),
                   QApplication.translate('BaseTableView', "Text file (*.csv)"),
                   QApplication.translate('BaseTableView', "Text file UTF-8 (*.csv)"))
        if not ExportToExcel.isAvailable():
            filters = filters[1:]

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
                raise

            export.open()

            parts = []
            for param in self.listParam.columns:
                if not param.enabled:
                    continue

                field = model.fields.field(param.fieldid)
                if field.type in Type.ImageTypes:
                    continue

                parts.append(field.title)

            export.writeHeader(parts)

            for i in range(model.rowCount()):
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                index = self._mapToSource(self.proxyModel.index(i, 0))
                record = model.record(index.row())
                parts = []
                for param in self.listParam.columns:
                    field = model.fields.field(param.fieldid)
                    if field.type in Type.ImageTypes:
                        continue

                    if not param.enabled:
                        continue

                    if record.isNull(param.fieldid):
                        parts.append('')
                    else:
                        parts.append(record.value(param.fieldid))

                export.writeRow(parts)

            export.close()

            progressDlg.reset()

    def _edit(self, index=None):
        if not index:
            index = self.currentIndex()

        record = self.model().record(index.row())
        record_id = record.value('id')
        dialog = EditCoinDialog(self.model(), record, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            updatedRecord = dialog.getRecord()
            self.model().setRecord(index.row(), updatedRecord)
            self.model().submitAll()

            if record_id == self.model().record(index.row()).value('id'):
                self.scrollToIndex(index)

    def _multiEdit(self, indexes=None):
        if not indexes:
            indexes = self.selectedCoins()

        # Fill multi record for editing
        multiRecord = self.model().record(indexes[0].row())
        usedFields = [Qt.Checked] * multiRecord.count()
        for index in indexes:
            record = self.model().record(index.row())
            for i in range(multiRecord.count()):
                value = record.value(i)
                if multiRecord.value(i) != value or not value:
                    multiRecord.setNull(i)
                    usedFields[i] = Qt.Unchecked

        dialog = EditCoinDialog(self.model(), multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            progressDlg = Gui.ProgressDialog(
                QApplication.translate('BaseTableView', "Updating records"),
                QApplication.translate('BaseTableView', "Cancel"),
                len(indexes), self)

            # Fill records by used fields in multi record
            multiRecord = dialog.getRecord()
            usedFields = dialog.getUsedFields()

            # Sort and reverse indexes for updating records that out
            # filtered after updating
            rindexes = sorted(indexes, key=operator.methodcaller('row'),
                              reverse=True)
            for index in rindexes:
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                record = self.model().record(index.row())
                for i in range(multiRecord.count()):
                    if usedFields[i] == Qt.Checked:
                        record.setValue(i, multiRecord.value(i))
                self.model().setRecord(index.row(), record)

            progressDlg.setLabelText(
                QApplication.translate('BaseTableView', "Saving..."))
            self.model().submitAll()

            progressDlg.reset()

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
                elif isinstance(value, QtCore.QByteArray):
                    textRecordData.append('')
                    pickleRecordData.append(value.data())
                else:
                    textRecordData.append(textToClipboard(str(value)))
                    pickleRecordData.append(value)

            textData.append('\t'.join(textRecordData))
            pickleData.append(pickleRecordData)

        mime = QtCore.QMimeData()
        mime.setText('\n'.join(textData))
        mime.setData(ListView.MimeType, pickle.dumps(pickleData))

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime)

    def __insertCoin(self, record, count):
        dialog = EditCoinDialog(self.model(), record, self)
        if count > 1:
            dialog.setManyCoins()
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.model().appendRecord(record)

        return dialog.clickedButton

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
                        record.setValue(i, QtCore.QByteArray(recordData[i]))
                    else:
                        record.setValue(i, recordData[i])

                if progressDlg:
                    self.model().appendRecord(record)
                else:
                    btn = self.__insertCoin(record, len(pickleData) - progress)
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
            # http://docs.python.org/3.2/library/csv.html#csv.excel_tab
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
                for i in range(len(data)):
                    record.setValue(i, clipboardToText(data[i]))

                if progressDlg:
                    self.model().appendRecord(record)
                else:
                    btn = self.__insertCoin(record, len(textData) - progress)
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
            QApplication.translate('BaseTableView', "Are you sure to remove a %n coin(s)?",
                                   '', len(indexes)),
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
            rect.translate((rect.width() - pixmap.width()) / 2,
                           (rect.height() - pixmap.height()) / 2)
            rect.setSize(pixmap.size())
            painter.drawPixmap(rect, pixmap)


class SortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, model, parent=None):
        super().__init__(parent)

        self.model = model
        self.setSourceModel(model)

        self.setDynamicSortFilter(True)

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

    def lessThan(self, left, right):
        leftData = self.model.dataDisplayRole(left)
        rightData = self.model.dataDisplayRole(right)

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
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)
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

    def sortChangedEvent(self, logicalIndex, order):
        sort_column_id = self.model().fields.sort_id.id
        if logicalIndex == sort_column_id:
            self.sortingChanged = False
        else:
            self.sortingChanged = True

        if self.listParam.store_sorting:
            # Clear all sort orders
            for column in self.listParam.columns:
                column.sortorder = None

            visualIndex = self.horizontalHeader().visualIndex(logicalIndex)
            # Set sort order only in required column
            if visualIndex in self.listParam.columns:
                column = self.listParam.columns[visualIndex]
                column.sortorder = order
            self.listParam.save_lists()

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
        menu.exec_(self.mapToGlobal(pos))
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
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.listParam.save_lists()

            self._moveColumns()

            for param in self.listParam.columns:
                self.setColumnHidden(param.fieldid, not param.enabled)

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
        self.sortingChanged = False

        apply_sorting = model.settings['store_sorting']
        for param in self.listParam.columns:
            if param.enabled:
                self.showColumn(param.fieldid)

                if apply_sorting:
                    if param.sortorder in (Qt.AscendingOrder, Qt.DescendingOrder):
                        self.sortByColumn(param.fieldid, param.sortorder)

                        sort_column_id = model.fields.sort_id.id
                        if param.fieldid == sort_column_id:
                            self.sortingChanged = False
                        else:
                            self.sortingChanged = True

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

            indexes = self.proxyModel.match(startIndex, Qt.DisplayRole,
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
                height = self.defaultHeight * height_multiplex

        self.verticalHeader().setDefaultSectionSize(height)

        self.horizontalHeader().sectionMoved.connect(self.columnMoved)

        self._updateHeaderButtons()

    def contextMenuEvent(self, pos):
        selected_count = len(self.selectedCoins())
        if not selected_count:
            return

        menu = QMenu(self)
        act = menu.addAction(createIcon('pencil.png'),
                             self.tr("Edit..."), self._edit)
        act.setShortcut('Enter')
        # Disable Edit when more than one record selected
        act.setEnabled(selected_count == 1)
        menu.setDefaultAction(act)

        menu.addAction(createIcon('page_copy.png'),
                       self.tr("Copy"), self._copy, QKeySequence.Copy)
        menu.addAction(createIcon('page_paste.png'),
                       self.tr("Paste"), self._paste, QKeySequence.Paste)

        menu.addSeparator()
        act = menu.addAction(self.tr("Clone"), self._clone)
        # Disable Clone when more than one record selected
        act.setEnabled(selected_count == 1)
        act = menu.addAction(self.tr("Multi edit..."), self._multiEdit)
        # Disable Multi edit when only one record selected
        act.setEnabled(selected_count > 1)

        menu.addSeparator()
        act = menu.addAction(createIcon('funnel.png'),
                             self.tr("Filter in"), self._filter)
        act.setEnabled(selected_count == 1)

        menu.addSeparator()
        index = QTableView.currentIndex(self)
        row = index.row()
        act = menu.addAction(createIcon('bullet_arrow_up.png'),
                             self.tr("Move up"), self._moveUp)
        if (selected_count > 1) or (row == 0):
            act.setEnabled(False)

        act = menu.addAction(createIcon('bullet_arrow_down.png'),
                             self.tr("Move down"), self._moveDown)
        if (selected_count > 1) or (row == self.model().rowCount() - 1):
            act.setEnabled(False)

        menu.addSeparator()
        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        menu.addAction(icon, self.tr("Delete"),
                       self._delete, QKeySequence.Delete)
        menu.exec_(self.mapToGlobal(pos))

    def currentChanged(self, current, previous):
        if current.row() != previous.row():
            self.rowChanged.emit(self.currentIndex())

        return super().currentChanged(current, previous)

    def selectedCoins(self):
        indexes = self.selectedIndexes()
        if not indexes:
            if self.currentIndex().row() >= 0:
                indexes.append(self.currentIndex())
                self.selectRow(self.currentIndex().row())
        else:
            rowsIndexes = {}
            for index in indexes:
                rowsIndexes[index.row()] = self._mapToSource(index)
            indexes = list(rowsIndexes.values())

        return indexes

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

                    e.accept()
                    return

        super().dropEvent(e)

    def _moveUp(self):
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
                back_color = palette.color(QPalette.Midlight)

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
            rect.translate((rect.width() - pixmap.width()) / 2,
                           (rect.height() + 35 - pixmap.height()) / 2)
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
                back_color = palette.color(QPalette.Midlight)

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
                                 rect.width(), rect.height() / 2)

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
            obverse_rect.translate((obverse_rect.width() - pixmap.width()) / 2,
                                   (obverse_rect.height() - pixmap.height()) / 2)
            obverse_rect.setSize(pixmap.size())
            painter.drawPixmap(obverse_rect, pixmap)

            reverse_rect = QRect(rect.x(), rect.y() + rect.height() / 2,
                                 rect.width(), rect.height() / 2)

            image = QImage()
            image.loadFromData(reverse_data)
            if image.width() > maxWidth or image.height() > maxHeight:
                scaledImage = image.scaled(maxWidth, maxHeight,
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                scaledImage = image
            pixmap = QPixmap.fromImage(scaledImage)
            # Set rect at center of item
            reverse_rect.translate((reverse_rect.width() - pixmap.width()) / 2,
                                   (reverse_rect.height() - pixmap.height()) / 2)
            reverse_rect.setSize(pixmap.size())
            painter.drawPixmap(reverse_rect, pixmap)


class CardModel(QAbstractProxyModel):

    def __init__(self, model, parent):
        super().__init__(parent)

        self.parent_widget = parent

        self.columns = 1

        self.model = model
        self.setSourceModel(model)
        self.model.modelChanged.connect(self.modelChanged)

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

    def modelChanged(self):
        self.repaint(True)

    def rowCount(self, parent=QModelIndex()):
        count = self.model.rowCount()
        return (count + (self.columns - 1)) / self.columns

    def columnCount(self, parent=QModelIndex()):
        return self.columns

    def mapToSource(self, index):
        num = index.row() * self.columns + index.column()
        return self.model.index(num, 0)

    def mapFromSource(self, index):
        return self.model.index(index.row() / self.columns,
                                index.row() % self.columns)

    def repaint(self, immediately=False):
        width = self.parent_widget.width()
        vertical_bar = self.parent_widget.verticalScrollBar()
        if vertical_bar.isVisible():
            width -= vertical_bar.width() + 2
        col_width = self.parent_widget.columnWidth(0)
        old = self.columns
        new = int(width / col_width)
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
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

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
        self.verticalHeader().setDefaultSectionSize(height + 41)
        self.horizontalHeader().setDefaultSectionSize(height * 2 + 10 * height_multiplex)

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

            indexes = self.proxyModel.model.match(startIndex, Qt.DisplayRole,
                                        self.selectedId, 1, Qt.MatchExactly)
            if indexes:
                self.scrollToIndex(indexes[0])
            else:
                self.selectedId = None

    def scrollToIndex(self, index):
        realRowIndex = self.proxyModel.mapFromSource(index)
        self.selectionModel().setCurrentIndex(realRowIndex,
                                              QItemSelectionModel.ClearAndSelect)
        self.scrollTo(realRowIndex)

    def clearAllFilters(self):
        self.searchText = ''
        self.model().clearFilters()

    def contextMenuEvent(self, pos):
        selected_count = len(self.selectedCoins())
        if not selected_count:
            return

        menu = QMenu(self)
        act = menu.addAction(createIcon('pencil.png'),
                             QApplication.translate('IconView', "Edit..."),
                             self._edit)
        act.setShortcut('Enter')
        # Disable Edit when more than one record selected
        act.setEnabled(selected_count == 1)
        menu.setDefaultAction(act)

        menu.addAction(createIcon('page_copy.png'),
                       QApplication.translate('IconView', "Copy"),
                       self._copy, QKeySequence.Copy)
        menu.addAction(createIcon('page_paste.png'),
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
        act = menu.addAction(createIcon('bullet_arrow_up.png'),
                             self.tr("Move up"), self._moveUp)
        if (selected_count > 1) or (row == 0):
            act.setEnabled(False)

        act = menu.addAction(createIcon('bullet_arrow_down.png'),
                             self.tr("Move down"), self._moveDown)
        if (selected_count > 1) or (row == self.model().rowCount() - 1):
            act.setEnabled(False)

        menu.addSeparator()
        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        menu.addAction(icon, QApplication.translate('IconView', "Delete"),
                       self._delete, QKeySequence.Delete)
        menu.exec_(self.mapToGlobal(pos))

    def currentChanged(self, current, previous):
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

                    e.accept()
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
        self.verticalHeader().setDefaultSectionSize(height * 2 + 42)
        self.horizontalHeader().setDefaultSectionSize(height + 10 * height_multiplex)
