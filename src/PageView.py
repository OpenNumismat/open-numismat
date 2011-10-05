from PyQt4 import QtCore, QtGui

from ListView import ListView
from EditCoinDialog.ImageLabel import ImageLabel

class PageView(QtGui.QSplitter):
    def __init__(self, listParam, parent=None):
        super(PageView, self).__init__(parent)
        
        self.tableView = ListView(listParam, self)
        self.tableView.rowChanged.connect(self.rowChanged)
        
        self.layout = QtGui.QVBoxLayout()
        self.layout.setContentsMargins(QtCore.QMargins())
        widget = QtGui.QWidget(self)
        widget.resize(120, 0)
        widget.setLayout(self.layout)
        
        self.addWidget(self.tableView)
        self.addWidget(widget)
        
        self.splitterMoved.connect(self.splitterPosChanged)

    def setModel(self, model):
        self.tableView.setModel(model)
    
    def model(self):
        return self.tableView.model()
    
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
    
    def rowChanged(self, current):
        for _ in range(self.layout.count()):
            item = self.layout.itemAt(0)
            item.widget().clear()
            self.layout.removeItem(item)

        images = []
        for field in ['obverseimg', 'reverseimg']:
            index = self.model().index(current.row(), self.model().fieldIndex(field))
            if not index.data() or not index.data().isNull():
                images.append(index.data())

        for imageData in images:
            image = ImageLabel(self)
            image.loadFromData(imageData)
            self.layout.addWidget(image)
