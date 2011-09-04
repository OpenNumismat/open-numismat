from .BaseFormLayout import BaseFormLayout
from .BaseFormLayout import FormItemTypes as Type

class SaleLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(SaleLayout, self).__init__(parent)
        
        self.addItem('saledate', "Date", Type.Date) 
        self.addItem('saleprice', "Price", Type.Money)
        self.addItem('buyer', "Buyer", Type.String)
        self.addItem('saleplace', "Place", Type.String)
        self.addItem('saleinfo', "Info", Type.Text)
        
        self.addRow(self.item('saledate'), self.item('saleprice'))
        self.addRow(self.item('buyer'))
        self.addRow(self.item('saleplace'))
        self.addRow(self.item('saleinfo'))

        self.fillItems(record)
