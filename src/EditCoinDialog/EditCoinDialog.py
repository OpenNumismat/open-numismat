from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from .AuctionParser import getParser
from .DetailsTabWidget import FormDetailsTabWidget

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, model, record, parent=None, usedFields=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.usedFields = usedFields
        self.record = record
        self.model = model
        
        self.tab = FormDetailsTabWidget(model.reference, self, usedFields)
        self.items = self.tab.items

        self.tab.fillItems(record)

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
    
    def keyPressEvent(self, event):
        if self.items['status'].widget().data() == 'pass':
            if event.matches(QtGui.QKeySequence.Paste):
                mime = QtGui.QApplication.clipboard().mimeData()
                if not mime.hasText():
                    return
                parser = getParser(mime.text(), self)
                if not parser:
                    return
                lot = parser.parse()
                if not lot:
                    return
                for key in ['payprice', 'obverseimg', 'reverseimg', 'edgeimg',
                            'photo1', 'photo2', 'photo3', 'photo4']:
                    self.items[key].clear()
                self.items['saleplace'].setValue(lot.place)
                self.items['saleprice'].setValue(lot.price)
                self.items['totalpayprice'].setValue(lot.totalPayPrice)
                self.items['totalsaleprice'].setValue(lot.totalSalePrice)
                self.items['saller'].setValue(lot.saller)
                self.items['buyer'].setValue(lot.buyer)
                self.items['saleinfo'].setValue(lot.info)
                self.items['saledate'].setValue(lot.date)
                self.items['grade'].setValue(lot.grade)
                
                # Add images
                imageFields = ['reverseimg', 'obverseimg',
                            'photo1', 'photo2', 'photo3', 'photo4']
                for i, imageUrl in enumerate(lot.images):
                    if i < len(imageFields):
                        self.items[imageFields[i]].widget().loadFromUrl(imageUrl)
                    else:
                        QtGui.QMessageBox.information(self, self.tr("Parse auction lot"),
                                    self.tr("Too many images"),
                                    QtGui.QMessageBox.Ok)
                        break
                
                self.tab.setCurrentIndex(1)
    
    def save(self):
        # Clear unused fields
        if self.items['status'].widget().data() in ['demo', 'wish']:
            for key in ['paydate', 'payprice', 'totalpayprice', 'saller',
                        'payplace', 'payinfo', 'saledate', 'saleprice',
                        'totalsaleprice', 'buyer', 'saleplace', 'saleinfo', 'grade']:
                self.items[key].clear()
        elif self.items['status'].widget().data() in ['owned', 'sale']:
            for key in ['paydate', 'payprice', 'totalpayprice', 'saller',
                        'payplace', 'payinfo']:
                self.items[key].clear()
        
        if not self.usedFields:
            if not self.items['title'].value():
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                                 self.tr("Coin title not set. Save without title?"),
                                 QtGui.QMessageBox.Save | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return

        # Checking that TotalPrice not less than Price
        payprice = self.items['payprice'].value()
        totalpayprice = self.items['totalpayprice'].value()
        if payprice and totalpayprice:
            if float(totalpayprice) < float(payprice):
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                                 self.tr("Pay price is great than total paid price. Save?"),
                                 QtGui.QMessageBox.Save | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return
        saleprice = self.items['saleprice'].value()
        totalsaleprice = self.items['totalsaleprice'].value()
        if saleprice and totalsaleprice:
            if float(saleprice) < float(totalsaleprice):
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                                 self.tr("Sale price is less than total bailed price. Save?"),
                                 QtGui.QMessageBox.Save | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return

        for item in self.items.values():
            value = item.value()
            if isinstance(value, str):
                value = value.strip()
            self.record.setValue(item.field(), value)

        if not self.usedFields:
            if self.model.isExist(self.record):
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                                self.tr("Similar coin already exists. Save?"),
                                QtGui.QMessageBox.Save | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return
        
        self.accept()
    
    def getUsedFields(self):
        for item in self.items.values():
            self.usedFields[self.record.indexOf(item.field())] = item.label().checkState()
        return self.usedFields

    def getRecord(self):
        return self.record
    
    def done(self, r):
        settings = QtCore.QSettings()
        settings.setValue('editcoinwindow/size', self.size());
        super(EditCoinDialog, self).done(r)
