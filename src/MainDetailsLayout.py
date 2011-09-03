from PyQt4 import QtGui

from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type

class MainDetailsLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(MainDetailsLayout, self).__init__(parent)
        self.columnCount = 5
        
        self.items = [ Item('title', "Name", Type.String, parent), 
            Item('value', "Value", Type.Money, parent),
            Item('unit', "Unit", Type.String, parent),
            Item('country', "Country", Type.String, parent),
            Item('year', "Year", Type.Number, parent),
            Item('period', "Period", Type.String, parent),
            Item('mint', "Mint", Type.String, parent),
            Item('mintmark', "Mint mark", Type.ShortString, parent),
            Item('type', "Type", Type.String, parent),
            Item('series', "Series", Type.String, parent) ]

        item = self.items[0]
        btn = QtGui.QPushButton(self.tr("Generate"), parent)
        btn.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        btn.clicked.connect(self.clickGenerate)
        self.addRow(item, btn)

        item = self.items[3]
        self.addRow(item)

        item = self.items[5]
        self.addRow(item)

        item1 = self.items[1]
        item2 = self.items[2]
        self.addRow(item1, item2)

        item = self.items[4]
        self.addRow(item)

        item1 = self.items[7]
        item2 = self.items[6]
        self.addRow(item1, item2)

        item = self.items[8]
        self.addRow(item)

        item = self.items[9]
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
    
    def clickGenerate(self):
        titleParts = []
        value = str(self.items[1].value())
        if value:
            titleParts.append(value) 
        value = str(self.items[2].value())
        if value:
            titleParts.append(value)
        value = str(self.items[4].value())
        if value:
            titleParts.append(value)
        value = str(self.items[7].value())
        if value:
            titleParts.append(value)

        title = ' '.join(titleParts)
        self.items[0].widget().setText(title)

if __name__ == '__main__':
    from main import run
    run()
