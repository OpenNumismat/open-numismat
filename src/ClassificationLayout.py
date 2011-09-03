from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class ClassificationLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ClassificationLayout, self).__init__(parent)
        
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
        
        self.addRow(self.item('catalognum1'))
        self.addRow(self.item('catalognum2'))
        self.addRow(self.item('catalognum3'))
        self.addRow(self.item('rarity'))
        self.addRow(self.item('price1'), self.item('price2'))
        self.addRow(self.item('price3'), self.item('price4'))
        self.addRow(self.item('price5'), self.item('price6'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
