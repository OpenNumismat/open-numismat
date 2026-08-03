from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlTableModel
from PySide6.QtWidgets import QDataWidgetMapper, QHBoxLayout, QPushButton, QTableView, QVBoxLayout

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.BaseFormLayout import BaseFormLayout, FormItem


class ExtTableLayout(QVBoxLayout):

    def __init__(self, readonly, settings, db, table, parent):
        super().__init__()

        self.model = QSqlTableModel(self, db)
        self.model.setTable(table)
        # self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnRowChange)
        self.model.select()
        self.model.setFilter("FALSE")

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.SubmitPolicy.ManualSubmit)

        self.table_view = QTableView(parent)
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_view.setEditTriggers(QTableView.NoEditTriggers)
        self.table_view.verticalHeader().hide()
        self.table_view.clicked.connect(self.handle_row_click)

        for column_name in ('id', 'coin_id', 'position'):
            column_index = self.model.fieldIndex(column_name)
            self.table_view.hideColumn(column_index)

        self.addWidget(self.table_view)

        layout = BaseFormLayout()

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

        for item in self.items:
            column_index = self.model.fieldIndex(item.field())
            self.model.setHeaderData(column_index, Qt.Horizontal, item.title())

            self.mapper.addMapping(item.widget(), column_index)

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
        self.coin_id = -1

    def handle_row_click(self, index):
        target_row = index.row()
        if target_row == self.current_row:
            return

        self.current_row = target_row
        self.mapper.setCurrentIndex(target_row)

    def save_record(self):
        if self.current_row != -1:
            self.mapper.submit()
            if self.model.submitAll():
                return True

        return False

    def add_record(self):
        if self.coin_id != -1:
            row = self.model.rowCount()
            self.model.insertRow(row)

            column_index = self.model.fieldIndex('coin_id')
            self.model.setData(self.model.index(row, column_index), self.coin_id)

            if self.model.submitAll():
                self.model.select()
                self.table_view.selectRow(row)
                self.current_row = row
                self.mapper.setCurrentIndex(self.current_row)

    def delete_record(self):
        if self.current_row != -1:
            self.model.removeRow(self.current_row)
            self.model.submitAll()
            self.model.select()

            self.current_row = -1
            self.mapper.setCurrentIndex(-1)
            for item in self.items:
                item.clear()

    def fill(self, record):
        self.coin_id = record.value('id')
        self.model.setFilter(f"coin_id = {self.coin_id}")

        self.current_row = -1
        self.mapper.setCurrentIndex(-1)
        for item in self.items:
            item.clear()
