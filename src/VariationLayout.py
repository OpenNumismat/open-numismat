from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class VariationLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(VariationLayout, self).__init__(parent)
        
        self.addItem('obversevar', "Obverse", Type.Text) 
        self.addItem('reversevar', "Reverse", Type.Text)
        self.addItem('edgevar', "Edge", Type.Text)
        
        self.addRow(self.item('obversevar'))
        self.addRow(self.item('reversevar'))
        self.addRow(self.item('edgevar'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
