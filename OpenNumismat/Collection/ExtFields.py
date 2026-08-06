from dataclasses import dataclass

from PySide6.QtCore import QObject
from PySide6.QtSql import QSqlQuery

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type


@dataclass(slots=True)
class ExtField:
    name: str
    title: str
    type: int
    position: int
    enabled: bool = True
    width: int = 100


class ExtFields(QObject):

    def __init__(self, table, db, parent):
        super().__init__(parent)

        self.table = table
        self.db = db
        self.fields = []
        self.index = 0

        if table == 'catalogs':
            deafult_fields = self._default_catalog_fields()
        elif table == 'prices':
            deafult_fields = self._default_prices_fields()

        for i, field_data in enumerate(deafult_fields):
            field = ExtField(field_data[0], field_data[1], field_data[2], i, field_data[3])
            self.fields.append(field)

        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM ext_column_settings WHERE table_name=?")
        query.addBindValue(self.table)
        query.exec()
        while query.next():
            record = query.record()
            field_name = record.value('column_name')
            field = self.field(field_name)

            field.title = record.value('title')
            field.enabled = record.value('enabled')
            field.position = record.value('position')
            field.width = record.value('width')

    def field(self, name):
        for field in self.fields:
            if field.name == name:
                return field

    def names(self):
        return [field.name for field in self.fields]

    def __len__(self):
        return len(self.fields)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index == len(self.fields):
            raise StopIteration
        self.index = self.index + 1
        return self.fields[self.index - 1]

    def _default_catalog_fields(self):
        return (
            ('catalog', self.tr("Catalog"), Type.String, True),
            ('year', self.tr("Year"), Type.Number, True),
            ('number', self.tr("#"), Type.String, True),
            ('currency', self.tr("Currency"), Type.String, False),
            ('price8', self.tr("MS-65"), Type.Money, False),
            ('price7', self.tr("MS-63"), Type.Money, False),
            ('price6', self.tr("BU"), Type.Money, True),
            ('price5', self.tr("Unc"), Type.Money, True),
            ('price4', self.tr("AU"), Type.Money, True),
            ('price3', self.tr("XF"), Type.Money, True),
            ('price2', self.tr("VF"), Type.Money, True),
            ('price1', self.tr("Fine"), Type.Money, True),
        )

    def _default_prices_fields(self):
        return (
            ('action', self.tr("Action"), Type.String, True),
            ('date', self.tr("Date"), Type.Date, True),
            ('quantity', self.tr("Quantity"), Type.BigInt, True),
            ('price', self.tr("Price"), Type.Money, True),
            ('currency', self.tr("Currency"), Type.String, False),
            ('total_price', self.tr("Total price"), Type.Money, True),
            ('shipping', self.tr("Shipping"), Type.Money, False),
            ('grade', self.tr("Grade"), Type.String, True),
            ('url', self.tr("URL"), Type.String, True),
            ('place', self.tr("Place"), Type.String, True),
            ('number', self.tr("#"), Type.String, False),
            ('counterparty', self.tr("Counterparty"), Type.String, True),
            ('info', self.tr("Info"), Type.Text, True),
            ('start_bid', self.tr("Start bid"), Type.Money, False),
        )
