from PyQt4 import QtGui

from .BaseFormLayout import BaseFormLayout
from .BaseFormLayout import FormItemTypes as Type

class MainDetailsLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(MainDetailsLayout, self).__init__(parent)
        self.columnCount = 5
        
        self.addItem('title', "Name", Type.String) 
        self.addItem('value', "Value", Type.Money)
        self.addItem('unit', "Unit", Type.String)
        self.addItem('country', "Country", Type.String)
        self.addItem('year', "Year", Type.Number)
        self.addItem('period', "Period", Type.String)
        self.addItem('mint', "Mint", Type.String)
        self.addItem('mintmark', "Mint mark", Type.ShortString)
        self.addItem('type', "Type", Type.String)
        self.addItem('series', "Series", Type.String)

        btn = QtGui.QPushButton(self.tr("Generate"), parent)
        btn.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        btn.clicked.connect(self.clickGenerate)
        self.addRow(self.item('title'), btn)

        self.addRow(self.item('country'))
        self.addRow(self.item('period'))
        self.addRow(self.item('value'), self.item('unit'))
        self.addRow(self.item('year'))
        self.addRow(self.item('mintmark'), self.item('mint'))
        self.addRow(self.item('type'))
        self.addRow(self.item('series'))

        self.fillItems(record)
    
    def clickGenerate(self):
        titleParts = []
        value = str(self.item('value').value())
        if value:
            titleParts.append(value) 
        value = str(self.item('unit').value())
        if value:
            titleParts.append(value)
        value = str(self.item('year').value())
        if value:
            titleParts.append(value)
        value = str(self.item('mintmark').value())
        if value:
            titleParts.append(value)

        title = ' '.join(titleParts)
        self.items[0].widget().setText(title)
