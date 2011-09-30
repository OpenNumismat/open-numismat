from PyQt4 import QtGui
from PyQt4.QtCore import QT_TR_NOOP

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

class LineEditRef(QtGui.QComboBox):
    def __init__(self, reference, parent=None):
        super(LineEditRef, self).__init__(parent)

        self.reference = reference
        self.reference.changed.connect(self.setText)

        self.setEditable(True)
        self.lineEdit().setMaxLength(1024)
        
        self.setModel(reference.model)
        self.setModelColumn(reference.model.fieldIndex('value'))
        
        self.dependents = []
    
    def setText(self, text):
        if text:
            self.lineEdit().setText(text)
            index = self.findText(text)
            if index >= 0:
                self.updateDependents(index)
                self.setCurrentIndex(index)
    
    def text(self):
        return self.currentText()
    
    def addDependent(self, reference):
        self.currentIndexChanged.connect(self.updateDependents)
        self.dependents.append(reference)
    
    def updateDependents(self, index):
        for dependent in self.dependents:
            idIndex = self.model().fieldIndex('id')
            parentIndex = self.model().index(index, idIndex)
            dependent.model.setFilter('parentid=%d' % self.model().data(parentIndex))
            dependent.parentIndex = parentIndex
    
class StateEdit(QtGui.QComboBox):
    items = [('demo', QT_TR_NOOP("Demo")), ('pass', QT_TR_NOOP("Pass")),
             ('in', QT_TR_NOOP("in")), ('out', QT_TR_NOOP("out")),
             ('exchange', QT_TR_NOOP("exchange"))]
    
    def __init__(self, parent=None):
        super(StateEdit, self).__init__(parent)
        
        for item in StateEdit.items:
            self.addItem(item[1])
    
    def data(self):
        return StateEdit.items[self.currentIndex()][0]
    
    def setCurrentValue(self, value):
        index = -1
        for item in StateEdit.items:
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
        validator = DoubleValidator(0, 9999999999, 3, parent)
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
        validator = DoubleValidator(0, 9999999999, 2, parent)
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
