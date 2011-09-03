from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class MintingLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(MintingLayout, self).__init__(parent)
        
        self.addItem('issuedate', "Date of issue", Type.Date) 
        self.addItem('dateemis', "Emission period", Type.String)
        self.addItem('mintage', "Mintage", Type.BigInt)
        
        self.addRow(self.item('issuedate'), self.item('mintage'))
        self.addRow(self.item('dateemis'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
