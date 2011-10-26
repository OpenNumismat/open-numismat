from PyQt4.QtCore import Qt, QDate

from .FormItems import *
from .ImageLabel import ImageEdit, EdgeImageEdit
from Collection.CollectionFields import FieldTypes as Type

class FormItem(object):
    def __init__(self, field, title, itemType, reference=None, parent=None):
        self._field = field
        self._title = title
        if itemType & Type.Checkable:
            self._label = QtGui.QCheckBox(title, parent)
            self._label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
            self._label.stateChanged.connect(self.checkBoxChanged)
        else:
            self._label = QtGui.QLabel(title, parent)
            self._label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            self._label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        
        type_ = itemType & Type.Mask
        if type_ == Type.String:
            if reference:
                self._widget = LineEditRef(reference, parent)
            else:
                self._widget = LineEdit(parent)
        elif type_ == Type.ShortString:
            self._widget = ShortLineEdit(parent)
        elif type_ == Type.Number:
            self._widget = NumberEdit(parent)
        elif type_ == Type.BigInt:
            self._widget = BigIntEdit(parent)
        elif type_ == Type.Value:
            self._widget = ValueEdit(parent)
        elif type_ == Type.Money:
            self._widget = MoneyEdit(parent)
        elif type_ == Type.Text:
            self._widget = TextEdit(parent)
        elif type_ == Type.Image:
            self._widget = ImageEdit(parent)
        elif type_ == Type.EdgeImage:
            self._widget = EdgeImageEdit(parent)
        elif type_ == Type.Date:
            self._widget = DateEdit(parent)
        elif type_ == Type.Status:
            self._widget = StatusEdit(parent)
        elif type_ == Type.DateTime:
            self._widget = DateEdit(parent)
        elif type_ == Type.EdgeImage:
            self._widget = EdgeImageEdit(parent)
        else:
            raise
        
        if itemType & Type.Disabled:
            if type_ == Type.Status or type_ == Type.Image or type_ == Type.EdgeImage:
                self._widget.setDisabled(True)
            else:
                self._widget.setReadOnly(True)

        if itemType & Type.Checkable:
            # Disable fields with unchecked labels
            self._widget.setDisabled(True)
    
    def checkBoxChanged(self, state):
        self._widget.setDisabled(state == Qt.Unchecked)
    
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
            return self._widget.date().toString(Qt.ISODate)
        elif isinstance(self._widget, QtGui.QAbstractSpinBox):
            return self._widget.value()
        elif isinstance(self._widget, ImageEdit):
            return self._widget.data()
        elif isinstance(self._widget, StatusEdit):
            return self._widget.data()
        else:
            return self._widget.text()

    def setValue(self, value):
        if isinstance(self._widget, ImageEdit):
            self._widget.loadFromData(value)
        elif isinstance(self._widget, QtGui.QSpinBox):
            self._widget.setValue(int(value))
        elif isinstance(self._widget, QtGui.QDoubleSpinBox):
            self._widget.setValue(float(value))
        elif isinstance(self._widget, QtGui.QDateTimeEdit):
            self._widget.setDate(QDate.fromString(str(value), Qt.ISODate))
        elif isinstance(self._widget, StatusEdit):
            self._widget.setCurrentValue(value)
        else: 
            self._widget.setText(str(value))
    
    def clear(self):
        if isinstance(self._widget, StatusEdit):
            self._widget.setCurrentValue('demo')
        else: 
            self._widget.clear()

class BaseFormLayout(QtGui.QGridLayout):
    def __init__(self, parent=None):
        super(BaseFormLayout, self).__init__()
        self.row = 0
        self.columnCount = 5

    def addRow(self, item1, item2=None):
        if not item2:
            self.addWidget(item1.label(), self.row, 0)
            widget = item1.widget()
            # NOTE: columnSpan parameter in addWidget don't work with value -1
            # for 2-columns grid
            # self.addWidget(widget, self.row, 1, 1, -1)
            self.addWidget(widget, self.row, 1, 1, self.columnCount-1)
            if isinstance(widget, NumberEdit):
                widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        else:
            self.addWidget(item1.label(), self.row, 0)

            if isinstance(item2, QtGui.QAbstractButton):
                self.addWidget(item1.widget(), self.row, 1, 1, 4)
                self.addWidget(item2, self.row, 5)
            else:
                widget = item1.widget()
                self.addWidget(widget, self.row, 1)
                widget = QtGui.QWidget()
                widget.setMinimumWidth(0)
                if self.columnCount == 6:
                    widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
                self.addWidget(widget, self.row, 2)
        
                if item2.widget().sizePolicy().horizontalPolicy() == QtGui.QSizePolicy.Fixed:
                    item2.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
                self.addWidget(item2.label(), self.row, 3)
                self.addWidget(item2.widget(), self.row, 4, 1, self.columnCount-4)

        self.row = self.row + 1

class BaseFormGroupBox(QtGui.QGroupBox):
    def __init__(self, title, parent=None):
        super(BaseFormGroupBox, self).__init__(title, parent)
        
        self.layout = BaseFormLayout(self)
        self.setLayout(self.layout)
    
    def addRow(self, item1, item2=None):
        self.layout.addRow(item1, item2)
