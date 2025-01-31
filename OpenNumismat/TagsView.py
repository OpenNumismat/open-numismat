from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class TagsView(QTreeWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)
        self.setAutoScroll(False)

        self.currentItemChanged.connect(self.itemActivatedEvent)

    def setModel(self, model):
        self.db = model.database()
        self.model = model

        self.update()

    def update(self):
        self.clear()

        sql = "SELECT id, tag, position, parent_id, icon FROM tags ORDER BY position"
        query = QSqlQuery(self.db)
        query.exec(sql)

        items = {}
        while query.next():
            record = query.record()

            tag_id = record.value(0)
            # position = record.value(2)
            tag = record.value(1)
            parent_id = record.value(3)
            icon_data = record.value(4)

            item = QTreeWidgetItem((tag,))
            item.setData(0, Qt.UserRole, tag_id)
            # item.setData(0, Qt.UserRole + 1, position)
            item.setData(0, Qt.UserRole + 2, parent_id)
            if icon_data:
                pixmap = QPixmap()
                if pixmap.loadFromData(icon_data):
                    item.setData(0, Qt.DecorationRole, pixmap)

            items[tag_id] = item

        for tag_id, item in items.items():
            parent_id = item.data(0, Qt.UserRole + 2)

            if parent_id:
                parent_item = items[parent_id]
                parent_item.addChild(item)
            else:
                self.addTopLevelItem(item)

        self.expandAll()

    def itemActivatedEvent(self, current, _previous):
        if current:
            self.scrollToItem(current)
            self.resizeColumnToContents(0)

            tag_id = current.data(0, Qt.UserRole)
            sql = f"SELECT coin_id FROM coins_tags WHERE tag_id={tag_id}"
            query = QSqlQuery(self.db)
            query.exec(sql)
            coin_ids = []
            while query.next():
                record = query.record()

                coin_id = record.value(0)
                coin_ids.append(str(coin_id))

            if coin_ids:
                # TODO: Use INNER JOIN instead filtering by id
                filter_ = f"id IN ({','.join(coin_ids)})"
            else:
                filter_ = "FALSE"
            self.model.setAdditionalFilter(filter_)

    def tagsChanged(self):
        self.update()

    def clearSelection(self):
        super().clearSelection()
        self.setCurrentItem(None)
