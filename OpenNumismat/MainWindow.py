import sys

from PyQt4 import QtGui, QtCore

from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.Description import DescriptionDialog
from OpenNumismat.Collection.Password import PasswordSetDialog
from OpenNumismat.Reference.Reference import Reference
from OpenNumismat.TabView import TabView
from OpenNumismat.Settings import Settings, SettingsDialog
from OpenNumismat.LatestCollections import LatestCollections
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.Gui import createIcon
from OpenNumismat.Reports.Preview import PreviewDialog
from OpenNumismat import version

from OpenNumismat.Collection.Import import *


class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.setWindowIcon(createIcon('main.ico'))

        self.createStatusBar()

        settingsAct = QtGui.QAction(createIcon('cog.png'),
                                    self.tr("Settings..."), self)
        settingsAct.triggered.connect(self.settingsEvent)

        exitAct = QtGui.QAction(createIcon('door_in.png'),
                                self.tr("E&xit"), self)
        exitAct.setShortcut(QtGui.QKeySequence.Quit)
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        file = menubar.addMenu(self.tr("&File"))
        file.addAction(settingsAct)
        file.addSeparator()
        file.addAction(exitAct)

        addCoinAct = QtGui.QAction(createIcon('add.png'),
                                   self.tr("Add"), self)
        addCoinAct.setShortcut('Insert')
        addCoinAct.triggered.connect(self.addCoin)

        editCoinAct = QtGui.QAction(createIcon('pencil.png'),
                                   self.tr("Edit..."), self)
        editCoinAct.triggered.connect(self.editCoin)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)
        deleteCoinAct = QtGui.QAction(icon,
                                   self.tr("Delete"), self)
        deleteCoinAct.setShortcut(QtGui.QKeySequence.Delete)
        deleteCoinAct.triggered.connect(self.deleteCoin)

        coin = menubar.addMenu(self.tr("Coin"))
        coin.addAction(addCoinAct)
        coin.addAction(editCoinAct)
        coin.addAction(deleteCoinAct)

        viewBrowserAct = QtGui.QAction(createIcon('page_white_world.png'),
                                   self.tr("View in browser"), self)
        viewBrowserAct.triggered.connect(self.viewBrowser)

        newCollectionAct = QtGui.QAction(self.tr("&New..."), self)
        newCollectionAct.triggered.connect(self.newCollectionEvent)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        openCollectionAct = QtGui.QAction(icon, self.tr("&Open..."), self)
        openCollectionAct.setShortcut(QtGui.QKeySequence.Open)
        openCollectionAct.triggered.connect(self.openCollectionEvent)

        backupCollectionAct = QtGui.QAction(
                                    createIcon('database_backup.png'),
                                    self.tr("Backup"), self)
        backupCollectionAct.triggered.connect(self.backupCollectionEvent)

        vacuumCollectionAct = QtGui.QAction(
                                    createIcon('compress.png'),
                                    self.tr("Vacuum"), self)
        vacuumCollectionAct.triggered.connect(self.vacuumCollectionEvent)

        descriptionCollectionAct = QtGui.QAction(self.tr("Description"), self)
        descriptionCollectionAct.triggered.connect(
                                            self.descriptionCollectionEvent)

        passwordCollectionAct = QtGui.QAction(createIcon('key.png'),
                                              self.tr("Set password..."), self)
        passwordCollectionAct.triggered.connect(self.passwordCollectionEvent)

        importMenu = QtGui.QMenu(self.tr("Import"), self)

        if ImportNumizmat.isAvailable():
            importNumizmatAct = QtGui.QAction(
                                    createIcon('numizmat.ico'),
                                    self.tr("Numizmat 2.1"), self)
            importNumizmatAct.triggered.connect(self.importNumizmat)
            importMenu.addAction(importNumizmatAct)

        if ImportCabinet.isAvailable():
            importCabinetAct = QtGui.QAction(
                                    createIcon('cabinet.ico'),
                                    self.tr("Cabinet 2.0.2.0, 2011"), self)
            importCabinetAct.triggered.connect(self.importCabinet)
            importMenu.addAction(importCabinetAct)

        if ImportCoinsCollector.isAvailable():
            importCoinsCollectorAct = QtGui.QAction(
                                    createIcon('CoinsCollector.ico'),
                                    self.tr("CoinsCollector 2.6"), self)
            importCoinsCollectorAct.triggered.connect(
                                                    self.importCoinsCollector)
            importMenu.addAction(importCoinsCollectorAct)

        if ImportCoinManage.isAvailable():
            importCoinManageAct = QtGui.QAction(
                                    createIcon('CoinManage.ico'),
                                    self.tr("CoinManage 2011"), self)
            importCoinManageAct.triggered.connect(self.importCoinManage)
            importMenu.addAction(importCoinManageAct)

        if ImportCollectionStudio.isAvailable():
            importCollectionStudioAct = QtGui.QAction(
                                    createIcon('CollectionStudio.ico'),
                                    self.tr("Collection Studio 3.65"), self)
            importCollectionStudioAct.triggered.connect(
                                                self.importCollectionStudio)
            importMenu.addAction(importCollectionStudioAct)

        collectionMenu = menubar.addMenu(self.tr("Collection"))
        collectionMenu.addAction(newCollectionAct)
        collectionMenu.addAction(openCollectionAct)
        collectionMenu.addAction(backupCollectionAct)
        collectionMenu.addAction(vacuumCollectionAct)
        collectionMenu.addAction(passwordCollectionAct)
        collectionMenu.addAction(descriptionCollectionAct)
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
        listMenu.addAction(actions['select'])
        listMenu.addSeparator()
        listMenu.addAction(actions['close'])
        listMenu.addAction(actions['remove'])

        self.referenceMenu = menubar.addMenu(self.tr("Reference"))

        reportAct = QtGui.QAction(self.tr("Report..."), self)
        reportAct.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_P)
        reportAct.triggered.connect(self.report)

        saveTableAct = QtGui.QAction(createIcon('table.png'),
                                     self.tr("Save current list..."), self)
        saveTableAct.triggered.connect(self.saveTable)

        report = menubar.addMenu(self.tr("Report"))
        report.addAction(reportAct)
        report.addAction(saveTableAct)
        report.addAction(viewBrowserAct)

        helpAct = QtGui.QAction(createIcon('help.png'),
                                self.tr("Online help"), self)
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
        toolBar.addAction(editCoinAct)
        toolBar.addAction(viewBrowserAct)
        toolBar.addSeparator()
        toolBar.addAction(settingsAct)
        self.addToolBar(toolBar)

        self.setWindowTitle(version.AppName)

        self.reference = Reference(self)
        self.reference.open(Settings()['reference'])

        if len(sys.argv) > 1:
            fileName = sys.argv[1]
        else:
            latest = LatestCollections(self)
            fileName = latest.latest()

        self.collection = Collection(self.reference, self)
        self.openCollection(fileName)

        self.setCentralWidget(self.viewTab)

        settings = QtCore.QSettings()
        pageIndex = settings.value('tabwindow/page')
        if pageIndex != None:
            self.viewTab.setCurrentIndex(int(pageIndex))

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
                    self.tr("The application will need to restart to apply "
                            "the new settings. Restart it now?"),
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                    QtGui.QMessageBox.Yes)
        if result == QtGui.QMessageBox.Yes:
            self.close()
            program = sys.executable
            argv = []
            if program != sys.argv[0]:
                # Process running as Python arg
                argv.append(sys.argv[0])
            QtCore.QProcess.startDetached(program, argv)

    def importNumizmat(self):
        defaultDir = ImportNumizmat.defaultDir()
        file = QtGui.QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.fdb")
        if file:
            imp = ImportNumizmat(self)
            imp.importData(file, self.viewTab.currentModel())

    def importCabinet(self):
        defaultDir = ImportCabinet.defaultDir()
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                self.tr("Select directory"), defaultDir)
        if directory:
            imp = ImportCabinet(self)
            imp.importData(directory, self.viewTab.currentModel())

    def importCoinsCollector(self):
        defaultDir = ImportCoinsCollector.defaultDir()
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                self.tr("Select directory"), defaultDir)
        if directory:
            imp = ImportCoinsCollector(self)
            imp.importData(directory, self.viewTab.currentModel())

    def importCoinManage(self):
        defaultDir = ImportCoinManage.defaultDir()
        file = QtGui.QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.mdb")
        if file:
            btn = QtGui.QMessageBox.question(self, self.tr("Importing"),
                                self.tr("Import pre-defined coins?"),
                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                QtGui.QMessageBox.Yes)
            if btn == QtGui.QMessageBox.Yes:
                imp = ImportCoinManagePredefined(self)
                res = imp.importData(file, self.viewTab.currentModel())
                if not res:
                    return

            imp = ImportCoinManage(self)
            imp.importData(file, self.viewTab.currentModel())

    def importCollectionStudio(self):
        QtGui.QMessageBox.information(self, self.tr("Importing"),
                self.tr("Before importing you should export existing "
                        "collection from Collection Studio to XML Table "
                        "(choose Collection Studio menu Tools > Export...)."))

        defaultDir = ImportCollectionStudio.defaultDir()
        file = QtGui.QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.xml")
        if file:
            imp = ImportCollectionStudio(self)
            imp.importData(file, self.viewTab.currentModel())

    def addCoin(self):
        model = self.viewTab.currentModel()
        model.addCoin(model.record(), self)

    def editCoin(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedRows()
        if len(indexes) == 1:
            listView._edit(indexes[0])
        elif len(indexes) > 1:
            listView._multiEdit(indexes)

    def deleteCoin(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedRows()
        if len(indexes):
            listView._delete(indexes)

    def viewBrowser(self):
        listView = self.viewTab.currentListView()
        listView.viewInBrowser()

    def report(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedRows()
        model = listView.model()

        records = []
        for index in indexes:
            records.append(model.record(index.row()))

        preview = PreviewDialog(model, records, self)
        preview.exec_()

    def saveTable(self):
        listView = self.viewTab.currentListView()
        listView.saveTable()

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
                self.tr("Collections (*.db)"),
                QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName:
            self.__saveParams()

            if self.collection.create(fileName):
                self.setCollection(self.collection)

    def descriptionCollectionEvent(self, checked):
        dialog = DescriptionDialog(self.collection.getDescription(), self)
        dialog.exec_()

    def passwordCollectionEvent(self, checked):
        dialog = PasswordSetDialog(self.collection, self)
        dialog.exec_()

    def backupCollectionEvent(self, checked):
        self.collection.backup()

    def vacuumCollectionEvent(self, checked):
        self.collection.vacuum()

    def openCollection(self, fileName):
        self.__saveParams()

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
        title = "%s - %s" % (collection.getCollectionName(), version.AppName)
        self.setWindowTitle(title)

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
        self.__saveParams()

        settings = QtCore.QSettings()

        if self.collection.fileName:
            self.viewTab.savePagePositions()
            # Save latest opened page
            settings.setValue('tabwindow/page', self.viewTab.currentIndex())

        # Save main window size
        settings.setValue('mainwindow/size', self.size())
        settings.setValue('mainwindow/maximized', self.isMaximized())

    def __saveParams(self):
        if self.collection.pages():
            for param in self.collection.pages().pagesParam():
                param.listParam.save()

    def about(self):
        QtGui.QMessageBox.about(self, self.tr("About %s") % version.AppName,
                self.tr("%s %s\n\n"
                        "Copyright (C) 2011-2013 Vitaly Ignatov\n\n"
                        "%s is freeware licensed under a GPLv3.") %
                        (version.AppName, version.Version, version.AppName))

    def onlineHelp(self):
        url = QtCore.QUrl(version.Web + 'wiki/MainPage')
        url.setQueryItems([('wl', Settings()['locale'])])

        executor = QtGui.QDesktopServices()
        executor.openUrl(url)

    def autoUpdate(self):
        if Settings()['updates']:
            currentDate = QtCore.QDate.currentDate()

            settings = QtCore.QSettings()
            lastUpdateDateStr = settings.value('mainwindow/last_update')
            if lastUpdateDateStr:
                lastUpdateDate = QtCore.QDate.fromString(lastUpdateDateStr,
                                                         QtCore.Qt.ISODate)
                if lastUpdateDate.addDays(10) < currentDate:
                    currentDateStr = currentDate.toString(QtCore.Qt.ISODate)
                    settings.setValue('mainwindow/last_update', currentDateStr)
                    self.checkUpdates()
            else:
                currentDateStr = currentDate.toString(QtCore.Qt.ISODate)
                settings.setValue('mainwindow/last_update', currentDateStr)
                self.checkUpdates()

    def checkUpdates(self):
        newVersion = self.__getNewVersion()
        if newVersion != version.Version:
            result = QtGui.QMessageBox.question(self, self.tr("New version"),
                        self.tr("New version is available. Download it now?"),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Yes)
            if result == QtGui.QMessageBox.Yes:
                url = QtCore.QUrl(version.Web + 'wiki/MainPage')
                url.setQueryItems([('wl', Settings()['locale'])])

                executor = QtGui.QDesktopServices()
                executor.openUrl(url)

    @waitCursorDecorator
    def __getNewVersion(self):
        import urllib.request
        from xml.dom.minidom import parseString

        newVersion = version.Version

        try:
            url = "http://wiki.open-numismat.googlecode.com/git/data/pad.xml"
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(req).read()
            xml = parseString(data)
            tag = xml.getElementsByTagName('Program_Version')[0]
            newVersion = tag.firstChild.nodeValue
        except:
            pass

        return newVersion
