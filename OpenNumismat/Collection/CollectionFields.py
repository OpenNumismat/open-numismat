from PyQt5.QtCore import QT_TRANSLATE_NOOP, QObject
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlDatabase, QSqlQuery


class FieldTypes():
    String = 1
    ShortString = 2
    Number = 3
    Text = 4
    Money = 5
    Date = 6
    BigInt = 7
    Image = 8
    Value = 9
    Status = 10
    DateTime = 11
    EdgeImage = 12
    PreviewImage = 13
    Denomination = 14

    Mask = 0xFF
    Checkable = 0x100
    Disabled = 0x200

    ImageTypes = (Image, EdgeImage, PreviewImage)

    @staticmethod
    def toSql(type_):
        if type_ == FieldTypes.String:
            sql_type = 'TEXT'
        elif type_ == FieldTypes.ShortString:
            sql_type = 'TEXT'
        elif type_ == FieldTypes.Number:
            sql_type = 'INTEGER'
        elif type_ == FieldTypes.Text:
            sql_type = 'TEXT'
        elif type_ == FieldTypes.Money:
            sql_type = 'NUMERIC'
        elif type_ == FieldTypes.Denomination:
            sql_type = 'NUMERIC'
        elif type_ == FieldTypes.Date:
            sql_type = 'TEXT'
        elif type_ == FieldTypes.BigInt:
            sql_type = 'INTEGER'
        elif type_ == FieldTypes.PreviewImage:
            sql_type = 'INTEGER'
        elif type_ == FieldTypes.Image:
            sql_type = 'INTEGER'
        elif type_ == FieldTypes.Value:
            sql_type = 'NUMERIC'
        elif type_ == FieldTypes.Status:
            sql_type = 'TEXT'
        elif type_ == FieldTypes.DateTime:
            sql_type = 'TEXT'
        elif type_ == FieldTypes.EdgeImage:
            sql_type = 'INTEGER'
        else:
            raise

        return sql_type


class Status(dict):
    Keys = ('demo', 'pass', 'owned', 'ordered',
            'sold', 'sale', 'wish', 'missing')
    Titles = (
        QT_TRANSLATE_NOOP("Status", "Demo"),
        QT_TRANSLATE_NOOP("Status", "Pass"),
        QT_TRANSLATE_NOOP("Status", "Owned"),
        QT_TRANSLATE_NOOP("Status", "Ordered"),
        QT_TRANSLATE_NOOP("Status", "Sold"),
        QT_TRANSLATE_NOOP("Status", "Sale"),
        QT_TRANSLATE_NOOP("Status", "Wish"),
        QT_TRANSLATE_NOOP("Status", "Missing"),
    )

    def __init__(self):
        for key, value in zip(self.Keys, self.Titles):
            dict.__setitem__(self, key, value)

    def keys(self):
        return self.Keys

    def items(self):
        result = []
        for key in self.Keys:
            result.append((key, self.__getitem__(key)))
        return result

    def values(self):
        result = []
        for key in self.Keys:
            result.append(self.__getitem__(key))
        return result

    def __getitem__(self, key):
        try:
            if isinstance(key, int):
                value = dict.__getitem__(self, self.Keys[key])
            else:
                value = dict.__getitem__(self, key)
            return QApplication.translate("Status", value)
        except KeyError:
            return None


Statuses = Status()


class CollectionField():
    def __init__(self, id_, name, title, type_):
        self.id = id_
        self.name = name
        self.title = title
        self.type = type_


class CollectionFieldsBase(QObject):
    def __init__(self, parent=None):
        from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
        super().__init__(parent)

        fields = [
                ('id', QApplication.translate('CollectionFieldsBase', "ID"), Type.BigInt),

                ('title', QApplication.translate('CollectionFieldsBase', "Name"), Type.String),
                ('value', QApplication.translate('CollectionFieldsBase', "Value"), Type.Denomination),
                ('unit', QApplication.translate('CollectionFieldsBase', "Unit"), Type.String),
                ('country', QApplication.translate('CollectionFieldsBase', "Country"), Type.String),
                ('year', QApplication.translate('CollectionFieldsBase', "Year"), Type.Number),
                ('period', QApplication.translate('CollectionFieldsBase', "Period"), Type.String),
                ('mint', QApplication.translate('CollectionFieldsBase', "Mint"), Type.String),
                ('mintmark', QApplication.translate('CollectionFieldsBase', "Mint mark"), Type.ShortString),
                ('issuedate', QApplication.translate('CollectionFieldsBase', "Date of issue"), Type.Date),
                ('type', QApplication.translate('CollectionFieldsBase', "Type"), Type.String),
                ('series', QApplication.translate('CollectionFieldsBase', "Series"), Type.String),
                ('subjectshort', QApplication.translate('CollectionFieldsBase', "Subject"), Type.String),
                ('status', QApplication.translate('CollectionFieldsBase', "Status"), Type.Status),
                ('material', QApplication.translate('CollectionFieldsBase', "Material"), Type.String),
                ('fineness', QApplication.translate('CollectionFieldsBase', "Fineness"), Type.Number),  # 4 digits for Canadian Gold Maple Leaf
                ('shape', QApplication.translate('CollectionFieldsBase', "Shape"), Type.String),
                ('diameter', QApplication.translate('CollectionFieldsBase', "Diameter"), Type.Value),
                ('thickness', QApplication.translate('CollectionFieldsBase', "Thickness"), Type.Value),
                ('weight', QApplication.translate('CollectionFieldsBase', "Weight"), Type.Value),
                ('grade', QApplication.translate('CollectionFieldsBase', "Grade"), Type.String),
                ('edge', QApplication.translate('CollectionFieldsBase', "Type"), Type.String),
                ('edgelabel', QApplication.translate('CollectionFieldsBase', "Label"), Type.String),
                ('obvrev', QApplication.translate('CollectionFieldsBase', "ObvRev"), Type.String),
                ('quality', QApplication.translate('CollectionFieldsBase', "Quality"), Type.String),
                ('mintage', QApplication.translate('CollectionFieldsBase', "Mintage"), Type.BigInt),
                ('dateemis', QApplication.translate('CollectionFieldsBase', "Emission period"), Type.String),
                ('catalognum1', QApplication.translate('CollectionFieldsBase', "1#"), Type.String),
                ('catalognum2', QApplication.translate('CollectionFieldsBase', "2#"), Type.String),
                ('catalognum3', QApplication.translate('CollectionFieldsBase', "3#"), Type.String),
                ('catalognum4', QApplication.translate('CollectionFieldsBase', "4#"), Type.String),
                ('rarity', QApplication.translate('CollectionFieldsBase', "Rarity"), Type.String),
                ('price1', QApplication.translate('CollectionFieldsBase', "Fine"), Type.Money),
                ('price2', QApplication.translate('CollectionFieldsBase', "VF"), Type.Money),
                ('price3', QApplication.translate('CollectionFieldsBase', "XF"), Type.Money),
                ('price4', QApplication.translate('CollectionFieldsBase', "Unc"), Type.Money),
                ('variety', QApplication.translate('CollectionFieldsBase', "Variety"), Type.String),
                ('obversevar', QApplication.translate('CollectionFieldsBase', "Obverse"), Type.String),
                ('reversevar', QApplication.translate('CollectionFieldsBase', "Reverse"), Type.String),
                ('edgevar', QApplication.translate('CollectionFieldsBase', "Edge"), Type.String),
                ('paydate', QApplication.translate('CollectionFieldsBase', "Date"), Type.Date),
                ('payprice', QApplication.translate('CollectionFieldsBase', "Price"), Type.Money),
                ('totalpayprice', QApplication.translate('CollectionFieldsBase', "Paid"), Type.Money),
                ('saller', QApplication.translate('CollectionFieldsBase', "Seller"), Type.String),
                ('payplace', QApplication.translate('CollectionFieldsBase', "Place"), Type.String),
                ('payinfo', QApplication.translate('CollectionFieldsBase', "Info"), Type.Text),
                ('saledate', QApplication.translate('CollectionFieldsBase', "Date"), Type.Date),
                ('saleprice', QApplication.translate('CollectionFieldsBase', "Price"), Type.Money),
                ('totalsaleprice', QApplication.translate('CollectionFieldsBase', "Bailed"), Type.Money),
                ('buyer', QApplication.translate('CollectionFieldsBase', "Buyer"), Type.String),
                ('saleplace', QApplication.translate('CollectionFieldsBase', "Place"), Type.String),
                ('saleinfo', QApplication.translate('CollectionFieldsBase', "Info"), Type.Text),
                ('note', QApplication.translate('CollectionFieldsBase', "Note"), Type.Text),
                ('image', QApplication.translate('CollectionFieldsBase', "Image"), Type.PreviewImage),
                ('obverseimg', QApplication.translate('CollectionFieldsBase', "Obverse"), Type.Image),
                ('obversedesign', QApplication.translate('CollectionFieldsBase', "Design"), Type.Text),
                ('obversedesigner', QApplication.translate('CollectionFieldsBase', "Designer"), Type.String),
                ('reverseimg', QApplication.translate('CollectionFieldsBase', "Reverse"), Type.Image),
                ('reversedesign', QApplication.translate('CollectionFieldsBase', "Design"), Type.Text),
                ('reversedesigner', QApplication.translate('CollectionFieldsBase', "Designer"), Type.String),
                ('edgeimg', QApplication.translate('CollectionFieldsBase', "Edge"), Type.EdgeImage),
                ('subject', QApplication.translate('CollectionFieldsBase', "Subject"), Type.Text),
                ('photo1', QApplication.translate('CollectionFieldsBase', "Photo 1"), Type.Image),
                ('photo2', QApplication.translate('CollectionFieldsBase', "Photo 2"), Type.Image),
                ('photo3', QApplication.translate('CollectionFieldsBase', "Photo 3"), Type.Image),
                ('photo4', QApplication.translate('CollectionFieldsBase', "Photo 4"), Type.Image),
                ('defect', QApplication.translate('CollectionFieldsBase', "Defect"), Type.String),
                ('storage', QApplication.translate('CollectionFieldsBase', "Storage"), Type.String),
                ('features', QApplication.translate('CollectionFieldsBase', "Features"), Type.Text),
                ('createdat', QApplication.translate('CollectionFieldsBase', "Created at"), Type.DateTime),
                ('updatedat', QApplication.translate('CollectionFieldsBase', "Updated at"), Type.DateTime),
                ('quantity', QApplication.translate('CollectionFieldsBase', "Quantity"), Type.BigInt),
                ('url', QApplication.translate('CollectionFieldsBase', "URL"), Type.String),
                ('barcode', QApplication.translate('CollectionFieldsBase', "Barcode"), Type.String),
                ('ruler', QApplication.translate('CollectionFieldsBase', "Ruler"), Type.String),
                ('region', QApplication.translate('CollectionFieldsBase', "Region"), Type.String),
                ('obverseengraver', QApplication.translate('CollectionFieldsBase', "Engraver"), Type.String),
                ('reverseengraver', QApplication.translate('CollectionFieldsBase', "Engraver"), Type.String),
                ('obversecolor', QApplication.translate('CollectionFieldsBase', "Color"), Type.String),
                ('reversecolor', QApplication.translate('CollectionFieldsBase', "Color"), Type.String),
                ('varietydesc', QApplication.translate('CollectionFieldsBase', "Description"), Type.Text),
                ('varietyimg', QApplication.translate('CollectionFieldsBase', "Variety"), Type.Image),
                ('format', QApplication.translate('CollectionFieldsBase', "Format"), Type.String),
                ('condition', QApplication.translate('CollectionFieldsBase', "Condition"), Type.String),
            ]

        self.fields = []
        for id_, field in enumerate(fields):
            self.fields.append(
                            CollectionField(id_, field[0], field[1], field[2]))
            setattr(self, self.fields[id_].name, self.fields[id_])

        self.systemFields = [self.id, self.createdat, self.updatedat, self.image]
        self.userFields = list(self.fields)
        for item in (self.id, self.createdat, self.updatedat):
            self.userFields.remove(item)

    def field(self, id_):
        return self.fields[id_]

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index == len(self.fields):
            raise StopIteration
        self.index = self.index + 1
        return self.fields[self.index - 1]


class CollectionFields(CollectionFieldsBase):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        if 'fields' not in self.db.tables():
            self.create(self.db)

        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM fields")
        query.exec_()
        self.userFields = []
        self.disabledFields = []
        while query.next():
            record = query.record()
            fieldId = record.value('id')
            field = self.field(fieldId)
            field.title = record.value('title')
            field.enabled = bool(record.value('enabled'))
            if field.enabled:
                self.userFields.append(field)
            else:
                self.disabledFields.append(field)

    def save(self):
        self.db.transaction()

        for field in self.fields:
            query = QSqlQuery(self.db)
            query.prepare("UPDATE fields SET title=?, enabled=? WHERE id=?")
            query.addBindValue(field.title)
            query.addBindValue(int(field.enabled))
            query.addBindValue(field.id)
            query.exec_()

        self.db.commit()

    @staticmethod
    def create(db=QSqlDatabase()):
        db.transaction()

        sql = """CREATE TABLE fields (
            id INTEGER NOT NULL PRIMARY KEY,
            title TEXT,
            enabled INTEGER)"""
        QSqlQuery(sql, db)

        fields = CollectionFieldsBase()

        for field in fields:
            query = QSqlQuery(db)
            query.prepare("""INSERT INTO fields (id, title, enabled)
                VALUES (?, ?, ?)""")
            query.addBindValue(field.id)
            query.addBindValue(field.title)
            enabled = field in fields.userFields
            query.addBindValue(int(enabled))
            query.exec_()

        db.commit()
