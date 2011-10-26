from PyQt4 import QtGui
from PyQt4.QtCore import QT_TR_NOOP, QMargins

# Reimplementing QDoubleValidator for replace comma with dot
class DoubleValidator(QtGui.QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super(DoubleValidator, self).__init__(bottom, top, decimals, parent)
    
    def validate(self, input, pos):
        input = input.replace(',', '.')
        return super(DoubleValidator, self).validate(input, pos)

class LineEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)
        self.setMaxLength(1024)
        self.setMinimumWidth(100)

class LineEditRef(QtGui.QWidget):
    def __init__(self, reference, parent=None):
        super(LineEditRef, self).__init__(parent)

        self.reference = reference
        self.reference.changed.connect(self.setText)

        self.comboBox = QtGui.QComboBox(self)
        self.comboBox.setEditable(True)
        self.comboBox.lineEdit().setMaxLength(1024)
        self.comboBox.setMinimumWidth(120)
        self.comboBox.setInsertPolicy(QtGui.QComboBox.NoInsert)
        
        self.comboBox.setModel(reference.model)
        self.comboBox.setModelColumn(reference.model.fieldIndex('value'))
        
        self.comboBox.setCurrentIndex(-1)

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.comboBox)
        layout.addWidget(reference.button(self))
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)
        
        self.dependents = []
    
    def clear(self):
        self.comboBox.clear()
    
    def setText(self, text):
        self.comboBox.setCurrentIndex(-1)
        self.comboBox.lineEdit().setText(text)
        index = self.comboBox.findText(text)
        self.updateDependents(index)
        if index >= 0:
            self.comboBox.setCurrentIndex(index)
    
    def text(self):
        return self.comboBox.currentText()
    
    def addDependent(self, reference):
        if not self.dependents:
            self.comboBox.currentIndexChanged.connect(self.updateDependents)
            self.comboBox.editTextChanged.connect(self.updateDependents)
        self.dependents.append(reference)
    
    def updateDependents(self, index):
        if isinstance(index, str):
            index = self.comboBox.findText(index)

        if index >= 0:
            model = self.comboBox.model()
            idIndex = model.fieldIndex('id')
            parentIndex = model.index(index, idIndex)
            for dependent in self.dependents:
                text = dependent.text()
                reference = dependent.reference
                reference.model.setFilter('parentid=%d' % model.data(parentIndex))
                reference.parentIndex = parentIndex
                dependent.setText(text)
        else:
            for dependent in self.dependents:
                text = dependent.text()
                reference = dependent.reference
                reference.model.setFilter('parentid IS NULL')
                reference.parentIndex = None
                dependent.setText(text)
    
class StatusEdit(QtGui.QComboBox):
    items = [('demo', QT_TR_NOOP("Demo")), ('pass', QT_TR_NOOP("Pass")),
             ('owned', QT_TR_NOOP("owned")), ('sold', QT_TR_NOOP("Sold")),
             ('sale', QT_TR_NOOP("sale")), ('wish', QT_TR_NOOP("Wish"))]
    
    def __init__(self, parent=None):
        super(StatusEdit, self).__init__(parent)
        
        for item in StatusEdit.items:
            self.addItem(item[1])
    
    def data(self):
        return StatusEdit.items[self.currentIndex()][0]
    
    def clear(self):
        self.setCurrentIndex(-1)
    
    def setCurrentValue(self, value):
        index = -1
        for item in StatusEdit.items:
            if item[0] == value:
                index = self.findText(item[1])
        
        if index >= 0:
            self.setCurrentIndex(index)

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
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))

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
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))

class ValueEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(ValueEdit, self).__init__(parent)
        validator = DoubleValidator(0, 9999999999, 3, parent)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))
    
    def sizeHint(self):
        return self.minimumSizeHint()

class MoneyEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        super(MoneyEdit, self).__init__(parent)
        validator = DoubleValidator(0, 9999999999, 2, parent)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))
    
    def sizeHint(self):
        return self.minimumSizeHint()

class TextEdit(QtGui.QTextEdit):
    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)
        
        self.setTabChangesFocus(True)

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
