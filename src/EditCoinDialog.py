from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from MainDetailsLayout import MainDetailsLayout
from ParametersLayout import ParametersLayout
from ObverseDesignLayout import ObverseDesignLayout
from ReverseDesignLayout import ReverseDesignLayout
from EdgeDesignLayout import EdgeDesignLayout
from ClassificationLayout import ClassificationLayout
from MintingLayout import MintingLayout
from StateLayout import StateLayout
from PayLayout import PayLayout
from SaleLayout import SaleLayout
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

        groupBox = QtGui.QGroupBox(self.tr("Minting"))
        groupBox.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.minting = MintingLayout(record, self)
        groupBox.setLayout(self.minting)
        pageLayout.addWidget(groupBox)

        # Convert layout to widget and add to tab page
        w = QtGui.QWidget(tab)
        w.setLayout(pageLayout)
        tab.addTab(w, self.tr("Coin"))

        # Create State page
        pageLayout = QtGui.QVBoxLayout(self)

        groupBox = QtGui.QGroupBox(self.tr("State"))
        self.state = StateLayout(record, groupBox)
        groupBox.setLayout(self.state)
        pageLayout.addWidget(groupBox)
        
        groupBox = QtGui.QGroupBox(self.tr("Pay"))
        self.pay = PayLayout(record, groupBox)
        groupBox.setLayout(self.pay)
        pageLayout.addWidget(groupBox)
        
        groupBox = QtGui.QGroupBox(self.tr("Sale"))
        self.sale = SaleLayout(record, groupBox)
        groupBox.setLayout(self.sale)
        pageLayout.addWidget(groupBox)
        
        # Convert layout to widget and add to tab page
        w = QtGui.QWidget(tab)
        w.setLayout(pageLayout)
        tab.addTab(w, self.tr("State"))

        # Create Design page
        pageLayout = QtGui.QVBoxLayout(self)

        groupBox = QtGui.QGroupBox(self.tr("Obverse"))
        self.obverse = ObverseDesignLayout(record, groupBox)
        groupBox.setLayout(self.obverse)
        pageLayout.addWidget(groupBox)
        
        groupBox = QtGui.QGroupBox(self.tr("Reverse"))
        self.reverse = ReverseDesignLayout(record, groupBox)
        groupBox.setLayout(self.reverse)
        pageLayout.addWidget(groupBox)

        groupBox = QtGui.QGroupBox(self.tr("Edge"))
        self.edge = EdgeDesignLayout(record, groupBox)
        groupBox.setLayout(self.edge)
        pageLayout.addWidget(groupBox)

        # Convert layout to widget and add to tab page
        w = QtGui.QWidget(tab)
        w.setLayout(pageLayout)
        tab.addTab(w, self.tr("Design"))

        # Create Classification page
        self.classification = ClassificationLayout(record, self)
        # Convert layout to widget and add to tab page
        w = QtGui.QWidget(tab)
        w.setLayout(self.classification)
        tab.addTab(w, self.tr("Classification"))

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
        
        val = self.state.values()
        for column in val.keys():
            self.record.setValue(column, val[column])
        
        val = self.pay.values()
        for column in val.keys():
            self.record.setValue(column, val[column])
        
        val = self.sale.values()
        for column in val.keys():
            self.record.setValue(column, val[column])
        
        val = self.obverse.values()
        for column in val.keys():
            self.record.setValue(column, val[column])

        val = self.reverse.values()
        for column in val.keys():
            self.record.setValue(column, val[column])

        val = self.edge.values()
        for column in val.keys():
            self.record.setValue(column, val[column])

        val = self.classification.values()
        for column in val.keys():
            self.record.setValue(column, val[column])

        val = self.minting.values()
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
