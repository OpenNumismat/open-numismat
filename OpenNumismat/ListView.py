import operator
import pickle
import os.path

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtCore import QCollator, QLocale
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

    def sort(self, column, order=Qt.AscendingOrder):
        self.model = self.sourceModel()
        super().sort(column, order)

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


class ListView(QTableView):
    rowChanged = pyqtSignal(object)
    # TODO: Changes mime type
    MimeType = 'num/data'

    def __init__(self, listParam, parent=None):
        super().__init__(parent)

        self.searchText = ''
        self.listParam = listParam

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
        if listParam.store_sorting:
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

        self.listCountLabel = QLabel()
        self.listSelectedLabel = QLabel(self.tr("0 coin(s) selected"))

        # Show image data as images
        for field in listParam.fields:
            if field.type in Type.ImageTypes:
                self.setItemDelegateForColumn(field.id, ImageDelegate(self))

        self.selectedRowId = None

    def sortChangedEvent(self, logicalIndex, order):
        # Clear all sort orders
        for column in self.listParam.columns:
            column.sortorder = None

        visualIndex = self.horizontalHeader().visualIndex(logicalIndex)
        # Set sort order only in required column
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

    def model(self):
        if not super().model():
            return None
        return self.proxyModel.sourceModel()

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

    def setModel(self, model):
        model.rowInserted.connect(self.scrollToIndex)

        self.proxyModel = SortFilterProxyModel(self)
        self.proxyModel.setSourceModel(model)
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

        self._moveColumns()

        for i in range(model.columnCount()):
            self.hideColumn(i)

        apply_sorting = model.settings['store_sorting']
        for param in self.listParam.columns:
            if param.enabled:
                self.showColumn(param.fieldid)

                if apply_sorting:
                    if param.sortorder in (Qt.AscendingOrder, Qt.DescendingOrder):
                        self.horizontalHeader().setSortIndicator(param.fieldid, param.sortorder)
                        self.sortByColumn(param.fieldid, Qt.AscendingOrder)

        for param in self.listParam.columns:
            if param.width:
                self.horizontalHeader().resizeSection(param.fieldid,
                                                      param.width)

        self.horizontalHeader().sectionResized.connect(self.columnResized)

        self._updateHeaderButtons()

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

        labelText = self.tr("%d/%d coins") % (newCount, totalCount)
        self.listCountLabel.setText(labelText)

        # Restore selected row
        if self.selectedRowId is not None:
            idIndex = self.model().fieldIndex('id')
            startIndex = self.model().index(0, idIndex)

            indexes = self.proxyModel.match(startIndex, Qt.DisplayRole,
                                        self.selectedRowId, 1, Qt.MatchExactly)
            if indexes:
                self.selectRow(indexes[0].row())
            else:
                self.selectedRowId = None

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

        col = []
        for i in range(self.model().columnCount()):
            col.append(i)

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

    def itemDClicked(self, index):
        self._edit(self.currentIndex())

    def keyPressEvent(self, event):
        key = event.key()
        if (key == Qt.Key_Return) or (key == Qt.Key_Enter):
            self._edit(self.currentIndex())
        elif event.matches(QKeySequence.Copy):
            self._copy(self.selectedRows())
        elif event.matches(QKeySequence.Paste):
            self._paste()
        elif event.matches(QKeySequence.Delete):
            self._delete(self.selectedRows())
        else:
            return super().keyPressEvent(event)

    def contextMenuEvent(self, pos):
        selected_count = len(self.selectedRows())

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

        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        menu.addAction(icon, self.tr("Delete"),
                       self._delete, QKeySequence.Delete)
        menu.exec_(self.mapToGlobal(pos))

    def currentChanged(self, current, previous):
        if current.row() != previous.row():
            self.rowChanged.emit(self.currentIndex())

        index = self.currentIndex()
        if index.isValid():
            id_col = self.model().fieldIndex('id')
            id_index = self.model().index(index.row(), id_col)
            self.selectedRowId = self.model().dataDisplayRole(id_index)

        return super().currentChanged(current, previous)

    def selectionChanged(self, selected, deselected):
        self.listSelectedLabel.setText(self.tr("%n coin(s) selected", '',
                                               len(self.selectedRows())))
        return super().selectionChanged(selected, deselected)

    def __mapToSource(self, index):
        return self.proxyModel.mapToSource(index)

    def currentIndex(self):
        index = super().currentIndex()
        return self.__mapToSource(index)

    def selectedRows(self):
        indexes = self.selectedIndexes()
        if not indexes:
            if self.currentIndex().row() >= 0:
                indexes.append(self.currentIndex())
                self.selectRow(self.currentIndex().row())
        else:
            rowsIndexes = {}
            for index in indexes:
                rowsIndexes[index.row()] = self.__mapToSource(index)
            indexes = list(rowsIndexes.values())

        return indexes

    def report(self):
        indexes = self.selectedRows()
        if indexes:
            preview = PreviewDialog(self.model(), indexes, self)
            preview.exec_()
        else:
            QMessageBox.information(
                self, self.tr("Report preview"),
                self.tr("Nothing selected.\nSelect required coins by clicking "
                        "with Ctrl or Shift, or Ctrl+A for select all coins."))

    def viewInBrowser(self, template=None):
        if not template:
            template = Settings()['template']
        template_name = os.path.basename(template)
        dstPath = os.path.join(TemporaryDir.path(), template_name + '.htm')
        report = Report(self.model(), template, dstPath, self)
        indexes = self.selectedRows()
        if indexes:
            fileName = report.generate(indexes)
            if fileName:
                executor = QDesktopServices()
                executor.openUrl(QtCore.QUrl.fromLocalFile(fileName))
        else:
            QMessageBox.information(
                self, self.tr("Report preview"),
                self.tr("Nothing selected.\nSelect required coins by clicking "
                        "with Ctrl or Shift, or Ctrl+A for select all coins."))

    def saveTable(self):
        filters = (self.tr("Excel document (*.xls)"),
                   self.tr("Web page (*.htm *.html)"),
                   self.tr("Text file (*.csv)"),
                   self.tr("Text file UTF-8 (*.csv)"))
        if not ExportToExcel.isAvailable():
            filters = filters[1:]

        defaultFileName = self.listParam.page.title
        fileName, selectedFilter = getSaveFileName(
            self, 'export_table', defaultFileName,
            OpenNumismat.HOME_PATH, filters)
        if fileName:
            model = self.model()
            progressDlg = Gui.ProgressDialog(self.tr("Saving list"),
                                    self.tr("Cancel"), model.rowCount(), self)

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

                index = self.__mapToSource(self.proxyModel.index(i, 0))
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
            indexes = self.selectedRows()

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
            progressDlg = Gui.ProgressDialog(self.tr("Updating records"),
                                        self.tr("Cancel"), len(indexes), self)

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

            progressDlg.setLabelText(self.tr("Saving..."))
            self.model().submitAll()

            progressDlg.reset()

    def _copy(self, indexes=None):
        if not indexes:
            indexes = self.selectedRows()

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
                                    self.tr("Inserting records"),
                                    self.tr("Cancel"), len(pickleData), self)

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
                                    self.tr("Inserting records"),
                                    self.tr("Cancel"), len(pickleData), self)

            if progressDlg:
                progressDlg.reset()

    def _delete(self, indexes=None):
        if not indexes:
            indexes = self.selectedRows()

        result = QMessageBox.information(self, self.tr("Delete"),
                    self.tr("Are you sure to remove a %n coin(s)?", '',
                                                                 len(indexes)),
                    QMessageBox.Yes | QMessageBox.Cancel,
                    QMessageBox.Cancel)
        if result == QMessageBox.Yes:
            progressDlg = Gui.ProgressDialog(self.tr("Deleting records"),
                                        self.tr("Cancel"), len(indexes), self)

            model = self.model()
            for index in indexes:
                progressDlg.step()
                if progressDlg.wasCanceled():
                    break

                model.removeRow(index.row())

            progressDlg.setLabelText(self.tr("Saving..."))
            model.submitAll()

            progressDlg.reset()

    def _clone(self, index=None):
        if not index:
            index = self.currentIndex()

        record = self.model().record(index.row())
        self.model().addCoin(record, self)

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
