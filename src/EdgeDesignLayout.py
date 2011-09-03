from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type

class EdgeDesignLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(EdgeDesignLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.items = [ Item('edgeimg', "", Type.Image, parent),
            Item('edge', "Type", Type.String, parent), 
            Item('edgelabel', "Label", Type.String, parent) ]

        item = self.items[0]
        self.setColumnMinimumWidth(2, 160)
        self.addWidget(item.widget(), 0, 2, 2, 1)
        
        item = self.items[1]
        self.addRow(item)

        item = self.items[2]
        self.addRow(item)

        if not record.isEmpty():
            for item in self.items:
                if not record.isNull(item.field()):
                    value = record.value(item.field())
                    item.setValue(value)

    def values(self):
        val = {}
        for item in self.items:
            val[item.field()] = item.value()
        return val

if __name__ == '__main__':
    from main import run
    run()
