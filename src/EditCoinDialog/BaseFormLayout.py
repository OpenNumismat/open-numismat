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
        
        self._type = itemType & Type.Mask
        if self._type == Type.String:
            if reference:
                self._widget = LineEditRef(reference, parent)
            else:
                self._widget = LineEdit(parent)
        elif self._type == Type.ShortString:
            self._widget = ShortLineEdit(parent)
        elif self._type == Type.Number:
            self._widget = NumberEdit(parent)
        elif self._type == Type.BigInt:
            self._widget = BigIntEdit(parent)
        elif self._type == Type.Value:
            self._widget = ValueEdit(parent)
        elif self._type == Type.Money:
            self._widget = MoneyEdit(parent)
        elif self._type == Type.Text:
            self._widget = TextEdit(parent)
        elif self._type == Type.Image:
            self._widget = ImageEdit(parent)
        elif self._type == Type.EdgeImage:
            self._widget = EdgeImageEdit(parent)
        elif self._type == Type.Date:
            self._widget = DateEdit(parent)
        elif self._type == Type.Status:
            self._widget = StatusEdit(parent)
        elif self._type == Type.DateTime:
            self._widget = DateEdit(parent)
        elif self._type == Type.EdgeImage:
            self._widget = EdgeImageEdit(parent)
        else:
            raise
        
        if itemType & Type.Disabled:
            if self._type in [Type.Status, Type.Image, Type.EdgeImage]:
                self._widget.setDisabled(True)
            else:
                self._widget.setReadOnly(True)

        if itemType & Type.Checkable:
            # Disable fields with unchecked labels
            self._widget.setDisabled(True)

        self.hidden = False
    
    def setHidden(self):
        self.hidden = True
    
    def isHidden(self):
        return self.hidden
    
    def checkBoxChanged(self, state):
        self._widget.setDisabled(state == Qt.Unchecked)
    
    def field(self):
        return self._field

    def title(self):
        return self._title

    def label(self):
        return self._label
    
    def type(self):
        return self._type

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

    def isEmpty(self):
        return self.row == 0

    def addRow(self, item1, item2=None):
        if not item2:
            if item1.isHidden():
                return
            self.addWidget(item1.label(), self.row, 0)
            widget = item1.widget()
            # NOTE: columnSpan parameter in addWidget don't work with value -1
            # for 2-columns grid
            # self.addWidget(widget, self.row, 1, 1, -1)
            self.addWidget(widget, self.row, 1, 1, self.columnCount-1)
            if isinstance(widget, NumberEdit):
                widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        else:
            if item1.isHidden() and item2.isHidden():
                return

            if isinstance(item2, QtGui.QAbstractButton):
                if item1.isHidden():
                    return

                self.addWidget(item1.label(), self.row, 0)
                self.addWidget(item1.widget(), self.row, 1, 1, 4)
                self.addWidget(item2, self.row, 5)
            else:
                col = 0
                if not item1.isHidden():
                    self.addWidget(item1.label(), self.row, col)
                    col = col + 1
                    self.addWidget(item1.widget(), self.row, col)
                    col = col + 1

                    widget = QtGui.QWidget()
                    widget.setMinimumWidth(0)
                    if self.columnCount == 6:
                        widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
                    self.addWidget(widget, self.row, col)
                    col = col + 1
        
                if not item2.isHidden():
                    if item2.widget().sizePolicy().horizontalPolicy() == QtGui.QSizePolicy.Fixed:
                        item2.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
                    self.addWidget(item2.label(), self.row, col)
                    col = col + 1
                    self.addWidget(item2.widget(), self.row, col, 1, self.columnCount-4)

        self.row = self.row + 1

class BaseFormGroupBox(QtGui.QGroupBox):
    def __init__(self, title, parent=None):
        super(BaseFormGroupBox, self).__init__(title, parent)
        
        self.layout = BaseFormLayout(self)
        self.setLayout(self.layout)
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
    
    def isEmpty(self):
        return self.layout.isEmpty()
    
    def addRow(self, item1, item2=None):
        self.layout.addRow(item1, item2)

        # If field is a Text - make it vertical size preferred
        self.fixSizePolicy(item1)
        if item2 and not isinstance(item2, QtGui.QAbstractButton):
            self.fixSizePolicy(item2)

    def fixSizePolicy(self, item):
        if not item.isHidden() and item.type() == Type.Text:
            self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)

class ImageFormLayout(BaseFormLayout):
    def __init__(self, parent=None):
        super(ImageFormLayout, self).__init__(parent)
        
        self.imagesCount = 0
    
    def addImages(self, images):
        for image in images:
            if not image.isHidden():
                image.label().setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
                if isinstance(image.label(), QtGui.QLabel):
                    image.label().setAlignment(Qt.AlignLeft)
                
                row = int(self.imagesCount/2)
                col = self.imagesCount%2
                
                self.addWidget(image.label(), row*2, col)
                self.addWidget(image.widget(), row*2+1, col)
                
                self.setRowMinimumHeight(row*2+1, 120)
                self.setColumnMinimumWidth(col, 160)
                
                self.imagesCount = self.imagesCount+1
    
    def isEmpty(self):
        return (self.imagesCount == 0)

class DesignFormLayout(BaseFormGroupBox):
    def __init__(self, title, parent=None):
        super(DesignFormLayout, self).__init__(title, parent)
        self.layout.columnCount = 2
    
    def addImage(self, image):
        if not image.isHidden():
            self.layout.addWidget(image.widget(), 0, 2, 2, 1)
            self.layout.setColumnMinimumWidth(2, 160)
