from PySide6.QtWidgets import QWidget, QVBoxLayout

from OpenNumismat.EditCoinDialog.DetailsTabWidget import DetailsTabWidget


class DetailsView(QWidget):

    def __init__(self, direction, parent=None):
        super().__init__(parent)

        self.direction = direction

        self.resize(120, 120)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def setModel(self, model):
        self.model = model

        self.widget = DetailsTabWidget(model, self.direction)
        self.layout.addWidget(self.widget)

    def rowChangedEvent(self, current):
        if current.isValid():
            record = self.model.record(current.row())
            self.widget.fillItems(record)
        else:
            self.widget.clear()
