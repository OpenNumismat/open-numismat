#!/usr/bin/python

from PyQt4 import QtGui, QtCore

from Collection import Collection
from EditCoinDialog.EditCoinDialog import EditCoinDialog
from TableView import TableView
from LatestCollections import LatestCollections

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
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

        separator = QtGui.QAction(self)
        separator.setSeparator(True)

        collectionMenu = menubar.addMenu(self.tr("Collection"))
        collectionMenu.addAction(newCollectionAct)
        collectionMenu.addAction(openCollectionAct)
        collectionMenu.addAction(separator)

        # TODO: Update menu on the fly
        latest = LatestCollections(self)
        for act in latest.actions():
            act.latestTriggered.connect(self.openLatest)
            collectionMenu.addAction(act)

        self.setWindowTitle(self.tr("Num"))

        self.view = TableView()

        latest = LatestCollections(self)
        self.collection = Collection(self)
        if self.collection.open(latest.latest()):
            self.setCollection(self.collection)
        
        self.setCentralWidget(self.view)
        
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
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            rec = dialog.getRecord()
            self.model.insertRecord(-1, rec)
            self.model.submitAll()

    def openCollection(self):
        dir_ = QtCore.QFileInfo(self.collection.fileName).absolutePath()
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                self.tr("Open collection"), dir_,
                self.tr("Collections (*.db)"))
        if fileName:
            if self.collection.open(fileName):
                self.setCollection(self.collection)
            # TODO: Remove collection from latest collections list
    
    def newCollection(self):
        dir_ = QtCore.QFileInfo(self.collection.fileName).absolutePath()
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("New collection"), dir_,
                self.tr("Collections (*.db)"), QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName:
            if self.collection.create(fileName):
                self.setCollection(self.collection)
    
    def openLatest(self, fileName):
        if fileName:
            if self.collection.open(fileName):
                self.setCollection(self.collection)
    
    def setCollection(self, collection):
        self.setWindowTitle(collection.getCollectionName() + ' - ' + self.tr("Num"))

        latest = LatestCollections(self)
        latest.setLatest(collection.getFileName())

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
