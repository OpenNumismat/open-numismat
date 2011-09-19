#!/usr/bin/python

from PyQt4 import QtGui, QtCore

from Collection.Collection import Collection
from EditCoinDialog.EditCoinDialog import EditCoinDialog
from ListView import ListView
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

        separator = QtGui.QAction(self)
        separator.setSeparator(True)

        collectionMenu = menubar.addMenu(self.tr("Collection"))
        collectionMenu.addAction(newCollectionAct)
        collectionMenu.addAction(openCollectionAct)
        collectionMenu.addAction(separator)

        self.latestActions = []
        self.__updateLatest(collectionMenu)

        listMenu = menubar.addMenu(self.tr("List"))
        newListAct = QtGui.QAction(self.tr("New..."), self)
        newListAct.triggered.connect(self.newList)
        listMenu.addAction(newListAct)
        renameListAct = QtGui.QAction(self.tr("Rename..."), self)
        renameListAct.triggered.connect(self.renamePage)
        listMenu.addAction(renameListAct)
        closeListAct = QtGui.QAction(self.tr("Close"), self)
        closeListAct.triggered.connect(self.closePage)
        listMenu.addAction(closeListAct)
        removeListAct = QtGui.QAction(self.tr("Remove"), self)
        removeListAct.triggered.connect(self.removePage)
        listMenu.addAction(removeListAct)

        self.setWindowTitle(self.tr("Num"))
        
        self.viewTab = QtGui.QTabWidget(self)
        self.viewTab.setMovable(True)
        self.viewTab.setTabsClosable(True)
        self.viewTab.tabCloseRequested.connect(self.closePage)
        
        latest = LatestCollections(self)
        self.collection = Collection(self)
        if self.collection.open(latest.latest()):
            self.setCollection(self.collection)
        
        self.setCentralWidget(self.viewTab)
        
        settings = QtCore.QSettings()
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
        
        for page in collection.pages().pages():
            if page[2]:
                listView = ListView()
                listView.setModel(self.collection.model())
                listView.id = page[0]
                self.viewTab.addTab(listView, page[1])

    def newList(self):
        label, ok = QtGui.QInputDialog.getText(self, self.tr("New list"), self.tr("Enter list title"))
        if ok and label:
            listView = ListView()
            listView.setModel(self.collection.model())
            self.viewTab.addTab(listView, label)
            self.viewTab.setCurrentWidget(listView)
            
            self.collection.pages().addPage(listView, label)

    def renamePage(self):
        index = self.viewTab.currentIndex()
        oldLabel = self.viewTab.tabText(index)
        label, ok = QtGui.QInputDialog.getText(self, self.tr("Rename list"), self.tr("Enter new list title"), text=oldLabel)
        if ok and label:
            self.viewTab.setTabText(index, label)
            page = self.viewTab.widget(index)
            self.collection.pages().renamePage(page, label)

    def closePage(self, index=None):
        if not index:
            index = self.viewTab.currentIndex()
        page = self.viewTab.widget(index)
        self.viewTab.removeTab(index)
        self.collection.pages().closePage(page)

    def removePage(self):
        index = self.viewTab.currentIndex()
        page = self.viewTab.widget(index)
        self.viewTab.removeTab(index)
        self.collection.pages().removePage(page)

    def closeEvent(self, e):
        # Save page positions
        pages = []
        for i in range(self.viewTab.count()):
            pages.append(self.viewTab.widget(i))
        self.collection.pages().savePositions(pages)
        
        # Save main window size
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
