from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from .BaseFormLayout import BaseFormLayout, FormItem
from .BaseFormLayout import FormItemTypes as Type

class EditCoinDialog(QtGui.QDialog):
    def __init__(self, record, parent=None):
        super(EditCoinDialog, self).__init__(parent)
        
        self.record = record
        
        self.tab = QtGui.QTabWidget(self)
        
        self.createItems()

        # Create Coin page
        main = self.mainDetailsLayout()
        groupBox1 = self.__layoutToGroupBox(main, self.tr("Main details"))
        groupBox1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        
        state = self.stateLayout()
        groupBox2 = self.__layoutToGroupBox(state, self.tr("State"))
        
        self.addTabPage(self.tr("Coin"), [groupBox1, groupBox2])

        # Create State page
        pay = self.payLayout()
        groupBox1 = self.__layoutToGroupBox(pay, self.tr("Pay"))
        
        sale = self.saleLayout()
        groupBox2 = self.__layoutToGroupBox(sale, self.tr("Sale"))
        
        self.addTabPage(self.tr("Traffic"), [groupBox1, groupBox2])

        # Create Parameters page
        parameters = self.parametersLayout()
        groupBox1 = self.__layoutToGroupBox(parameters, self.tr("Parameters"))
        groupBox1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        minting = self.mintingLayout()
        groupBox2 = self.__layoutToGroupBox(minting, self.tr("Minting"))
        groupBox2.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        self.addTabPage(self.tr("Parameters"), [groupBox1, groupBox2])

        # Create Design page
        obverse = self.obverseDesignLayout()
        groupBox1 = self.__layoutToGroupBox(obverse, self.tr("Obverse"))
        
        reverse = self.reverseDesignLayout()
        groupBox2 = self.__layoutToGroupBox(reverse, self.tr("Reverse"))

        edge = self.edgeDesignLayout()
        groupBox3 = self.__layoutToGroupBox(edge, self.tr("Edge"))

        subject = self.subjectLayout()

        self.addTabPage(self.tr("Design"), [groupBox1, groupBox2, groupBox3, subject])

        # Create Classification page
        classification = self.classificationLayout()

        price = self.priceLayout()
        groupBox1 = self.__layoutToGroupBox(price, self.tr("Price"))
        groupBox1.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)

        variation = self.variationLayout()
        groupBox2 = self.__layoutToGroupBox(variation, self.tr("Variation"))

        self.addTabPage(self.tr("Classification"), [classification, groupBox1, groupBox2])

        # Create Images page
        images = self.imagesLayout()
        self.addTabPage(self.tr("Images"), images)

        self.fillItems(record)

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
        for item in self.items.values():
            self.record.setValue(item.field(), item.value())

        self.accept()

    def getRecord(self):
        return self.record
    
    def done(self, r):
        settings = QtCore.QSettings()
        settings.setValue('editcoinwindow/size', self.size());
        super(EditCoinDialog, self).done(r)
    
    def addItem(self, field, title, itemType):
        item = FormItem(field, title, itemType, self)
        self.items[field] = item
    
    def createItems(self):
        self.items = {}

        self.addItem('title', "Name", Type.String) 
        self.addItem('value', "Value", Type.Money)
        self.addItem('unit', "Unit", Type.String)
        self.addItem('country', "Country", Type.String)
        self.addItem('year', "Year", Type.Number)
        self.addItem('period', "Period", Type.String)
        self.addItem('mint', "Mint", Type.String)
        self.addItem('mintmark', "Mint mark", Type.ShortString)
        self.addItem('type', "Type", Type.String)
        self.addItem('series', "Series", Type.String)

        self.addItem('state', "State", Type.String)
        self.addItem('grade', "Grade", Type.String)
        self.addItem('note', "Note", Type.Text)

        self.addItem('paydate', "Date", Type.Date) 
        self.addItem('payprice', "Price", Type.Money)
        self.addItem('saller', "Saller", Type.String)
        self.addItem('payplace', "Place", Type.String)
        self.addItem('payinfo', "Info", Type.Text)
        
        self.addItem('saledate', "Date", Type.Date) 
        self.addItem('saleprice', "Price", Type.Money)
        self.addItem('buyer', "Buyer", Type.String)
        self.addItem('saleplace', "Place", Type.String)
        self.addItem('saleinfo', "Info", Type.Text)
        
        self.addItem('metal', "Metal", Type.String) 
        self.addItem('fineness', "Fineness", Type.Number)
        self.addItem('form', "Form", Type.String)
        self.addItem('diameter', "Diameter", Type.Value)
        self.addItem('thick', "Thick", Type.Value)
        self.addItem('mass', "Mass", Type.Value)
        self.addItem('obvrev', "ObvRev", Type.String)
        
        self.addItem('issuedate', "Date of issue", Type.Date) 
        self.addItem('dateemis', "Emission period", Type.String)
        self.addItem('mintage', "Mintage", Type.BigInt)
        
        self.addItem('obverseimg', "", Type.Image)
        self.addItem('obversedesign', "Design", Type.Text) 
        self.addItem('obversedesigner', "Designer", Type.String)

        self.addItem('reverseimg', "", Type.Image)
        self.addItem('reversedesign', "Design", Type.Text)
        self.addItem('reversedesigner', "Designer", Type.String)

        self.addItem('edgeimg', "", Type.Image),
        self.addItem('edge', "Type", Type.String) 
        self.addItem('edgelabel', "Label", Type.String)

        self.addItem('subject', "Subject", Type.Text)
        
        self.addItem('catalognum1', "#", Type.String) 
        self.addItem('catalognum2', "#", Type.String)
        self.addItem('catalognum3', "#", Type.String)
        self.addItem('rarity', "Rarity", Type.ShortString)
        
        self.addItem('price1', "Fine", Type.Money)
        self.addItem('price2', "VF", Type.Money)
        self.addItem('price3', "XF", Type.Money)
        self.addItem('price4', "AU", Type.Money)
        self.addItem('price5', "Unc", Type.Money)
        self.addItem('price6', "Proof", Type.Money)
        
        self.addItem('obversevar', "Obverse", Type.Text)
        self.addItem('reversevar', "Reverse", Type.Text)
        self.addItem('edgevar', "Edge", Type.Text)
        
        self.addItem('photo1', "Photo 1", Type.Image)
        self.addItem('photo2', "Photo 2", Type.Image)
        self.addItem('photo3', "Photo 3", Type.Image)
        self.addItem('photo4', "Photo 4", Type.Image)
        
    def fillItems(self, record):
        if not record.isEmpty():
            for item in self.items.values():
                if not record.isNull(item.field()):
                    value = record.value(item.field())
                    item.setValue(value)

    def mainDetailsLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        layout.columnCount = 5
       
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

        return layout

    def stateLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['state'], self.items['grade'])
        layout.addRow(self.items['note'])

        return layout

    def payLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['paydate'], self.items['payprice'])
        layout.addRow(self.items['saller'])
        layout.addRow(self.items['payplace'])
        layout.addRow(self.items['payinfo'])

        return layout

    def saleLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['saledate'], self.items['saleprice'])
        layout.addRow(self.items['buyer'])
        layout.addRow(self.items['saleplace'])
        layout.addRow(self.items['saleinfo'])

        return layout

    def parametersLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['metal'])
        layout.addRow(self.items['fineness'], self.items['mass'])
        layout.addRow(self.items['diameter'], self.items['thick'])
        layout.addRow(self.items['form'])
        layout.addRow(self.items['obvrev'])

        return layout

    def mintingLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['issuedate'], self.items['mintage'])
        layout.addRow(self.items['dateemis'])

        return layout

    def obverseDesignLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        layout.columnCount = 2
        
        item = self.items['obverseimg']
        layout.setColumnMinimumWidth(2, 160)
        layout.addWidget(item.widget(), 0, 2, 2, 1)
        
        layout.addRow(self.items['obversedesign'])
        layout.addRow(self.items['obversedesigner'])

        return layout

    def reverseDesignLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        layout.columnCount = 2
        
        item = self.items['reverseimg']
        layout.setColumnMinimumWidth(2, 160)
        layout.addWidget(item.widget(), 0, 2, 2, 1)
        
        layout.addRow(self.items['reversedesign'])
        layout.addRow(self.items['reversedesigner'])

        return layout

    def edgeDesignLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        layout.columnCount = 2
        
        item = self.items['edgeimg']
        layout.setColumnMinimumWidth(2, 160)
        layout.addWidget(item.widget(), 0, 2, 2, 1)
        
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
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['price1'], self.items['price2'])
        layout.addRow(self.items['price3'], self.items['price4'])
        layout.addRow(self.items['price5'], self.items['price6'])

        return layout

    def variationLayout(self, parent=None):
        layout = BaseFormLayout(parent)
        
        layout.addRow(self.items['obversevar'])
        layout.addRow(self.items['reversevar'])
        layout.addRow(self.items['edgevar'])

        return layout

    def imagesLayout(self, parent=None):
        layout = BaseFormLayout(parent)

        item = self.items['photo1']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(), 0, 0)
        layout.addWidget(item.widget(), 1, 0)
        item = self.items['photo2']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(),0,1)
        layout.addWidget(item.widget(),1,1)
        item = self.items['photo3']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        item.label().setAlignment(Qt.AlignLeft)
        layout.addWidget(item.label(),2,0)
        layout.addWidget(item.widget(),3,0)
        item = self.items['photo4']
        item.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        item.label().setAlignment(Qt.AlignLeft)
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
