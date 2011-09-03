from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type
from PyQt4 import QtGui

class ImagesLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ImagesLayout, self).__init__(parent)

        self.addItem('photo1', "Photo 1", Type.Image)
        self.addItem('photo2', "Photo 2", Type.Image)
        self.addItem('photo3', "Photo 3", Type.Image)
        self.addItem('photo4', "Photo 4", Type.Image)
        
        item = self.item('photo1')
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(), 0, 0)
        self.addWidget(item.widget(), 1, 0)
        item = self.item('photo2')
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(),0,1)
        self.addWidget(item.widget(),1,1)
        item = self.item('photo3')
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(),2,0)
        self.addWidget(item.widget(),3,0)
        item = self.item('photo4')
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(item.label(),2,1)
        self.addWidget(item.widget(),3,1)

        self.setRowMinimumHeight(1, 120)
        self.setRowMinimumHeight(3, 120)
        self.setColumnMinimumWidth(0, 160)
        self.setColumnMinimumWidth(1, 160)

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
