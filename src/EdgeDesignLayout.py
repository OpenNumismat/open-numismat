from BaseFormLayout import BaseFormLayout
from BaseFormLayout import LineEdit, ShortLineEdit, NumberEdit, ValueEdit
from BaseFormLayout import FormItem as Item
from ImageLabel import ImageLabel

class EdgeDesignLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(EdgeDesignLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.items = [ Item('edgeimg', "", parent),
            Item('edge', "Type", parent), 
            Item('edgelabel', "Label", parent) ]

        item = self.items[0]
        item.setWidget(ImageLabel(parent))
        self.setColumnMinimumWidth(2, 160)
        self.addWidget(item.widget(), 0, 2, 2, 1)
        
        item = self.items[1]
        item.setWidget(LineEdit(parent))
        self.addRow(item)

        item = self.items[2]
        item.setWidget(LineEdit(parent))
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
