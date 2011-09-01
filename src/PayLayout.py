from PyQt4 import QtGui

from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item

class PayLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(PayLayout, self).__init__(parent)
        
        self.items = [ Item('paydate', "Date", parent), 
            Item('payprice', "Price", parent), Item('saller', "Saller", parent),
            Item('payplace', "Place", parent), Item('payinfo', "Info", parent) ]
        
        item1 = self.items[0]
        item1.setWidget(QtGui.QLineEdit(parent))
        item2 = self.items[1]
        item2.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item1, item2)

        item = self.items[2]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[3]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[4]
        item.setWidget(QtGui.QTextEdit(parent))
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
