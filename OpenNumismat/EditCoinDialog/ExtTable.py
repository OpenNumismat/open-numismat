from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QTableView, QVBoxLayout

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.BaseFormLayout import BaseFormLayout, FormItem


class ExtTableLayout(QVBoxLayout):

    def __init__(self, settings, readonly, parent):
        super().__init__()

        additional_type = 0
        if readonly:
            additional_type = Type.Disabled

        self.items = (
            FormItem(settings, 'catalog', self.tr("Catalog"), Type.String | additional_type),
            FormItem(settings, 'catalogs.year', self.tr("Year"), Type.Number | additional_type),
            FormItem(settings, 'number', self.tr("#"), Type.String | additional_type),
            FormItem(settings, 'currency', self.tr("Currency"), Type.String | additional_type),
            FormItem(settings, 'price8', self.tr("Price 8"), Type.Money | additional_type),
            FormItem(settings, 'price7', self.tr("Price 7"), Type.Money | additional_type),
            FormItem(settings, 'price6', self.tr("BU"), Type.Money | additional_type),
            FormItem(settings, 'price5', self.tr("Unc"), Type.Money | additional_type),
            FormItem(settings, 'price4', self.tr("AU"), Type.Money | additional_type),
            FormItem(settings, 'price3', self.tr("XF"), Type.Money | additional_type),
            FormItem(settings, 'price2', self.tr("VF"), Type.Money | additional_type),
            FormItem(settings, 'price1', self.tr("Fine"), Type.Money | additional_type),
        )

        self.model = QStandardItemModel(0, len(self.items), self)

        for i, item in enumerate(self.items):
            self.model.setHeaderData(i, Qt.Horizontal, item.title())

        self.table_view = QTableView(parent)
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.verticalHeader().hide()
        self.table_view.clicked.connect(self.handle_row_click)

        self.addWidget(self.table_view)

        layout = BaseFormLayout()

        layout.addRow(self.items[0], self.items[1])
        layout.addRow(self.items[2], self.items[3])
        layout.addRow(self.items[4], self.items[5])
        layout.addRow(self.items[6], self.items[7])
        layout.addRow(self.items[8], self.items[9])
        layout.addRow(self.items[10], self.items[11])

        self.addLayout(layout)

        if not readonly:
            buttons_layout = QHBoxLayout()

            self.btn_save = QPushButton(self.tr("Save"))
            self.btn_save.clicked.connect(self.save_record)
            buttons_layout.addWidget(self.btn_save)
            self.btn_add = QPushButton(self.tr("Add"))
            self.btn_add.clicked.connect(self.add_record)
            buttons_layout.addWidget(self.btn_add)
            self.btn_delete = QPushButton(self.tr("Delete"))
            self.btn_delete.clicked.connect(self.delete_record)
            buttons_layout.addWidget(self.btn_delete)

            self.addLayout(buttons_layout)

        self.current_row = -1

    def handle_row_click(self, index):
        target_row = index.row()
        if target_row == self.current_row:
            return

        self.current_row = target_row
        for i, item in enumerate(self.items):
            table_item = self.model.item(self.current_row, i)
            if table_item:
                value = table_item.data(Qt.EditRole)
                item.setValue(value)
            else:
                item.clear()

    def save_record(self):
        if self.current_row != -1:
            for i, item in enumerate(self.items):
                value = item.value()
                if value:
                    table_item = QStandardItem(str(value))
                    table_item.setData(value, Qt.EditRole)
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
        self.current_row = row
        for item in self.items:
            item.clear()

    def delete_record(self):
        if self.current_row != -1:
            self.model.removeRow(self.current_row)

            self.current_row = -1
            for item in self.items:
                item.clear()
            self.table_view.selectionModel().clearSelection()

    def fill(self, record):
        self.model.setRowCount(0)

        row_idx = 0
        catalogs_data = record.value('catalogs')
        for catalog_data in catalogs_data:
            for i, item in enumerate(self.items):
                value = catalog_data[i]
                if value:
                    table_item = QStandardItem(str(value))
                    table_item.setData(value, Qt.EditRole)
                    self.model.setItem(row_idx, i, table_item)
            row_idx += 1

        self.current_row = -1
        for item in self.items:
            item.clear()

    def getCatalogs(self):
        catalogs = []
        for r in range(self.model.rowCount()):
            row = []
            for c in range(self.model.columnCount()):
                item = self.model.item(r, c)
                if item:
                    value = item.data(Qt.EditRole)
                    row.append(value)
                else:
                    row.append(None)
            catalogs.append(row)
        return catalogs
