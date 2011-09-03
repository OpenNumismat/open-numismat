from BaseFormLayout import BaseFormLayout
from BaseFormLayout import FormItem as Item
from BaseFormLayout import FormItemTypes as Type

class StateLayout(BaseFormLayout):
    def __init__(self, record, parent=None):
        super(StateLayout, self).__init__(parent)
        
        self.items = [ Item('state', "State", Type.String, parent), 
            Item('grade', "Grade", Type.String, parent),
            Item('note', "Note", Type.Text, parent) ]
        
        item1 = self.items[0]
        item2 = self.items[1]
        self.addRow(item1, item2)

        item = self.items[2]
        self.addRow(item)

        if not record.isEmpty():
            for item in self.items:
                if not record.isNull(item.field()):
                    value = record.value(item.field())
                    item.setValue(str(value))

    def values(self):
        val = {}
        for item in self.items:
            val[item.field()] = item.value()
        return val

if __name__ == '__main__':
    from main import run
    run()
