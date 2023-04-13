from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import *

from OpenNumismat.Collection.CollectionFields import ImageFields
from OpenNumismat.EditCoinDialog.DetailsTabWidget import FormDetailsTabWidget
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

        layout = QVBoxLayout()
        layout.addWidget(self.tab)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def clicked(self, button):
        buttons = (QDialogButtonBox.Save, QDialogButtonBox.SaveAll,
                   QDialogButtonBox.Cancel, QDialogButtonBox.Abort)
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

    def save(self):
        # Clear unused fields
        status = self.items['status'].widget().data()
        if status in ('demo', 'wish'):
            for key in ('paydate', 'payprice', 'totalpayprice', 'saller',
                        'payplace', 'payinfo'):
                self.items[key].clear()
        if status in ('demo', 'wish', 'owned', 'sale', 'ordered', 'missing',
                      'bidding', 'duplicate', 'replacement'):
            for key in ('saledate', 'saleprice', 'totalsaleprice', 'buyer',
                        'saleplace', 'saleinfo'):
                self.items[key].clear()

        settings = QSettings()
        key = 'show_info/save_without_title'
        show = settings.value(key, True, type=bool)
        if show:
            if not self.usedFields:
                if not self.items['title'].value():
                    msg_box = QMessageBox(QMessageBox.Warning, self.tr("Save"),
                                          self.tr("Coin title not set. Save without title?"),
                                          QMessageBox.Save | QMessageBox.No,
                                          self)
                    msg_box.setDefaultButton(QMessageBox.No)
                    cb = QCheckBox(self.tr("Don't show this again"))
                    msg_box.setCheckBox(cb)
                    result = msg_box.exec_()
                    if result != QMessageBox.Save:
                        return
                    else:
                        if cb.isChecked():
                            settings.setValue(key, False)

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
                                self.tr("Total revenue price is negative. Save?"),
                                QMessageBox.Save | QMessageBox.No,
                                QMessageBox.No)
                if result != QMessageBox.Save:
                    return
        if saleprice_str and totalsaleprice_str:
            saleprice = stringToMoney(saleprice_str)
            if saleprice < totalsaleprice:
                result = QMessageBox.warning(self, self.tr("Save"),
                            self.tr("Sale price is less than total "
                                    "revenue price. Save?"),
                            QMessageBox.Save | QMessageBox.No,
                            QMessageBox.No)
                if result != QMessageBox.Save:
                    return

        for item in self.items.values():
            value = item.value()
            if isinstance(value, str):
                value = value.strip()
            self.record.setValue(item.field(), value)

        for image_field in ImageFields:
            item = self.items[image_field]
            value = item.widget().title
            if isinstance(value, str):
                value = value.strip()
            self.record.setValue(image_field + '_title', value)

        key = 'show_info/save_similar'
        show = settings.value(key, True, type=bool)
        if show:
            if not self.usedFields:
                if self.model.isExist(self.record):
                    msg_box = QMessageBox(QMessageBox.Warning, self.tr("Save"),
                                          self.tr("Similar coin already exists. Save?"),
                                          QMessageBox.Save | QMessageBox.No,
                                          self)
                    msg_box.setDefaultButton(QMessageBox.No)
                    cb = QCheckBox(self.tr("Don't show this again"))
                    msg_box.setCheckBox(cb)
                    result = msg_box.exec_()
                    if result != QMessageBox.Save:
                        return
                    else:
                        if cb.isChecked():
                            settings.setValue(key, False)

        self.accept()

    def getUsedFields(self):
        for item in self.items.values():
            index = self.record.indexOf(item.field())
            self.usedFields[index] = item.label().checkState()
        return self.usedFields
