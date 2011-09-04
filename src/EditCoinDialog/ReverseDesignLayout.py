from .BaseFormLayout import BaseFormLayout
from .BaseFormLayout import FormItemTypes as Type

class ReverseDesignLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ReverseDesignLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.addItem('reverseimg', "", Type.Image)
        self.addItem('reversedesign', "Design", Type.Text)
        self.addItem('reversedesigner', "Designer", Type.String)

        item = self.item('reverseimg')
        self.setColumnMinimumWidth(2, 160)
        self.addWidget(item.widget(), 0, 2, 2, 1)
        
        self.addRow(self.item('reversedesign'))
        self.addRow(self.item('reversedesigner'))

        self.fillItems(record)
