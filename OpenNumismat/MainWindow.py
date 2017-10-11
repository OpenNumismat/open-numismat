import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.Description import DescriptionDialog
from OpenNumismat.Collection.Password import PasswordSetDialog
from OpenNumismat.Reference.Reference import Reference
from OpenNumismat.TabView import TabView
from OpenNumismat.Settings import Settings
from OpenNumismat.SettingsDialog import SettingsDialog
from OpenNumismat.LatestCollections import LatestCollections
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.Gui import createIcon
from OpenNumismat.Reports.Preview import PreviewDialog
from OpenNumismat import version
from OpenNumismat.Collection.Export import ExportDialog

from OpenNumismat.Collection.Import import *


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowIcon(createIcon('main.ico'))

        self.createStatusBar()
        menubar = self.menuBar()

        self.collectionActs = []

        settingsAct = QAction(createIcon('cog.png'),
                                    self.tr("Settings..."), self)
        settingsAct.triggered.connect(self.settingsEvent)
        self.collectionActs.append(settingsAct)

        cancelFilteringAct = QAction(createIcon('funnel.png'),
                                    self.tr("Clear all filters"), self)
        cancelFilteringAct.triggered.connect(self.cancelFilteringEvent)
        self.collectionActs.append(cancelFilteringAct)

        self.exitAct = QAction(createIcon('door_in.png'),
                                self.tr("E&xit"), self)
        self.exitAct.setShortcut(QKeySequence.Quit)
        self.exitAct.triggered.connect(self.close)

        newCollectionAct = QAction(self.tr("&New..."), self)
        newCollectionAct.triggered.connect(self.newCollectionEvent)

        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_DialogOpenButton)
        openCollectionAct = QAction(icon, self.tr("&Open..."), self)
        openCollectionAct.setShortcut(QKeySequence.Open)
        openCollectionAct.triggered.connect(self.openCollectionEvent)

        backupCollectionAct = QAction(
                                    createIcon('database_backup.png'),
                                    self.tr("Backup"), self)
        backupCollectionAct.triggered.connect(self.backupCollectionEvent)
        self.collectionActs.append(backupCollectionAct)

        vacuumCollectionAct = QAction(
                                    createIcon('compress.png'),
                                    self.tr("Vacuum"), self)
        vacuumCollectionAct.triggered.connect(self.vacuumCollectionEvent)
        self.collectionActs.append(vacuumCollectionAct)

        descriptionCollectionAct = QAction(self.tr("Description"), self)
        descriptionCollectionAct.triggered.connect(
                                            self.descriptionCollectionEvent)
        self.collectionActs.append(descriptionCollectionAct)

        passwordCollectionAct = QAction(createIcon('key.png'),
                                              self.tr("Set password..."), self)
        passwordCollectionAct.triggered.connect(self.passwordCollectionEvent)
        self.collectionActs.append(passwordCollectionAct)

        importMenu = QMenu(self.tr("Import"), self)
        self.collectionActs.append(importMenu)

        if ImportNumizmat.isAvailable():
            importNumizmatAct = QAction(
                                    createIcon('numizmat.ico'),
                                    self.tr("Numizmat 2.1"), self)
            importNumizmatAct.triggered.connect(self.importNumizmat)
            self.collectionActs.append(importNumizmatAct)
            importMenu.addAction(importNumizmatAct)

        if ImportCabinet.isAvailable():
            importCabinetAct = QAction(
                                    createIcon('cabinet.ico'),
                                    self.tr("Cabinet 2.2.2.1, 2013"), self)
            importCabinetAct.triggered.connect(self.importCabinet)
            self.collectionActs.append(importCabinetAct)
            importMenu.addAction(importCabinetAct)

        if ImportCoinsCollector.isAvailable():
            importCoinsCollectorAct = QAction(
                                    createIcon('CoinsCollector.ico'),
                                    self.tr("CoinsCollector 2.6"), self)
            importCoinsCollectorAct.triggered.connect(
                                                    self.importCoinsCollector)
            self.collectionActs.append(importCoinsCollectorAct)
            importMenu.addAction(importCoinsCollectorAct)

        if ImportCoinManage.isAvailable():
            importCoinManageAct = QAction(
                                    createIcon('CoinManage.ico'),
                                    self.tr("CoinManage 2011"), self)
            importCoinManageAct.triggered.connect(self.importCoinManage)
            self.collectionActs.append(importCoinManageAct)
            importMenu.addAction(importCoinManageAct)

        if ImportCollectionStudio.isAvailable():
            importCollectionStudioAct = QAction(
                                    createIcon('CollectionStudio.ico'),
                                    self.tr("Collection Studio 3.65"), self)
            importCollectionStudioAct.triggered.connect(
                                                self.importCollectionStudio)
            self.collectionActs.append(importCollectionStudioAct)
            importMenu.addAction(importCollectionStudioAct)

        if ImportNumizmatik_Ru.isAvailable():
            importNumizmaticRuAct = QAction(
                                    createIcon('Numizmatik_Ru.ico'),
                                    self.tr("Numizmatik_Ru 1.0.0.82"), self)
            importNumizmaticRuAct.triggered.connect(self.importNumizmatik_Ru)
            self.collectionActs.append(importNumizmaticRuAct)
            importMenu.addAction(importNumizmaticRuAct)

        if ImportUcoin.isAvailable():
            importUcoinAct = QAction(
                                    createIcon('ucoin.png'),
                                    self.tr("uCoin.net"), self)
            importUcoinAct.triggered.connect(self.importUcoin)
            self.collectionActs.append(importUcoinAct)
            importMenu.addAction(importUcoinAct)

        if ImportTellico.isAvailable():
            importTellicoAct = QAction(
                                    createIcon('tellico.png'),
                                    self.tr("Tellico"), self)
            importTellicoAct.triggered.connect(self.importTellico)
            self.collectionActs.append(importTellicoAct)
            importMenu.addAction(importTellicoAct)
 
        mergeCollectionAct = QAction(self.tr("Add from another..."), self)
        mergeCollectionAct.triggered.connect(self.mergeCollectionEvent)
        self.collectionActs.append(mergeCollectionAct)


        exportMenu = QMenu(self.tr("Export"), self)
        self.collectionActs.append(exportMenu)

        exportMobileAct = QAction(self.tr("For Android version"), self)
        exportMobileAct.triggered.connect(self.exportMobile)
        self.collectionActs.append(exportMobileAct)
        exportMenu.addAction(exportMobileAct)

        file = menubar.addMenu(self.tr("&File"))

        file.addAction(newCollectionAct)
        file.addAction(openCollectionAct)
        file.addSeparator()
        file.addAction(backupCollectionAct)
        file.addAction(vacuumCollectionAct)
        file.addAction(passwordCollectionAct)
        file.addAction(descriptionCollectionAct)
        file.addSeparator()
        file.addMenu(importMenu)
        file.addAction(mergeCollectionAct)
        file.addSeparator()
        file.addMenu(exportMenu)
        file.addSeparator()

        self.latestActions = []
        self.__updateLatest(file)

        file.addAction(settingsAct)
        file.addSeparator()

        file.addAction(self.exitAct)

        addCoinAct = QAction(createIcon('add.png'),
                                   self.tr("Add"), self)
        addCoinAct.setShortcut('Insert')
        addCoinAct.triggered.connect(self.addCoin)
        self.collectionActs.append(addCoinAct)

        editCoinAct = QAction(createIcon('pencil.png'),
                                   self.tr("Edit..."), self)
        editCoinAct.triggered.connect(self.editCoin)
        self.collectionActs.append(editCoinAct)

        style = QApplication.style()
        icon = style.standardIcon(QStyle.SP_TrashIcon)
        deleteCoinAct = QAction(icon,
                                   self.tr("Delete"), self)
        deleteCoinAct.setShortcut(QKeySequence.Delete)
        deleteCoinAct.triggered.connect(self.deleteCoin)
        self.collectionActs.append(deleteCoinAct)

        copyCoinAct = QAction(createIcon('page_copy.png'),
                                   self.tr("Copy"), self)
        copyCoinAct.setShortcut(QKeySequence.Copy)
        copyCoinAct.triggered.connect(self.copyCoin)
        self.collectionActs.append(copyCoinAct)

        pasteCoinAct = QAction(createIcon('page_paste.png'),
                                   self.tr("Paste"), self)
        pasteCoinAct.setShortcut(QKeySequence.Paste)
        pasteCoinAct.triggered.connect(self.pasteCoin)
        self.collectionActs.append(pasteCoinAct)

        coin = menubar.addMenu(self.tr("Coin"))
        self.collectionActs.append(coin)
        coin.addAction(addCoinAct)
        coin.addAction(editCoinAct)
        coin.addSeparator()
        coin.addAction(copyCoinAct)
        coin.addAction(pasteCoinAct)
        coin.addSeparator()
        coin.addAction(deleteCoinAct)

        viewBrowserAct = QAction(createIcon('page_white_world.png'),
                                   self.tr("View in browser"), self)
        viewBrowserAct.triggered.connect(self.viewBrowser)
        self.collectionActs.append(viewBrowserAct)

        self.viewTab = TabView(self)

        actions = self.viewTab.actions()
        listMenu = menubar.addMenu(self.tr("List"))
        self.collectionActs.append(listMenu)
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
        self.collectionActs.append(self.referenceMenu)

        reportAct = QAction(self.tr("Report..."), self)
        reportAct.setShortcut(Qt.CTRL + Qt.Key_P)
        reportAct.triggered.connect(self.report)
        self.collectionActs.append(reportAct)

        saveTableAct = QAction(createIcon('table.png'),
                                     self.tr("Save current list..."), self)
        saveTableAct.triggered.connect(self.saveTable)
        self.collectionActs.append(saveTableAct)

        report = menubar.addMenu(self.tr("Report"))
        self.collectionActs.append(report)
        report.addAction(reportAct)
        report.addAction(saveTableAct)
        report.addAction(viewBrowserAct)

        helpAct = QAction(createIcon('help.png'),
                                self.tr("Online help"), self)
        helpAct.setShortcut(QKeySequence.HelpContents)
        helpAct.triggered.connect(self.onlineHelp)
        checkUpdatesAct = QAction(self.tr("Check for updates"), self)
        checkUpdatesAct.triggered.connect(self.manualUpdate)
        aboutAct = QAction(self.tr("About %s") % version.AppName, self)
        aboutAct.triggered.connect(self.about)

        help_ = menubar.addMenu(self.tr("&Help"))
        help_.addAction(helpAct)
        help_.addSeparator()
        help_.addAction(checkUpdatesAct)
        help_.addSeparator()
        help_.addAction(aboutAct)

        toolBar = QToolBar(self.tr("Toolbar"), self)
        toolBar.setMovable(False)
        toolBar.addAction(openCollectionAct)
        toolBar.addSeparator()
        toolBar.addAction(addCoinAct)
        toolBar.addAction(editCoinAct)
        toolBar.addAction(viewBrowserAct)
        toolBar.addSeparator()
        toolBar.addAction(cancelFilteringAct)
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

        settings = QSettings()
        pageIndex = settings.value('tabwindow/page')
        if pageIndex != None:
            self.viewTab.setCurrentIndex(int(pageIndex))

        if settings.value('mainwindow/maximized', False, type=bool):
            self.showMaximized()
            size = settings.value('mainwindow/maximizedsize')
        else:
            size = settings.value('mainwindow/size')

        if size:
            self.resize(size)

        self.autoUpdate()

    def createStatusBar(self):
        self.collectionFileLabel = QLabel()
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
            self.__menu.insertAction(self.exitAct, act)
        self.__menu.insertSeparator(self.exitAct)

    def cancelFilteringEvent(self):
        listView = self.viewTab.currentListView()
        listView.clearAllFilters()

    def settingsEvent(self):
        dialog = SettingsDialog(self.collection, self)
        res = dialog.exec_()
        if res == QDialog.Accepted:
            result = QMessageBox.question(self, self.tr("Settings"),
                        self.tr("The application will need to restart to apply "
                                "the new settings. Restart it now?"),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes)
            if result == QMessageBox.Yes:
                self.restart()

    def restart(self):
        self.close()
        program = sys.executable
        argv = []
        if program != sys.argv[0]:
            # Process running as Python arg
            argv.append(sys.argv[0])
        QProcess.startDetached(program, argv)

    def importNumizmat(self):
        defaultDir = ImportNumizmat.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.fdb")
        if file:
            imp = ImportNumizmat(self)
            imp.importData(file, self.viewTab.currentModel())

    def importCabinet(self):
        QMessageBox.information(self, self.tr("Importing"),
                self.tr("Before importing you should export existing "
                        "collection from Cabinet."))

        defaultDir = ImportCabinet.defaultDir()
        directory = QFileDialog.getExistingDirectory(self,
                                self.tr("Select directory"), defaultDir)
        if directory:
            imp = ImportCabinet(self)
            imp.importData(directory, self.viewTab.currentModel())

    def importCoinsCollector(self):
        defaultDir = ImportCoinsCollector.defaultDir()
        directory = QFileDialog.getExistingDirectory(self,
                                self.tr("Select directory"), defaultDir)
        if directory:
            imp = ImportCoinsCollector(self)
            imp.importData(directory, self.viewTab.currentModel())

    def importCoinManage(self):
        defaultDir = ImportCoinManage.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.mdb")
        if file:
            btn = QMessageBox.question(self, self.tr("Importing"),
                                self.tr("Import pre-defined coins?"),
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes)
            if btn == QMessageBox.Yes:
                imp = ImportCoinManagePredefined(self)
                res = imp.importData(file, self.viewTab.currentModel())
                if not res:
                    return

            imp = ImportCoinManage(self)
            imp.importData(file, self.viewTab.currentModel())

    def importCollectionStudio(self):
        QMessageBox.information(self, self.tr("Importing"),
                self.tr("Before importing you should export existing "
                        "collection from Collection Studio to XML Table "
                        "(choose Collection Studio menu Tools > Export...)."))

        defaultDir = ImportCollectionStudio.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.xml")
        if file:
            imp = ImportCollectionStudio(self)
            imp.importData(file, self.viewTab.currentModel())

    def importNumizmatik_Ru(self):
        defaultDir = ImportNumizmatik_Ru.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.mdb")
        if file:
            btn = QMessageBox.question(self, self.tr("Importing"),
                                self.tr("Import club catalog?"),
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.Yes)
            if btn == QMessageBox.Yes:
                imp = ImportNumizmatik_RuPredefined(self)
                res = imp.importData(file, self.viewTab.currentModel())
                if not res:
                    return

            imp = ImportNumizmatik_Ru(self)
            imp.importData(file, self.viewTab.currentModel())

    def importUcoin(self):
        QMessageBox.information(self, self.tr("Importing"),
                self.tr("Before importing you should export existing "
                        "collection from uCoin.net to Comma-Separated (CSV) "
                        "format."))

        defaultDir = ImportUcoin.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.csv")
        if file:
            imp = ImportUcoin(self)
            imp.importData(file, self.viewTab.currentModel())

    def importTellico(self):
        defaultDir = ImportTellico.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), defaultDir, "*.tc")
        if file:
            imp = ImportTellico(self)
            imp.importData(file, self.viewTab.currentModel())
 
    def exportMobile(self):
        dialog = ExportDialog(self.collection, self)
        res = dialog.exec_()
        if res == QDialog.Accepted:
            self.collection.exportToMobile(dialog.params)

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

    def copyCoin(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedRows()
        if len(indexes):
            listView._copy(indexes)

    def pasteCoin(self):
        listView = self.viewTab.currentListView()
        listView._paste()

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
        return QFileInfo(fileName).absolutePath()

    def openCollectionEvent(self):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                self.tr("Open collection"), self.__workingDir(),
                self.tr("Collections (*.db)"))
        if fileName:
            self.openCollection(fileName)

    def newCollectionEvent(self):
        fileName, _selectedFilter = QFileDialog.getSaveFileName(self,
                self.tr("New collection"), self.__workingDir(),
                self.tr("Collections (*.db)"), "",
                QFileDialog.DontConfirmOverwrite)
        if fileName:
            self.__closeCollection()
            if self.collection.create(fileName):
                self.setCollection(self.collection)

    def descriptionCollectionEvent(self, checked):
        dialog = DescriptionDialog(self.collection.getDescription(), self)
        dialog.exec_()

    def passwordCollectionEvent(self, checked):
        dialog = PasswordSetDialog(self.collection.settings, self)
        dialog.exec_()

    def backupCollectionEvent(self, checked):
        self.collection.backup()

    def vacuumCollectionEvent(self, checked):
        self.collection.vacuum()

    def mergeCollectionEvent(self, checked):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                self.tr("Open collection"), self.__workingDir(),
                self.tr("Collections (*.db)"))
        if fileName:
            self.collection.merge(fileName)

    def openCollection(self, fileName):
        self.__closeCollection()
        if self.collection.open(fileName):
            self.setCollection(self.collection)
        else:
            # Remove wrong collection from latest collections list
            latest = LatestCollections(self)
            latest.delete(fileName)
            self.__updateLatest()

    @waitCursorDecorator
    def setCollection(self, collection):
        self.__setEnabledActs(True)

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

    def __setEnabledActs(self, enabled):
        for act in self.collectionActs:
            act.setEnabled(enabled)

    def __closeCollection(self):
        self.__saveParams()

        self.__setEnabledActs(False)
        self.viewTab.clear()

        self.referenceMenu.clear()

        self.collectionFileLabel.setText(
                self.tr("Create new collection or open one of the existing"))

        self.setWindowTitle(version.AppName)

    def closeEvent(self, e):
        self.__shutDown()

    def __shutDown(self):
        self.__saveParams()

        settings = QSettings()

        if self.collection.fileName:
            # Save latest opened page
            settings.setValue('tabwindow/page', self.viewTab.currentIndex())

        # Save main window size
        settings.setValue('mainwindow/maximized', self.isMaximized())
        if self.isMaximized():
            settings.setValue('mainwindow/maximizedsize', self.size())
        else:
            settings.setValue('mainwindow/size', self.size())

    def __saveParams(self):
        if self.collection.pages():
            for param in self.collection.pages().pagesParam():
                param.listParam.save_lists(only_if_changed=True)

            self.viewTab.savePagePositions(only_if_changed=True)

    def about(self):
        QMessageBox.about(self, self.tr("About %s") % version.AppName,
                self.tr("%s %s\n\n"
                        "Copyright (C) 2011-2017 Vitaly Ignatov\n\n"
                        "%s is freeware licensed under a GPLv3.") %
                        (version.AppName, version.Version, version.AppName))

    def onlineHelp(self):
        url = QUrl(version.Web)

        executor = QDesktopServices()
        executor.openUrl(url)

    def autoUpdate(self):
        if Settings()['updates']:
            currentDate = QDate.currentDate()

            settings = QSettings()
            lastUpdateDateStr = settings.value('mainwindow/last_update')
            if lastUpdateDateStr:
                lastUpdateDate = QDate.fromString(lastUpdateDateStr,
                                                         Qt.ISODate)
                if lastUpdateDate.addDays(10) < currentDate:
                    self.checkUpdates()
            else:
                self.checkUpdates()

    def manualUpdate(self):
        if not self.checkUpdates():
            QMessageBox.information(self, self.tr("Updates"),
                    self.tr("You already have the latest version."))

    def checkUpdates(self):
        currentDate = QDate.currentDate()
        currentDateStr = currentDate.toString(Qt.ISODate)
        settings = QSettings()
        settings.setValue('mainwindow/last_update', currentDateStr)

        newVersion = self.__getNewVersion()
        if newVersion and newVersion != version.Version:
            result = QMessageBox.question(self, self.tr("New version"),
                        self.tr("New version is available. Download it now?"),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes)
            if result == QMessageBox.Yes:
                url = QUrl(version.Web)

                executor = QDesktopServices()
                executor.openUrl(url)

            return True
        else:
            return False

    @waitCursorDecorator
    def __getNewVersion(self):
        import urllib.request
        from xml.dom.minidom import parseString

        newVersion = version.Version

        try:
            url = "http://opennumismat.github.io/data/pad.xml"
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(req).read()
            xml = parseString(data)
            tag = xml.getElementsByTagName('Program_Version')[0]
            newVersion = tag.firstChild.nodeValue
        except:
            return None

        return newVersion
