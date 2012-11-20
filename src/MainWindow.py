import sys

from PyQt4 import QtGui, QtCore

from Collection.Collection import Collection
from Collection.Description import DescriptionDialog
from Collection.Password import PasswordSetDialog
from Reference.Reference import Reference
from TabView import TabView
from Settings import Settings, SettingsDialog
from LatestCollections import LatestCollections
from Tools.CursorDecorators import waitCursorDecorator
import version

from Collection.Import import *

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        self.setWindowIcon(QtGui.QIcon('icons/main.ico'))
        
        self.createStatusBar()
        
        settingsAct = QtGui.QAction(QtGui.QIcon('icons/cog.png'), self.tr("Settings..."), self)
        settingsAct.triggered.connect(self.settingsEvent)
        
        exitAct = QtGui.QAction(QtGui.QIcon('icons/door_in.png'), self.tr("E&xit"), self)
        exitAct.setShortcut(QtGui.QKeySequence.Quit)
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        file = menubar.addMenu(self.tr("&File"))
        file.addAction(settingsAct)
        file.addSeparator()
        file.addAction(exitAct)

        addCoinAct = QtGui.QAction(QtGui.QIcon('icons/add.png'), self.tr("Add"), self)
        addCoinAct.setShortcut('Insert')
        addCoinAct.triggered.connect(self.addCoin)

        coin = menubar.addMenu(self.tr("Coin"))
        coin.addAction(addCoinAct)

        newCollectionAct = QtGui.QAction(self.tr("&New..."), self)
        newCollectionAct.triggered.connect(self.newCollectionEvent)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        openCollectionAct = QtGui.QAction(icon, self.tr("&Open..."), self)
        openCollectionAct.setShortcut(QtGui.QKeySequence.Open)
        openCollectionAct.triggered.connect(self.openCollectionEvent)

        backupCollectionAct = QtGui.QAction(QtGui.QIcon('icons/database_backup.png'), self.tr("Backup"), self)
        backupCollectionAct.triggered.connect(self.backupCollectionEvent)

        descriptionCollectionAct = QtGui.QAction(self.tr("Description"), self)
        descriptionCollectionAct.triggered.connect(self.descriptionCollectionEvent)

        passwordCollectionAct = QtGui.QAction(QtGui.QIcon('icons/key.png'), self.tr("Set password..."), self)
        passwordCollectionAct.triggered.connect(self.passwordCollectionEvent)

        importNumizmatAct = QtGui.QAction(QtGui.QIcon('icons/numizmat.ico'), self.tr("Numizmat 2.1"), self)
        importNumizmatAct.triggered.connect(self.importNumizmat)
        importCabinetAct = QtGui.QAction(QtGui.QIcon('icons/cabinet.ico'), self.tr("Cabinet 2.0.2.0, 2011"), self)
        importCabinetAct.triggered.connect(self.importCabinet)
        importCoinsCollectorAct = QtGui.QAction(QtGui.QIcon('icons/CoinsCollector.ico'), self.tr("CoinsCollector 2.6"), self)
        importCoinsCollectorAct.triggered.connect(self.importCoinsCollector)
        importCoinManageAct = QtGui.QAction(QtGui.QIcon('icons/CoinManage.ico'), self.tr("CoinManage 2011"), self)
        importCoinManageAct.triggered.connect(self.importCoinManage)
        importCollectionStudioAct = QtGui.QAction(QtGui.QIcon('icons/CollectionStudio.ico'), self.tr("Collection Studio 3.65"), self)
        importCollectionStudioAct.triggered.connect(self.importCollectionStudio)
        
        importMenu = QtGui.QMenu(self.tr("Import"), self)
        importMenu.addAction(importNumizmatAct)
        importMenu.addAction(importCabinetAct)
        importMenu.addAction(importCoinsCollectorAct)
        importMenu.addAction(importCoinManageAct)
        importMenu.addAction(importCollectionStudioAct)

        collectionMenu = menubar.addMenu(self.tr("Collection"))
        collectionMenu.addAction(newCollectionAct)
        collectionMenu.addAction(openCollectionAct)
        collectionMenu.addAction(backupCollectionAct)
        collectionMenu.addAction(descriptionCollectionAct)
        collectionMenu.addAction(passwordCollectionAct)
        collectionMenu.addSeparator()
        collectionMenu.addMenu(importMenu)
        collectionMenu.addSeparator()

        self.latestActions = []
        self.__updateLatest(collectionMenu)

        self.viewTab = TabView(self)
        
        actions = self.viewTab.actions()
        listMenu = menubar.addMenu(self.tr("List"))
        listMenu.addAction(actions['new'])
        listMenu.addMenu(actions['open'])
        listMenu.aboutToShow.connect(self.viewTab.updateOpenPageMenu)
        listMenu.addAction(actions['rename'])
        listMenu.addSeparator()
        listMenu.addAction(actions['close'])
        listMenu.addAction(actions['remove'])

        self.referenceMenu = menubar.addMenu(self.tr("Reference"))

        helpAct = QtGui.QAction(QtGui.QIcon('icons/help.png'), self.tr("Online help"), self)
        helpAct.setShortcut(QtGui.QKeySequence.HelpContents)
        helpAct.triggered.connect(self.onlineHelp)
        aboutAct = QtGui.QAction(self.tr("About %s") % version.AppName, self)
        aboutAct.triggered.connect(self.about)

        file = menubar.addMenu(self.tr("&Help"))
        file.addAction(helpAct)
        file.addSeparator()
        file.addAction(aboutAct)

        toolBar = QtGui.QToolBar(self.tr("Toolbar"), self)
        toolBar.setMovable(False)
        toolBar.addAction(addCoinAct)
        toolBar.addSeparator()
        toolBar.addAction(settingsAct)
        self.addToolBar(toolBar)

        self.setWindowTitle(version.AppName)
        
        self.reference = Reference(self)
        self.reference.open(Settings().reference)
        
        latest = LatestCollections(self)
        self.collection = Collection(self.reference, self)
        self.openCollection(latest.latest())
        
        self.setCentralWidget(self.viewTab)
        
        settings = QtCore.QSettings()
        pageIndex = settings.value('tabwindow/page')
        if pageIndex:
            self.viewTab.setCurrentIndex(pageIndex)

        if settings.value('mainwindow/maximized') == 'true':
            self.setWindowState(self.windowState() | QtCore.Qt.WindowMaximized)
        else:
            size = settings.value('mainwindow/size')
            if size:
                self.resize(size)
        
        self.autoUpdate()
    
    def createStatusBar(self):
        self.collectionFileLabel = QtGui.QLabel()
        self.statusBar().addWidget(self.collectionFileLabel)
    
    def __updateLatest(self, menu=None):
        if menu:
            self.__menu = menu
        for act in self.latestActions:
            self.__menu.removeAction(act)

        self.latestActions = []
        latest = LatestCollections(self)
        for act in latest.actions():
            self.latestActions.append(act)
            act.latestTriggered.connect(self.openCollection)
            self.__menu.addAction(act)
    
    def settingsEvent(self):
        dialog = SettingsDialog(self.collection, self)
        res = dialog.exec_()
        if res == QtGui.QDialog.Accepted:
            self.__restart()
    
    def __restart(self):
        result = QtGui.QMessageBox.question(self, self.tr("Settings"),
                    self.tr("The application will need to restart to apply the new settings. Restart it now?"),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        if result == QtGui.QMessageBox.Yes:
            self.close()
            program = sys.executable
            QtCore.QProcess.startDetached(program, sys.argv)
    
    def importNumizmat(self):
        defaultDir = ImportNumizmat.defaultDir()
        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select file"), defaultDir, "*.fdb")
        if file:
            imp = ImportNumizmat(self)
            imp.importData(file, self.viewTab.currentModel())
    
    def importCabinet(self):
        defaultDir = ImportCabinet.defaultDir()
        directory = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Select directory"), defaultDir)
        if directory:
            imp = ImportCabinet(self)
            imp.importData(directory, self.viewTab.currentModel())
    
    def importCoinsCollector(self):
        defaultDir = ImportCoinsCollector.defaultDir()
        directory = QtGui.QFileDialog.getExistingDirectory(self, self.tr("Select directory"), defaultDir)
        if directory:
            imp = ImportCoinsCollector(self)
            imp.importData(directory, self.viewTab.currentModel())
    
    def importCoinManage(self):
        defaultDir = ImportCoinManage.defaultDir()
        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open CoinManage file"),
                                                 defaultDir, "*.mdb")
        if file:
            btn = QtGui.QMessageBox.question(self, self.tr("Importing"), self.tr("Import pre-defined coins?"),
                                       buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                       defaultButton=QtGui.QMessageBox.Yes)
            if btn == QtGui.QMessageBox.Yes:
                imp = ImportCoinManagePredefined(self)
                res = imp.importData(file, self.viewTab.currentModel())
                if not res:
                    return
            
            imp = ImportCoinManage(self)
            imp.importData(file, self.viewTab.currentModel())
    
    def importCollectionStudio(self):
        QtGui.QMessageBox.information(self, self.tr("Importing"),
                                      self.tr("Before importing you should export existing collection from Collection Studio to XML Table (choose Collection Studio menu Tools > Export...)."))
        
        defaultDir = ImportCollectionStudio.defaultDir()
        file = QtGui.QFileDialog.getOpenFileName(self, self.tr("Select file"), defaultDir, "*.xml")
        if file:
            imp = ImportCollectionStudio(self)
            imp.importData(file, self.viewTab.currentModel())
    
    def addCoin(self):
        model = self.viewTab.currentModel()
        model.addCoin(model.record(), self)
    
    def __workingDir(self):
        fileName = self.collection.fileName
        if not fileName:
            fileName = LatestCollections.DefaultCollectionName
        return QtCore.QFileInfo(fileName).absolutePath()

    def openCollectionEvent(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                self.tr("Open collection"), self.__workingDir(),
                self.tr("Collections (*.db)"))
        if fileName:
            self.openCollection(fileName)

    def newCollectionEvent(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("New collection"), self.__workingDir(),
                self.tr("Collections (*.db)"), QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName:
            if self.collection.create(fileName):
                self.setCollection(self.collection)
    
    def descriptionCollectionEvent(self, checked):
        dialog = DescriptionDialog(self.collection, self)
        dialog.exec_()
    
    def passwordCollectionEvent(self, checked):
        dialog = PasswordSetDialog(self.collection, self)
        dialog.exec_()
    
    def backupCollectionEvent(self, checked):
        self.collection.backup()

    def openCollection(self, fileName):
        if self.collection.open(fileName):
            self.setCollection(self.collection)
        else:
            # Remove wrong collection from latest collections list
            latest = LatestCollections(self)
            latest.delete(fileName)
            self.__updateLatest()
    
    @waitCursorDecorator
    def setCollection(self, collection):
        self.collectionFileLabel.setText(collection.getFileName())
        self.setWindowTitle(collection.getCollectionName() + ' - ' + version.AppName)

        latest = LatestCollections(self)
        latest.add(collection.getFileName())
        self.__updateLatest()
        
        self.viewTab.setCollection(collection)
        
        self.referenceMenu.clear()
        for action in self.collection.referenceMenu(self):
            self.referenceMenu.addAction(action)
        
    def closeEvent(self, e):
        self.__shutDown()
    
    def __shutDown(self):
        settings = QtCore.QSettings()

        if self.collection.fileName:
            self.viewTab.savePagePositions()
            # Save latest opened page
            settings.setValue('tabwindow/page', self.viewTab.currentIndex())
        
        # Save main window size
        settings.setValue('mainwindow/size', self.size())
        settings.setValue('mainwindow/maximized', self.isMaximized())
    
    def about(self):
        QtGui.QMessageBox.about(self, self.tr("About %s") % version.AppName, self.tr("%s %s\n\nCopyright (C) 2011-2012 Vitaly Ignatov\n\n%s is freeware licensed under a GPLv3.") % (version.AppName, version.Version, version.AppName))

    def onlineHelp(self):
        url = QtCore.QUrl(version.Web + 'wiki/MainPage')
        url.setQueryItems([('wl', Settings().language)])

        executor = QtGui.QDesktopServices()
        executor.openUrl(url)
    
    def autoUpdate(self):
        if Settings().checkUpdates:
            currentDate = QtCore.QDate.currentDate()
            currentDateStr = currentDate.toString(QtCore.Qt.ISODate)
            
            settings = QtCore.QSettings()
            lastUpdateDateStr = settings.value('mainwindow/last_update')
            if lastUpdateDateStr:
                lastUpdateDate = QtCore.QDate.fromString(lastUpdateDateStr, QtCore.Qt.ISODate)
                if lastUpdateDate.addDays(10) < currentDate:
                    self.checkUpdates()
    
            settings.setValue('mainwindow/last_update', currentDateStr)
    
    def checkUpdates(self):
        newVersion = self.__getNewVersion()
        if newVersion != version.Version:
            result = QtGui.QMessageBox.question(self, self.tr("New version"),
                        self.tr("New version is available. Download it now?"),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
            if result == QtGui.QMessageBox.Yes:
                url = QtCore.QUrl(version.Web + 'wiki/MainPage')
                url.setQueryItems([('wl', Settings().language)])
        
                executor = QtGui.QDesktopServices()
                executor.openUrl(url)

    @waitCursorDecorator
    def __getNewVersion(self):
        import urllib.request
        from xml.dom.minidom import parseString
        
        newVersion = version.Version
        
        try:
            req = urllib.request.Request("http://wiki.open-numismat.googlecode.com/git/data/pad.xml")
            data = urllib.request.urlopen(req).read()
            xml = parseString(data)
            tag = xml.getElementsByTagName('Program_Version')[0]
            newVersion = tag.firstChild.nodeValue
        except:
            pass
        
        return newVersion
