from PyQt4 import QtGui

from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item

class StateLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(StateLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.items = [ Item('state', "State", parent), 
            Item('grade', "Grade", parent), Item('note', "Note", parent) ]
        
        item = self.items[0]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[1]
        item.setWidget(QtGui.QLineEdit(parent))
        self.addRow(item)

        item = self.items[2]
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
