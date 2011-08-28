from PyQt4 import QtGui
from PyQt4.QtCore import Qt

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, record, parent=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.record = record
        
        print(self.record.value(0))
        
        labels = []
        for column in ['Name', 'par']:
            labels.append(QtGui.QLabel(column, self))
        edit1 = QtGui.QLineEdit() 
        edit2 = QtGui.QLineEdit() 
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal);
        buttonBox.addButton(QtGui.QDialogButtonBox.Save);
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel);
        layout = QtGui.QGridLayout(self)
        layout.addWidget(labels[0],0,0)
        layout.addWidget(edit1,0,1)
        layout.addWidget(labels[1],1,0)
        layout.addWidget(edit2,1,1)
        layout.addWidget(buttonBox,2,1)
        self.setLayout(layout)

        buttonBox.accepted.connect(self.save);
        buttonBox.rejected.connect(self.close);
        
    def save(self):
        self.record.setValue('title', 'df')
        self.close()

    def getRecord(self):
        return self.record