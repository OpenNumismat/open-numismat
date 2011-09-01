from PyQt4 import QtGui

from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item

class SubjectLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(SubjectLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.items = [ Item('subject', "Subject", parent) ]
        
        item = self.items[0]
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
