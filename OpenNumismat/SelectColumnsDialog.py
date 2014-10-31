from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from OpenNumismat.Collection.ListPageParam import ColumnListParam
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


@storeDlgSizeDecorator
class SelectColumnsDialog(QDialog):
    DataRole = 16

    def __init__(self, listParam, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.listParam = listParam

        self.setWindowTitle(self.tr("Columns"))

        self.listWidget = QListWidget(self)
        # TODO: Disable resizing
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setDropIndicatorShown(True)
        self.listWidget.setWrapping(True)

        allFields = listParam.fields
        collectionFields = list(allFields.userFields)
        for param in listParam.columns:
            field = allFields.field(param.fieldid)
            if field in allFields.disabledFields:
                continue
            item = QListWidgetItem(field.title, self.listWidget)
            item.setData(SelectColumnsDialog.DataRole, param)
            checked = Qt.Unchecked
            if param.enabled:
                checked = Qt.Checked
            item.setCheckState(checked)
            self.listWidget.addItem(item)

            collectionFields.remove(field)  # mark field as processed

        # Process missed columns
        for field in collectionFields:
            item = QListWidgetItem(field.title, self.listWidget)
            item.setData(SelectColumnsDialog.DataRole,
                         ColumnListParam(field.id, False))
            item.setCheckState(Qt.Unchecked)
            self.listWidget.addItem(item)

        # TODO: Add buttons SelectAll, ClearAll, EnabledToTop

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def resizeEvent(self, event):
        self.listWidget.setWrapping(True)

    def save(self):
        self.listParam.columns = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            param = item.data(SelectColumnsDialog.DataRole)
            param.enabled = (item.checkState() == Qt.Checked)
            self.listParam.columns.append(param)

        self.accept()
