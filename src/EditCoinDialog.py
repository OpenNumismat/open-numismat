from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from MainDetailsLayout import MainDetailsLayout
from ParametersLayout import ParametersLayout
from ObverseDesignLayout import ObverseDesignLayout
from ReverseDesignLayout import ReverseDesignLayout
from EdgeDesignLayout import EdgeDesignLayout
from SubjectLayout import SubjectLayout
from ClassificationLayout import ClassificationLayout
from PriceLayout import PriceLayout
from VariationLayout import VariationLayout
from MintingLayout import MintingLayout
from StateLayout import StateLayout
from PayLayout import PayLayout
from SaleLayout import SaleLayout
from ImagesLayout import ImagesLayout

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, record, parent=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.record = record
        
        self.tab = QtGui.QTabWidget(self)
        
        self.parts = []

        # Create Coin page
        main = MainDetailsLayout(record)
        groupBox1 = self.__layoutToGroupBox(main, self.tr("Main details"))
        groupBox1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.parts.append(main)
        
        state = StateLayout(record)
        groupBox2 = self.__layoutToGroupBox(state, self.tr("State"))
        self.parts.append(state)
        
        self.addTabPage(self.tr("Coin"), [groupBox1, groupBox2])

        # Create State page
        pay = PayLayout(record)
        groupBox1 = self.__layoutToGroupBox(pay, self.tr("Pay"))
        self.parts.append(pay)
        
        sale = SaleLayout(record)
        groupBox2 = self.__layoutToGroupBox(sale, self.tr("Sale"))
        self.parts.append(sale)
        
        self.addTabPage(self.tr("Traffic"), [groupBox1, groupBox2])

        # Create Parameters page
        parameters = ParametersLayout(record)
        groupBox1 = self.__layoutToGroupBox(parameters, self.tr("Parameters"))
        groupBox1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.parts.append(parameters)

        minting = MintingLayout(record)
        groupBox2 = self.__layoutToGroupBox(minting, self.tr("Minting"))
        groupBox2.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.parts.append(minting)

        self.addTabPage(self.tr("Parameters"), [groupBox1, groupBox2])

        # Create Design page
        obverse = ObverseDesignLayout(record)
        groupBox1 = self.__layoutToGroupBox(obverse, self.tr("Obverse"))
        self.parts.append(obverse)
        
        reverse = ReverseDesignLayout(record)
        groupBox2 = self.__layoutToGroupBox(reverse, self.tr("Reverse"))
        self.parts.append(reverse)

        edge = EdgeDesignLayout(record)
        groupBox3 = self.__layoutToGroupBox(edge, self.tr("Edge"))
        self.parts.append(edge)

        self.subject = SubjectLayout(record, self)

        self.addTabPage(self.tr("Design"), [groupBox1, groupBox2, groupBox3, self.subject])

        # Create Classification page
        classification = ClassificationLayout(record, self)
        self.parts.append(classification)

        price = PriceLayout(record, self)
        groupBox1 = self.__layoutToGroupBox(price, self.tr("Price"))
        groupBox1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        self.parts.append(price)

        variation = VariationLayout(record, self)
        groupBox2 = self.__layoutToGroupBox(variation, self.tr("Variation"))
        self.parts.append(variation)

        self.addTabPage(self.tr("Classification"), [classification, groupBox1, groupBox2])

        # Create Images page
        images = ImagesLayout(record, self)
        self.addTabPage(self.tr("Images"), images)
        self.parts.append(images)

        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal);
        buttonBox.addButton(QtGui.QDialogButtonBox.Save);
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel);
        buttonBox.accepted.connect(self.save);
        buttonBox.rejected.connect(self.reject);

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        settings = QtCore.QSettings()
        size = settings.value('editcoinwindow/size')
        if size:
            self.resize(size)
    
    def __layoutToWidget(self, layout):
        widget = QtGui.QWidget(self.tab)
        widget.setLayout(layout)
        return widget
    
    def __layoutToGroupBox(self, layout, title):
        groupBox = QtGui.QGroupBox(title)
        groupBox.setLayout(layout)
        return groupBox
    
    def addTabPage(self, title, parts):
        if isinstance(parts, list):
            pageLayout = QtGui.QVBoxLayout(self)
            # Fill layout with it's parts
            for part in parts:
                if isinstance(part, QtGui.QWidget):
                    pageLayout.addWidget(part)
                else:
                    pageLayout.addLayout(part)

            # Convert layout to widget and add to tab page
            self.tab.addTab(self.__layoutToWidget(pageLayout), title)
        else:
            # Convert layout to widget and add to tab page
            self.tab.addTab(self.__layoutToWidget(parts), title)

    def save(self):
        for part in self.parts:
            val = part.values()
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
