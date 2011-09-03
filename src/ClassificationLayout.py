from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type

class ClassificationLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ClassificationLayout, self).__init__(parent)
        
        self.items = [ Item('catalognum1', "#", Type.String, parent), 
            Item('catalognum2', "#", Type.String, parent),
            Item('catalognum3', "#", Type.String, parent),
            Item('rarity', "Rarity", Type.ShortString, parent),
            Item('price1', "Fine", Type.Money, parent),
            Item('price2', "VF", Type.Money, parent),
            Item('price3', "XF", Type.Money, parent),
            Item('price4', "AU", Type.Money, parent),
            Item('price5', "Unc", Type.Money, parent),
            Item('price6', "Proof", Type.Money, parent) ]
        
        item = self.items[0]
        self.addRow(item)

        item = self.items[1]
        self.addRow(item)

        item = self.items[2]
        self.addRow(item)

        item = self.items[3]
        self.addRow(item)

        item1 = self.items[4]
        item2 = self.items[5]
        self.addRow(item1, item2)

        item1 = self.items[6]
        item2 = self.items[7]
        self.addRow(item1, item2)

        item1 = self.items[8]
        item2 = self.items[9]
        self.addRow(item1, item2)

        if not record.isEmpty():
            for item in self.items:
                if not record.isNull(item.field()):
                    value = record.value(item.field())
                    item.setValue(str(value))

    def values(self):
        val = {}
        for item in self.items:
            val[item.field()] = item.value()
        return val

if __name__ == '__main__':
    from main import run
    run()
