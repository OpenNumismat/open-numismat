from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type
from PyQt4 import QtGui

from ImageLabel import ImageLabel

class ImagesLayout(QtGui.QGridLayout):
    def __init__(self, record, parent=None):
        super(ImagesLayout, self).__init__(parent)

        self.items = [ Item('photo1', "Photo 1", Type.Image, parent),
            Item('photo2', "Photo 2", Type.Image, parent),
            Item('photo3', "Photo 3", Type.Image, parent),
            Item('photo4', "Photo 4", Type.Image, parent) ]
        
        item = self.items[0]
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(), 0, 0)
        self.addWidget(item.widget(), 1, 0)
        item = self.items[1]
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(),0,1)
        self.addWidget(item.widget(),1,1)
        item = self.items[2]
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(),2,0)
        self.addWidget(item.widget(),3,0)
        item = self.items[3]
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(),2,1)
        self.addWidget(item.widget(),3,1)
        self.setRowMinimumHeight(1, 120)
        self.setRowMinimumHeight(3, 120)
        self.setColumnMinimumWidth(0, 160)
        self.setColumnMinimumWidth(1, 160)

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
