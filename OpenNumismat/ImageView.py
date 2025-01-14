from PySide6.QtCore import Qt, QObject, QMargins
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.ImageLabel import ImageLabel
from OpenNumismat.ImageEditor import ImageProxy, ImageScrollLabel


class ImageView(QWidget):
    prevRecordEvent = pyqtSignal(QObject)
    nextRecordEvent = pyqtSignal(QObject)

    def __init__(self, direction, parent=None):
        super().__init__(parent)

        self.currentIndex = None

        if direction == QBoxLayout.LeftToRight:
            layout = self.__createHorizontalLayout()
        else:
            layout = self.__createVerticalLayout()

        self.setLayout(layout)

    def __createVerticalLayout(self):
        layout = QVBoxLayout()

        self.imageLayout = QVBoxLayout()
        self.imageLayout.setContentsMargins(QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(widget)

        return layout

    def __createHorizontalLayout(self):
        layout = QHBoxLayout()

        self.buttonLayout = QVBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.imageLayout = QHBoxLayout()
        self.imageLayout.setContentsMargins(QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        return layout

    def setModel(self, model):
        self.model = model

        self.imageFields = []
        for field in self.model.fields.userFields:
            if field.type == Type.Image:
                self.imageFields.append(field)

        self.showedMask = self.model.settings['images_view_mask']

        self.imageButtons = []
        for field in self.imageFields:
            button = QCheckBox(self)
            button.setToolTip(field.title)
            button.setDisabled(True)
            button.checkStateChanged.connect(self.buttonClicked)
            self.imageButtons.append(button)
            self.buttonLayout.addWidget(button)

    def clear(self):
        while self.imageLayout.count():
            item = self.imageLayout.takeAt(0)
            w = item.widget()
            self.imageLayout.removeItem(item)
            w.clear()
            w.deleteLater()

    def buttonClicked(self, _state):
        self.clear()

        current = self.currentIndex
        for i, field in enumerate(self.imageFields):
            if self.imageButtons[i].isChecked():
                index = self.model.index(current.row(), field.id)
                data = index.data(Qt.UserRole)
                img = self.model.getImage(data)

                image = ImageLabel(field.name, field.title, self)
                image.loadFromData(img)
                title = self.model.getImageTitle(data)
                image.setToolTip(title)

                self.imageLayout.addWidget(image)

                self.showedMask |= 1 << i
            else:
                if self.imageButtons[i].isEnabled():
                    self.showedMask &= ~(1 << i)

        self.model.settings['images_view_mask'] = self.showedMask
        self.model.settings.save()

    def rowChangedEvent(self, current):
        self.currentIndex = current
        self.clear()

        for i, field in enumerate(self.imageFields):
            self.imageButtons[i].checkStateChanged.disconnect(self.buttonClicked)
            self.imageButtons[i].setCheckState(Qt.Unchecked)
            self.imageButtons[i].setDisabled(True)

            index = self.model.index(current.row(), field.id)
            data = index.data(Qt.UserRole)
            img = self.model.getImage(data)
            if img and not img.isNull():
                if self.showedMask & (1 << i):
                    image = ImageLabel(field.name, field.title, self)
                    image.loadFromData(img)
                    title = self.model.getImageTitle(data)
                    image.setToolTip(title)

                    self.imageLayout.addWidget(image)

                    self.imageButtons[i].setCheckState(Qt.Checked)

                self.imageButtons[i].setDisabled(False)

            self.imageButtons[i].checkStateChanged.connect(self.buttonClicked)

    def imageEdited(self, image):
        record = self.model.record(self.currentIndex.row())
        record.setValue(image.field, image.image)
        self.model.setRecord(self.currentIndex.row(), record)
        self.model.submitAll()

        for i in range(self.imageLayout.count()):
            image_label = self.imageLayout.itemAt(i).widget()
            if image_label.field == image.field:
                image_label._setImage(image.image)

    def getImageProxy(self):
        imageProxy = ImageProxy(self)
        imageProxy.prevRecordEvent.connect(self.prevRecordEvent)
        imageProxy.nextRecordEvent.connect(self.nextRecordEvent)

        for field in self.imageFields:
            index = self.model.index(self.currentIndex.row(), field.id)
            data = index.data(Qt.UserRole)
            img = self.model.getImage(data)
            if img and not img.isNull():
                image = ImageScrollLabel(field.name, field.title, self)
                image.loadFromData(img)
                image.imageEdited.connect(self.imageEdited)
                imageProxy.append(image)

        return imageProxy

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget
