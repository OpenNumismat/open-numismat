from .BaseFormLayout import BaseFormLayout
from .BaseFormLayout import FormItemTypes as Type

class EdgeDesignLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(EdgeDesignLayout, self).__init__(parent)
        self.columnCount = 2
        
        self.addItem('edgeimg', "", Type.Image),
        self.addItem('edge', "Type", Type.String) 
        self.addItem('edgelabel', "Label", Type.String)

        item = self.item('edgeimg')
        self.setColumnMinimumWidth(2, 160)
        self.addWidget(item.widget(), 0, 2, 2, 1)
        
        self.addRow(self.item('edge'))
        self.addRow(self.item('edgelabel'))

        self.fillItems(record)
