from .BaseFormLayout import BaseFormLayout
from .BaseFormLayout import FormItemTypes as Type

class ObverseDesignLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ObverseDesignLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.addItem('obverseimg', "", Type.Image)
        self.addItem('obversedesign', "Design", Type.Text) 
        self.addItem('obversedesigner', "Designer", Type.String)

        item = self.item('obverseimg')
        self.setColumnMinimumWidth(2, 160)
        self.addWidget(item.widget(), 0, 2, 2, 1)
        
        self.addRow(self.item('obversedesign'))
        self.addRow(self.item('obversedesigner'))

        self.fillItems(record)
