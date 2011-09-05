#!/usr/bin/python

from PyQt4 import QtGui, QtCore

from Collection import Collection
from EditCoinDialog.EditCoinDialog import EditCoinDialog
from TableView import TableView

class MainWindow(QtGui.QMainWindow):
    DefaultCollectionName = "../db/demo.db"
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        self.view = TableView()

        self.collection = Collection(self)
        self.collection.open(MainWindow.DefaultCollectionName)
        self.setCollection(self.collection)
        
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

        newCollectionAct = QtGui.QAction(self.tr("&New..."), self)
        newCollectionAct.setShortcut('Ctrl+N')
        newCollectionAct.triggered.connect(self.newCollection)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        openCollectionAct = QtGui.QAction(icon, self.tr("&Open..."), self)
        openCollectionAct.setShortcut('Ctrl+O')
        openCollectionAct.triggered.connect(self.openCollection)

        collection = menubar.addMenu(self.tr("Collection"))
        collection.addAction(newCollectionAct)
        collection.addAction(openCollectionAct)

        self.setCentralWidget(self.view)
        
        self.setWindowTitle(self.tr("Num"))

        settings = QtCore.QSettings()
        if settings.value('mainwindow/maximized') == 'true':
            self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
        else:
            size = settings.value('mainwindow/size')
            if size:
                self.resize(size)
            else:
                self.resize(350, 250)

    def addCoin(self):
        record = self.model.record()
        dialog = EditCoinDialog(record, self)
        dialog.exec_()
        rec = dialog.getRecord()
        self.model.insertRecord(-1, rec)
        self.model.submitAll()

    def openCollection(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                self.tr("Open collection"), MainWindow.DefaultCollectionName,
                self.tr("Collections (*.db)"))
        if fileName:
            self.collection = Collection(self)
            self.collection.open(fileName)
            self.setCollection(self.collection)
    
    def newCollection(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("New collection"), MainWindow.DefaultCollectionName,
                self.tr("Collections (*.db)"))
        if fileName:
            self.collection = Collection(self)
            self.collection.create(fileName)
            self.setCollection(self.collection)
    
    def setCollection(self, collection):
        self.model = self.collection.model()
        self.model.setTable('coins')
        
        self.model.select()
        
        self.model.setHeaderData(1, QtCore.Qt.Horizontal, self.tr("Name"))
        
        self.view.setModel(self.model)
    
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
