#!/usr/bin/python

from PyQt4 import QtGui, QtCore
from PyQt4.QtSql import *

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        db = QSqlDatabase.addDatabase("QSQLITE")
        
        db.setDatabaseName("../db/COLLECTION.DB")
        if not db.open():
            print(db.lastError().text()) 

        QSqlQuery("CREATE TABLE IF NOT EXISTS coins \
            (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,\
             title CHAR NOT NULL, \
             par NUMERIC(10,2), \
             unit CHAR, \
             country CHAR, \
             year NUMERIC(4), \
             period CHAR, \
             mint CHAR, \
             mintmark CHAR(10), \
             type CHAR, \
             series CHAR, \
             metal CHAR, \
             probe NUMERIC(3,3), \
             form CHAR, \
             diametr NUMERIC(10,3), \
             thick NUMERIC(10,3), \
             mass NUMERIC(10,3), \
             grade CHAR, \
             edge CHAR, \
             edgelabel CHAR, \
             obvrev CHAR, \
             state CHAR,\
             mintage INTEGER, \
             dateemis CHAR, \
             catalognum CHAR,\
             paydate CHAR, \
             payprice NUMERIC(10,2), \
             saledate CHAR, \
             saleprice NUMERIC(10,2), \
             note TEXT, \
             hang TEXT, \
             obverse BLOB, \
             reverse BLOB \
            )")

        model = QSqlTableModel(None, db)
        model.setTable("coins")
        
        model.select()
        
        model.setHeaderData(0, QtCore.Qt.Horizontal, "Name")
        
        view = QtGui.QTableView()
        view.setModel(model)
        view.resizeRowsToContents()
        
        view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        
        self.resize(350, 250)
        self.setWindowTitle('Num')

        exit = QtGui.QAction(QtGui.QIcon('icons/exit.png'), 'Exit', self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip('Exit application')
        self.connect(exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

        menubar = self.menuBar()
        file = menubar.addMenu('&File')
        file.addAction(exit)

        self.setCentralWidget(view)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
