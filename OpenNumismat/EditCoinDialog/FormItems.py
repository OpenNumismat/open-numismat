# -*- coding: utf-8 -*-

import math
import os
import re

from PySide6.QtCore import QMargins, QDate, QLocale, QPointF, QSize, QUrl
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import (
    Qt,
    QDesktopServices,
    QDoubleValidator,
    QIcon,
    QIntValidator,
    QPainter,
    QPalette,
    QPolygonF,
    QValidator,
)
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QTextBrowser,
    QTextEdit,
    QWidget,
)

from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Gui import statusIcon
from OpenNumismat.Tools.Converters import numberWithFraction, htmlToPlainText, numberToFraction


# Reimplementing QDoubleValidator for replace comma with dot
class DoubleValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(bottom, top, decimals, parent)
        self.setNotation(QDoubleValidator.StandardNotation)

    def validate(self, input_, pos):
        input_ = input_.lstrip()
        if len(input_) == 0:
            return QValidator.Intermediate, input_, pos

        lastWasDigit = False
        decPointFound = False
        decDigitCnt = 0
        value = '0'
        ts = [QLocale.system().groupSeparator(), ]
        if ts[0] == chr(0xA0):
            ts.append(' ')
        dp = [QLocale.system().decimalPoint(), ]
        if dp[0] == ',' and '.' not in ts:
            dp.append('.')

        for c in input_:
            if c.isdigit():
                if decPointFound and self.decimals() > 0:
                    if decDigitCnt < self.decimals():
                        decDigitCnt += 1
                    else:
                        return QValidator.Invalid, input_, pos

                value = value + c
                lastWasDigit = True
            else:
                if c in dp and self.decimals() != 0:
                    if decPointFound:
                        return QValidator.Invalid, input_, pos
                    else:
                        value += '.'
                        decPointFound = True
                elif c in ts:
                    if not lastWasDigit or decPointFound:
                        return QValidator.Invalid, input_, pos
                elif c == '-' and value == '0':
                    if self.bottom() > 0:
                        return QValidator.Invalid, input_, pos
                    value = '-0'
                else:
                    return QValidator.Invalid, input_, pos

                lastWasDigit = False

        try:
            val = float(value)
        except ValueError:
            return QValidator.Invalid, input_, pos

        if self.bottom() > val or val > self.top():
            return QValidator.Invalid, input_, pos

        return QValidator.Acceptable, input_, pos


class DenominationValidator(DoubleValidator):
    def __init__(self, parent=None):
        super().__init__(0, 9999999999999., 2, parent)
        self.setNotation(QDoubleValidator.StandardNotation)

    def validate(self, input_, pos):
        result, input_, pos = super().validate(input_, pos)
        
        if result == QValidator.Invalid:
            values = ('1/24', '1/16', '1/12', '1/10', '1/8', '1/6', '1/5',
                      '1/4', '1/3', '1/2', '2/3', '3/4')
            for val in values:
                if input_ == val:
                    return QValidator.Acceptable, input_, pos
                if val.startswith(input_):
                    return QValidator.Intermediate, input_, pos

        return result, input_, pos


# Reimplementing QDoubleValidator for replace thousands separators
class BigIntValidator(QDoubleValidator):
    def __init__(self, bottom, top, parent=None):
        super().__init__(bottom, top, 0, parent)

    def validate(self, input_, pos):
        input_ = input_.lstrip()
        if len(input_) == 0:
            return QValidator.Intermediate, input_, pos

        lastWasDigit = False
        value = '0'
        ts = [QLocale.system().groupSeparator(), ]
        if ts[0] == chr(0xA0):
            ts.append(' ')
        tss = (ts[0], ' ', chr(0xA0), '.', ',')

        for c in input_:
            if c.isdigit():
                value = value + c
                lastWasDigit = True
            else:
                if c in tss:
                    if not lastWasDigit:
                        return QValidator.Invalid, input_, pos
                else:
                    return QValidator.Invalid, input_, pos

                lastWasDigit = False

        try:
            val = int(value)
        except ValueError:
            return QValidator.Invalid, input_, pos

        if not lastWasDigit and len(input_) > 0 and input_[-1] not in ts:
            return QValidator.Invalid, input_, pos

        if self.bottom() > val or val > self.top():
            return QValidator.Invalid, input_, pos

        return QValidator.Acceptable, input_, pos


class NumberValidator(QIntValidator):
    def validate(self, input_, pos):
        input_ = input_.strip()
        if len(input_) == 0:
            return QValidator.Intermediate, input_, pos

        try:
            val = int(input_)
        except ValueError:
            return QValidator.Invalid, input_, pos

        if self.bottom() > val or val > self.top():
            return QValidator.Invalid, input_, pos

        return QValidator.Acceptable, input_, pos


class LineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaxLength(1024)
        self.setMinimumWidth(100)


class UrlLineEditInternal(LineEdit):

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            url = mime.urls()[0]
            self.parent().setPath(url.toLocalFile())


class UrlLineEdit(QWidget):

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.basePath = os.path.dirname(settings.db.databaseName())
        self.relativeUrl = settings['relative_url']
        self.lineEdit = UrlLineEditInternal(self)

        buttonLoad = QPushButton(QIcon(':/world.png'), '', self)
        buttonLoad.setFixedWidth(25)
        buttonLoad.setToolTip(self.tr("Open specified URL"))
        buttonLoad.clicked.connect(self.clickedButtonLoad)

        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_DialogOpenButton)

        self.buttonOpen = QPushButton(icon, '', parent)
        self.buttonOpen.setFixedWidth(25)
        self.buttonOpen.setToolTip(self.tr("Select file from disc"))
        self.buttonOpen.clicked.connect(self.clickedButtonOpen)

        layout = QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.buttonOpen)
        layout.addWidget(buttonLoad)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

    def clickedButtonOpen(self):
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), self.getPath(), "*.*")
        if file:
            self.setPath(file)

    def clickedButtonLoad(self):
        url = QUrl(self.getPath())

        executor = QDesktopServices()
        executor.openUrl(url)

    def getPath(self):
        file = self.text()
        if self.relativeUrl:
            if not file.startswith(('file', 'http')):
                file = os.path.join(self.basePath, file).replace('\\', '/')

        return file

    def setPath(self, file):
        if self.relativeUrl:
            try:
                file = os.path.relpath(file, self.basePath)
            except ValueError:
                pass

        self.setText(file)

    def clear(self):
        self.lineEdit.clear()

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text().replace('\\', '/')

    def home(self, mark):
        self.lineEdit.home(mark)

    def setReadOnly(self, b):
        self.lineEdit.setReadOnly(b)

        if b:
            self.buttonOpen.hide()
        else:
            self.buttonOpen.show()


class AddressLineEdit(QWidget):
    findClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineEdit = LineEdit(self)
        self.lineEdit.returnPressed.connect(self.clickedButtonAddress)

        self.buttonAddress = QPushButton(QIcon(':/find.png'), '', self)
        self.buttonAddress.setFixedWidth(25)
        self.buttonAddress.setToolTip(self.tr("Find address"))
        self.buttonAddress.clicked.connect(self.clickedButtonAddress)

        layout = QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.buttonAddress)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

    def clickedButtonAddress(self):
        text = self.text().strip()
        if text:
            self.findClicked.emit(text)

    def clear(self):
        self.lineEdit.clear()

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text()

    def home(self, mark):
        self.lineEdit.home(mark)

    def setReadOnly(self, b):
        self.lineEdit.setReadOnly(b)

        if b:
            self.buttonAddress.hide()
        else:
            self.buttonAddress.show()


class GraderLineEdit(QWidget):
    clickedButton = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineEdit = LineEdit(self)

        buttonLoad = QPushButton(QIcon(':/world.png'), '', self)
        buttonLoad.setFixedWidth(25)
        buttonLoad.setToolTip(self.tr("View on grader site"))
        buttonLoad.clicked.connect(self.clickedButton)

        layout = QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(buttonLoad)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

    def clear(self):
        self.lineEdit.clear()

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text()

    def home(self, mark):
        self.lineEdit.home(mark)

    def setReadOnly(self, b):
        self.lineEdit.setReadOnly(b)

    def addAction(self, icon, position):
        return self.lineEdit.addAction(icon, position)
    
    def actions(self):
        return self.lineEdit.actions()
    
    def removeAction(self, act):
        return self.lineEdit.removeAction(act)


class BarcodeLineEdit(QWidget):
    clickedButton = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineEdit = LineEdit(self)

        self.buttonScan = QPushButton(QIcon(':/barcode.png'), '', self)
        self.buttonScan.setFixedWidth(25)
        self.buttonScan.setToolTip(self.tr("Scan barcode"))
        self.buttonScan.clicked.connect(self.clickedButton)

        layout = QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.buttonScan)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

    def clear(self):
        self.lineEdit.clear()

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text()

    def home(self, mark):
        self.lineEdit.home(mark)

    def setReadOnly(self, b):
        self.lineEdit.setReadOnly(b)

        if b:
            self.buttonScan.hide()
        else:
            self.buttonScan.show()

    def addAction(self, icon, position):
        return self.lineEdit.addAction(icon, position)

    def actions(self):
        return self.lineEdit.actions()

    def removeAction(self, act):
        return self.lineEdit.removeAction(act)


class LineEditRef(QWidget):
    def __init__(self, reference, parent=None):
        super().__init__(parent)

        self.comboBox = QComboBox(self)
        self.comboBox.setEditable(True)
        self.comboBox.lineEdit().setMaxLength(1024)
        self.comboBox.setMinimumWidth(120)
        self.comboBox.setInsertPolicy(QComboBox.NoInsert)

        self.model = reference.model
        self.proxyModel = self.model.proxyModel()
        self.comboBox.setModel(self.proxyModel)
        self.comboBox.setModelColumn(self.model.fieldIndex('value'))

        self.comboBox.setCurrentIndex(-1)

        self.reference = reference
        self.reference.beforeReload.connect(self.beforeReload)
        self.reference.afterReload.connect(self.afterReload)

        button = QPushButton(self.reference.letter, self)
        button.setFixedWidth(25)
        button.clicked.connect(self.clickedButton)

        layout = QHBoxLayout()
        layout.addWidget(self.comboBox)
        layout.addWidget(button)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

        self.dependents = []

    def beforeReload(self):
        self.old_text = self.text()

    def afterReload(self):
        self.setText(self.old_text)

    def clickedButton(self):
        dialog = self.reference._getDialog(self)
        result = dialog.exec()
        if result == QDialog.Accepted:
            self.reference.reload()

            index = dialog.selectedIndex()
            if index:
                self.setText(index.data())
        dialog.deleteLater()

    def clear(self):
        self.comboBox.setCurrentIndex(-1)

    def setText(self, text):
        index = self.comboBox.findText(text)
        if index >= 0:
            self.comboBox.setCurrentIndex(index)
        else:
            self.comboBox.setCurrentIndex(-1)
            self.comboBox.lineEdit().setText(text)
            self.comboBox.lineEdit().setCursorPosition(0)

    def text(self):
        return self.comboBox.currentText()

    def home(self, mark):
        self.comboBox.lineEdit().home(mark)

    def addDependent(self, reference):
        # Clear reference
        reference.reference.model.setFilter(None)
        reference.reference.parentIndex = None

        if not self.dependents:
            # TODO: For support nonunique values uncomment next line
            # self.comboBox.currentIndexChanged.connect(self.updateDependents)
            self.comboBox.editTextChanged.connect(self.updateDependents)
        self.dependents.append(reference)

    def hasDependents(self):
        return bool(self.dependents)

    def updateDependents(self, index):
        if isinstance(index, str):
            index = self.comboBox.findText(index)

        if index >= 0:
            idIndex = self.model.fieldIndex('id')
            parentIndex = self.proxyModel.index(index, idIndex)
            parent_id = parentIndex.data()
            if parent_id:
                for dependent in self.dependents:
                    text = dependent.text()
                    reference = dependent.reference
                    reference.model.setFilter(
                        '%s.parentid=%d' % (reference.model.tableName(), parent_id))
                    reference.parentIndex = parentIndex
                    dependent.setText(text)
        else:
            for dependent in self.dependents:
                text = dependent.text()
                reference = dependent.reference
                if self.comboBox.currentText():
                    reference.model.setFilter('0')  # nothing select
                else:
                    reference.model.setFilter(None)  # select all
                reference.parentIndex = None
                dependent.setText(text)


class StatusEdit(QComboBox):

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(120)

        for status, statusTitle in Statuses.items():
            if settings[status + '_status_used']:
                self.addItem(statusIcon(status), statusTitle, status)

    def data(self):
        return self.currentData()

    def clear(self):
        self.setCurrentIndex(-1)

    def setCurrentValue(self, value):
        index = self.findData(value)
        if index >= 0:
            old_index = self.currentIndex()
            self.setCurrentIndex(index)
            if old_index == index:
                self.currentIndexChanged.emit(index)
        else:
            # Add real coin status when it disabled in settings
            self.addItem(statusIcon(value), Statuses[value], value)
            self.setCurrentValue(value)


class StatusBrowser(QLineEdit):
    currentIndexChanged = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(100)
        self.data = ''

    def setCurrentValue(self, value):
        self.setText(Statuses[value])
        self.home(False)

        for act in self.actions():
            self.removeAction(act)
        icon = statusIcon(value)
        self.action = self.addAction(icon, QLineEdit.LeadingPosition)

        self.data = value

        self.currentIndexChanged.emit(-1)

    def currentData(self):
        return self.data

    def clear(self):
        for act in self.actions():
            self.removeAction(act)
        super().clear()


class ShortLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaxLength(15)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self):
        return self.minimumSizeHint()


class UserNumericEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaxLength(25)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Fixed, QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class _NumberEdit(QLineEdit):

    def __init__(self, bottom, top, parent=None):
        super().__init__(parent)
        validator = NumberValidator(bottom, top, parent)
        self.setValidator(validator)
        self.setMaxLength(4)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Fixed, QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class NumberEdit(_NumberEdit):

    def __init__(self, parent=None):
        super().__init__(0, 9999, parent)


class AxisDegreeEdit(_NumberEdit):

    def __init__(self, parent=None):
        super().__init__(0, 359, parent)


class AxisHourEdit(QSpinBox):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRange(0, 12)
        self.setSpecialValueText(" ")  # TODO: Not working without value
        self.setSuffix(self.tr("h"))

        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed))

    def setReadOnly(self, r):
        if r:
            self.setButtonSymbols(QAbstractSpinBox.NoButtons)
        else:
            self.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

        return super().setReadOnly(r)

    def sizeHint(self):
        return self.minimumSizeHint()

    def showEvent(self, event):
        if not self.cleanText():
            self.setValue(0)
        return super().showEvent(event)

    def focusOutEvent(self, event):
        if not self.cleanText():
            self.setValue(0)
        return super().focusOutEvent(event)

    def setText(self, text):
        try:
            value = int(text)
        except ValueError:
            self.setValue(0)
            return

        value += 360 / 12 / 2
        value /= 360 / 12
        value = int(value)
        if value == 0:
            value = 12

        self.setValue(value)

    def value(self):
        value = super().value()
        if value == 0:
            return None
        elif value == 12:
            return 0
        else:
            return value * 30


class YearEdit(QWidget):
    def __init__(self, is_free, parent=None):
        super().__init__(parent)

        if is_free:
            self.numberEdit = UserNumericEdit(parent)
        else:
            self.numberEdit = NumberEdit(parent)

        self.bcBtn = QCheckBox(self.tr("BC"))
        self.bcBtn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.bcLbl = QLabel()
        self.bcLbl.hide()

        layout = QHBoxLayout()
        layout.addWidget(self.numberEdit)
        layout.addWidget(self.bcBtn)
        layout.addWidget(self.bcLbl)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

    def clear(self):
        self.numberEdit.clear()
        self.bcBtn.setCheckState(Qt.Unchecked)

    def setText(self, text):
        if text and text[0] == '-':
            text = text[1:]
            self.bcBtn.setChecked(True)
            self.bcLbl.setText(self.tr("BC"))
        else:
            self.bcLbl.clear()
        self.numberEdit.setText(text)

    def text(self):
        text = self.numberEdit.text()
        if text and self.bcBtn.isChecked():
            text = '-' + text

        return text

    def home(self, mark):
        self.numberEdit.home(mark)

    def setReadOnly(self, b):
        self.numberEdit.setReadOnly(b)

        if b:
            self.bcBtn.hide()
            self.bcLbl.show()
        else:
            self.bcBtn.show()
            self.bcLbl.hide()


class NativeYearEdit(QWidget):
    clickedButton = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lineEdit = UserNumericEdit(self)

        self.calcBtn = QPushButton(QIcon(':/date.png'), '', self)
        self.calcBtn.setFixedWidth(25)
        self.calcBtn.setToolTip(self.tr("Year calculator"))
        self.calcBtn.clicked.connect(self.clickedButton)

        layout = QHBoxLayout()
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.calcBtn)
        layout.setContentsMargins(QMargins())

        self.setLayout(layout)

    def clear(self):
        self.lineEdit.clear()

    def setText(self, text):
        self.lineEdit.setText(text)

    def text(self):
        return self.lineEdit.text()

    def home(self, mark):
        self.lineEdit.home(mark)

    def addAction(self, icon, position):
        return self.lineEdit.addAction(icon, position)
    
    def actions(self):
        return self.lineEdit.actions()
    
    def removeAction(self, act):
        return self.lineEdit.removeAction(act)

    def setReadOnly(self, b):
        self.lineEdit.setReadOnly(b)

        if b:
            self.calcBtn.hide()
        else:
            self.calcBtn.show()


class _DoubleEdit(QLineEdit):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(parent)
        self._decimals = decimals

        validator = DoubleValidator(bottom, top, decimals, parent)
        self.setValidator(validator)

    def focusInEvent(self, event):
        self._updateText()
        return super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._updateText()
        return super().focusOutEvent(event)

    def setText(self, text):
        ts = QLocale.system().groupSeparator()
        if ts == '.':
            text = text.replace('.', ',')
        super().setText(text)
        self._updateText()

    def text(self):
        text = super().text()
        # First, get rid of the grouping
        ts = QLocale.system().groupSeparator()
        if ts:
            text = text.replace(ts, '')
            if ts == chr(0xA0):
                text = text.replace(' ', '')
        # next, replace the decimal point with a dot
        if self._decimals:
            dp = QLocale.system().decimalPoint()
            if dp:
                text = text.replace(dp, '.')
        return text

    def _updateText(self):
        text = self.text()
        if text:
            src_text = text

            if not self.hasFocus() or self.isReadOnly():
                try:
                    if self._decimals:
                        text = QLocale.system().toString(float(text), 'f',
                                                         precision=self._decimals)
                    else:
                        text = QLocale.system().toString(int(text))
                except ValueError:
                    return

                if self._decimals:
                    # Strip empty fraction
                    dp = QLocale.system().decimalPoint()
                    text = text.rstrip('0').rstrip(dp)
            else:
                ts = QLocale.system().groupSeparator()
                if ts == '.':
                    text = text.replace('.', ',')

            if src_text != text:
                super().setText(text)


class BigIntEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super().__init__(0, 999999999999999., 0, parent)

        validator = BigIntValidator(0, 999999999999999., parent)
        self.setValidator(validator)

        self.setMaxLength(15 + 4)  # additional 4 symbol for thousands separator
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Fixed, QSizePolicy.SpinBox))

    def text(self):
        text = super().text()
        ts = (QLocale.system().groupSeparator(), ' ', chr(0xA0), '.', ',')
        for c in ts:
            text = text.replace(c, '')
        return text


class ValueEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super().__init__(0, 9999999999., 3, parent)
        self.setMaxLength(17)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Fixed, QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class CoordEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super().__init__(-180, 180, 6, parent)
        self.setMaxLength(9)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Fixed, QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class MoneyEdit(_DoubleEdit):
    def __init__(self, parent=None):
        super().__init__(0, 9999999999., 2, parent)
        self.setMaxLength(16)
        self.setMinimumWidth(100)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,
                                       QSizePolicy.Fixed, QSizePolicy.SpinBox))

    def sizeHint(self):
        return self.minimumSizeHint()


class UserDenominationEdit(UserNumericEdit):
    def focusInEvent(self, event):
        self._updateText()
        return super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._updateText()
        return super().focusOutEvent(event)

    def setText(self, text):
        super().setText(text)
        self._updateText()

    def text(self):
        text = super().text()
        return numberToFraction(text)

    def _updateText(self):
        text = self.text()
        if text:
            if not self.hasFocus() or self.isReadOnly():
                text, _ = numberWithFraction(text)

            if QLineEdit.text(self) != text:
                QLineEdit.setText(self, text)


class DenominationEdit(MoneyEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaxLength(20)

        validator = DenominationValidator()
        self.setValidator(validator)

    def text(self):
        text = super().text()
        return numberToFraction(text)

    def _updateText(self):
        text = self.text()
        if text:
            if not self.hasFocus() or self.isReadOnly():
                text, converted = numberWithFraction(text)
                if not converted:
                    try:
                        text = QLocale.system().toString(float(text), 'f', precision=2)
                        # Strip empty fraction
                        dp = QLocale.system().decimalPoint()
                        text = text.rstrip('0').rstrip(dp)
                    except ValueError:
                        return
            else:
                ts = QLocale.system().groupSeparator()
                if ts == '.':
                    text = text.replace('.', ',')

            if QLineEdit.text(self) != text:
                QLineEdit.setText(self, text)


RICH_PREFIX = ('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '
               '"http://www.w3.org/TR/REC-html40/strict.dtd">',
               '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" '
               '"https://www.w3.org/TR/REC-html40/strict.dtd">')


class TextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)

        self.setOpenLinks(False)
        self.anchorClicked.connect(self.anchorClickedEvent)

    def anchorClickedEvent(self, link):
        executor = QDesktopServices()
        executor.openUrl(link)

    def sizeHint(self):
        return self.minimumSizeHint()

    def setText(self, text):
        text = htmlToPlainText(text)

        urls = re.findall(r'(https?://[^\s]+|file:///[^\s]+)', text)
        if urls:
            beg = 0
            new_text = ''
            for url in urls:
                i = text.index(url, beg)
                new_text += text[beg:i] + '<a href="%s">%s</a>' % (url, url)
                beg = i + len(url)
            new_text += text[beg:]

            text = new_text.replace('\n', '<br>')

        super().setText(text)

    def text(self):
        return self.toPlainText()


class RichTextBrowser(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptRichText(True)
        self.setTabChangesFocus(True)

        self.setOpenLinks(False)
        self.anchorClicked.connect(self.anchorClickedEvent)

    def anchorClickedEvent(self, link):
        executor = QDesktopServices()
        executor.openUrl(link)

    def sizeHint(self):
        return self.minimumSizeHint()

    def setText(self, text):
        if not text.startswith(RICH_PREFIX):
            urls = re.findall(r'(https?://[^\s]+|file:///[^\s]+)', text)
            if urls:
                beg = 0
                new_text = ''
                for url in urls:
                    i = text.index(url, beg)
                    new_text += text[beg:i] + '<a href="%s">%s</a>' % (url, url)
                    beg = i + len(url)
                new_text += text[beg:]

                text = new_text.replace('\n', '<br>')

        super().setText(text)


class TextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptRichText(False)
        self.setTabChangesFocus(True)

    def sizeHint(self):
        return self.minimumSizeHint()

    def text(self):
        return self.toPlainText()

    def setText(self, text):
        text = htmlToPlainText(text)
        self.setPlainText(text)


class RichTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAcceptRichText(True)
        self.setTabChangesFocus(True)

    def sizeHint(self):
        return self.minimumSizeHint()

    def text(self):
        if self.toPlainText():
            return self.toHtml()
        else:
            return ''

    def setText(self, text):
        if not text.startswith(RICH_PREFIX):
            urls = re.findall(r'(https?://[^\s]+|file:///[^\s]+)', text)
            if urls:
                beg = 0
                new_text = ''
                for url in urls:
                    i = text.index(url, beg)
                    new_text += text[beg:i] + '<a href="%s">%s</a>' % (url, url)
                    beg = i + len(url)
                new_text += text[beg:]

                text = new_text.replace('\n', '<br>')

        super().setText(text)


class CalendarWidget(QCalendarWidget):
    DEFAULT_DATE = QDate(2000, 1, 1)
    
    def __init__(self):
        super().__init__()
        
        self._height_fixed = False

        self._today_button = QPushButton(self.tr("Today"))
        self._today_button.clicked.connect(self.updateToday)
        self._clean_button = QPushButton(self.tr("Clean"))
        self._clean_button.clicked.connect(self.cleanDate)
        buttons = QHBoxLayout()
        buttons.addWidget(self._today_button)
        buttons.addWidget(self._clean_button)
        self.layout().addLayout(buttons)
    
    def updateToday(self):
        today = QDate.currentDate()
        self.clicked.emit(today)

    def cleanDate(self):
        self.clicked.emit(self.DEFAULT_DATE)

    def showEvent(self, e):
        if not self._height_fixed:
            self.setFixedHeight(self.height() + self._clean_button.height())
            self._height_fixed = True

        if self.selectedDate() == self.DEFAULT_DATE:
            self.showToday()


class DateEdit(QDateEdit):
    DEFAULT_DATE = QDate(2000, 1, 1)

    def __init__(self, parent=None):
        super().__init__(parent)
        calendar = CalendarWidget()
        calendar.setGridVisible(True)
        self.setCalendarPopup(True)
        self.setCalendarWidget(calendar)
        self.setMinimumWidth(85)

    def clear(self):
        self.setDate(self.DEFAULT_DATE)
        super().clear()

    def showEvent(self, e):
        super().showEvent(e)
        self.__clearDefaultDate()

    def focusInEvent(self, event):
        if not self.isReadOnly():
            self.setDate(self.date())
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.__clearDefaultDate()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            lineEdit = self.findChild(QLineEdit)
            if lineEdit.selectedText() == lineEdit.text():
                self.setDate(self.DEFAULT_DATE)

        super().keyPressEvent(event)

    def __clearDefaultDate(self):
        if self.date() == self.DEFAULT_DATE:
            lineEdit = self.findChild(QLineEdit)
            lineEdit.setCursorPosition(0)
            lineEdit.setText("")


class RatingEdit(QLabel):
    PaintingScaleFactor = 18

    def __init__(self, maxStarCount, parent=None):
        super().__init__(parent)
        
        self.maxStarCount = maxStarCount
        self.starCount = 0
        self.currentStarCount = self.starCount
        self.setReadOnly(False)

        self.starPolygon = QPolygonF()
        self.starPolygon.append(QPointF(1.0, 0.5))
        for i in range(5):
            point = QPointF(0.5 + 0.5 * math.cos(0.8 * i * math.pi),
                            0.5 + 0.5 * math.sin(0.8 * i * math.pi))
            self.starPolygon.append(point)

        self.diamondPolygon = QPolygonF((
            QPointF(0.4, 0.5), QPointF(0.5, 0.4), QPointF(0.6, 0.5),
            QPointF(0.5, 0.6), QPointF(0.4, 0.5)
        ))

    def enterEvent(self, event):
        if not self.readOnly:
            self.setAutoFillBackground(True)

        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.readOnly:
            self.setAutoFillBackground(False)
            self.currentStarCount = self.starCount

        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        if not self.readOnly:
            star = self.starAtPosition(event.position().toPoint().x())

            if star != self.currentStarCount and star != -1:
                self.currentStarCount = star
                self.update()

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.underMouse():
            self.starCount = self.currentStarCount
        super().mouseReleaseEvent(event)

    def starAtPosition(self, x):
        star = math.ceil((x - 5) / (self.sizeHint().width() / self.maxStarCount))
        if star < 0 or star > self.maxStarCount:
            return -1

        return star

    def setReadOnly(self, b):
        self.readOnly = b

        self.setMouseTracking(not self.readOnly)

    def clear(self):
        return

    def text(self):
        return '*' * math.ceil(self.starCount * (10 / self.maxStarCount))

    def setText(self, text):
        self.starCount = math.ceil(text.count('*') / (10 / self.maxStarCount))
        self.currentStarCount = self.starCount

        if self.readOnly:
            super().setText('⭐' * self.starCount)

    def home(self, _mark):
        return

    def paintEvent(self, event):
        if self.readOnly:
            return super().paintEvent(event)

        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        palette = QPalette()
        if self.readOnly:
            brush = palette.windowText()
        else:
            brush = palette.highlight()
        painter.setBrush(brush)

        rect = self.rect()
        yOffset = (rect.height() - self.PaintingScaleFactor) / 2
        painter.translate(rect.x(), rect.y() + yOffset)
        painter.scale(self.PaintingScaleFactor, self.PaintingScaleFactor)

        for i in range(self.maxStarCount):
            if i < self.currentStarCount:
                painter.drawPolygon(self.starPolygon, Qt.WindingFill)
            elif not self.readOnly:
                painter.drawPolygon(self.diamondPolygon, Qt.WindingFill)
            painter.translate(1.0, 0.0)

    def sizeHint(self):
        return self.PaintingScaleFactor * QSize(self.maxStarCount, 1)
