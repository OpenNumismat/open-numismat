from PyQt4 import QtGui

from ImageLabel import ImageLabel

class ImagesLayout(QtGui.QGridLayout):
    def __init__(self, record, parent=None):
        super(ImagesLayout, self).__init__(parent)

        columns = {'obverseimg': "Obverse", 'reverseimg': "Reverse", 'edgeimg': "Edge", \
                   'photo1': "Photo 1", 'photo2': "Photo 2", 'photo3': "Photo 3"}

        self.images = {}
        for column in columns.keys():
            self.images[column] = ImageLabel(parent)

        imageLabel = QtGui.QLabel(columns['obverseimg'], parent)
        imageLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(imageLabel,0,0)
        self.addWidget(self.images['obverseimg'],1,0)
        imageLabel = QtGui.QLabel(columns['reverseimg'], parent)
        imageLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(imageLabel,0,1)
        self.addWidget(self.images['reverseimg'],1,1)
        imageLabel = QtGui.QLabel(columns['edgeimg'], parent)
        imageLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(imageLabel,0,2)
        self.addWidget(self.images['edgeimg'],1,2)
        imageLabel = QtGui.QLabel(columns['photo1'], parent)
        imageLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(imageLabel,2,0)
        self.addWidget(self.images['photo1'],3,0)
        imageLabel = QtGui.QLabel(columns['photo2'], parent)
        imageLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(imageLabel,2,1)
        self.addWidget(self.images['photo2'],3,1)
        imageLabel = QtGui.QLabel(columns['photo3'], parent)
        imageLabel.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.addWidget(imageLabel,2,2)
        self.addWidget(self.images['photo3'],3,2)
        self.setRowMinimumHeight(1, 120)
        self.setRowMinimumHeight(3, 120)
        self.setColumnMinimumWidth(0, 160)
        self.setColumnMinimumWidth(1, 160)
        self.setColumnMinimumWidth(2, 160)

        if not record.isEmpty():
            for column in columns.keys():
                if not record.isNull(column):
                    self.images[column].loadFromData(record.value(column))
    
    def values(self):
        val = {}
        for column in self.images.keys():
            val[column] = self.images[column].data()
        return val

if __name__ == '__main__':
    from main import run
    run()
