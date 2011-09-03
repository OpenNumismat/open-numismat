from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type

class MintingLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(MintingLayout, self).__init__(parent)
        
        self.items = [ Item('issuedate', "Date of issue", Type.Date, parent), 
            Item('dateemis', "Emission period", Type.String, parent),
            Item('mintage', "Mintage", Type.BigInt, parent) ]
        
        item1 = self.items[0]
        item2 = self.items[2]
        self.addRow(item1, item2)

        item = self.items[1]
        self.addRow(item)

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
