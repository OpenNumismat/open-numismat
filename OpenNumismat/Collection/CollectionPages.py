from PySide6.QtCore import QObject
from PySide6.QtSql import QSqlQuery

from OpenNumismat.Collection.CollectionFields import CollectionFields
from OpenNumismat.Collection.ListPageParam import ListPageParam
from OpenNumismat.Collection.TreeParam import TreeParam
from OpenNumismat.Statistics.StatisticsParam import StatisticsParam
from OpenNumismat.Tools.db_utils import DBTransaction, execute_query


class CollectionPageTypes:
    Default = 0
    TypeMask = 0x0F
    List = 0
    Icon = 1
    Card = 2
    InfoTypeMask = 0xF0
    Details = 0
    Statistics = 0x10
    Map = 0x20


class CollectionPageParam(QObject):
    def __init__(self, record, parent=None):
        super().__init__(parent)

        for name in ('id', 'title', 'isopen'):
            setattr(self, name, record.value(name))
        setattr(self, 'type',
                record.value('type') & CollectionPageTypes.TypeMask)
        info_type = record.value('type') & CollectionPageTypes.InfoTypeMask
        setattr(self, 'info_type', info_type)


class CollectionPages(QObject):
    def __init__(self, db, parent=None):
        super().__init__(parent)

        self.db = db

        query = QSqlQuery(self.db)
        sql = "CREATE TABLE IF NOT EXISTS pages (\
            id INTEGER PRIMARY KEY,\
            title TEXT,\
            isopen INTEGER,\
            position INTEGER,\
            type INTEGER,\
            icon BLOB)"
        execute_query(query, sql)

        self.fields = CollectionFields(self.db)
        self.params = []

    def pagesParam(self):
        if not self.params:
            query = QSqlQuery(self.db)
            sql = "SELECT * FROM pages ORDER BY position"
            execute_query(query, sql)
            self.params = self.__queryToParam(query)
        return self.params

    def addPage(self, title):
        query = QSqlQuery(self.db)

        sql = ("INSERT INTO pages (title, isopen, type, position)"
               " VALUES (?, ?, ?, (SELECT COUNT(*) FROM pages))")
        params = (title, int(True), CollectionPageTypes.Default)
        execute_query(query, sql, params)

        sql = "SELECT * FROM pages WHERE id=last_insert_rowid()"
        execute_query(query, sql)
        param = self.__queryToParam(query)[0]  # get only one item

        self.params.append(param)

        return param

    def renamePage(self, page, title):
        query = QSqlQuery(self.db)
        sql = "UPDATE pages SET title=? WHERE id=?"
        params = (title, page.id)
        execute_query(query, sql, params)

    def closePage(self, page):
        query = QSqlQuery(self.db)
        sql = "UPDATE pages SET isopen=? WHERE id=?"
        params = (int(False), page.id)
        execute_query(query, sql, params)

    def openPage(self, page):
        query = QSqlQuery(self.db)
        sql = "UPDATE pages SET isopen=? WHERE id=?"
        params = (int(True), page.id)
        execute_query(query, sql, params)

    def removePage(self, page):
        page.listParam.remove()
        page.treeParam.remove()
        page.statisticsParam.remove()

        query = QSqlQuery(self.db)
        sql = "DELETE FROM pages WHERE id=?"
        params = (page.id,)
        execute_query(query, sql, params)

    def savePositions(self, pages):
        with DBTransaction(self.db):
            query = QSqlQuery(self.db)
            for position, page in enumerate(pages):
                sql = "UPDATE pages SET position=? WHERE id=?"
                params = (position, page.id)
                execute_query(query, sql, params)

    def closedPages(self):
        query = QSqlQuery(self.db)
        sql = "SELECT * FROM pages WHERE isopen=? ORDER BY title"
        params = (int(False),)
        execute_query(query, sql, params)
        return self.__queryToParam(query)

    def changeView(self, page, type_):
        query = QSqlQuery(self.db)
        sql = "UPDATE pages SET type=? WHERE id=?"
        params = (type_ | page.info_type, page.id)
        execute_query(query, sql, params)

    def changeInfoType(self, page, info_type):
        query = QSqlQuery(self.db)
        sql = "UPDATE pages SET type=? WHERE id=?"
        params = (info_type | page.type, page.id)
        execute_query(query, sql, params)

    def __queryToParam(self, query):
        pagesParam = []
        while query.next():
            param = CollectionPageParam(query.record())
            param.fields = self.fields
            param.db = self.db
            # TODO: Improve code
            if param.type == CollectionPageTypes.List:
                param.listParam = ListPageParam(param)
            elif param.type == CollectionPageTypes.Card:
                param.listParam = ListPageParam(param)
            elif param.type == CollectionPageTypes.Icon:
                param.listParam = ListPageParam(param)
            param.treeParam = TreeParam(param)
            param.statisticsParam = StatisticsParam(param)
            pagesParam.append(param)

        return pagesParam
