from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from OpenNumismat.EditCoinDialog.FormItems import *
from OpenNumismat.EditCoinDialog.ImageLabel import ImageEdit, EdgeImageEdit
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Settings import Settings


class FormItem(object):
    def __init__(self, field, title, itemType, reference=None, parent=None):
        settings = Settings()

        self._field = field
        self._title = title
        if itemType & Type.Checkable:
            self._label = QCheckBox(title, parent)
            self._label.setSizePolicy(QSizePolicy.Fixed,
                                      QSizePolicy.Preferred)
            self._label.stateChanged.connect(self.checkBoxChanged)
        else:
            self._label = QLabel(title, parent)
            self._label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            self._label.setSizePolicy(QSizePolicy.Fixed,
                                      QSizePolicy.Preferred)

        self._type = itemType & Type.Mask
        if self._type == Type.String:
            if reference:
                self._widget = LineEditRef(reference, parent)
            else:
                if self._field == 'url':
                    self._widget = UrlLineEdit(parent)
                else:
                    self._widget = LineEdit(parent)
        elif self._type == Type.ShortString:
            self._widget = ShortLineEdit(parent)
        elif self._type == Type.Number:
            if settings['free_numeric']:
                self._widget = UserNumericEdit(parent)
            else:
                self._widget = NumberEdit(parent)
        elif self._type == Type.BigInt:
            if settings['free_numeric']:
                self._widget = UserNumericEdit(parent)
            else:
                self._widget = BigIntEdit(parent)
        elif self._type == Type.Value:
            if settings['free_numeric']:
                self._widget = UserNumericEdit(parent)
            else:
                self._widget = ValueEdit(parent)
        elif self._type == Type.Money:
            if settings['free_numeric']:
                self._widget = UserNumericEdit(parent)
            else:
                self._widget = MoneyEdit(parent)
        elif self._type == Type.Denomination:
            if settings['free_numeric']:
                self._widget = UserNumericEdit(parent)
            elif settings['convert_fraction']:
                self._widget = DenominationEdit(parent)
            else:
                self._widget = MoneyEdit(parent)
        elif self._type == Type.Text:
            self._widget = TextEdit(parent)
        elif self._type == Type.Image:
            self._widget = ImageEdit(field, parent)
        elif self._type == Type.PreviewImage:
            self._widget = ImageEdit(field, parent)
        elif self._type == Type.EdgeImage:
            self._widget = EdgeImageEdit(field, parent)
        elif self._type == Type.Date:
            self._widget = DateEdit(parent)
        elif self._type == Type.Status:
            self._widget = StatusEdit(parent)
        elif self._type == Type.DateTime:
            self._widget = DateTimeEdit(parent)
        else:
            raise

        if itemType & Type.Disabled:
            if self._type == Type.Status or self._type in Type.ImageTypes:
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
        if isinstance(self._widget, QTextEdit):
            return self._widget.toPlainText()
        elif isinstance(self._widget, QDateTimeEdit):
            date = self._widget.date()
            if date == self._widget.DEFAULT_DATE:
                return ''
            else:
                return date.toString(Qt.ISODate)
        elif isinstance(self._widget, QAbstractSpinBox):
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
        elif isinstance(self._widget, QSpinBox):
            self._widget.setValue(int(value))
        elif isinstance(self._widget, QDoubleSpinBox):
            self._widget.setValue(float(value))
        elif isinstance(self._widget, QDateTimeEdit):
            value = str(value)
            if value:
                self._widget.setDate(QDate.fromString(str(value), Qt.ISODate))
            else:
                self._widget.setDate(self._widget.DEFAULT_DATE)
                lineEdit = self._widget.findChild(QLineEdit)
                lineEdit.setText("")
        elif isinstance(self._widget, StatusEdit):
            self._widget.setCurrentValue(value)
        elif isinstance(self._widget, TextEdit):
            self._widget.setText(str(value))
        else:
            self._widget.setText(str(value))
            self._widget.home(False)

    def clear(self):
        if isinstance(self._widget, StatusEdit):
            self._widget.setCurrentValue('demo')
        else:
            self._widget.clear()


class BaseFormLayout(QGridLayout):
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
            self.addWidget(widget, self.row, 1, 1, self.columnCount - 1)
            if item1.type() == Type.Number:
                widget.setSizePolicy(QSizePolicy.Fixed,
                                     QSizePolicy.Fixed)
        else:
            if item1.isHidden() and item2.isHidden():
                return

            if isinstance(item2, QAbstractButton):
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

                    widget = QWidget()
                    widget.setMinimumWidth(0)
                    if self.columnCount == 6:
                        widget.setSizePolicy(QSizePolicy.Fixed,
                                             QSizePolicy.Fixed)
                    self.addWidget(widget, self.row, col)
                    col = col + 1

                if not item2.isHidden():
                    if item2.widget().sizePolicy().horizontalPolicy() == QSizePolicy.Fixed:
                        item2.label().setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                    self.addWidget(item2.label(), self.row, col)
                    col = col + 1
                    self.addWidget(item2.widget(), self.row, col, 1, self.columnCount - 4)

        self.row = self.row + 1

    def addHalfRow(self, item1):
        if item1.isHidden():
            return

        col = 0
        if not item1.isHidden():
            self.addWidget(item1.label(), self.row, col)
            col = col + 1
            self.addWidget(item1.widget(), self.row, col)
            col = col + 1

            widget = QWidget()
            widget.setMinimumWidth(0)
            if self.columnCount == 6:
                widget.setSizePolicy(QSizePolicy.Fixed,
                                     QSizePolicy.Fixed)
            self.addWidget(widget, self.row, col)
            col = col + 1

        self.row = self.row + 1


class BaseFormGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super(BaseFormGroupBox, self).__init__(title, parent)

        self.layout = BaseFormLayout(self)
        self.setLayout(self.layout)
        self.setSizePolicy(QSizePolicy.Preferred,
                           QSizePolicy.Fixed)

    def isEmpty(self):
        return self.layout.isEmpty()

    def addRow(self, item1, item2=None):
        self.layout.addRow(item1, item2)

        # If field is a Text - make it vertical size preferred
        self.fixSizePolicy(item1)
        if item2 and not isinstance(item2, QAbstractButton):
            self.fixSizePolicy(item2)

    def addHalfRow(self, item1):
        self.layout.addHalfRow(item1)

    def fixSizePolicy(self, item):
        if not item.isHidden() and item.type() == Type.Text:
            self.setSizePolicy(QSizePolicy.Preferred,
                               QSizePolicy.Preferred)


class ImageFormLayout(BaseFormLayout):
    def __init__(self, parent=None):
        super(ImageFormLayout, self).__init__(parent)

        self.imagesCount = 0

    def addImages(self, images):
        for image in images:
            if not image.isHidden():
                image.label().setSizePolicy(QSizePolicy.Preferred,
                                            QSizePolicy.Fixed)
                if isinstance(image.label(), QLabel):
                    image.label().setAlignment(Qt.AlignLeft)

                row = int(self.imagesCount / 2)
                col = self.imagesCount % 2

                self.addWidget(image.label(), row * 2, col)
                self.addWidget(image.widget(), row * 2 + 1, col)

                self.setRowMinimumHeight(row * 2 + 1, 120)
                self.setColumnMinimumWidth(col, 160)

                self.imagesCount = self.imagesCount + 1

    def isEmpty(self):
        return (self.imagesCount == 0)


class DesignFormLayout(BaseFormGroupBox):
    def __init__(self, title, parent=None):
        super(DesignFormLayout, self).__init__(title, parent)
        self.layout.columnCount = 3
        self.imagesCount = 0
        self.defaultHeight = 30

    def addImage(self, image):
        if not image.isHidden():
            if isinstance(image.label(), QLabel):
                self.layout.addWidget(image.widget(), 0, 3, 2, 2)
                self.layout.setColumnMinimumWidth(2, 160)
                self.layout.setRowMinimumHeight(0, self.defaultHeight)
            else:
                image.label().setText("")
                self.layout.addWidget(image.label(), 0, 3, 1, 1)
                self.layout.addWidget(image.widget(), 0, 4, 2, 1)
                self.layout.setColumnMinimumWidth(4, 160)
                self.layout.setRowMinimumHeight(0, self.defaultHeight)

            self.imagesCount = self.imagesCount + 1

    def isEmpty(self):
        return (self.imagesCount == 0) and super(DesignFormLayout, self).isEmpty()
