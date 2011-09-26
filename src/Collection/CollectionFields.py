from PyQt4.QtCore import QObject

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
    State = 10
    
    Mask = int('FF', 16)  # 0xFF
    Checkable = int('100', 16)  # 0x100

class CollectionField():
    def __init__(self, id, name, title, type):
        self.id = id
        self.name = name
        self.title = title
        self.type = type

class CollectionFields(QObject):
    def __init__(self):
        from Collection.CollectionFields import FieldTypes as Type
        super(CollectionFields, self).__init__()
        
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
                ('metal', self.tr("Metal"), Type.String),
                ('fineness', self.tr("Fineness"), Type.Number),
                ('form', self.tr("Form"), Type.String),
                ('diameter', self.tr("Diameter"), Type.Value),
                ('thick', self.tr("Thick"), Type.Value),
                ('mass', self.tr("Mass"), Type.Value),
                ('grade', self.tr("Grade"), Type.String),
                ('edge', self.tr("Type"), Type.String),
                ('edgelabel', self.tr("Label"), Type.String),
                ('obvrev', self.tr("ObvRev"), Type.String),
                ('state', self.tr("State"), Type.State),
                ('mintage', self.tr("Mintage"), Type.BigInt),
                ('dateemis', self.tr("Emission period"), Type.String),
                ('catalognum1', self.tr("1#"), Type.String),
                ('catalognum2', self.tr("2#"), Type.String),
                ('catalognum3', self.tr("3#"), Type.String),
                ('rarity', self.tr("Rarity"), Type.ShortString),
                ('price1', self.tr("Fine"), Type.Money),
                ('price2', self.tr("VF"), Type.Money),
                ('price3', self.tr("XF"), Type.Money),
                ('price4', self.tr("AU"), Type.Money),
                ('price5', self.tr("Unc"), Type.Money),
                ('price6', self.tr("Proof"), Type.Money),
                ('obversevar', self.tr("Obverse"), Type.Text),
                ('reversevar', self.tr("Reverse"), Type.Text),
                ('edgevar', self.tr("Edge"), Type.Text),
                ('paydate', self.tr("Date"), Type.Date),
                ('payprice', self.tr("Price"), Type.Money),
                ('saller', self.tr("Saller"), Type.String),
                ('payplace', self.tr("Place"), Type.String),
                ('payinfo', self.tr("Info"), Type.Text),
                ('saledate', self.tr("Date"), Type.Date),
                ('saleprice', self.tr("Price"), Type.Money),
                ('buyer', self.tr("Buyer"), Type.String),
                ('saleplace', self.tr("Place"), Type.String),
                ('saleinfo', self.tr("Info"), Type.Text),
                ('note', self.tr("Note"), Type.Text),
                ('obverseimg', self.tr("Obverse"), Type.Image),
                ('obversedesign', self.tr("Design"), Type.Text),
                ('obversedesigner', self.tr("Designer"), Type.String),
                ('reverseimg', self.tr("Reverse"), Type.Image),
                ('reversedesign', self.tr("Design"), Type.Text),
                ('reversedesigner', self.tr("Designer"), Type.String),
                ('edgeimg', self.tr("Edge"), Type.Image),
                ('subject', self.tr("Subject"), Type.Text),
                ('photo1', self.tr("Photo 1"), Type.Image),
                ('photo2', self.tr("Photo 2"), Type.Image),
                ('photo3', self.tr("Photo 3"), Type.Image),
                ('photo4', self.tr("Photo 4"), Type.Image),
                ('totalpayprice', self.tr("Total price"), Type.Money),
                ('totalsaleprice', self.tr("Total price"), Type.Money)
            ]

        self.fields = []
        for id, field in enumerate(fields):
            self.fields.append(CollectionField(id, field[0], field[1], field[2]))
            setattr(self, self.fields[id].name, self.fields[id])

    def __iter__(self):
        self.index = 0
        return self
    
    def __next__(self):
        if self.index == len(self.fields):
            raise StopIteration
        self.index = self.index + 1
        return self.fields[self.index-1]
