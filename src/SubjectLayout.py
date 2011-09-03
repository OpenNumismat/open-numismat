from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItemTypes as Type

class SubjectLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(SubjectLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.addItem('subject', "Subject", Type.Text)
        
        self.addRow(self.item('subject'))

        self.fillItems(record)

if __name__ == '__main__':
    from main import run
    run()
