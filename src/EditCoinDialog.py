from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from MainDetailsLayout import MainDetailsLayout
from ParametersLayout import ParametersLayout
from ImagesLayout import ImagesLayout

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, record, parent=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.record = record
        
        tab = QtGui.QTabWidget(self)

        # Create Coin page
        pageLayout = QtGui.QVBoxLayout(self)

        groupBox = QtGui.QGroupBox(self.tr("Main details"))
        groupBox.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.main = MainDetailsLayout(record, groupBox)
        groupBox.setLayout(self.main)
        pageLayout.addWidget(groupBox)
        
        groupBox = QtGui.QGroupBox(self.tr("Parameters"))
        groupBox.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.parameters = ParametersLayout(record, groupBox)
        groupBox.setLayout(self.parameters)
        pageLayout.addWidget(groupBox)

        # Convert layout to widget and add to tab page
        w = QtGui.QWidget(tab)
        w.setLayout(pageLayout)
        tab.addTab(w, self.tr("Coin"))

        # Create Images page
        self.images = ImagesLayout(record, self)
        # Convert layout to widget and add to tab page
        w = QtGui.QWidget(tab)
        w.setLayout(self.images)
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

        settings = QtCore.QSettings()
        size = settings.value('editcoinwindow/size')
        if size:
            self.resize(size)

    def save(self):
        val = self.main.values()
        for column in val.keys():
            self.record.setValue(column, val[column])

        val = self.parameters.values()
        for column in val.keys():
            self.record.setValue(column, val[column])
        
        val = self.images.values()
        for column in val.keys():
            self.record.setValue(column, val[column])

        self.accept()

    def getRecord(self):
        return self.record
    
    def done(self, r):
        settings = QtCore.QSettings()
        settings.setValue('editcoinwindow/size', self.size());
        super(EditCoinDialog, self).done(r)

if __name__ == '__main__':
    from main import run
    run()
