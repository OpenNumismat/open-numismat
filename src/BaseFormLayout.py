from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate

from ImageLabel import ImageLabel

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

class LineEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)
        self.setMaxLength(1024)

class ShortLineEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(ShortLineEdit, self).__init__(parent)
        self.setMaxLength(10)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    
    def sizeHint(self):
        return self.minimumSizeHint()

class NumberEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(NumberEdit, self).__init__(parent)
        validator = QtGui.QIntValidator(0, 9999, parent)
        self.setValidator(validator)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

    def sizeHint(self):
        return self.minimumSizeHint()

class BigIntEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(BigIntEdit, self).__init__(parent)
        validator = QtGui.QDoubleValidator(0, 999999999999999, 0, parent)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)

class ValueEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(ValueEdit, self).__init__(parent)
        validator = QtGui.QDoubleValidator(0, 9999999999, 3, parent)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    
    def sizeHint(self):
        return self.minimumSizeHint()

class MoneyEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(MoneyEdit, self).__init__(parent)
        validator = QtGui.QDoubleValidator(0, 9999999999, 2, parent)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
    
    def sizeHint(self):
        return self.minimumSizeHint()

class TextEdit(QtGui.QTextEdit):
    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)

    def sizeHint(self):
        return self.minimumSizeHint()

class DateEdit(QtGui.QDateEdit):
    def __init__(self, parent=None):
        super(DateEdit, self).__init__(parent)
        calendar = QtGui.QCalendarWidget()
        calendar.setGridVisible(True)
        self.setCalendarPopup(True)
        self.setCalendarWidget(calendar)
        self.setMinimumWidth(85)

class FormItem(object):
    def __init__(self, field, title, itemType, parent=None):
        self._field = field
        self._title = title
        self._label = QtGui.QLabel(title, parent)
        self._label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self._label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)

        if itemType == FormItemTypes.String:
            self._widget = LineEdit(parent)
        elif itemType == FormItemTypes.ShortString:
            self._widget = ShortLineEdit(parent)
        elif itemType == FormItemTypes.Number:
            self._widget = NumberEdit(parent)
        elif itemType == FormItemTypes.BigInt:
            self._widget = BigIntEdit(parent)
        elif itemType == FormItemTypes.Value:
            self._widget = ValueEdit(parent)
        elif itemType == FormItemTypes.Money:
            self._widget = MoneyEdit(parent)
        elif itemType == FormItemTypes.Text:
            self._widget = TextEdit(parent)
        elif itemType == FormItemTypes.Image:
            self._widget = ImageLabel(parent)
        elif itemType == FormItemTypes.Date:
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
        type(self._widget)
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
    def __init__(self, record, parent=None):
        super(BaseFormLayout, self).__init__(parent)
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
            if item1.widget().sizePolicy().horizontalPolicy() == QtGui.QSizePolicy.Fixed:
                item1.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
            self.addWidget(item1.label(), self.row, 0)

            if isinstance(item2, QtGui.QAbstractButton):
                self.addWidget(item1.widget(), self.row, 1, 1, 3)
                self.addWidget(item2, self.row, 4)
            else:
                self.addWidget(item1.widget(), self.row, 1)
        
                if item2.widget().sizePolicy().horizontalPolicy() == QtGui.QSizePolicy.Fixed:
                    item2.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
                self.addWidget(item2.label(), self.row, 2)
                self.addWidget(item2.widget(), self.row, 3, 1, -1)

        self.row = self.row + 1

if __name__ == '__main__':
    from main import run
    run()
