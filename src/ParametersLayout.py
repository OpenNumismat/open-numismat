from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type

class ParametersLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ParametersLayout, self).__init__(parent)
        
        self.items = [ Item('metal', "Metal", Type.String, parent), 
            Item('fineness', "Fineness", Type.Number, parent),
            Item('form', "Form", Type.String, parent),
            Item('diameter', "Diameter", Type.Value, parent),
            Item('thick', "Thick", Type.Value, parent),
            Item('mass', "Mass", Type.Value, parent),
            Item('obvrev', "ObvRev", Type.String, parent) ]
        
        item = self.items[0]
        self.addRow(item)

        item1 = self.items[1]
        item2 = self.items[5]
        self.addRow(item1, item2)

        item1 = self.items[3]
        item2 = self.items[4]
        self.addRow(item1, item2)

        item = self.items[2]
        self.addRow(item)

        item = self.items[6]
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
