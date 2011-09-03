from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class StateLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(StateLayout, self).__init__(parent)
        
        self.addItem('state', "State", Type.String) 
        self.addItem('grade', "Grade", Type.String)
        self.addItem('note', "Note", Type.Text)
        
        self.addRow(self.item('state'), self.item('grade'))
        self.addRow(self.item('note'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
