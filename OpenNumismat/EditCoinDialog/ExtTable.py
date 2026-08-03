from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlTableModel
from PySide6.QtWidgets import QDataWidgetMapper, QTableView, QVBoxLayout

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.BaseFormLayout import BaseFormLayout, FormItem


class ExtTableLayout(QVBoxLayout):

    def __init__(self, settings, db, table, parent):
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

        self.items = (
            FormItem(settings, 'catalog', self.tr("Catalog"), Type.String),
            FormItem(settings, 'catalogs.year', self.tr("Year"), Type.Number),
            FormItem(settings, 'number', self.tr("#"), Type.String),
            FormItem(settings, 'currency', self.tr("Currency"), Type.String),
            FormItem(settings, 'price8', self.tr("Price 8"), Type.Money),
            FormItem(settings, 'price7', self.tr("Price 7"), Type.Money),
            FormItem(settings, 'price6', self.tr("BU"), Type.Money),
            FormItem(settings, 'price5', self.tr("Unc"), Type.Money),
            FormItem(settings, 'price4', self.tr("AU"), Type.Money),
            FormItem(settings, 'price3', self.tr("XF"), Type.Money),
            FormItem(settings, 'price2', self.tr("VF"), Type.Money),
            FormItem(settings, 'price1', self.tr("Fine"), Type.Money),
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

    def handle_row_click(self, index):
        target_row = index.row()
        self.mapper.setCurrentIndex(target_row)

    def fill(self, record):
        coin_id = record.value('id')
        self.model.setFilter(f"coin_id = {coin_id}")

        self.mapper.setCurrentIndex(-1)
        for item in self.items:
            item.clear()
