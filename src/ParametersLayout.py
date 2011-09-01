from PyQt4 import QtGui

from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item

class ParametersLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ParametersLayout, self).__init__(parent)
        
        self.items = [ Item('metal', "Metal", parent), 
            Item('probe', "Probe", parent), Item('form', "Form", parent),
            Item('diameter', "Diameter", parent), Item('thick', "Thick", parent),
            Item('mass', "Mass", parent), Item('obvrev', "ObvRev", parent) ]
        
        item = self.items[0]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item1 = self.items[1]
        item1.setWidget(QtGui.QLineEdit(parent))
        item2 = self.items[5]
        item2.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item1, item2)

        item1 = self.items[3]
        item1.setWidget(QtGui.QLineEdit(parent))
        item2 = self.items[4]
        item2.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item1, item2)

        item = self.items[2]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[6]
        item.setWidget(QtGui.QLineEdit(parent))
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
