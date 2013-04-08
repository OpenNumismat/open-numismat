from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from OpenNumismat.EditCoinDialog.Auctions import getParser
from OpenNumismat.EditCoinDialog.DetailsTabWidget import FormDetailsTabWidget
from OpenNumismat.EditCoinDialog.CbrParser import CbrParser
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


@storeDlgSizeDecorator
class EditCoinDialog(QtGui.QDialog):
    def __init__(self, model, record, parent=None, usedFields=None):
        super(EditCoinDialog, self).__init__(parent, Qt.WindowSystemMenuHint)

        self.clickedButton = QtGui.QDialogButtonBox.Abort

        self.usedFields = usedFields
        self.record = record
        self.model = model

        self.tab = FormDetailsTabWidget(model, self, usedFields)
        self.items = self.tab.items

        self.textChangedTitle()
        self.tab.items['title'].widget().textChanged.connect(
                                                        self.textChangedTitle)
        self.tab.fillItems(record)

        self.buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        self.buttonBox.addButton(QtGui.QDialogButtonBox.Save)
        self.buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.save)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.clicked.connect(self.clicked)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.tab)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def clicked(self, button):
        buttons = [QtGui.QDialogButtonBox.Save, QtGui.QDialogButtonBox.SaveAll,
                   QtGui.QDialogButtonBox.Cancel, QtGui.QDialogButtonBox.Abort]
        for btn in buttons:
            if self.buttonBox.button(btn) == button:
                self.clickedButton = btn

    # Enable 'Save all' button
    def setManyCoins(self, many=True):
        if many:
            self.buttonBox.addButton(QtGui.QDialogButtonBox.SaveAll)
            self.buttonBox.addButton(QtGui.QDialogButtonBox.Abort)

    def textChangedTitle(self, text=''):
        if self.usedFields:
            title = [self.tr("Multi edit"), ]
        elif self.record.isNull('id'):
            title = [self.tr("New"), ]
        else:
            title = [self.tr("Edit"), ]

        if text:
            title.insert(0, text)
        self.setWindowTitle(' - '.join(title))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.matches(QtGui.QKeySequence.Paste):
            if self.items['status'].widget().data() == 'pass':
                mime = QtGui.QApplication.clipboard().mimeData()
                if not mime.hasText():
                    return
                parser = getParser(mime.text(), self)
                if not parser:
                    return
                lot = parser.parse(mime.text())
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
                        self.items[imageFields[i]].widget().loadFromUrl(
                                                                    imageUrl)
                    else:
                        QtGui.QMessageBox.information(self,
                                    self.tr("Parse auction lot"),
                                    self.tr("Too many images"),
                                    QtGui.QMessageBox.Ok)
                        break

                self.tab.setCurrentIndex(1)
            elif self.items['status'].widget().data() == 'demo':
                mime = QtGui.QApplication.clipboard().mimeData()
                if not mime.hasText():
                    return
                if not CbrParser.verifyDomain(mime.text()):
                    return
                parser = CbrParser(mime.text(), self)
                lot = parser.parse(mime.text())
                if not lot:
                    return
                self.items['title'].setValue(lot.title)
                self.items['series'].setValue(lot.series)
                self.items['subjectshort'].setValue(lot.subjectshort)
                self.items['issuedate'].setValue(lot.issuedate)
                self.items['catalognum1'].setValue(lot.catalognum1)
                self.items['issuedate'].setValue(lot.issuedate)
                self.items['year'].setValue(lot.year)
                self.items['value'].setValue(lot.value)
                self.items['quality'].setValue(lot.quality)
                self.items['material'].setValue(lot.material)
                self.items['fineness'].setValue(lot.fineness)
                self.items['weight'].setValue(lot.weight)
                self.items['diameter'].setValue(lot.diameter)
                self.items['thickness'].setValue(lot.thickness)
                self.items['mintage'].setValue(lot.mintage)
                self.items['obversedesign'].setValue(lot.obversedesign)
                self.items['reversedesign'].setValue(lot.reversedesign)
                self.items['subject'].setValue(lot.subject)
                self.items['reversedesigner'].setValue(lot.reversedesigner)
                self.items['obversedesigner'].setValue(lot.obversedesigner)
                self.items['edgelabel'].setValue(lot.edgelabel)
                self.items['mintmark'].setValue(lot.mintmark)
                self.items['mint'].setValue(lot.mint)
                self.items['url'].setValue(lot.url)

                # Add images
                imageFields = ['obverseimg', 'reverseimg']
                for i, imageUrl in enumerate(lot.images):
                    self.items[imageFields[i]].widget().loadFromUrl(imageUrl)

                self.tab.setCurrentIndex(3)

    def save(self):
        # Clear unused fields
        if self.items['status'].widget().data() in ['demo', 'wish']:
            for key in ['paydate', 'payprice', 'totalpayprice', 'saller',
                        'payplace', 'payinfo', 'saledate', 'saleprice',
                        'totalsaleprice', 'buyer', 'saleplace', 'saleinfo']:
                self.items[key].clear()
        elif self.items['status'].widget().data() in ['owned', 'sale']:
            for key in ['saledate', 'saleprice', 'totalsaleprice', 'buyer',
                        'saleplace', 'saleinfo']:
                self.items[key].clear()

        if not self.usedFields:
            if not self.items['title'].value():
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Coin title not set. Save without title?"),
                            QtGui.QMessageBox.Save | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return

        # Checking that TotalPrice not less than Price
        payprice = self.items['payprice'].value()
        totalpayprice = self.items['totalpayprice'].value()
        if totalpayprice and float(totalpayprice) < 0:
            result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Total paid price is negative. Save?"),
                            QtGui.QMessageBox.Save | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No)
            if result != QtGui.QMessageBox.Save:
                return
        if payprice and totalpayprice:
            if float(totalpayprice) < float(payprice):
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Pay price is great than total "
                                    "paid price. Save?"),
                            QtGui.QMessageBox.Save | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return
        saleprice = self.items['saleprice'].value()
        totalsaleprice = self.items['totalsaleprice'].value()
        if totalsaleprice and float(totalsaleprice) < 0:
            result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Total bailed price is negative. Save?"),
                            QtGui.QMessageBox.Save | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No)
            if result != QtGui.QMessageBox.Save:
                return
        if saleprice and totalsaleprice:
            if float(saleprice) < float(totalsaleprice):
                result = QtGui.QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Sale price is less than total "
                                    "bailed price. Save?"),
                            QtGui.QMessageBox.Save | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No)
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
                            QtGui.QMessageBox.Save | QtGui.QMessageBox.No,
                            QtGui.QMessageBox.No)
                if result != QtGui.QMessageBox.Save:
                    return

        self.accept()

    def getUsedFields(self):
        for item in self.items.values():
            index = self.record.indexOf(item.field())
            self.usedFields[index] = item.label().checkState()
        return self.usedFields

    def getRecord(self):
        return self.record
