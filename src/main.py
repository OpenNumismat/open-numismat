#!/usr/bin/python

from PyQt4 import QtGui, QtCore
from PyQt4.QtSql import *

from EditCoinDialog import EditCoinDialog
from TableView import TableView

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        db = QSqlDatabase.addDatabase('QSQLITE')
        
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
             saller CHAR, \
             payplace CHAR, \
             payinfo TEXT, \
             saledate CHAR, \
             saleprice NUMERIC(10,2), \
             buyer CHAR, \
             saleplace CHAR, \
             saleinfo TEXT, \
             note TEXT, \
             hang TEXT, \
             obverseimg BLOB, \
             reverseimg BLOB, \
             edgeimg BLOB, \
             photo1 BLOB, \
             photo2 BLOB, \
             photo3 BLOB \
            )")

        self.model = QSqlTableModel(None, db)
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model.setTable('coins')
        
        self.model.select()
        
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, self.tr("Name"))
        
        view = TableView()
        view.setModel(self.model)
        
        self.resize(350, 250)
        self.setWindowTitle(self.tr("Num"))

        exit = QtGui.QAction(QtGui.QIcon('icons/exit.png'), self.tr("Exit"), self)
        exit.setShortcut('Ctrl+Q')
        exit.setStatusTip(self.tr("Exit application"))
        exit.triggered.connect(self.close)

        menubar = self.menuBar()
        file = menubar.addMenu(self.tr("&File"))
        file.addAction(exit)

        add_coin = QtGui.QAction(QtGui.QIcon('icons/add_coin.png'), self.tr("Add"), self)
        add_coin.setShortcut('Shift+Ins')
        add_coin.setStatusTip(self.tr("Add new coin"))
        add_coin.triggered.connect(self.addCoin)

        coin = menubar.addMenu(self.tr("Coin"))
        coin.addAction(add_coin)

        self.setCentralWidget(view)
        
        settings = QtCore.QSettings()
        if settings.value('mainwindow/maximized') == 'true':
            self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
        else:
            size = settings.value('mainwindow/size')
            if size:
                self.resize(size)

    def addCoin(self):
        record = self.model.record()
        dialog = EditCoinDialog(record, self)
        dialog.exec_()
        rec = dialog.getRecord()
        self.model.insertRecord(-1, rec)
        self.model.submitAll()
    
    def closeEvent(self, e):
        settings = QtCore.QSettings()
        settings.setValue('mainwindow/size', self.size());
        settings.setValue('mainwindow/maximized', self.isMaximized());
    
def run():
    import sys

    app = QtGui.QApplication(sys.argv)

    # TODO: Fill application fields
    QtCore.QCoreApplication.setOrganizationName("MySoft");
    QtCore.QCoreApplication.setOrganizationDomain("mysoft.com");
    QtCore.QCoreApplication.setApplicationName("Star Runner");

    translator = QtCore.QTranslator()
    translator.load('lang_'+QtCore.QLocale.system().name());
    app.installTranslator(translator);

    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
