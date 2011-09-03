from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class ClassificationLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ClassificationLayout, self).__init__(parent)
        
        self.addItem('catalognum1', "#", Type.String) 
        self.addItem('catalognum2', "#", Type.String)
        self.addItem('catalognum3', "#", Type.String)
        self.addItem('rarity', "Rarity", Type.ShortString)
        
        self.addRow(self.item('catalognum1'))
        self.addRow(self.item('catalognum2'))
        self.addRow(self.item('catalognum3'))
        self.addRow(self.item('rarity'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
