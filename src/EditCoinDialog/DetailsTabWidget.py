from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from .BaseFormLayout import BaseFormLayout, BaseFormGroupBox, FormItem
from Collection.CollectionFields import CollectionFields
from Collection.CollectionFields import FieldTypes as Type

class DetailsTabWidget(QtGui.QTabWidget):
    def __init__(self, reference, parent=None, usedFields=None):
        super(DetailsTabWidget, self).__init__(parent)
        
        self.usedFields = usedFields
        self.reference = reference
        
        self.createItems()

        # Create Coin page
        main = self.mainDetailsLayout()
        main.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        state = self.stateLayout()
        self.addTabPage(self.tr("Coin"), [main, state])

        # Create Traffic page
        self.oldTrafficIndex = 0
        parts = self.__createTrafficParts(self.oldTrafficIndex)
        self.addTabPage(self.tr("Traffic"), parts)

        # Create Parameters page
        parameters = self.parametersLayout()
        parameters.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        minting = self.mintingLayout()
        minting.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        self.addTabPage(self.tr("Parameters"), [parameters, minting])

        # Create Design page
        obverse = self.obverseDesignLayout()
        reverse = self.reverseDesignLayout()
        edge = self.edgeDesignLayout()
        subject = self.subjectLayout()

        self.addTabPage(self.tr("Design"), [obverse, reverse, edge, subject])

        # Create Classification page
        classification = self.classificationLayout()

        price = self.priceLayout()
        price.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        variation = self.variationLayout()

        self.addTabPage(self.tr("Classification"), [classification, price, variation])

        # Create Images page
        images = self.imagesLayout()
        self.addTabPage(self.tr("Images"), images)
    
    def __layoutToWidget(self, layout):
        widget = QtGui.QWidget(self)
        widget.setLayout(layout)
        return widget
    
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
            self.addTab(self.__layoutToWidget(pageLayout), title)
            if len(parts) == 0:
                self.setTabEnabled(1, False)
        else:
            # Convert layout to widget and add to tab page
            self.addTab(self.__layoutToWidget(parts), title)
    
    def addItem(self, field):
        checkable = 0
        if self.usedFields:
            checkable = Type.Checkable

        refSection = None
        if self.reference:
            refSection = self.reference.section(field.name)

        item = FormItem(field.name, field.title, field.type | checkable, refSection)
        self.items[field.name] = item
    
    def createItems(self):
        self.items = {}
        
        fields = CollectionFields()
        skippedFields = [fields.id,]
        for field in fields:
            if field in skippedFields:
                continue
            self.addItem(field)
        
        self.connectReference(self.reference)
        
    def connectReference(self, reference):
        if reference:
            self.items['country'].widget().addDependent(self.items['period'].widget())
            self.items['country'].widget().addDependent(self.items['unit'].widget())
            self.items['country'].widget().addDependent(self.items['mint'].widget())
            self.items['country'].widget().addDependent(self.items['series'].widget())
    
    def fillItems(self, record):
        if not record.isEmpty():
            fields = CollectionFields()
            skippedFields = [fields.id,]
            for field in fields:
                if field in skippedFields:
                    continue
                item = self.items[field.name]
                if not record.isNull(item.field()):
                    value = record.value(item.field())
                    item.setValue(value)

            if self.usedFields:
                for item in self.items.values():
                    if self.usedFields[record.indexOf(item.field())]:
                        item.label().setCheckState(Qt.Checked)
            
        self.indexChangedState(self.oldTrafficIndex)

    def mainDetailsLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Main details"), parent)
        layout.layout.columnCount = 6
       
        btn = QtGui.QPushButton(self.tr("Generate"), parent)
        btn.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        btn.clicked.connect(self.clickGenerateTitle)
        self.items['title'].widget().textChanged.connect(self.textChangedTitle)
        layout.addRow(self.items['title'], btn)

        layout.addRow(self.items['country'])
        layout.addRow(self.items['period'])
        layout.addRow(self.items['value'], self.items['unit'])
        layout.addRow(self.items['year'])
        layout.addRow(self.items['mintmark'], self.items['mint'])
        layout.addRow(self.items['type'])
        layout.addRow(self.items['series'])

        return layout

    def stateLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("State"), parent)
        
        self.items['state'].widget().currentIndexChanged.connect(self.indexChangedState)
        layout.addRow(self.items['state'], self.items['grade'])
        layout.addRow(self.items['note'])

        return layout

    def payLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Buy"), parent)
        
        layout.addRow(self.items['paydate'], self.items['payprice'])

        # Add auxiliary field
        item = self.addPayCommission()

        layout.addRow(self.items['totalpayprice'], item)
        layout.addRow(self.items['saller'])
        layout.addRow(self.items['payplace'])
        layout.addRow(self.items['payinfo'])

        return layout

    def saleLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Sale"), parent)
        
        layout.addRow(self.items['saledate'], self.items['saleprice'])

        # Add auxiliary field
        item = self.addSaleCommission()
        layout.addRow(self.items['totalsaleprice'], item)

        layout.addRow(self.items['buyer'])
        layout.addRow(self.items['saleplace'])
        layout.addRow(self.items['saleinfo'])

        return layout

    def passLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Pass"), parent)
        
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
        layout = BaseFormGroupBox(self.tr("Parameters"), parent)
        
        layout.addRow(self.items['metal'])
        layout.addRow(self.items['fineness'], self.items['mass'])
        layout.addRow(self.items['diameter'], self.items['thick'])
        layout.addRow(self.items['form'])
        layout.addRow(self.items['obvrev'])

        return layout

    def mintingLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Minting"), parent)
        
        layout.addRow(self.items['issuedate'], self.items['mintage'])
        layout.addRow(self.items['dateemis'])

        return layout

    def obverseDesignLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Obverse"), parent)
        layout.layout.columnCount = 2
        
        item = self.items['obverseimg']
        layout.layout.setColumnMinimumWidth(2, 160)
        layout.layout.addWidget(item.widget(), 0, 2, 2, 1)
        
        layout.addRow(self.items['obversedesign'])
        layout.addRow(self.items['obversedesigner'])

        return layout

    def reverseDesignLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Reverse"), parent)
        layout.layout.columnCount = 2
        
        item = self.items['reverseimg']
        layout.layout.setColumnMinimumWidth(2, 160)
        layout.layout.addWidget(item.widget(), 0, 2, 2, 1)
        
        layout.addRow(self.items['reversedesign'])
        layout.addRow(self.items['reversedesigner'])

        return layout

    def edgeDesignLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Edge"), parent)
        layout.layout.columnCount = 2
        
        item = self.items['edgeimg']
        layout.layout.setColumnMinimumWidth(2, 160)
        layout.layout.addWidget(item.widget(), 0, 2, 2, 1)
        
        layout.addRow(self.items['edge'])
        layout.addRow(self.items['edgelabel'])

        return layout

    def subjectLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        layout.columnCount = 2
        
        layout.addRow(self.items['subject'])

        return layout

    def classificationLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['catalognum1'])
        layout.addRow(self.items['catalognum2'])
        layout.addRow(self.items['catalognum3'])
        layout.addRow(self.items['rarity'])

        return layout

    def priceLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Price"), parent)
        
        layout.addRow(self.items['price1'], self.items['price2'])
        layout.addRow(self.items['price3'], self.items['price4'])
        layout.addRow(self.items['price5'], self.items['price6'])

        return layout

    def variationLayout(self, parent=None):
        layout = BaseFormGroupBox(self.tr("Variation"), parent)
        
        layout.addRow(self.items['obversevar'])
        layout.addRow(self.items['reversevar'])
        layout.addRow(self.items['edgevar'])

        return layout

    def imagesLayout(self, parent=None):
        layout = BaseFormLayout(parent)

        item = self.items['photo1']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
#        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(), 0, 0)
        layout.addWidget(item.widget(), 1, 0)
        item = self.items['photo2']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
#        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(),0,1)
        layout.addWidget(item.widget(),1,1)
        item = self.items['photo3']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
#        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(),2,0)
        layout.addWidget(item.widget(),3,0)
        item = self.items['photo4']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
#        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(),2,1)
        layout.addWidget(item.widget(),3,1)

        layout.setRowMinimumHeight(1, 120)
        layout.setRowMinimumHeight(3, 120)
        layout.setColumnMinimumWidth(0, 160)
        layout.setColumnMinimumWidth(1, 160)

        return layout

    def clickGenerateTitle(self):
        titleParts = []
        for key in ['value', 'unit', 'year', 'mintmark']:
            value = str(self.items[key].value())
            if value:
                titleParts.append(value) 

        title = ' '.join(titleParts)
        self.items['title'].setValue(title)

    def textChangedTitle(self, text):
        if self.usedFields:
            self.parent().setWindowTitle(self.tr("Multi edit"))
        else:
            title = [self.tr("Edit"),]
            if text:
                title.insert(0, text)
            self.parent().setWindowTitle(' - '.join(title))
    
    def __createTrafficParts(self, index=0):
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
            pageParts.append(pay)
            sale = self.saleLayout()
            pageParts.append(sale)
        elif index == 4:
            pay = self.payLayout()
            pageParts.append(pay)
        
        self.oldTrafficIndex = index
        
        return pageParts

    def indexChangedState(self, index):
        self.removeTab(1)
        pageParts = self.__createTrafficParts(index)

        pageLayout = QtGui.QVBoxLayout()
        # Fill layout with it's parts
        for part in pageParts:
            pageLayout.addWidget(part)

        # Convert layout to widget and add to tab page
        self.insertTab(1, self.__layoutToWidget(pageLayout), self.tr("Traffic"))
        if len(pageParts) == 0:
            self.setTabEnabled(1, False)
            self.items['grade'].widget().setEnabled(False)
        else:
            self.items['grade'].widget().setEnabled(True)
    
    def addPayCommission(self):
        item = FormItem(None, self.tr("Commission"), Type.Money)
        self.payCommission = item.widget()
        validator = CommissionValidator(0, 9999999999, 2, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.payCommission.setValidator(validator)
        
        price = textToFloat(self.items['payprice'].value())
        totalPrice = textToFloat(self.items['totalpayprice'].value())
        self.payCommission.setText(floatToText(totalPrice - price))

        self.items['payprice'].widget().textChanged.connect(self.payCommissionChanged)
        self.payCommission.textChanged.connect(self.payCommissionChanged)
        self.items['totalpayprice'].widget().textChanged.connect(self.payTotalPriceChanged)
        
        return item
    
    def addSaleCommission(self):
        item = FormItem('', self.tr("Commission"), Type.Money)
        self.saleCommission = item.widget()
        validator = CommissionValidator(0, 9999999999, 2, self)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.saleCommission.setValidator(validator)
        
        price = textToFloat(self.items['saleprice'].value())
        totalPrice = textToFloat(self.items['totalsaleprice'].value())
        self.saleCommission.setText(floatToText(price - totalPrice))

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
