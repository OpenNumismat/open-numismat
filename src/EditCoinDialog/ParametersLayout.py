from .BaseFormLayout import BaseFormLayout
from .BaseFormLayout import FormItemTypes as Type

class ParametersLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(ParametersLayout, self).__init__(parent)
        
        self.addItem('metal', "Metal", Type.String) 
        self.addItem('fineness', "Fineness", Type.Number)
        self.addItem('form', "Form", Type.String)
        self.addItem('diameter', "Diameter", Type.Value)
        self.addItem('thick', "Thick", Type.Value)
        self.addItem('mass', "Mass", Type.Value)
        self.addItem('obvrev', "ObvRev", Type.String)
        
        self.addRow(self.item('metal'))
        self.addRow(self.item('fineness'), self.item('mass'))
        self.addRow(self.item('diameter'), self.item('thick'))
        self.addRow(self.item('form'))
        self.addRow(self.item('obvrev'))

        self.fillItems(record)
