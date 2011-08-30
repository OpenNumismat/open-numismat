from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from ImageLabel import ImageLabel

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, record, parent=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.record = record
        
        labels = []
        for column in ['Name', 'par']:
            labels.append(QtGui.QLabel(column, self))
        self.edit1 = QtGui.QLineEdit()
        self.edit2 = QtGui.QLineEdit()
        
        layout = QtGui.QGridLayout(self)
        layout.addWidget(labels[0],0,0)
        layout.addWidget(self.edit1,0,1)
        layout.addWidget(labels[1],1,0)
        layout.addWidget(self.edit2,1,1)
        
        self.imageLabel = ImageLabel()
        layout.setRowMinimumHeight(2, 100) 
        layout.addWidget(self.imageLabel,2,1)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal);
        buttonBox.addButton(QtGui.QDialogButtonBox.Save);
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel);
        buttonBox.accepted.connect(self.save);
        buttonBox.rejected.connect(self.reject);
        layout.addWidget(buttonBox,3,1)

        self.setLayout(layout)

        if not record.isEmpty():
            self.edit1.setText(self.record.value('title'))
            
            if not self.record.isNull('obverse'):
                self.imageLabel.loadFromData(self.record.value('obverse'))
    
    def save(self):
        self.record.setValue('title', self.edit1.text())
        self.record.setValue('obverse', self.imageLabel.data())

        self.accept()

    def getRecord(self):
        return self.record

if __name__ == '__main__':
    import sys
    from main import MainWindow
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
