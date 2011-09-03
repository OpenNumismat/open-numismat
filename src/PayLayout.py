from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class PayLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(PayLayout, self).__init__(parent)
        
        self.addItem('paydate', "Date", Type.Date) 
        self.addItem('payprice', "Price", Type.Money)
        self.addItem('saller', "Saller", Type.String)
        self.addItem('payplace', "Place", Type.String)
        self.addItem('payinfo', "Info", Type.Text)
        
        self.addRow(self.item('paydate'), self.item('payprice'))
        self.addRow(self.item('saller'))
        self.addRow(self.item('payplace'))
        self.addRow(self.item('payinfo'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
