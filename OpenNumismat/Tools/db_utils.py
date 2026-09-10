from PySide6.QtSql import QSqlDatabase


class DBTransaction:

    def __init__(self, db: QSqlDatabase):
        self.db = db
        self.in_transaction = False

    def __enter__(self):
        print(self.in_transaction)
        if self.db.transaction():
            self.in_transaction = True
        return self

    def __exit__(self, exc_type, _exc_val, _exc_tb):
        if self.in_transaction:
            if exc_type is not None:
                self.db.rollback()
                return False

            if not self.db.commit():
                self.db.rollback()
                raise RuntimeError(self.db.lastError().text())

        return True


def execute_query(query, sql, params=None):
    if not query.prepare(sql):
        raise RuntimeError(query.lastError().text())

    if params:
        for value in params:
            query.addBindValue(value)

    if not query.exec():
        raise RuntimeError(query.lastError().text())

    return query
