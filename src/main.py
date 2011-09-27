#!/usr/bin/python

from PyQt4 import QtGui, QtCore

from Collection.Collection import Collection
from EditCoinDialog.EditCoinDialog import EditCoinDialog
from TabView import TabView
from LatestCollections import LatestCollections

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        exitAct = QtGui.QAction(QtGui.QIcon('icons/exit.png'), self.tr("Exit"), self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip(self.tr("Exit application"))
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        file = menubar.addMenu(self.tr("&File"))
        file.addAction(exitAct)

        add_coin = QtGui.QAction(QtGui.QIcon('icons/add_coin.png'), self.tr("Add"), self)
        add_coin.setStatusTip(self.tr("Add new coin"))
        add_coin.triggered.connect(self.addCoin)

        coin = menubar.addMenu(self.tr("Coin"))
        coin.addAction(add_coin)

        newCollectionAct = QtGui.QAction(self.tr("&New..."), self)
        newCollectionAct.triggered.connect(self.newCollection)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        openCollectionAct = QtGui.QAction(icon, self.tr("&Open..."), self)
        openCollectionAct.setShortcut('Ctrl+O')
        openCollectionAct.triggered.connect(self.openCollection)

        collectionMenu = menubar.addMenu(self.tr("Collection"))
        collectionMenu.addAction(newCollectionAct)
        collectionMenu.addAction(openCollectionAct)
        collectionMenu.addSeparator()

        self.latestActions = []
        self.__updateLatest(collectionMenu)

        self.viewTab = TabView(self)
        
        listMenu = menubar.addMenu(self.tr("List"))
        newListAct = QtGui.QAction(self.tr("New..."), self)
        newListAct.triggered.connect(self.viewTab.newList)
        listMenu.addAction(newListAct)
        openPageMenu = QtGui.QMenu(self.tr("Open"), self)
        self.viewTab.setOpenPageMenu(openPageMenu)
        listMenu.addMenu(openPageMenu)
        renameListAct = QtGui.QAction(self.tr("Rename..."), self)
        renameListAct.triggered.connect(self.viewTab.renamePage)
        listMenu.addAction(renameListAct)
        listMenu.addSeparator()
        closeListAct = QtGui.QAction(self.tr("Close"), self)
        closeListAct.triggered.connect(self.viewTab.closePage)
        listMenu.addAction(closeListAct)
        removeListAct = QtGui.QAction(self.tr("Remove"), self)
        removeListAct.triggered.connect(self.viewTab.removePage)
        listMenu.addAction(removeListAct)

        self.setWindowTitle(self.tr("Num"))
        
        latest = LatestCollections(self)
        self.collection = Collection(self)
        if self.collection.open(latest.latest()):
            self.setCollection(self.collection)
        
        self.setCentralWidget(self.viewTab)
        
        settings = QtCore.QSettings()
        pageIndex = settings.value('tabwindow/page') or 0
        self.viewTab.setCurrentIndex(pageIndex)

        if settings.value('mainwindow/maximized') == 'true':
            self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
        else:
            size = settings.value('mainwindow/size')
            if size:
                self.resize(size)
            else:
                self.resize(350, 250)
    
    def __updateLatest(self, menu=None):
        if menu:
            self.__menu = menu
        for act in self.latestActions:
            self.__menu.removeAction(act)

        self.latestActions = []
        latest = LatestCollections(self)
        for act in latest.actions():
            self.latestActions.append(act)
            act.latestTriggered.connect(self.openLatest)
            self.__menu.addAction(act)

    def addCoin(self):
        record = self.collection.model().record()
        dialog = EditCoinDialog(record, self)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            rec = dialog.getRecord()
            self.collection.model().insertRecord(-1, rec)
            self.collection.model().submitAll()

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
        self.__updateLatest()
        
        self.viewTab.setCollection(collection)

    def closeEvent(self, e):
        settings = QtCore.QSettings()

        self.viewTab.savePagePositions()
        # Save latest opened page
        settings.setValue('tabwindow/page', self.viewTab.currentIndex());
        
        # Save main window size
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
