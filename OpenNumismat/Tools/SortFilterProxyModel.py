from PyQt5.QtCore import Qt, QCollator, QLocale, QSortFilterProxyModel

from OpenNumismat.Settings import Settings


class StringSortProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))

    def sort(self, column, order=Qt.AscendingOrder):
        self.model = self.sourceModel()
        super().sort(column, order)

    def lessThan(self, left, right):
        leftData = self.model.data(left, Qt.DisplayRole)
        rightData = self.model.data(right, Qt.DisplayRole)

        return self.collator.compare(leftData, rightData) < 0
