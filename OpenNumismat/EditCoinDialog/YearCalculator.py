# -*- coding: utf-8 -*-

import math

from PyQt5.QtCore import Qt, QMargins, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QFont, QValidator, QIcon
from PyQt5.QtWidgets import *


class YearCalculatorDialog(QDialog):
    def __init__(self, year, native_year, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.buttonBox = QDialogButtonBox(Qt.Horizontal)
        self.buttonBox.addButton(QDialogButtonBox.Save)
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        combo = QComboBox()
        combo.addItems((HebrewCalendar.TITLE, IslamicCalendar.TITLE))
        combo.activated.connect(self.calendarChanged)

        hlayout = QHBoxLayout()
        year_layout = self.gregoryanLayout(year)
        hlayout.addLayout(year_layout)
        hlayout.setAlignment(year_layout, Qt.AlignTop)
        hlayout.addSpacing(20)

        self.hebrew_layout = self.nationalCalc(HebrewCalendar(), native_year)
        hlayout.addWidget(self.hebrew_layout)
        hlayout.setAlignment(self.hebrew_layout, Qt.AlignTop)
        
        self.islamic_layout = self.nationalCalc(IslamicCalendar(), native_year)
        hlayout.addWidget(self.islamic_layout)
        hlayout.setAlignment(self.islamic_layout, Qt.AlignTop)

        layout = QVBoxLayout()
        layout.addWidget(combo)
        layout.addLayout(hlayout)
        layout.addWidget(self.buttonBox)
        layout.setSizeConstraint(QLayout.SetFixedSize)

        self.setLayout(layout)
        
        self.calendarChanged(0)
    
    def calendarChanged(self, index):
        if index == 0:
            self.nationalYearEditor = self.hebrew_layout.EDITOR
            
            self.hebrew_layout.show()
            self.islamic_layout.hide()
        else:
            self.nationalYearEditor = self.islamic_layout.EDITOR
            
            self.hebrew_layout.hide()
            self.islamic_layout.show()

    def gregoryanLayout(self, year):
        layout = QGridLayout()
        layout.setContentsMargins(QMargins())

        edit = QLineEdit(year)
        validator = GregorianValidator(self)
        edit.setValidator(validator)
        layout.addWidget(edit, 1, 0, 1, 5)
        
        btn = ClearButton(edit)
        layout.addWidget(btn, 2, 0)
        btn = BackButton(edit)
        layout.addWidget(btn, 2, 1)
        btn = ConvertButton()
        btn.clicked.connect(self.convertGregorian)
        layout.addWidget(btn, 2, 2, 1, 3)

        self.yearEditor = edit

        digits = (("1", "2", "3", "4", "5"), ("6", "7", "8", "9", "0"))
        
        for row, line in enumerate(digits):
            for col, dig in enumerate(line):
                btn = CalcButton(dig, edit)
                layout.addWidget(btn, row+3, col)

        return layout
    
    def nationalCalc(self, calendar, year):
        layout = QGridLayout()
        layout.setContentsMargins(QMargins())

        edit = QLineEdit(year)
        edit.setValidator(calendar)
        layout.addWidget(edit, 1, 0, 1, 5)

        btn = ClearButton(edit)
        layout.addWidget(btn, 2, 0)
        btn = BackButton(edit)
        layout.addWidget(btn, 2, 1)
        btn = ConvertButton()
        btn.clicked.connect(self.convertToGregorian)
        layout.addWidget(btn, 2, 2, 1, 3)
        
        digits = calendar.CALC
        
        for row, line in enumerate(digits):
            for col, dig in enumerate(line):
                if dig:
                    btn = CalcButton(dig, edit)
                    layout.addWidget(btn, row+3, col)

        widget = QWidget()
        widget.setLayout(layout)
        widget.EDITOR = edit

        return widget

    def convertGregorian(self):
        text = self.yearEditor.text()
        res, _, _ = self.yearEditor.validator().validate(text, 0)
        if res == QValidator.Acceptable:
            text = self.nationalYearEditor.validator().fromGregorian(text)
            self.nationalYearEditor.setText(text)
    
    def convertToGregorian(self):
        text = self.nationalYearEditor.text()
        res, _, _ = self.nationalYearEditor.validator().validate(text, 0)
        if res == QValidator.Acceptable:
            text = self.nationalYearEditor.validator().toGregorian(text)
            self.yearEditor.setText(text)
    
    def year(self):
        text = self.yearEditor.text()
        res, _, _ = self.yearEditor.validator().validate(text, 0)
        if res == QValidator.Acceptable:
            return text
        else:
            return ''
    
    def nativeYear(self):
        text = self.nationalYearEditor.text()
        res, _, _ = self.nationalYearEditor.validator().validate(text, 0)
        if res == QValidator.Acceptable:
            return text
        else:
            return ''


class HebrewCalendar(QValidator):
    TITLE = QT_TRANSLATE_NOOP("HebrewCalendar", "Hebrew")
    CALC = (("א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"),
            ("י", "כ", "ל", "‭מ", "נ", "ס", "ע", "פ", "צ"),
#           ("י", "כ/ך", "ל", "‭מ/ם", "נ/ן", "ס", "ע", "פ/ף", "צ/ץ"),
            ("ק", "ר", "ש", "ת", None, None, None, None, "״"))

    def validate(self, input_, pos):
        for c in input_:
            if c not in "‭אבגדהוזחטיכךלמםנןסעפףצץקרשת‏״":
                return QValidator.Invalid, input_, pos
        if input_.count('״') > 1:
            return QValidator.Invalid, input_, pos

        if len(input_) < 3:
            return QValidator.Intermediate, input_, pos

        if '״' not in input_ or input_[-1] == '״':
            return QValidator.Intermediate, input_, pos

        if input_[-2] != '״':
            return QValidator.Invalid, input_, pos

        if len(input_) > 6:
            return QValidator.Invalid, input_, pos
        
        return QValidator.Acceptable, input_, pos
    
    def toGregorian(self, year):
        _DIGITS = {"א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
                  "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
                  "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90,
                  "ק": 100, "ר": 200, "ש": 300, "ת": 400, "״": 0}
        
        result = 5000
        
        for i in range(len(year)):
            if i == 0 and year[i] == "ה":
                continue
            result += _DIGITS[year[i]]
        
        return str(result - 3760)

    def fromGregorian(self, year):
        _GEMATRIOS = {
            1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט',
            10: 'י', 20: 'כ', 30: 'ל', 40: 'מ', 50: 'נ', 60: 'ס', 70: 'ע', 80: 'פ',
            90: 'צ', 100: 'ק', 200: 'ר', 300: 'ש', 400: 'ת'
        }
        
        num = int(year) + 3760
        
        ones = num % 10
        tens = num % 100 - ones
        hundreds = num % 1000 - tens - ones
        four_hundreds = ''.join(['ת' for _ in range(hundreds // 400)])
        ones = _GEMATRIOS.get(ones, '')
        tens = _GEMATRIOS.get(tens, '')
        hundreds = _GEMATRIOS.get(hundreds % 400, '')
        if 5708 > num or num > 5740:
            thousands = num // 1000
            thousands = _GEMATRIOS.get(thousands, '')
        else:
            thousands = ''
        letters = thousands + four_hundreds + hundreds + tens + ones
        
        letters = letters.replace('יה', 'טו').replace('יו', 'טז')
        
        if len(letters) > 1:
            letters = letters[:-1] + '״' + letters[-1]
        
        return letters


class IslamicCalendar(QValidator):
    TITLE = QT_TRANSLATE_NOOP("IslamicCalendar", "Islamic")
    CALC = (("١", "٢", "٣", "٤", "٥", "٦", "٧", "۸", "٩", "٠"),
            (None, None, None, "۴", "۵", "۶", None, None, None, None))

    def validate(self, input_, pos):
        for c in input_:
            if c not in "١٢٣٤۴٥۵٦۶٧۸٩٠":
                return QValidator.Invalid, input_, pos

        if len(input_) < 3:
            return QValidator.Intermediate, input_, pos

        if len(input_) > 4:
            return QValidator.Invalid, input_, pos
        
        return QValidator.Acceptable, input_, pos
    
    def toGregorian(self, year):
        _DIGITS = {"١": 1, "٢": 2, "٣": 3, "٤": 4, "۴": 4, "٥": 5, "۵": 5,
                   "٦": 6, "۶": 6, "٧": 7, "۸": 8, "٩": 9, "٠": 0}
        
        result = 0
        
        for c in year:
            result *= 10
            result += _DIGITS[c]
        
        return str(math.ceil(0.969697 * result + 622))
    
    def fromGregorian(self, year):
        _DIGITS = {1: "١", 2: "٢", 3: "٣", 4: "٤", 5: "٥",
                   6: "٦", 7: "٧", 8: "۸", 9: "٩", 0: "٠"}
        
        num = int(1.03125 * (int(year) - 622))
        
        ones = num % 10
        tens = (num // 10)  % 10
        hundreds = (num // 100)  % 10
        thousands = (num // 1000)  % 10
        
        letters = _DIGITS[hundreds] + _DIGITS[tens] + _DIGITS[ones]
        if thousands:
            letters = _DIGITS[thousands] + letters
        
        return letters


class GregorianValidator(QValidator):
    def validate(self, input_, pos):
        if len(input_) == 0:
            return QValidator.Intermediate, input_, pos

        try:
            val = int(input_)
        except ValueError:
            return QValidator.Invalid, input_, pos

        if 0 > val or val > 9999:
            return QValidator.Invalid, input_, pos

        return QValidator.Acceptable, input_, pos


class CalcButton(QPushButton):
    def __init__(self, text, editor, parent=None):
        super().__init__(text, parent)
        
        self.editor = editor
        
        font = QFont("serif", 20)
        self.setFont(font)

        self.setFixedWidth(40)
        self.setFixedHeight(40)
        
        self.clicked.connect(self.onClicked)

    def onClicked(self):
        new_text = self.editor.text() + self.text()
        res, new_text, _ = self.editor.validator().validate(new_text, 0)
        if res != QValidator.Invalid:
            self.editor.setText(new_text)


class ClearButton(QPushButton):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        
        self.editor = editor
        
        self.setFixedWidth(40)
        self.setFixedHeight(40)
        self.setToolTip(self.tr("Clear"))
        self.setIcon(QIcon(':/cross.png'))
        
        self.clicked.connect(self.onClicked)

    def onClicked(self):
        self.editor.clear()


class BackButton(QPushButton):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        
        self.editor = editor
        
        self.setFixedWidth(40)
        self.setFixedHeight(40)
        self.setToolTip(self.tr("Backspace"))
        self.setIcon(QIcon(':/backspace.png'))
        
        self.clicked.connect(self.onClicked)

    def onClicked(self):
        text = self.editor.text()
        if text:
            self.editor.setText(text[:-1])


class ConvertButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        font = QFont("serif", 16)
        self.setFont(font)

        self.setFixedHeight(40)
        self.setToolTip(self.tr("Convert"))
        self.setText(self.tr("Convert"))
        self.setIcon(QIcon(':/tick.png'))
