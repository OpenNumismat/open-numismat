from PyQt4.QtCore import Qt, QDate

from .FormItems import *
from .ImageLabel import ImageLabel

class FormItemTypes():
    String = 1
    ShortString = 2
    Number = 3
    Text = 4
    Money = 5
    Date = 6
    BigInt = 7
    Image = 8
    Money = 9
    Value = 10
    
    Mask = int('FF', 16)  # 0xFF
    Checkable = int('100', 16)  # 0x100

class FormItem(object):
    def __init__(self, field, title, itemType, parent=None):
        self._field = field
        self._title = title
        if itemType & FormItemTypes.Checkable:
            self._label = QtGui.QCheckBox(title, parent)
            self._label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        else:
            self._label = QtGui.QLabel(title, parent)
            self._label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            self._label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        
        type = itemType & FormItemTypes.Mask
        if type == FormItemTypes.String:
            self._widget = LineEdit(parent)
        elif type == FormItemTypes.ShortString:
            self._widget = ShortLineEdit(parent)
        elif type == FormItemTypes.Number:
            self._widget = NumberEdit(parent)
        elif type == FormItemTypes.BigInt:
            self._widget = BigIntEdit(parent)
        elif type == FormItemTypes.Value:
            self._widget = ValueEdit(parent)
        elif type == FormItemTypes.Money:
            self._widget = MoneyEdit(parent)
        elif type == FormItemTypes.Text:
            self._widget = TextEdit(parent)
        elif type == FormItemTypes.Image:
            self._widget = ImageLabel(parent)
        elif type == FormItemTypes.Date:
            self._widget = DateEdit(parent)
        else:
            raise
    
    def field(self):
        return self._field

    def title(self):
        return self._title

    def label(self):
        return self._label

    def widget(self):
        return self._widget
    
    def setWidget(self, widget):
        self._widget = widget
        
    def value(self):
        if isinstance(self._widget, QtGui.QTextEdit):
            return self._widget.toPlainText()
        elif isinstance(self._widget, QtGui.QDateTimeEdit):
            return self._widget.date().toString()
        elif isinstance(self._widget, QtGui.QAbstractSpinBox):
            return self._widget.value()
        elif isinstance(self._widget, ImageLabel):
            return self._widget.data()
        else:
            return self._widget.text()

    def setValue(self, value):
        if isinstance(self._widget, ImageLabel):
            self._widget.loadFromData(value)
        elif isinstance(self._widget, QtGui.QSpinBox):
            self._widget.setValue(int(value))
        elif isinstance(self._widget, QtGui.QDoubleSpinBox):
            self._widget.setValue(float(value))
        elif isinstance(self._widget, QtGui.QDateTimeEdit):
            self._widget.setDate(QDate.fromString(str(value)))
        else: 
            self._widget.setText(str(value))

class BaseFormLayout(QtGui.QGridLayout):
    def __init__(self, parent=None):
        super(BaseFormLayout, self).__init__()
        self.row = 0
        self.columnCount = 4

    def addRow(self, item1, item2=None):
        if not item2:
            self.addWidget(item1.label(), self.row, 0)
            # NOTE: columnSpan parameter in addWidget don't work with value -1
            # for 2-columns grid
            # self.addWidget(item1.widget(), self.row, 1, 1, -1)
            self.addWidget(item1.widget(), self.row, 1, 1, self.columnCount-1)
        else:
            self.addWidget(item1.label(), self.row, 0)

            if isinstance(item2, QtGui.QAbstractButton):
                self.addWidget(item1.widget(), self.row, 1, 1, 3)
                self.addWidget(item2, self.row, 4)
            else:
                self.addWidget(item1.widget(), self.row, 1)
        
                if item2.widget().sizePolicy().horizontalPolicy() == QtGui.QSizePolicy.Fixed:
                    item2.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
                self.addWidget(item2.label(), self.row, 2)
                self.addWidget(item2.widget(), self.row, 3, 1, self.columnCount-3)

        self.row = self.row + 1
