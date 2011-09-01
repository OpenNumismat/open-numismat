from PyQt4 import QtGui

from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item

class ClassificationLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ClassificationLayout, self).__init__(parent)
        
        self.items = [ Item('catalognum1', "#", parent), 
            Item('catalognum2', "#", parent), Item('catalognum3', "#", parent),
            Item('rarity', "Rarity", parent), Item('price1', "Fine", parent),
            Item('price2', "VF", parent), Item('price3', "XF", parent),
            Item('price4', "AU", parent), Item('price5', "Unc", parent),
            Item('price6', "Proof", parent) ]
        
        item = self.items[0]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[1]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[2]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[3]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item1 = self.items[4]
        item1.setWidget(QtGui.QLineEdit(parent))
        item2 = self.items[5]
        item2.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item1, item2)

        item1 = self.items[6]
        item1.setWidget(QtGui.QLineEdit(parent))
        item2 = self.items[7]
        item2.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item1, item2)

        item1 = self.items[8]
        item1.setWidget(QtGui.QLineEdit(parent))
        item2 = self.items[9]
        item2.setWidget(QtGui.QLineEdit(parent))
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
