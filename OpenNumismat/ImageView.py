from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtWidgets import *

from OpenNumismat.EditCoinDialog.ImageLabel import ImageLabel
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Settings import Settings


class ImageView(QWidget):

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
        self.imageLayout.setContentsMargins(QtCore.QMargins())
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
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        return layout

    def setModel(self, model):
        self.model = model

        self.imageFields = []
        for field in self.model.fields.userFields:
            if field.type == Type.Image:
                self.imageFields.append(field)

        # By default show only first 2 images
        self.showedCount = Settings()['images_by_default']

        self.imageButtons = []
        for field in self.imageFields:
            button = QCheckBox(self)
            button.setToolTip(field.title)
            button.setDisabled(True)
            button.stateChanged.connect(self.buttonClicked)
            self.imageButtons.append(button)
            self.buttonLayout.addWidget(button)

    def clear(self):
        while self.imageLayout.count():
            item = self.imageLayout.takeAt(0)
            w = item.widget()
            self.imageLayout.removeItem(item)
            w.deleteLater()

    def buttonClicked(self, _state):
        self.clear()

        current = self.currentIndex
        self.showedCount = 0
        for i, field in enumerate(self.imageFields):
            if self.imageButtons[i].isChecked():
                index = self.model.index(current.row(), field.id)
                data = index.data(Qt.UserRole)
                img = self.model.getImage(data)

                image = ImageLabel(field.title, self)
                image.loadFromData(img)
                title = self.model.getImageTitle(data)
                image.setToolTip(title)

                image.imageEdited.connect(self.imageEdited)
                self.imageLayout.addWidget(image)

                self.showedCount += 1

    def rowChangedEvent(self, current):
        self.currentIndex = current
        self.clear()

        for i, field in enumerate(self.imageFields):
            self.imageButtons[i].stateChanged.disconnect(self.buttonClicked)
            self.imageButtons[i].setCheckState(Qt.Unchecked)
            self.imageButtons[i].setDisabled(True)

            index = self.model.index(current.row(), field.id)
            data = index.data(Qt.UserRole)
            img = self.model.getImage(data)
            if img and not img.isNull():
                if self.imageLayout.count() < self.showedCount:
                    image = ImageLabel(field.title, self)
                    image.loadFromData(img)
                    title = self.model.getImageTitle(data)
                    image.setToolTip(title)

                    image.imageEdited.connect(self.imageEdited)
                    self.imageLayout.addWidget(image)

                    self.imageButtons[i].setCheckState(Qt.Checked)

                self.imageButtons[i].setDisabled(False)

            self.imageButtons[i].stateChanged.connect(self.buttonClicked)

    def imageEdited(self, image):
        record = self.model.record(self.currentIndex.row())
        record.setValue(image.field, image.image)
        self.model.setRecord(self.currentIndex.row(), record)
        # self.model.submitAll()

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget
