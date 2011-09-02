from PyQt4 import QtGui

from BaseFormLayout import FormItem as Item
from BaseFormLayout import LineEdit, ShortLineEdit, NumberEdit, ValueEdit, TextEdit
from ImageLabel import ImageLabel

class ReverseDesignLayout(QtGui.QGridLayout):
    def __init__(self, record, parent=None):
        super(ReverseDesignLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.items = [ Item('reverseimg', "", parent),
            Item('reversedesign', "Design", parent),
            Item('reversedesigner', "Designer", parent) ]

        item = self.items[0]
        item.setWidget(ImageLabel(parent))
        self.setColumnMinimumWidth(2, 160)
        self.addWidget(item.widget(), 0, 2, 2, 1)
        
        item = self.items[1]
        item.setWidget(TextEdit(parent))
        self.addWidget(item.label(), 0, 0)
        self.addWidget(item.widget(), 0, 1)

        item = self.items[2]
        item.setWidget(LineEdit(parent))
        self.addWidget(item.label(), 1, 0)
        self.addWidget(item.widget(), 1, 1)

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
