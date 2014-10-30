from PyQt5 import QtCore
from PyQt5.QtSql import QSqlQuery

from OpenNumismat.Collection.CollectionFields import CollectionFields
from OpenNumismat.Collection.ListPageParam import ListPageParam
from OpenNumismat.Collection.TreeParam import TreeParam


class CollectionPageTypes:
    List = 0


class CollectionPageParam(QtCore.QObject):
    def __init__(self, record, parent=None):
        QtCore.QObject.__init__(self, parent)

        for name in ['id', 'title', 'isopen', 'type']:
            setattr(self, name, record.value(name))


class CollectionPages(QtCore.QObject):
    def __init__(self, db, parent=None):
        super(CollectionPages, self).__init__(parent)

        self.db = db
        sql = "CREATE TABLE IF NOT EXISTS pages (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            title TEXT,\
            isopen INTEGER,\
            position INTEGER,\
            type INTEGER)"
        QSqlQuery(sql, self.db)

        self.fields = CollectionFields(self.db)
        self.params = None

    def pagesParam(self):
        if self.params is None:
            query = QSqlQuery("SELECT * FROM pages ORDER BY position")
            self.params = self.__queryToParam(query)
        return self.params

    def addPage(self, title):
        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO pages (title, isopen, type) "
                      "VALUES (?, ?, ?)")
        query.addBindValue(title)
        query.addBindValue(int(True))
        query.addBindValue(CollectionPageTypes.List)
        query.exec_()

        query = QSqlQuery("SELECT * FROM pages WHERE id=last_insert_rowid()",
                          self.db)
        return self.__queryToParam(query)[0]  # get only one item

    def renamePage(self, page, title):
        query = QSqlQuery(self.db)
        query.prepare("UPDATE pages SET title=? WHERE id=?")
        query.addBindValue(title)
        query.addBindValue(page.id)
        query.exec_()

    def closePage(self, page):
        query = QSqlQuery(self.db)
        query.prepare("UPDATE pages SET isopen=? WHERE id=?")
        query.addBindValue(int(False))
        query.addBindValue(page.id)
        query.exec_()

    def openPage(self, page):
        query = QSqlQuery(self.db)
        query.prepare("UPDATE pages SET isopen=? WHERE id=?")
        query.addBindValue(int(True))
        query.addBindValue(page.id)
        query.exec_()

    def removePage(self, page):
        page.listParam.remove()
        page.treeParam.remove()

        query = QSqlQuery(self.db)
        query.prepare("DELETE FROM pages WHERE id=?")
        query.addBindValue(page.id)
        query.exec_()

    def savePositions(self, pages):
        for position, page in enumerate(pages):
            query = QSqlQuery(self.db)
            query.prepare("UPDATE pages SET position=? WHERE id=?")
            query.addBindValue(position)
            query.addBindValue(page.id)
            query.exec_()

    def closedPages(self):
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM pages WHERE isopen=? ORDER BY title")
        query.addBindValue(int(False))
        query.exec_()
        return self.__queryToParam(query)

    def __queryToParam(self, query):
        pagesParam = []
        while query.next():
            param = CollectionPageParam(query.record())
            param.fields = self.fields
            param.db = self.db
            if param.type == CollectionPageTypes.List:
                param.listParam = ListPageParam(param)
                param.treeParam = TreeParam(param)
            pagesParam.append(param)

        return pagesParam
