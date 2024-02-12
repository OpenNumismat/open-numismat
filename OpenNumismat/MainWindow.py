from datetime import datetime
import sys
import urllib.request

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from OpenNumismat.Collection.Collection import Collection
from OpenNumismat.Collection.Description import DescriptionDialog
from OpenNumismat.Collection.Password import PasswordSetDialog
from OpenNumismat.Reports import Report
from OpenNumismat.TabView import TabView
from OpenNumismat.Settings import Settings
from OpenNumismat.SettingsDialog import SettingsDialog
from OpenNumismat.LatestCollections import LatestCollections
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Tools.misc import versiontuple
from OpenNumismat import version
from OpenNumismat.Collection.Export import ExportDialog
from OpenNumismat.FindDialog import FindDialog
from OpenNumismat.SummaryDialog import SummaryDialog
from OpenNumismat.Collection.Import.Colnect import ColnectDialog, colnectAvailable
from OpenNumismat.Collection.Import.Ans import AnsDialog, ansAvailable
from OpenNumismat.Collection.CollectionPages import CollectionPageTypes
from OpenNumismat.TagsDialog import TagsDialog
from OpenNumismat.EditCoinDialog.YearCalculator import YearCalculatorDialog

from OpenNumismat.Collection.Import import *


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setWindowIcon(QIcon(':/main.ico'))

        self.createStatusBar()
        menubar = self.menuBar()

        self.collectionActs = []

        self.tableViewAct = QAction(QIcon(':/application_view_list.png'),
                                    self.tr("Table view"), self)
        self.tableViewAct.setData(CollectionPageTypes.List)
        self.tableViewAct.triggered.connect(self.changeViewEvent)
        self.collectionActs.append(self.tableViewAct)

        self.iconViewAct = QAction(QIcon(':/application_view_icons.png'),
                                   self.tr("Icon view"), self)
        self.iconViewAct.setData(CollectionPageTypes.Icon)
        self.iconViewAct.triggered.connect(self.changeViewEvent)
        self.collectionActs.append(self.iconViewAct)

        self.cardViewAct = QAction(QIcon(':/application_view_tile.png'),
                                   self.tr("Card view"), self)
        self.cardViewAct.setData(CollectionPageTypes.Card)
        self.cardViewAct.triggered.connect(self.changeViewEvent)
        self.collectionActs.append(self.cardViewAct)

        viewMenu = QMenu(self.tr("Change view"), self)
        viewMenu.addAction(self.tableViewAct)
        viewMenu.addAction(self.iconViewAct)
        viewMenu.addAction(self.cardViewAct)

        self.viewButton = QToolButton()
        self.viewButton.setPopupMode(QToolButton.InstantPopup)
        self.viewButton.setMenu(viewMenu)
        self.viewButton.setDefaultAction(self.tableViewAct)

        findAct = QAction(QIcon(':/SimilarImageFinder.png'),
                          self.tr("Search by image..."), self)
        findAct.triggered.connect(self.findEvent)
        self.collectionActs.append(findAct)

        colnectAct = QAction(QIcon(':/colnect.png'),
                             "Colnect", self)
        colnectAct.triggered.connect(self.colnectEvent)
        self.collectionActs.append(colnectAct)

        ansAct = QAction(QIcon(':/ans.png'),
                              "American Numismatic Society", self)
        ansAct.triggered.connect(self.ansEvent)
        self.collectionActs.append(ansAct)

        self.detailsAct = QAction(QIcon(':/application-form.png'),
                                  self.tr("Info panel"), self)
        self.detailsAct.setCheckable(True)
        self.detailsAct.triggered.connect(self.detailsEvent)
        self.collectionActs.append(self.detailsAct)

        self.statisticsAct = QAction(QIcon(':/chart-bar.png'),
                                     self.tr("Statistics"), self)
        self.statisticsAct.setCheckable(True)
        self.statisticsAct.triggered.connect(self.statisticsEvent)
        self.collectionActs.append(self.statisticsAct)

        self.mapAct = QAction(QIcon(':/world.png'),
                              self.tr("Map"), self)
        self.mapAct.setCheckable(True)
        self.mapAct.triggered.connect(self.mapEvent)
        self.collectionActs.append(self.mapAct)

        summaryAct = QAction(self.tr("Summary"), self)
        summaryAct.triggered.connect(self.summaryEvent)
        self.collectionActs.append(summaryAct)

        settingsAct = QAction(QIcon(':/cog.png'),
                              self.tr("Settings..."), self)
        settingsAct.triggered.connect(self.settingsEvent)

        self.enableDragAct = QAction(QIcon(':/arrow_switch.png'),
                                     self.tr("Sort by drag-n-drop mode"), self)
        self.enableDragAct.setCheckable(True)
        self.enableDragAct.triggered.connect(self.enableDragEvent)
        self.collectionActs.append(self.enableDragAct)

        self.exitAct = QAction(QIcon(':/door_in.png'),
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
                                    QIcon(':/database_backup.png'),
                                    self.tr("Backup"), self)
        backupCollectionAct.triggered.connect(self.backupCollectionEvent)
        self.collectionActs.append(backupCollectionAct)

        vacuumCollectionAct = QAction(
                                    QIcon(':/compress.png'),
                                    self.tr("Vacuum"), self)
        vacuumCollectionAct.triggered.connect(self.vacuumCollectionEvent)
        self.collectionActs.append(vacuumCollectionAct)

        descriptionCollectionAct = QAction(self.tr("Description"), self)
        descriptionCollectionAct.triggered.connect(
                                            self.descriptionCollectionEvent)
        self.collectionActs.append(descriptionCollectionAct)

        passwordCollectionAct = QAction(QIcon(':/key.png'),
                                        self.tr("Set password..."), self)
        passwordCollectionAct.triggered.connect(self.passwordCollectionEvent)
        self.collectionActs.append(passwordCollectionAct)

        importMenu = QMenu(self.tr("Import"), self)
        self.collectionActs.append(importMenu)

        if ImportExcel.isAvailable():
            importExcelAct = QAction(
                                    QIcon(':/excel.png'),
                                    "Excel", self)
            importExcelAct.triggered.connect(self.importExcel)
            self.collectionActs.append(importExcelAct)
            importMenu.addAction(importExcelAct)

        if ImportColnect.isAvailable():
            importColnectAct = QAction(
                                    QIcon(':/colnect.png'),
                                    "Colnect", self)
            importColnectAct.triggered.connect(self.importColnect)
            self.collectionActs.append(importColnectAct)
            importMenu.addAction(importColnectAct)

        if ImportNumista.isAvailable():
            importNumistaAct = QAction(
                                    QIcon(':/numista.png'),
                                    "Numista", self)
            importNumistaAct.triggered.connect(self.importNumista)
            self.collectionActs.append(importNumistaAct)
            importMenu.addAction(importNumistaAct)

        if ImportCoinManage.isAvailable():
            importCoinManageAct = QAction(
                                    QIcon(':/CoinManage.png'),
                                    "CoinManage 2021", self)
            importCoinManageAct.triggered.connect(self.importCoinManage)
            self.collectionActs.append(importCoinManageAct)
            importMenu.addAction(importCoinManageAct)

        if ImportCollectionStudio.isAvailable():
            importCollectionStudioAct = QAction(
                                    QIcon(':/CollectionStudio.png'),
                                    "Collection Studio 3.65", self)
            importCollectionStudioAct.triggered.connect(
                                                self.importCollectionStudio)
            self.collectionActs.append(importCollectionStudioAct)
            importMenu.addAction(importCollectionStudioAct)

        if ImportUcoin2.isAvailable():
            importUcoinAct = QAction(
                                    QIcon(':/ucoin.png'),
                                    "uCoin.net", self)
            importUcoinAct.triggered.connect(self.importUcoin2)
            self.collectionActs.append(importUcoinAct)
            importMenu.addAction(importUcoinAct)
        elif ImportUcoin.isAvailable():
            importUcoinAct = QAction(
                                    QIcon(':/ucoin.png'),
                                    "uCoin.net", self)
            importUcoinAct.triggered.connect(self.importUcoin)
            self.collectionActs.append(importUcoinAct)
            importMenu.addAction(importUcoinAct)

        if ImportTellico.isAvailable():
            importTellicoAct = QAction(
                                    QIcon(':/tellico.png'),
                                    "Tellico", self)
            importTellicoAct.triggered.connect(self.importTellico)
            self.collectionActs.append(importTellicoAct)
            importMenu.addAction(importTellicoAct)

        mergeCollectionAct = QAction(
                                    QIcon(':/refresh.png'),
                                    self.tr("Synchronize..."), self)
        mergeCollectionAct.triggered.connect(self.mergeCollectionEvent)
        self.collectionActs.append(mergeCollectionAct)

        exportMenu = QMenu(self.tr("Export"), self)
        self.collectionActs.append(exportMenu)

        exportMobileAct = QAction(self.tr("For Android version"), self)
        exportMobileAct.triggered.connect(self.exportMobile)
        self.collectionActs.append(exportMobileAct)
        exportMenu.addAction(exportMobileAct)

        exportJsonAct = QAction(QIcon(':/json.png'), "JSON", self)
        exportJsonAct.triggered.connect(self.exportJson)
        self.collectionActs.append(exportJsonAct)
        exportMenu.addAction(exportJsonAct)

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

        addCoinAct = QAction(QIcon(':/add.png'),
                             self.tr("Add"), self)
        addCoinAct.setShortcut(Qt.Key_Insert)
        addCoinAct.triggered.connect(self.addCoin)
        self.collectionActs.append(addCoinAct)

        editCoinAct = QAction(QIcon(':/pencil.png'),
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

        copyCoinAct = QAction(QIcon(':/page_copy.png'),
                              self.tr("Copy"), self)
        copyCoinAct.setShortcut(QKeySequence.Copy)
        copyCoinAct.triggered.connect(self.copyCoin)
        self.collectionActs.append(copyCoinAct)

        pasteCoinAct = QAction(QIcon(':/page_paste.png'),
                               self.tr("Paste"), self)
        pasteCoinAct.setShortcut(QKeySequence.Paste)
        pasteCoinAct.triggered.connect(self.pasteCoin)
        self.collectionActs.append(pasteCoinAct)

        record = menubar.addMenu(self.tr("Record"))
        self.collectionActs.append(record)
        record.addAction(addCoinAct)
        record.addAction(editCoinAct)
        record.addSeparator()
        record.addAction(findAct)
        record.addSeparator()
        if colnectAvailable:
            record.addAction(colnectAct)
        if ansAvailable:
            record.addAction(ansAct)
        record.addSeparator()
        record.addAction(copyCoinAct)
        record.addAction(pasteCoinAct)
        record.addSeparator()
        record.addAction(deleteCoinAct)

        detailsMenu = QMenu(self.tr("Details"), self)
        detailsMenu.addAction(self.detailsAct)
        detailsMenu.addAction(self.statisticsAct)
        detailsMenu.addAction(self.mapAct)

        view = menubar.addMenu(self.tr("&View"))
        self.collectionActs.append(view)
        view.addMenu(detailsMenu)
        view.addMenu(viewMenu)

        viewBrowserAct = QAction(QIcon(':/page_white_world.png'),
                                 self.tr("View in browser"), self)
        viewBrowserAct.triggered.connect(self.viewBrowserEvent)
        self.collectionActs.append(viewBrowserAct)

        self.viewTab = TabView(self)

        actions = self.viewTab.actions()
        listMenu = menubar.addMenu(self.tr("List"))
        listMenu.addAction(actions['new'])
        listMenu.addMenu(actions['open'])
        listMenu.aboutToShow.connect(self.viewTab.updateOpenPageMenu)
        listMenu.addAction(actions['rename'])
        listMenu.addSeparator()
        listMenu.addAction(actions['select'])
        listMenu.addAction(actions['customize_tree'])
        listMenu.addSeparator()
        listMenu.addAction(actions['cancel_filtering'])
        self.collectionActs.append(actions['cancel_filtering'])
        listMenu.addAction(actions['cancel_sorting'])
        self.collectionActs.append(actions['cancel_sorting'])
        listMenu.addAction(actions['save_sorting'])
        self.collectionActs.append(actions['save_sorting'])
        listMenu.addSeparator()
        listMenu.addAction(actions['close'])
        listMenu.addAction(actions['remove'])
        self.collectionActs.append(listMenu)

        self.referenceMenu = menubar.addMenu(self.tr("Reference"))
        self.collectionActs.append(self.referenceMenu)

        self.tagsAct = QAction(self.tr("Tags..."), self)
        self.tagsAct.triggered.connect(self.tagsEvent)

        reportAct = QAction(self.tr("Report..."), self)
        reportAct.setShortcut(QKeySequence.Print)
        reportAct.triggered.connect(self.report)
        self.collectionActs.append(reportAct)

        saveTableAct = QAction(QIcon(':/table.png'),
                               self.tr("Save current list..."), self)
        saveTableAct.triggered.connect(self.saveTable)
        self.collectionActs.append(saveTableAct)

        report = menubar.addMenu(self.tr("Report"))
        self.collectionActs.append(report)
        report.addAction(reportAct)
        report.addAction(saveTableAct)
        default_template = Settings()['template']
        viewBrowserMenu = report.addMenu(QIcon(':/page_white_world.png'),
                                         self.tr("View in browser"))
        for template in Report.scanTemplates():
            act = QAction(template[0], self)
            act.setData(template[1])
            act.triggered.connect(self.viewBrowserEvent)
            viewBrowserMenu.addAction(act)
            if default_template == template[1]:
                viewBrowserMenu.setDefaultAction(act)
        self.collectionActs.append(exportMenu)
        report.addSeparator()
        report.addAction(summaryAct)

        yearCalculatorAct = QAction(self.tr("Year calculator"), self)
        yearCalculatorAct.triggered.connect(self.yearCalculator)
        referencesGeneratorAct = QAction(self.tr("References generator"), self)
        referencesGeneratorAct.triggered.connect(self.referencesGenerator)

        tools = menubar.addMenu(self.tr("Tools"))
        tools.addAction(yearCalculatorAct)
        tools.addAction(referencesGeneratorAct)

        helpAct = QAction(QIcon(':/help.png'),
                          self.tr("User manual"), self)
        helpAct.setShortcut(QKeySequence.HelpContents)
        helpAct.triggered.connect(self.onlineHelp)
        webAct = QAction(self.tr("Visit web-site"), self)
        webAct.triggered.connect(self.visitWeb)
        checkUpdatesAct = QAction(self.tr("Check for updates"), self)
        checkUpdatesAct.triggered.connect(self.manualUpdate)
        aboutAct = QAction(self.tr("About %s") % version.AppName, self)
        aboutAct.triggered.connect(self.about)

        help_ = menubar.addMenu(self.tr("&Help"))
        help_.addAction(helpAct)
        help_.addAction(webAct)
        help_.addSeparator()
        help_.addAction(checkUpdatesAct)
        help_.addSeparator()
        help_.addAction(aboutAct)

        toolBar = QToolBar(self.tr("Toolbar"), self)
        toolBar.setObjectName("Toolbar")
        toolBar.setMovable(False)
        toolBar.addAction(openCollectionAct)
        toolBar.addSeparator()
        toolBar.addAction(addCoinAct)
        toolBar.addAction(editCoinAct)
        toolBar.addAction(viewBrowserAct)
        toolBar.addSeparator()
        toolBar.addAction(actions['cancel_filtering'])
        toolBar.addAction(actions['cancel_sorting'])
        toolBar.addAction(actions['save_sorting'])
        toolBar.addAction(self.enableDragAct)
        toolBar.addSeparator()
        toolBar.addAction(findAct)
        toolBar.addSeparator()
        toolBar.addAction(settingsAct)
        toolBar.addSeparator()
        toolBar.addAction(self.detailsAct)
        toolBar.addAction(self.statisticsAct)
        toolBar.addAction(self.mapAct)
        if colnectAvailable or ansAvailable:
            toolBar.addSeparator()
        if colnectAvailable:
            toolBar.addAction(colnectAct)
        if ansAvailable:
            toolBar.addAction(ansAct)
        toolBar.addSeparator()
        toolBar.addWidget(self.viewButton)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolBar.addWidget(spacer)

        self.quickSearch = QLineEdit()
        self.quickSearch.setMaximumWidth(250)
        self.quickSearch.setClearButtonEnabled(True)
        self.quickSearch.setPlaceholderText(self.tr("Quick search"))
        self.quickSearch.textEdited.connect(self.quickSearchEdited)
        self.collectionActs.append(self.quickSearch)
        self.quickSearchTimer = QTimer(self)
        self.quickSearchTimer.setSingleShot(True)
        self.quickSearchTimer.timeout.connect(self.quickSearchClicked)
        toolBar.addWidget(self.quickSearch)

        self.addToolBar(toolBar)
        self.setContextMenuPolicy(Qt.NoContextMenu)

        self.setWindowTitle(version.AppName)

        if len(sys.argv) > 1:
            fileName = sys.argv[1]
        else:
            latest = LatestCollections(self)
            fileName = latest.latest()

        self.collection = Collection(self)
        self.openCollection(fileName)

        self.setCentralWidget(self.viewTab)

        settings = QSettings()
        pageIndex = settings.value('tabwindow/page', 0)
        if pageIndex is not None:
            self.viewTab.setCurrentIndex(int(pageIndex))

        geometry = settings.value('mainwindow/geometry')
        if geometry:
            self.restoreGeometry(geometry)
        winState = settings.value('mainwindow/winState')
        if winState:
            self.restoreState(winState)

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
            act.triggered.connect(self.openLatestCollectionEvent)
            self.__menu.insertAction(self.exitAct, act)
        self.__menu.insertSeparator(self.exitAct)

    def enableDragEvent(self):
        listView = self.viewTab.currentListView()
        if self.enableDragAct.isChecked():
            res = listView.tryDragMode()
            self.enableDragAct.setChecked(res)
        else:
            self.enableDragAct.setChecked(False)
            listView.selectMode()

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

    def changeViewEvent(self):
        type_ = self.sender().data()
        page = self.viewTab.currentPageView().param
        self.viewTab.collection.pages().changeView(page, type_)

        self.viewTab.clearStatusBar()
        page = self.viewTab.currentPageView()
        page.changeView(type_)
        self.viewTab.updatePage(page)

    def findEvent(self):
        model = self.viewTab.currentModel()
        dialog = FindDialog(model, self)
        dialog.exec_()

    def colnectEvent(self):
        model = self.viewTab.currentModel()
        dialog = ColnectDialog(model, self)
        dialog.exec_()

    def ansEvent(self):
        model = self.viewTab.currentModel()
        dialog = AnsDialog(model, self)
        dialog.exec_()

    def updateInfoType(self, info_type):
        self.detailsAct.setChecked(False)
        self.statisticsAct.setChecked(False)
        self.mapAct.setChecked(False)

        if info_type == CollectionPageTypes.Statistics:
            self.statisticsAct.setChecked(True)
        elif info_type == CollectionPageTypes.Map:
            self.mapAct.setChecked(True)
        else:
            self.detailsAct.setChecked(True)

    def detailsEvent(self, checked):
        self.updateInfoType(CollectionPageTypes.Details)
        if checked:
            page = self.viewTab.currentPageView()
            self.collection.pages().changeInfoType(page.param,
                                                   CollectionPageTypes.Details)
            page.showInfo(CollectionPageTypes.Details)

    def statisticsEvent(self, checked):
        self.updateInfoType(CollectionPageTypes.Statistics)
        if checked:
            page = self.viewTab.currentPageView()
            self.collection.pages().changeInfoType(page.param,
                                                   CollectionPageTypes.Statistics)
            page.showInfo(CollectionPageTypes.Statistics)

    def mapEvent(self, checked):
        self.updateInfoType(CollectionPageTypes.Map)
        if checked:
            page = self.viewTab.currentPageView()
            self.collection.pages().changeInfoType(page.param,
                                                   CollectionPageTypes.Map)
            page.showInfo(CollectionPageTypes.Map)

    def summaryEvent(self):
        model = self.viewTab.currentModel()
        dialog = SummaryDialog(model, self)
        dialog.exec_()

    def tagsEvent(self):
        model = self.viewTab.currentModel()
        dialog = TagsDialog(model.database(), self)
        res = dialog.exec_()
        if res == QDialog.Accepted:
            model.tagsChanged.emit()

    def restart(self):
        self.close()
        program = sys.executable
        argv = []
        if "__compiled__" in globals():
            # Process running as Nuitka
            program = sys.argv[0]
        elif program != sys.argv[0] and "__compiled__" not in globals():
            # Process running as Python arg
            argv.append(sys.argv[0])
        QProcess.startDetached(program, argv)

    def importCoinManage(self):
        defaultDir = ImportCoinManage.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(self,
                                self.tr("Select file"), defaultDir, "*.mdb")
        if file:
            imp = ImportCoinManage(self)
            res = imp.importData(file, self.viewTab.currentModel())
            if not res:
                return

            btn = QMessageBox.question(self, self.tr("Importing"),
                                self.tr("Import pre-defined coins?"),
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No)
            if btn == QMessageBox.Yes:
                imp = ImportCoinManagePredefined(self)
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

    def importUcoin(self):
        QMessageBox.information(
            self, self.tr("Importing"),
            self.tr("Before importing you should export existing "
                    "collection from uCoin.net to Comma-Separated (CSV) "
                    "format."))

        defaultDir = ImportUcoin.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), defaultDir,
            "Comma-Separated (*.csv)")
        if file:
            imp = ImportUcoin(self)
            imp.importData(file, self.viewTab.currentModel())

    def importUcoin2(self):
        QMessageBox.information(
            self, self.tr("Importing"),
            self.tr("Before importing you should export existing "
                    "collection from uCoin.net to Microsoft Excel (XLS) or "
                    "Comma-Separated (CSV) format."))

        defaultDir = ImportUcoin.defaultDir()
        file, selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), defaultDir,
            "Microsoft Excel (*.xlsx);;Comma-Separated (*.csv)")
        if file:
            if selectedFilter == "Microsoft Excel (*.xlsx)":
                imp = ImportUcoin2(self)
                imp.importData(file, self.viewTab.currentModel())
            else:
                imp = ImportUcoin(self)
                imp.importData(file, self.viewTab.currentModel())

    def importTellico(self):
        defaultDir = ImportTellico.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), defaultDir, "*.tc")
        if file:
            imp = ImportTellico(self)
            imp.importData(file, self.viewTab.currentModel())

    def importExcel(self):
        defaultDir = ImportExcel.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), defaultDir, "*.xlsx")
        if file:
            imp = ImportExcel(self)
            imp.importData(file, self.viewTab.currentModel())

    def importColnect(self):
        defaultDir = ImportColnect.defaultDir()
        file, _selectedFilter = QFileDialog.getOpenFileName(
            self, self.tr("Select file"), defaultDir, "*.csv")
        if file:
            imp = ImportColnect(self)
            imp.importData(file, self.viewTab.currentModel())

    def importNumista(self):
        imp = ImportNumista(self)
        imp.importData('Numista', self.viewTab.currentModel())

    def exportMobile(self):
        dialog = ExportDialog(self.collection, self)
        res = dialog.exec_()
        if res == QDialog.Accepted:
            self.collection.exportToMobile(dialog.params)

    def exportJson(self):
        self.collection.exportToJson()

    def addCoin(self):
        model = self.viewTab.currentModel()
        model.addCoin(model.record(), self)

    def editCoin(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedCoins()
        if len(indexes) == 1:
            listView._edit(indexes[0])
        elif len(indexes) > 1:
            listView._multiEdit(indexes)

    def deleteCoin(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedCoins()
        if len(indexes):
            listView._delete(indexes)

    def copyCoin(self):
        listView = self.viewTab.currentListView()
        indexes = listView.selectedCoins()
        if len(indexes):
            listView._copy(indexes)

    def pasteCoin(self):
        listView = self.viewTab.currentListView()
        listView._paste()

    def quickSearchEdited(self, _text):
        self.quickSearchTimer.start(180)

    def quickSearchClicked(self):
        listView = self.viewTab.currentListView()
        listView.search(self.quickSearch.text())

    def viewBrowserEvent(self):
        template = self.sender().data()
        listView = self.viewTab.currentListView()
        listView.viewInBrowser(template)

    def report(self):
        listView = self.viewTab.currentListView()
        listView.report()

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

    def descriptionCollectionEvent(self):
        dialog = DescriptionDialog(self.collection.getDescription(), self)
        dialog.exec_()

    def passwordCollectionEvent(self):
        dialog = PasswordSetDialog(self.collection.settings, self)
        dialog.exec_()

    def backupCollectionEvent(self):
        self.collection.backup()

    def vacuumCollectionEvent(self):
        # Fetch all List models before vacuum
        for i in range(self.viewTab.count()):
            listView = self.viewTab.widget(i)
            listView.modelChanged()

        self.collection.vacuum()

    def mergeCollectionEvent(self):
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

    def openLatestCollectionEvent(self):
        fileName = self.sender().data()
        self.openCollection(fileName)

    @waitCursorDecorator
    def setCollection(self, collection):
        self.collection.loadReference(Settings()['reference'])

        self.__setEnabledActs(True)

        self.collectionFileLabel.setText(collection.getFileName())
        title = "%s - %s" % (collection.getCollectionName(), version.AppName)
        self.setWindowTitle(title)

        latest = LatestCollections(self)
        latest.add(collection.getFileName())
        self.__updateLatest()

        self.viewTab.setCollection(collection)

        self.referenceMenu.clear()

        if collection.settings['tags_used']:
            self.referenceMenu.addAction(self.tagsAct)
            self.referenceMenu.addSeparator()

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
        self.quickSearch.clear()

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
        settings.setValue('mainwindow/geometry', self.saveGeometry())
        settings.setValue('mainwindow/winState', self.saveState())

    def __saveParams(self):
        if self.collection.isOpen():
            for param in self.collection.pages().pagesParam():
                param.listParam.save_lists(only_if_changed=True)

            self.viewTab.savePagePositions(only_if_changed=True)

            if Settings()['autobackup']:
                if self.collection.isNeedBackup():
                    self.collection.backup()

    def yearCalculator(self):
        year = datetime.today().strftime("%Y")
        dlg = YearCalculatorDialog(year, '', parent=self)
        dlg.buttonBox.clear()
        dlg.buttonBox.addButton(QDialogButtonBox.Close)
        dlg.exec()

    def referencesGenerator(self):
        self._openUrl("http://opennumismat.github.io/references/")

    def about(self):
        QMessageBox.about(self, self.tr("About %s") % version.AppName,
                        "%s %s\n\n" % (version.AppName, version.Version) +
                        "Copyright (C) 2011-2024 Vitaly Ignatov\n\n" +
                        self.tr("%s is freeware licensed under a GPLv3.") %
                        version.AppName)

    def onlineHelp(self):
        self._openUrl("http://opennumismat.github.io/open-numismat/manual.html")

    def visitWeb(self):
        self._openUrl(version.Web)

    def autoUpdate(self):
        if Settings()['updates']:
            settings = QSettings()
            lastUpdateDateStr = settings.value('mainwindow/last_update')
            if lastUpdateDateStr:
                lastUpdateDate = QDate.fromString(lastUpdateDateStr,
                                                  Qt.ISODate)
                currentDate = QDate.currentDate()
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

        new_version = self.__getNewVersion()
        if versiontuple(new_version) > versiontuple(version.Version):
            result = QMessageBox.question(self, self.tr("New version"),
                        self.tr("New version is available. Download it now?"),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes)
            if result == QMessageBox.Yes:
                self._openUrl(version.Web)

            return True
        else:
            return False

    def _openUrl(self, url):
        executor = QDesktopServices()
        executor.openUrl(QUrl(url))

    @waitCursorDecorator
    def __getNewVersion(self):
        from xml.dom.minidom import parseString

        try:
            url = "http://opennumismat.github.io/data/pad.xml"
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(req, timeout=2).read()
            xml = parseString(data)
            tag = xml.getElementsByTagName('Program_Version')[0]
            newVersion = tag.firstChild.nodeValue
        except:
            return "0.0.0"

        return newVersion
