from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from OpenNumismat.Collection.CollectionFields import TreeFields
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


class TreeWidget(QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)

        self.model().rowsRemoved.connect(self.rowsRemoved)

    def updateFlags(self):
        defaultFlags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

        self.invisibleRootItem().setFlags(defaultFlags)

        rootItem = self.topLevelItem(0)
        if rootItem.childCount():
            rootItem.setFlags(defaultFlags)
        else:
            rootItem.setFlags(defaultFlags | Qt.ItemIsDropEnabled)

        topItem = rootItem.child(0)
        if topItem:
            while topItem.childCount():
                topItem.setFlags(defaultFlags)
                topItem = topItem.child(0)
            topItem.setFlags(defaultFlags | Qt.ItemIsDropEnabled |
                             Qt.ItemIsDragEnabled)

    def expandAll(self):
        QTreeWidget.expandAll(self)
        self.resizeColumnToContents(0)

    def rowsRemoved(self, _parent, _start, _end):
        self.updateFlags()

    def dragMoveEvent(self, event):
        if event.source() == self:
            event.ignore()
            return

        return QTreeWidget.dragMoveEvent(self, event)

    def dropEvent(self, event):
        self.event = event
        if event.dropAction() & Qt.CopyAction:
            event.setDropAction(Qt.MoveAction)
        QTreeWidget.dropEvent(self, event)

    def dropMimeData(self, parent, index, data, action):
        res = QTreeWidget.dropMimeData(self, parent, index, data, action)
        if res:
            if (self.event.proposedAction() & Qt.CopyAction) and parent.parent():
                item = parent.takeChild(0)
                text = ' + '.join([parent.text(0), item.text(0)])
                parent.setText(0, text)
                data = parent.data(0, Qt.UserRole)
                data.extend(item.data(0, Qt.UserRole))
                parent.setData(0, Qt.UserRole, data)

            self.updateFlags()
            self.expandAll()

        return res


class ListWidget(QListWidget):

    def dataChanged(self, topLeft, bottomRight, roles=[]):
        if topLeft.row() == bottomRight.row():
            item = self.item(topLeft.row())
            data = item.data(Qt.UserRole)
            if data:
                field = data[0]
                item.setText(field.title)
                item.setData(Qt.UserRole, [field, ])
                for i, field in enumerate(data[1:]):
                    item = QListWidgetItem(field.title)
                    item.setData(Qt.UserRole, [field, ])
                    self.insertItem(topLeft.row() + i + 1, item)

    def dragMoveEvent(self, event):
        if event.dropAction() & Qt.CopyAction:
            event.setDropAction(Qt.MoveAction)

        if event.source() == self:
            event.ignore()
            return

        return QListWidget.dragMoveEvent(self, event)


@storeDlgSizeDecorator
class CustomizeTreeDialog(QDialog):

    def __init__(self, model, treeParam, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.setWindowTitle(self.tr("Customize tree"))

        self.treeWidget = TreeWidget(self)
        self.treeWidget.setDragDropMode(QAbstractItemView.DragDrop)
        self.treeWidget.setDropIndicatorShown(True)
        self.treeWidget.setDefaultDropAction(Qt.MoveAction)

        self.listWidget = ListWidget(self)
        self.listWidget.setDragDropMode(QAbstractItemView.DragDrop)
        self.listWidget.setDropIndicatorShown(True)
        self.listWidget.setDefaultDropAction(Qt.MoveAction)

        splitter = QSplitter(self)
        splitter.addWidget(self.treeWidget)
        splitter.addWidget(self.listWidget)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        clearButton = QPushButton(self.tr("Clear"))
        buttonBox.addButton(clearButton, QDialogButtonBox.ResetRole)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)
        clearButton.clicked.connect(self.clear)

        label = QLabel(self.tr("Hold down the Ctrl key to combine two fields (Value + Unit)"), self)
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(splitter)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        self.treeParam = treeParam
        allFields = model.fields

        rootItem = QTreeWidgetItem([self.treeParam.rootTitle, ])
        self.treeWidget.addTopLevelItem(rootItem)
        topItem = rootItem
        for param in self.treeParam:
            titleParts = [field.title for field in param]
            title = ' + '.join(titleParts)
            data = [field for field in param]

            item = QTreeWidgetItem([title, ])
            item.setData(0, Qt.UserRole, data)
            topItem.addChild(item)
            topItem = item

        self.treeWidget.updateFlags()
        self.treeWidget.expandAll()

        self.availableFields = []
        for field in allFields.userFields:
            if field.name in TreeFields:
                self.availableFields.append(field)
                if field.name not in self.treeParam.usedFieldNames():
                    item = QListWidgetItem(field.title)
                    item.setData(Qt.UserRole, [field, ])
                    self.listWidget.addItem(item)

    def save(self):
        self.treeParam.clear()

        rootItem = self.treeWidget.topLevelItem(0)
        topItem = rootItem.child(0)
        while topItem:
            self.treeParam.append(topItem.data(0, Qt.UserRole))
            topItem = topItem.child(0)

        self.accept()

    def clear(self):
        # Clear all sub-elements
        rootItem = self.treeWidget.topLevelItem(0)
        rootItem.takeChildren()

        self.listWidget.clear()
        for field in self.availableFields:
            item = QListWidgetItem(field.title)
            item.setData(Qt.UserRole, [field, ])
            self.listWidget.addItem(item)
