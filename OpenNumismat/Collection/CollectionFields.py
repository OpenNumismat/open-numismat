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
    Keys = ('demo', 'pass', 'owned', 'ordered', 'sold', 'sale', 'wish')
    Titles = (
        QT_TRANSLATE_NOOP("Status", "Demo"),
        QT_TRANSLATE_NOOP("Status", "Pass"),
        QT_TRANSLATE_NOOP("Status", "Owned"),
        QT_TRANSLATE_NOOP("Status", "Ordered"),
        QT_TRANSLATE_NOOP("Status", "Sold"),
        QT_TRANSLATE_NOOP("Status", "Sale"),
        QT_TRANSLATE_NOOP("Status", "Wish"),
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
        super(CollectionFieldsBase, self).__init__(parent)

        fields = [
                ('id', self.tr("ID"), Type.BigInt),

                ('title', self.tr("Name"), Type.String),
                ('value', self.tr("Value"), Type.Money),
                ('unit', self.tr("Unit"), Type.String),
                ('country', self.tr("Country"), Type.String),
                ('year', self.tr("Year"), Type.Number),
                ('period', self.tr("Period"), Type.String),
                ('mint', self.tr("Mint"), Type.String),
                ('mintmark', self.tr("Mint mark"), Type.ShortString),
                ('issuedate', self.tr("Date of issue"), Type.Date),
                ('type', self.tr("Type"), Type.String),
                ('series', self.tr("Series"), Type.String),
                ('subjectshort', self.tr("Subject"), Type.String),
                ('status', self.tr("Status"), Type.Status),
                ('material', self.tr("Material"), Type.String),
                ('fineness', self.tr("Fineness"), Type.Number),  # 4 digits for Canadian Gold Maple Leaf
                ('shape', self.tr("Shape"), Type.String),
                ('diameter', self.tr("Diameter"), Type.Value),
                ('thickness', self.tr("Thickness"), Type.Value),
                ('weight', self.tr("Weight"), Type.Value),
                ('grade', self.tr("Grade"), Type.String),
                ('edge', self.tr("Type"), Type.String),
                ('edgelabel', self.tr("Label"), Type.String),
                ('obvrev', self.tr("ObvRev"), Type.String),
                ('quality', self.tr("Quality"), Type.String),
                ('mintage', self.tr("Mintage"), Type.BigInt),
                ('dateemis', self.tr("Emission period"), Type.String),
                ('catalognum1', self.tr("1#"), Type.String),
                ('catalognum2', self.tr("2#"), Type.String),
                ('catalognum3', self.tr("3#"), Type.String),
                ('catalognum4', self.tr("4#"), Type.String),
                ('rarity', self.tr("Rarity"), Type.String),
                ('price1', self.tr("Fine"), Type.Money),
                ('price2', self.tr("VF"), Type.Money),
                ('price3', self.tr("XF"), Type.Money),
                ('price4', self.tr("Unc"), Type.Money),
                ('variety', self.tr("Variety"), Type.String),
                ('obversevar', self.tr("Obverse"), Type.String),
                ('reversevar', self.tr("Reverse"), Type.String),
                ('edgevar', self.tr("Edge"), Type.String),
                ('paydate', self.tr("Date"), Type.Date),
                ('payprice', self.tr("Price"), Type.Money),
                ('totalpayprice', self.tr("Paid"), Type.Money),
                ('seller', self.tr("Seller"), Type.String),
                ('payplace', self.tr("Place"), Type.String),
                ('payinfo', self.tr("Info"), Type.Text),
                ('saledate', self.tr("Date"), Type.Date),
                ('saleprice', self.tr("Price"), Type.Money),
                ('totalsaleprice', self.tr("Bundled"), Type.Money),
                ('buyer', self.tr("Buyer"), Type.String),
                ('saleplace', self.tr("Place"), Type.String),
                ('saleinfo', self.tr("Info"), Type.Text),
                ('note', self.tr("Note"), Type.Text),
                ('image', self.tr("Image"), Type.PreviewImage),
                ('obverseimg', self.tr("Obverse"), Type.Image),
                ('obversedesign', self.tr("Design"), Type.Text),
                ('obversedesigner', self.tr("Designer"), Type.String),
                ('reverseimg', self.tr("Reverse"), Type.Image),
                ('reversedesign', self.tr("Design"), Type.Text),
                ('reversedesigner', self.tr("Designer"), Type.String),
                ('edgeimg', self.tr("Edge"), Type.EdgeImage),
                ('subject', self.tr("Subject"), Type.Text),
                ('photo1', self.tr("Photo 1"), Type.Image),
                ('photo2', self.tr("Photo 2"), Type.Image),
                ('photo3', self.tr("Photo 3"), Type.Image),
                ('photo4', self.tr("Photo 4"), Type.Image),
                ('defect', self.tr("Defect"), Type.String),
                ('storage', self.tr("Storage"), Type.String),
                ('features', self.tr("Features"), Type.Text),
                ('createdat', self.tr("Created at"), Type.DateTime),
                ('updatedat', self.tr("Updated at"), Type.DateTime),
                ('quantity', self.tr("Quantity"), Type.BigInt),
                ('url', self.tr("URL"), Type.String),
                ('barcode', self.tr("Barcode"), Type.String),
            ]

        self.fields = []
        for id_, field in enumerate(fields):
            self.fields.append(
                            CollectionField(id_, field[0], field[1], field[2]))
            setattr(self, self.fields[id_].name, self.fields[id_])

        self.systemFields = [self.id, self.createdat, self.updatedat, self.image]
        self.userFields = list(self.fields)
        for item in [self.id, self.createdat, self.updatedat]:
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
        super(CollectionFields, self).__init__(parent)
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
