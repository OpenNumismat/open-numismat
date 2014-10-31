from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import *

from OpenNumismat.EditCoinDialog.Auctions import getParser
from OpenNumismat.EditCoinDialog.DetailsTabWidget import FormDetailsTabWidget
from OpenNumismat.EditCoinDialog.CbrParser import CbrParser
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Converters import stringToMoney


@storeDlgSizeDecorator
class EditCoinDialog(QDialog):
    def __init__(self, model, record, parent=None, usedFields=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.clickedButton = QDialogButtonBox.Abort

        self.usedFields = usedFields
        self.record = record
        self.model = model

        self.tab = FormDetailsTabWidget(model, self, usedFields)
        self.items = self.tab.items

        self.textChangedTitle()
        self.tab.items['title'].widget().textChanged.connect(
                                                        self.textChangedTitle)
        self.tab.fillItems(record)

        self.buttonBox = QDialogButtonBox(Qt.Horizontal)
        self.buttonBox.addButton(QDialogButtonBox.Save)
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.save)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.clicked.connect(self.clicked)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tab)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def clicked(self, button):
        buttons = [QDialogButtonBox.Save, QDialogButtonBox.SaveAll,
                   QDialogButtonBox.Cancel, QDialogButtonBox.Abort]
        for btn in buttons:
            if self.buttonBox.button(btn) == button:
                self.clickedButton = btn

    # Enable 'Save all' button
    def setManyCoins(self, many=True):
        if many:
            self.buttonBox.addButton(QDialogButtonBox.SaveAll)
            self.buttonBox.addButton(QDialogButtonBox.Abort)

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
        elif event.matches(QKeySequence.Paste):
            if self.items['status'].widget().data() == 'pass':
                mime = QApplication.clipboard().mimeData()
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
                        QMessageBox.information(self,
                                    self.tr("Parse auction lot"),
                                    self.tr("Too many images"),
                                    QMessageBox.Ok)
                        break

                self.tab.setCurrentIndex(1)
            elif self.items['status'].widget().data() == 'demo':
                mime = QApplication.clipboard().mimeData()
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
        elif self.items['status'].widget().data() in ['owned', 'sale', 'ordered']:
            for key in ['saledate', 'saleprice', 'totalsaleprice', 'buyer',
                        'saleplace', 'saleinfo']:
                self.items[key].clear()

        if not self.usedFields:
            if not self.items['title'].value():
                result = QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Coin title not set. Save without title?"),
                            QMessageBox.Save | QMessageBox.No,
                            QMessageBox.No)
                if result != QMessageBox.Save:
                    return

        # Checking that TotalPrice not less than Price
        payprice_str = self.items['payprice'].value()
        totalpayprice_str = self.items['totalpayprice'].value()
        if totalpayprice_str:
            totalpayprice = stringToMoney(totalpayprice_str)
            if totalpayprice < 0:
                result = QMessageBox.warning(self, self.tr("Save"),
                                self.tr("Total paid price is negative. Save?"),
                                QMessageBox.Save | QMessageBox.No,
                                QMessageBox.No)
                if result != QMessageBox.Save:
                    return
        if payprice_str and totalpayprice_str:
            payprice = stringToMoney(payprice_str)
            if totalpayprice < payprice:
                result = QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Pay price is great than total "
                                    "paid price. Save?"),
                            QMessageBox.Save | QMessageBox.No,
                            QMessageBox.No)
                if result != QMessageBox.Save:
                    return
        saleprice_str = self.items['saleprice'].value()
        totalsaleprice_str = self.items['totalsaleprice'].value()
        if totalsaleprice_str:
            totalsaleprice = stringToMoney(totalsaleprice_str)
            if totalsaleprice < 0:
                result = QMessageBox.warning(self, self.tr("Save"),
                                self.tr("Total bailed price is negative. Save?"),
                                QMessageBox.Save | QMessageBox.No,
                                QMessageBox.No)
                if result != QMessageBox.Save:
                    return
        if saleprice_str and totalsaleprice_str:
            saleprice = stringToMoney(saleprice_str)
            if saleprice < totalsaleprice:
                result = QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Sale price is less than total "
                                    "bailed price. Save?"),
                            QMessageBox.Save | QMessageBox.No,
                            QMessageBox.No)
                if result != QMessageBox.Save:
                    return

        for item in self.items.values():
            value = item.value()
            if isinstance(value, str):
                value = value.strip()
            self.record.setValue(item.field(), value)

        if not self.usedFields:
            if self.model.isExist(self.record):
                result = QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Similar coin already exists. Save?"),
                            QMessageBox.Save | QMessageBox.No,
                            QMessageBox.No)
                if result != QMessageBox.Save:
                    return

        self.accept()

    def getUsedFields(self):
        for item in self.items.values():
            index = self.record.indexOf(item.field())
            self.usedFields[index] = item.label().checkState()
        return self.usedFields

    def getRecord(self):
        return self.record
