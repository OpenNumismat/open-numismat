from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from ImageLabel import ImageLabel

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, record, parent=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.record = record
        
        columns = {'title': "Name", 'par': 'par'}
        
        labels = {}
        self.edits = {}
        for column in columns.keys():
            self.edits[column] = QtGui.QLineEdit(self)
            labels[column] = QtGui.QLabel(columns[column], self)
        
        row = 0
        layout = QtGui.QGridLayout(self)
        for column in columns.keys():
            layout.addWidget(labels[column], row, 0)
            layout.addWidget(self.edits[column], row, 1)
            row = row + 1
        
        tab = QtGui.QTabWidget(self)

        w = QtGui.QWidget(self)
        w.setLayout(layout)
        tab.addTab(w, self.tr("Coin"))

        columns = {'obverseimg': "Obverse", 'reverseimg': "Reverse", 'edgeimg': "Edge", \
                   'photo1': "Photo 1", 'photo2': "Photo 2", 'photo3': "Photo 3"}

        layout = QtGui.QGridLayout(self)
        self.images = {}
        for column in columns.keys():
            self.images[column] = ImageLabel(self)

        layout.addWidget(QtGui.QLabel(columns['obverseimg'], self),0,0)
        layout.addWidget(self.images['obverseimg'],1,0)
        layout.addWidget(QtGui.QLabel(columns['reverseimg'], self),0,1)
        layout.addWidget(self.images['reverseimg'],1,1)
        layout.addWidget(QtGui.QLabel(columns['edgeimg'], self),0,2)
        layout.addWidget(self.images['edgeimg'],1,2)
        layout.addWidget(QtGui.QLabel(columns['photo1'], self),2,0)
        layout.addWidget(self.images['photo1'],3,0)
        layout.addWidget(QtGui.QLabel(columns['photo2'], self),2,1)
        layout.addWidget(self.images['photo2'],3,1)
        layout.addWidget(QtGui.QLabel(columns['photo3'], self),2,2)
        layout.addWidget(self.images['photo3'],3,2)
        layout.setRowMinimumHeight(1, 120)
        layout.setRowMinimumHeight(3, 120)
        layout.setColumnMinimumWidth(0, 160)
        layout.setColumnMinimumWidth(1, 160)
        layout.setColumnMinimumWidth(2, 160)
        
        w = QtGui.QWidget(self)
        w.setLayout(layout)
        tab.addTab(w, self.tr("Images"))

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal);
        buttonBox.addButton(QtGui.QDialogButtonBox.Save);
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel);
        buttonBox.accepted.connect(self.save);
        buttonBox.rejected.connect(self.reject);

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        if not record.isEmpty():
            for column in self.edits.keys():
                if not self.record.isNull(column):
                    value = self.record.value(column)
                    self.edits[column].setText(str(value))
            
            for column in columns.keys():
                if not self.record.isNull(column):
                    self.images[column].loadFromData(self.record.value(column))
    
    def save(self):
        for column in self.edits.keys():
            self.record.setValue(column, self.edits[column].text())

        for column in self.images.keys():
            self.record.setValue(column, self.images[column].data())

        self.accept()

    def getRecord(self):
        return self.record

if __name__ == '__main__':
    from main import run
    run()
