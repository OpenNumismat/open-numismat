from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication

from .BaseFormLayout import BaseFormLayout, BaseFormGroupBox, ImageFormLayout, DesignFormLayout, FormItem
from Collection.CollectionFields import CollectionFields
from Collection.CollectionFields import FieldTypes as Type

class DetailsTabWidget(QtGui.QTabWidget):
    Direction = QtGui.QBoxLayout.LeftToRight
    Stretch = 'stretch item'
    
    def __init__(self, parent=None):
        super(DetailsTabWidget, self).__init__(parent)
        
        self.createItems()
        self.createPages()

    def createPages(self):
        self.createCoinPage()
        self.createTrafficPage()
        self.createParametersPage()
        self.createDesignPage()
        self.createClassificationPage()
    
    def createCoinPage(self):
        main = self.mainDetailsLayout()
        state = self.stateLayout()
        title = QApplication.translate('DetailsTabWidget', "Coin")
        self.addTabPage(title, [main, self.Stretch, state])

    def createTrafficPage(self):
        self.oldTrafficIndex = 0
        parts = self._createTrafficParts(self.oldTrafficIndex)
        title = QApplication.translate('DetailsTabWidget', "Traffic")
        self.addTabPage(title, parts)

    def createParametersPage(self):
        parameters = self.parametersLayout()
        minting = self.mintingLayout()
        note = self.noteLayout()
        
        title = QApplication.translate('DetailsTabWidget', "Parameters")
        self.addTabPage(title, [parameters, self.Stretch, minting, note])

    def createDesignPage(self):
        obverse = self.obverseDesignLayout()
        reverse = self.reverseDesignLayout()
        edge = self.edgeDesignLayout()
        subject = self.subjectLayout()

        title = QApplication.translate('DetailsTabWidget', "Design")
        self.addTabPage(title, [obverse, reverse, self.Stretch, edge, subject])

    def createClassificationPage(self):
        catalogue = self.catalogueLayout()
        rarity = self.rarityLayout()
        price = self.priceLayout()
        variation = self.variationLayout()

        title = QApplication.translate('DetailsTabWidget', "Classification")
        self.addTabPage(title, [catalogue, rarity, price, self.Stretch, variation])

    def _layoutToWidget(self, layout):
        widget = QtGui.QWidget(self)
        widget.setLayout(layout)
        return widget

    def createTabPage(self, parts):
        # Remove all empty parts
        for part in parts:
            if isinstance(part, BaseFormGroupBox):
                if part.isEmpty():
                    parts.remove(part)
        
        if self.Direction == QtGui.QBoxLayout.LeftToRight:
            newParts = []
            layout = QtGui.QVBoxLayout()
            stretchNeeded = True
            count = 0
            for part in parts:
                if part == self.Stretch:
                    if count > 0:
                        newParts.append(layout)
                        if stretchNeeded:
                            layout.insertStretch(-1)
                        layout = QtGui.QVBoxLayout()
                    stretchNeeded = True
                    count = 0
                else:
                    if isinstance(part, QtGui.QWidget):
                        layout.addWidget(part)
                        if part.sizePolicy().verticalPolicy() == QtGui.QSizePolicy.Preferred:
                            stretchNeeded = False
                    else:
                        layout.addLayout(part)
                    count = count + 1
            if count > 0:
                newParts.append(layout)
                if stretchNeeded:
                    layout.insertStretch(-1)
            parts = newParts
        else:
            for part in parts:
                if part == self.Stretch:
                    parts.remove(part)
        
        pageLayout = QtGui.QBoxLayout(self.Direction, self)
        # Fill layout with it's parts
        stretchNeeded = True
        for part in parts:
            if isinstance(part, QtGui.QWidget):
                pageLayout.addWidget(part)
                if part.sizePolicy().verticalPolicy() == QtGui.QSizePolicy.Preferred:
                    stretchNeeded = False
            else:
                pageLayout.addLayout(part)
                if isinstance(part, ImageFormLayout):
                    stretchNeeded = False

        if self.Direction == QtGui.QBoxLayout.TopToBottom and stretchNeeded:
            pageLayout.insertStretch(-1)
    
        return self._layoutToWidget(pageLayout)
    
    def addTabPage(self, title, parts):
        page = self.createTabPage(parts)
        index = self.addTab(page, title)
        # Disable if empty
        if len(parts) == 0:
            self.setTabEnabled(index, False)
    
    def addItem(self, field):
        item = FormItem(field.name, field.title, field.type | Type.Disabled)
        if not field.enabled:
            item.setHidden()
        self.items[field.name] = item
    
    def createItems(self):
        self.items = {}
        
        fields = CollectionFields()
        for field in fields:
            if field not in fields.systemFileds:
                self.addItem(field)
    
    def fillItems(self, record):
        if not record.isEmpty():
            fields = CollectionFields()
            for field in fields:
                if field not in fields.systemFileds:
                    item = self.items[field.name]
                    if not record.isNull(item.field()):
                        value = record.value(item.field())
                        item.setValue(value)
                    else:
                        item.widget().clear()
    
    def clear(self):
        for item in self.items.values():
            item.widget().clear()

    def mainDetailsLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Main details")
        layout = BaseFormGroupBox(title, parent)

        layout.addRow(self.items['title'])
        layout.addRow(self.items['country'])
        layout.addRow(self.items['period'])
        layout.addRow(self.items['value'], self.items['unit'])
        layout.addRow(self.items['year'])
        layout.addRow(self.items['mintmark'], self.items['mint'])
        layout.addRow(self.items['type'])
        layout.addRow(self.items['series'])
        layout.addRow(self.items['subjectshort'])

        return layout

    def stateLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "State")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['status'], self.items['grade'])
        self.items['status'].widget().currentIndexChanged.connect(self.indexChangedState)
        layout.addRow(self.items['storage'])
        layout.addRow(self.items['defect'])
        layout.addRow(self.items['features'])

        return layout

    def payLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Buy")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['paydate'], self.items['payprice'])

        # Add auxiliary field
        item = self.addPayCommission()

        layout.addRow(self.items['totalpayprice'], item)
        layout.addRow(self.items['saller'])
        layout.addRow(self.items['payplace'])
        layout.addRow(self.items['payinfo'])

        return layout

    def saleLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Sale")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['saledate'], self.items['saleprice'])

        # Add auxiliary field
        item = self.addSaleCommission()
        layout.addRow(self.items['totalsaleprice'], item)

        layout.addRow(self.items['buyer'])
        layout.addRow(self.items['saleplace'])
        layout.addRow(self.items['saleinfo'])

        return layout

    def passLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Pass")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['saledate'], self.items['saleprice'])

        # Add auxiliary field
        item = self.addPayCommission()
        layout.addRow(self.items['totalpayprice'], item)
        self.items['saleprice'].widget().textChanged.connect(self.items['payprice'].widget().setText)

        # Add auxiliary field
        item = self.addSaleCommission()
        layout.addRow(self.items['totalsaleprice'], item)

        layout.addRow(self.items['saller'])
        layout.addRow(self.items['buyer'])
        layout.addRow(self.items['saleplace'])
        layout.addRow(self.items['saleinfo'])

        return layout

    def parametersLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Parameters")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['metal'])
        layout.addRow(self.items['fineness'], self.items['mass'])
        layout.addRow(self.items['diameter'], self.items['thick'])
        layout.addRow(self.items['form'])
        layout.addRow(self.items['obvrev'])

        return layout

    def mintingLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Minting")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['issuedate'], self.items['mintage'])
        layout.addRow(self.items['dateemis'])

        item = self.items['quality']
        layout.layout.addWidget(item.label(), 2, 0)
        layout.layout.addWidget(item.widget(), 2, 1)
        item.widget().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        return layout

    def noteLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['note'])

        return layout

    def obverseDesignLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Obverse")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['obversedesign'])
        layout.addRow(self.items['obversedesigner'])

        return layout

    def reverseDesignLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Reverse")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['reversedesign'])
        layout.addRow(self.items['reversedesigner'])

        return layout

    def edgeDesignLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Edge")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['edge'])
        layout.addRow(self.items['edgelabel'])

        return layout

    def subjectLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['subject'])

        return layout

    def rarityLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        item = self.items['rarity']
        layout.addWidget(item.label(), 1, 0)
        layout.addWidget(item.widget(), 1, 1)
        layout.addWidget(QtGui.QWidget(), 1, 2)
        item.widget().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        return layout

    def catalogueLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Catalogue")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['catalognum1'], self.items['catalognum2'])
        layout.addRow(self.items['catalognum3'], self.items['catalognum4'])

        return layout

    def priceLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Price")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['price1'], self.items['price2'])
        layout.addRow(self.items['price3'], self.items['price4'])

        return layout

    def variationLayout(self, parent=None):
        title = QApplication.translate('DetailsTabWidget', "Variation")
        layout = BaseFormGroupBox(title, parent)
        
        layout.addRow(self.items['variety'])
        layout.addRow(self.items['obversevar'], self.items['reversevar'])
        item = self.items['edgevar']
        layout.layout.addWidget(item.label(), 3, 0)
        layout.layout.addWidget(item.widget(), 3, 1)

        return layout

    def _createTrafficParts(self, index=0):
        pageParts = []
        if index == 0:
            pass
        elif index == 1:
            pass_ = self.passLayout()
            pageParts.append(pass_)
        elif index == 2:
            pay = self.payLayout()
            pageParts.append(pay)
        elif index == 3:
            pay = self.payLayout()
            sale = self.saleLayout()
            pageParts.extend([pay, self.Stretch, sale])
        elif index == 4:
            pay = self.payLayout()
            pageParts.append(pay)
        elif index == 5:
            pass
        
        self.oldTrafficIndex = index
        
        return pageParts

    def indexChangedState(self, index):
        pageIndex = self.currentIndex()
        
        self.removeTab(1)
        pageParts = self._createTrafficParts(index)
        page = self.createTabPage(pageParts)

        title = QApplication.translate('DetailsTabWidget', "Traffic")
        self.insertTab(1, page, title)
        if len(pageParts) == 0:
            self.setTabEnabled(1, False)
            self.items['grade'].widget().setEnabled(False)
            if pageIndex == 1:
                self.setCurrentIndex(pageIndex-1)
        else:
            self.items['grade'].widget().setEnabled(True)
            self.setCurrentIndex(pageIndex)
    
    def addPayCommission(self):
        title = QApplication.translate('DetailsTabWidget', "Commission")
        self.payComission = FormItem(None, title, Type.Money)
        
        self.items['payprice'].widget().textChanged.connect(self.payPriceChanged)
        self.items['totalpayprice'].widget().textChanged.connect(self.payPriceChanged)

        return self.payComission
    
    def payPriceChanged(self, text):
        price = textToFloat(self.items['payprice'].value())
        totalPrice = textToFloat(self.items['totalpayprice'].value())
        self.payComission.widget().setText(floatToText(totalPrice - price))
    
    def addSaleCommission(self):
        title = QApplication.translate('DetailsTabWidget', "Commission")
        self.saleComission = FormItem(None, title, Type.Money)
        
        self.items['saleprice'].widget().textChanged.connect(self.salePriceChanged)
        self.items['totalsaleprice'].widget().textChanged.connect(self.salePriceChanged)

        return self.saleComission
    
    def salePriceChanged(self, text):
        price = textToFloat(self.items['saleprice'].value())
        totalPrice = textToFloat(self.items['totalsaleprice'].value())
        self.saleComission.widget().setText(floatToText(price - totalPrice))

class FormDetailsTabWidget(DetailsTabWidget):
    Direction = QtGui.QBoxLayout.TopToBottom

    def __init__(self, reference, parent=None, usedFields=None):
        self.usedFields = usedFields
        self.reference = reference

        super(FormDetailsTabWidget, self).__init__(parent)

    def createPages(self):
        self.createCoinPage()
        self.createTrafficPage()
        self.createParametersPage()
        self.createDesignPage()
        self.createClassificationPage()
        self.createImagePage()

    def createDesignPage(self):
        obverse = self.obverseDesignLayout()
        reverse = self.reverseDesignLayout()
        edge = self.edgeDesignLayout()
        subject = self.subjectLayout()

        self.addTabPage(self.tr("Design"), [obverse, reverse, self.Stretch, edge, subject])

    def createImagePage(self):
        images = self.imagesLayout()
        self.addTabPage(self.tr("Images"), [images,])
    
    def addItem(self, field):
        checkable = 0
        if self.usedFields:
            checkable = Type.Checkable

        refSection = None
        if self.reference:
            refSection = self.reference.section(field.name)

        item = FormItem(field.name, field.title, field.type | checkable, refSection)
        if not field.enabled:
            item.setHidden()
        self.items[field.name] = item
    
    def createItems(self):
        super(FormDetailsTabWidget, self).createItems()

        if self.reference:
            self.items['country'].widget().addDependent(self.items['period'].widget())
            self.items['country'].widget().addDependent(self.items['unit'].widget())
            self.items['country'].widget().addDependent(self.items['mint'].widget())
            self.items['country'].widget().addDependent(self.items['series'].widget())
    
    def fillItems(self, record):
        super(FormDetailsTabWidget, self).fillItems(record)
        
        if self.usedFields:
            for item in self.items.values():
                if self.usedFields[record.indexOf(item.field())]:
                    item.label().setCheckState(Qt.Checked)
    
    def mainDetailsLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Main details"), parent)
        layout.layout.columnCount = 6
       
        btn = QtGui.QPushButton(self.tr("Generate"), parent)
        btn.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        btn.clicked.connect(self.clickGenerateTitle)
        layout.addRow(self.items['title'], btn)

        layout.addRow(self.items['country'])
        layout.addRow(self.items['period'])
        layout.addRow(self.items['value'], self.items['unit'])
        layout.addRow(self.items['year'])
        layout.addRow(self.items['mintmark'], self.items['mint'])
        layout.addRow(self.items['type'])
        layout.addRow(self.items['series'])
        layout.addRow(self.items['subjectshort'])

        return layout

    def obverseDesignLayout(self, parent=None):
        layout = DesignFormLayout(self.tr("Obverse"), parent)
        
        layout.addImage(self.items['obverseimg'])
        layout.addRow(self.items['obversedesign'])
        layout.addRow(self.items['obversedesigner'])

        return layout

    def reverseDesignLayout(self, parent=None):
        layout = DesignFormLayout(self.tr("Reverse"), parent)
        
        layout.addImage(self.items['reverseimg'])
        layout.addRow(self.items['reversedesign'])
        layout.addRow(self.items['reversedesigner'])

        return layout

    def edgeDesignLayout(self, parent=None):
        layout = DesignFormLayout(self.tr("Edge"), parent)
        
        layout.addImage(self.items['edgeimg'])
        layout.addRow(self.items['edge'])
        layout.addRow(self.items['edgelabel'])

        return layout

    def imagesLayout(self, parent=None):
        layout = ImageFormLayout(parent)
        layout.addImages([self.items['photo1'], self.items['photo2'], self.items['photo3'], self.items['photo4']])
        return layout

    def clickGenerateTitle(self):
        titleParts = []
        for key in ['value', 'unit', 'year', 'subjectshort', 'mintmark', 'variety']:
            value = self.items[key].value()
            if value:
                titlePart = str(value)
                if key == 'unit':
                    titlePart = titlePart.lower()
                titleParts.append(titlePart) 

        title = ' '.join(titleParts)
        self.items['title'].setValue(title)

    def _createTrafficParts(self, index=0):
        if self.oldTrafficIndex == 0:
            pass
        elif self.oldTrafficIndex == 1:
            self.items['payprice'].widget().textChanged.disconnect(self.payCommissionChanged)
            self.items['totalpayprice'].widget().textChanged.disconnect(self.payTotalPriceChanged)
            self.payCommission.textChanged.disconnect(self.payCommissionChanged)
            self.items['saleprice'].widget().textChanged.disconnect(self.saleCommissionChanged)
            self.items['totalsaleprice'].widget().textChanged.disconnect(self.saleTotalPriceChanged)
            self.saleCommission.textChanged.disconnect(self.saleCommissionChanged)
            self.items['saleprice'].widget().textChanged.disconnect(self.items['payprice'].widget().setText)
        elif self.oldTrafficIndex == 2:
            self.items['payprice'].widget().textChanged.disconnect(self.payCommissionChanged)
            self.items['totalpayprice'].widget().textChanged.disconnect(self.payTotalPriceChanged)
            self.payCommission.textChanged.disconnect(self.payCommissionChanged)
        elif self.oldTrafficIndex == 3:
            self.items['payprice'].widget().textChanged.disconnect(self.payCommissionChanged)
            self.items['totalpayprice'].widget().textChanged.disconnect(self.payTotalPriceChanged)
            self.payCommission.textChanged.disconnect(self.payCommissionChanged)
            self.items['saleprice'].widget().textChanged.disconnect(self.saleCommissionChanged)
            self.items['totalsaleprice'].widget().textChanged.disconnect(self.saleTotalPriceChanged)
            self.saleCommission.textChanged.disconnect(self.saleCommissionChanged)
        elif self.oldTrafficIndex == 4:
            self.items['payprice'].widget().textChanged.disconnect(self.payCommissionChanged)
            self.items['totalpayprice'].widget().textChanged.disconnect(self.payTotalPriceChanged)
            self.payCommission.textChanged.disconnect(self.payCommissionChanged)
        elif self.oldTrafficIndex == 5:
            pass

        pageParts = super(FormDetailsTabWidget, self)._createTrafficParts(index)
        
        self.oldTrafficIndex = index
        
        return pageParts

    def addPayCommission(self):
        item = FormItem(None, self.tr("Commission"), Type.Money)
        self.payCommission = item.widget()

        validator = CommissionValidator(0, 9999999999, 2, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.payCommission.setValidator(validator)
        
        self.items['payprice'].widget().textChanged.connect(self.payCommissionChanged)
        self.payCommission.textChanged.connect(self.payCommissionChanged)
        self.items['totalpayprice'].widget().textChanged.connect(self.payTotalPriceChanged)
        
        return item
    
    def addSaleCommission(self):
        item = FormItem(None, self.tr("Commission"), Type.Money)
        self.saleCommission = item.widget()

        validator = CommissionValidator(0, 9999999999, 2, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.saleCommission.setValidator(validator)
        
        self.items['saleprice'].widget().textChanged.connect(self.saleCommissionChanged)
        self.saleCommission.textChanged.connect(self.saleCommissionChanged)
        self.items['totalsaleprice'].widget().textChanged.connect(self.saleTotalPriceChanged)
        
        return item
    
    def payCommissionChanged(self, text):
        self.items['totalpayprice'].widget().textChanged.disconnect(self.payTotalPriceChanged)
        
        price = textToFloat(self.items['payprice'].value())
        text = self.payCommission.text().strip()
        if len(text) > 0 and text[-1] == '%':
            commission = price * textToFloat(text[0:-1]) / 100
        else:
            commission = textToFloat(text)
        self.items['totalpayprice'].widget().setText(floatToText(price + commission))

        self.items['totalpayprice'].widget().textChanged.connect(self.payTotalPriceChanged)

    def payTotalPriceChanged(self, text):
        self.payCommission.textChanged.disconnect(self.payCommissionChanged)

        price = textToFloat(self.items['payprice'].value())
        totalPrice = textToFloat(self.items['totalpayprice'].value())
        self.payCommission.setText(floatToText(totalPrice - price))

        self.payCommission.textChanged.connect(self.payCommissionChanged)
    
    def saleCommissionChanged(self, text):
        self.items['totalsaleprice'].widget().textChanged.disconnect(self.saleTotalPriceChanged)
        
        price = textToFloat(self.items['saleprice'].value())
        text = self.saleCommission.text().strip()
        if len(text) > 0 and text[-1] == '%':
            commission = price * textToFloat(text[0:-1]) / 100
        else:
            commission = textToFloat(text)
        self.items['totalsaleprice'].widget().setText(floatToText(price - commission))

        self.items['totalsaleprice'].widget().textChanged.connect(self.saleTotalPriceChanged)

    def saleTotalPriceChanged(self, text):
        self.saleCommission.textChanged.disconnect(self.saleCommissionChanged)

        price = textToFloat(self.items['saleprice'].value())
        totalPrice = textToFloat(self.items['totalsaleprice'].value())
        self.saleCommission.setText(floatToText(price - totalPrice))

        self.saleCommission.textChanged.connect(self.saleCommissionChanged)
    
def textToFloat(text):
    text = text.replace(',', '.')
    return float(text.replace(' ', '') or 0)

def floatToText(value):
    return str(int((value)*100 + 0.5)/100)

# Reimplementing QDoubleValidator for replace comma with dot and accept %
class CommissionValidator(QtGui.QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super(CommissionValidator, self).__init__(bottom, top, decimals, parent)
    
    def validate(self, input, pos):
        numericValue = input.strip()
        if len(numericValue) > 0 and numericValue[-1] == '%':
            numericValue = numericValue[0:-1]
        numericValue = numericValue.replace(',', '.')
        state, numericValue, pos = super(CommissionValidator, self).validate(numericValue, pos)
        return state, input, pos
