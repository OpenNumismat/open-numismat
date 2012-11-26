import locale

from PyQt4 import QtGui
from PyQt4.QtCore import QMargins

from Collection.CollectionFields import Statuses


# Reimplementing QDoubleValidator for replace comma with dot
class DoubleValidator(QtGui.QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super(DoubleValidator, self).__init__(bottom, top, decimals, parent)

    def validate(self, input_, pos):
        input_ = input_.lstrip()
        if len(input_) == 0:
            return QtGui.QValidator.Intermediate, input_, pos

        lastWasDigit = False
        decPointFound = False
        decDigitCnt = 0
        value = '0'
        ts = locale.localeconv()['thousands_sep']
        dp = locale.localeconv()['decimal_point']

        for c in input_:
            if c.isdigit():
                if decPointFound and self.decimals() > 0:
                    if decDigitCnt < self.decimals():
                        decDigitCnt = decDigitCnt + 1
                    else:
                        return QtGui.QValidator.Invalid, input_, pos

                value = value + c
                lastWasDigit = True
            else:
                if (c == dp or c == '.') and self.decimals() != 0:
                    if decPointFound:
                        return QtGui.QValidator.Invalid, input_, pos
                    else:
                        value = value + '.'
                        decPointFound = True
                elif c == ts or (ts == chr(0xA0) and c == ' '):
                    if not lastWasDigit or decPointFound:
                        return QtGui.QValidator.Invalid, input_, pos
                else:
                    return QtGui.QValidator.Invalid, input_, pos

                lastWasDigit = False

        try:
            val = float(value)
        except ValueError:
            return QtGui.QValidator.Invalid, input_, pos

        if self.bottom() > val or val > self.top():
            return QtGui.QValidator.Invalid, input_, pos

        return QtGui.QValidator.Acceptable, input_, pos


class NumberValidator(QtGui.QIntValidator):
    def __init__(self, minimum, maximum, parent=None):
        super(NumberValidator, self).__init__(minimum, maximum, parent)

    def validate(self, input_, pos):
        input_ = input_.strip()
        if len(input_) == 0:
            return QtGui.QValidator.Intermediate, input_, pos

        try:
            val = int(input_)
        except ValueError:
            return QtGui.QValidator.Invalid, input_, pos

        if self.bottom() > val or val > self.top():
            return QtGui.QValidator.Invalid, input_, pos

        return QtGui.QValidator.Acceptable, input_, pos


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

    def home(self, mark):
        self.comboBox.lineEdit().home(mark)

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
            if model.data(parentIndex):
                for dependent in self.dependents:
                    text = dependent.text()
                    reference = dependent.reference
                    reference.model.setFilter(
                                    'parentid=%d' % model.data(parentIndex))
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
    def __init__(self, parent=None):
        super(StatusEdit, self).__init__(parent)

        for statusTitle in Statuses.values():
            self.addItem(statusTitle)

    def data(self):
        return Statuses.keys()[self.currentIndex()]

    def clear(self):
        self.setCurrentIndex(-1)

    def setCurrentValue(self, value):
        index = -1
        for status, statusTitle in Statuses.items():
            if status == value:
                index = self.findText(statusTitle)

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
        validator = NumberValidator(0, 9999, parent)
        self.setValidator(validator)
        self.setMaxLength(4)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,
                    QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class _DoubleEdit(QtGui.QLineEdit):
    def __init__(self, bottom, top, decimals, parent=None):
        super(_DoubleEdit, self).__init__(parent)
        self._decimals = decimals

        validator = DoubleValidator(bottom, top, decimals, parent)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        self.setValidator(validator)

    def focusInEvent(self, event):
        self.__updateText()
        return super(_DoubleEdit, self).focusInEvent(event)

    def focusOutEvent(self, event):
        self.__updateText()
        return super(_DoubleEdit, self).focusOutEvent(event)

    def setText(self, text):
        super(_DoubleEdit, self).setText(text)
        self.__updateText()

    def text(self):
        text = super(_DoubleEdit, self).text()
        # First, get rid of the grouping
        ts = locale.localeconv()['thousands_sep']
        if ts:
            text = text.replace(ts, '')
            if ts == chr(0xA0):
                text = text.replace(' ', '')
        # next, replace the decimal point with a dot
        if self._decimals:
            dp = locale.localeconv()['decimal_point']
            if dp:
                text = text.replace(dp, '.')
        return text

    def __updateText(self):
        text = self.text()
        if text:
            if not self.hasFocus() or self.isReadOnly():
                try:
                    if self._decimals:
                        text = locale.format("%%.%df" % self._decimals,
                                             float(text), grouping=True)
                    else:
                        text = locale.format("%d", int(text), grouping=True)
                except ValueError:
                    return

                if self._decimals:
                    # Strip empty fraction
                    dp = locale.localeconv()['decimal_point']
                    text = text.rstrip('0').rstrip(dp)

            super(_DoubleEdit, self).setText(text)


class BigIntEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super(BigIntEdit, self).__init__(0, 999999999999999, 0, parent)
        self.setMaxLength(15 + 4)  # additional 4 symbol for thousands separator
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,
                        QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))


class ValueEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super(ValueEdit, self).__init__(0, 9999999999, 3, parent)
        self.setMaxLength(17)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,
                        QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class MoneyEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super(MoneyEdit, self).__init__(0, 9999999999, 2, parent)
        self.setMaxLength(16)
        self.setMinimumWidth(100)
        self.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum,
                        QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.SpinBox))

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


class DateTimeEdit(QtGui.QDateTimeEdit):
    def __init__(self, parent=None):
        super(DateTimeEdit, self).__init__(parent)
