from PySide6.QtCore import Qt, QDate, QLocale, QSettings, QT_TRANSLATE_NOOP
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QMessageBox, QPushButton, QTableView, QVBoxLayout

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.BaseFormLayout import BaseFormLayout, FormItem
from OpenNumismat.Tools.Gui import statusIcon


class BaseExtTableLayout(QVBoxLayout):
    Actions = (
        ('buy', QT_TRANSLATE_NOOP("PriceAction", "Buy")),
        ('sell', QT_TRANSLATE_NOOP("PriceAction", "Sell")),
        ('auction', QT_TRANSLATE_NOOP("PriceAction", "Auction")),
    )

    def __init__(self, fields, reference, settings, readonly, parent):
        super().__init__()

        self.fields = fields
        self.reference = reference
        self.settings = settings
        self.readonly = readonly
        self.parent = parent

        self.locale = QLocale.system()

        self.items = self.get_items()

        self.model = QStandardItemModel(0, len(self.items), self)

        self.table_view = QTableView(parent)
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.verticalHeader().hide()
        self.table_view.setSortingEnabled(True)
        self.table_view.clicked.connect(self.handle_row_click)
        header = self.table_view.horizontalHeader()
        header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        header.setSectionsMovable(True)
        # Make header font always bold
        font = header.font()
        font.setBold(True)
        header.setFont(font)

        for i, field in enumerate(self.fields):
            self.model.setHeaderData(i, Qt.Horizontal, field.title)
            if not field.enabled:
                self.table_view.hideColumn(i)

        col = [field.name for field in self.fields]
        sorted_fields = sorted(self.fields, key=lambda x: x.position)
        header = self.table_view.horizontalHeader()
        for pos, field in enumerate(sorted_fields):
            if not field.enabled:
                continue
            index = col.index(field.name)
            col.remove(field.name)
            col.insert(pos, field.name)
            header.moveSection(index, pos)

        self.addWidget(self.table_view)

        layout = BaseFormLayout()
        self.fill_layout(layout)

        self.addLayout(layout)

        if not self.readonly:
            buttons_layout = QHBoxLayout()

            self.btn_add = QPushButton(self.tr("Add"))
            self.btn_add.clicked.connect(self.add_record)
            buttons_layout.addWidget(self.btn_add)
            self.btn_save = QPushButton(self.tr("Save"))
            self.btn_save.clicked.connect(self.save_record)
            self.btn_save.setDisabled(True)
            buttons_layout.addWidget(self.btn_save)
            self.btn_delete = QPushButton(self.tr("Delete"))
            self.btn_delete.clicked.connect(self.delete_record)
            self.btn_delete.setDisabled(True)
            buttons_layout.addWidget(self.btn_delete)

            self.addLayout(buttons_layout)

        self.current_row = -1

    def get_items(self):
        additional_type = 0
        if self.readonly:
            additional_type = Type.Disabled

        old_enable_bc = self.settings['enable_bc']
        self.settings['enable_bc'] = False
        items = []
        for field in self.fields:
            section = None
            if not self.readonly:
                if self.reference:
                    section = self.reference.section(field.name)

            item = FormItem(self.settings, field.name, field.title, field.type | additional_type,
                     section=section, reference=self.reference)
            if not field.enabled:
                item.setHidden()
            items.append(item)
        self.settings['enable_bc'] = old_enable_bc

        return items

    def fill_layout(self, layout):
        pass

    def handle_row_click(self, index):
        self.current_row = index.row()
        for i, item in enumerate(self.items):
            table_item = self.model.item(self.current_row, i)
            if table_item:
                value = table_item.data(Qt.UserRole)
                item.setValue(value)
            else:
                item.clear()

        if not self.readonly:
            self.btn_save.setEnabled(True)
            self.btn_delete.setEnabled(True)

    def save_record(self):
        if self.current_row != -1:
            for i, item in enumerate(self.items):
                data = item.value()
                if data:
                    field = self.fields.field(item.field())
                    text = self._format_data(field, data)
                    icon = self._format_icon(field, data)

                    table_item = QStandardItem(text)
                    table_item.setData(data, Qt.UserRole)
                    if icon:
                        table_item.setData(icon, Qt.DecorationRole)
                    self.model.setItem(self.current_row, i, table_item)
                else:
                    index = self.model.index(self.current_row, i);
                    self.model.clearItemData(index)

            return True

        return False

    def add_record(self):
        row = self.model.rowCount()
        self.model.insertRow(row)

        self.table_view.selectRow(row)
        index = self.model.index(row, 0)
        self.handle_row_click(index)

    def delete_record(self):
        if self.current_row != -1:
            key = f"show_warn/confirm_delete_{self.__class__.__name__}"
            settings = QSettings()
            show = settings.value(key, True, type=bool)
            if show:
                msg_box = QMessageBox(QMessageBox.Warning, self.tr("Delete"),
                                      self.tr("Are you sure to remove entry?"),
                                      QMessageBox.Yes | QMessageBox.Cancel,
                                      self.parent)
                msg_box.setDefaultButton(QMessageBox.Cancel)
                cb = QCheckBox(self.tr("Don't show this again"))
                msg_box.setCheckBox(cb)
                result = msg_box.exec()
                if result != QMessageBox.Yes:
                    return
                else:
                    if cb.isChecked():
                        settings.setValue(key, False)

            self.model.removeRow(self.current_row)

            self.current_row = -1
            for item in self.items:
                item.clear()
            self.table_view.selectionModel().clearSelection()
            self.btn_save.setDisabled(True)
            self.btn_delete.setDisabled(True)

    def fill(self, data):
        header = self.table_view.horizontalHeader()
        header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.model.setRowCount(0)

        row_idx = 0
        for row_data in data:
            for i, field in enumerate(self.fields):
                data = row_data[i]
                if data:
                    text = self._format_data(field, data)
                    icon = self._format_icon(field, data)

                    table_item = QStandardItem(text)
                    table_item.setData(data, Qt.UserRole)
                    if icon:
                        table_item.setData(icon, Qt.DecorationRole)
                    self.model.setItem(row_idx, i, table_item)
            row_idx += 1

        if row_idx > 0:
            self.table_view.selectRow(row_idx - 1)
            index = self.model.index(row_idx - 1, 0)
            self.handle_row_click(index)
        else:
            self.current_row = -1
            for item in self.items:
                item.clear()

    def getData(self):
        data = []
        for r in range(self.model.rowCount()):
            row_data = []
            for c in range(self.model.columnCount()):
                item = self.model.item(r, c)
                if item:
                    value = item.data(Qt.UserRole)
                    row_data.append(value)
                else:
                    row_data.append(None)
            data.append(row_data)
        return data

    def _format_data(self, field, data):
        try:
            if field.type == Type.Money:
                text = self.locale.toString(float(data), 'f', precision=2)
                dp = self.locale.decimalPoint()
                text = text.rstrip('0').rstrip(dp)
            elif field.type == Type.Date:
                date = QDate.fromString(data, Qt.ISODate)
                text = self.locale.toString(date, QLocale.ShortFormat)
            elif field.name == 'action':
                text = data
                for act, title in self.Actions:
                    if act == data:
                        text = title
                        break
            else:
                text = str(data)
        except (ValueError, TypeError):
            text = str(data)

        return text

    def _format_icon(self, field, data):
        icon = None
        if field.name == 'action':
            for act, _ in self.Actions:
                if act == data:
                    if act == 'sell':
                        icon = statusIcon('sold')
                    elif act == 'auction':
                        icon = statusIcon('pass')
                    else:
                        icon = statusIcon('owned')
                    break
        else:
            icon = self.reference.getIcon(field.name, data)
        return icon


class CatalogTableLayout(BaseExtTableLayout):

    def fill_layout(self, layout):
        layout.addRow(self.items[0], self.items[1])
        layout.addRow(self.items[2], self.items[3])
        layout.addRow(self.items[4], self.items[5])
        layout.addRow(self.items[6], self.items[7])
        layout.addRow(self.items[8], self.items[9])
        layout.addRow(self.items[10], self.items[11])


class PricesTableLayout(BaseExtTableLayout):

    def fill_layout(self, layout):
        layout.addRow(self.items[0], self.items[1])
        layout.addRow(self.items[2], self.items[7])
        layout.addRow(self.items[3], self.items[5])
        layout.addRow(self.items[6], self.items[4])
        layout.addRow(self.items[13], self.items[10])
        layout.addRow(self.items[9], self.items[11])
        layout.addRow(self.items[12])
        layout.addRow(self.items[8])
