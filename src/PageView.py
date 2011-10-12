from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt

from ListView import ListView
from EditCoinDialog.ImageLabel import ImageLabel
from Collection.CollectionFields import FieldTypes as Type

class PageView(QtGui.QSplitter):
    def __init__(self, listParam, parent=None):
        super(PageView, self).__init__(parent)
        
        self.listView = ListView(listParam, self)
        self.listView.rowChanged.connect(self.rowChanged)
        self.addWidget(self.listView)
        
        layout = QtGui.QVBoxLayout(self)
        
        self.imageLayout = QtGui.QVBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))
        
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        layout.addWidget(widget)
        
        widget = self.__layoutToWidget(layout)
        widget.resize(120, 0)
        self.addWidget(widget)
        
        self.splitterMoved.connect(self.splitterPosChanged)

    def setModel(self, model):
        self.listView.setModel(model)
        
        self.imageButtons = []
        self.imageFields = []
        for field in model.fields:
            if field.type == Type.Image:
                self.imageFields.append(field.name)
                button = QtGui.QCheckBox(self)
                button.setToolTip(field.title)
                button.setDisabled(True)
                button.stateChanged.connect(self.buttonClicked)
                self.imageButtons.append(button)
                self.buttonLayout.addWidget(button)
    
    def model(self):
        return self.listView.model()
    
    def splitterPosChanged(self, pos, index):
        settings = QtCore.QSettings()
        settings.setValue('pageview/splittersizes', self.sizes())

    def showEvent(self, e):
        settings = QtCore.QSettings()
        sizes = settings.value('pageview/splittersizes')
        if sizes:
            for i in range(len(sizes)):
                sizes[i] = int(sizes[i])

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)
    
    def buttonClicked(self, state):
        self.clear()

        current = self.listView.currentIndex()
        for i, field in enumerate(self.imageFields):
            if self.imageButtons[i].checkState() == Qt.Checked:
                image = ImageLabel(self)
                index = self.model().index(current.row(), self.model().fieldIndex(field))
                image.loadFromData(index.data())
                self.imageLayout.addWidget(image)
    
    def rowChanged(self, current):
        self.clear()
        
        images = []
        for i, field in enumerate(self.imageFields):
            self.imageButtons[i].stateChanged.disconnect(self.buttonClicked)
            self.imageButtons[i].setCheckState(Qt.Unchecked)
            self.imageButtons[i].setDisabled(True)

            index = self.model().index(current.row(), self.model().fieldIndex(field))
            if index.data() and not index.data().isNull():
                # By default show only first 2 images
                if len(images) < 2:
                    images.append(index.data())
                    self.imageButtons[i].setCheckState(Qt.Checked)
                self.imageButtons[i].setDisabled(False)

            self.imageButtons[i].stateChanged.connect(self.buttonClicked)

        for imageData in images:
            image = ImageLabel(self)
            image.loadFromData(imageData)
            self.imageLayout.addWidget(image)
    
    def clear(self):
        for _ in range(self.imageLayout.count()):
            item = self.imageLayout.itemAt(0)
            item.widget().clear()
            self.imageLayout.removeItem(item)

    def __layoutToWidget(self, layout):
        widget = QtGui.QWidget(self)
        widget.setLayout(layout)
        return widget
