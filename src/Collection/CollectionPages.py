from PyQt4 import QtCore
from PyQt4.QtSql import QSqlQuery

class CollectionPageTypes:
    List = 0

class CollectionPages(QtCore.QObject):
    def __init__(self, db, parent=None):
        super(CollectionPages, self).__init__(parent)
        
        self.db = db
        sql = "CREATE TABLE IF NOT EXISTS pages (\
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
            title CHAR,\
            isopen INTEGER,\
            position INTEGER,\
            type INTEGER)"
        QSqlQuery(sql, self.db)
        
        # TODO: Add default page if no one exists
    
    def pages(self):
        query = QSqlQuery("SELECT * FROM pages ORDER BY position")
        idNo = query.record().indexOf('id')
        titleNo = query.record().indexOf('title')
        isOpenNo = query.record().indexOf('isopen')
        pages = []
        while query.next():
            pages.append((query.value(idNo), query.value(titleNo), query.value(isOpenNo)))
        return pages

    def addPage(self, page, title):
        query = QSqlQuery(self.db)
        query.prepare("INSERT INTO pages (title, isopen, type) "
                      "VALUES (?, ?, ?)")
        query.addBindValue(title)
        query.addBindValue(int(True))
        query.addBindValue(CollectionPageTypes.List)
        query.exec_()

        query = QSqlQuery("SELECT last_insert_rowid() FROM pages", self.db)
        query.next()
        page.id = query.value(0)
    
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

    def removePage(self, page):
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
