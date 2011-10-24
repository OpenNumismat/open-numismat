#!/usr/bin/python

from PyQt4 import QtGui, QtCore

from Collection.Collection import Collection
from Reference.Reference import Reference
from TabView import TabView
from Settings import Settings, SettingsDialog
from LatestCollections import LatestCollections
import version

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        self.collectionFileLabel = QtGui.QLabel()
        self.statusBar().addWidget(self.collectionFileLabel)
        
        settingsAct = QtGui.QAction(QtGui.QIcon('icons/cog.png'), self.tr("Settings..."), self)
        settingsAct.triggered.connect(self.settingsEvent)
        
        exitAct = QtGui.QAction(QtGui.QIcon('icons/door_in.png'), self.tr("Exit"), self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        file = menubar.addMenu(self.tr("&File"))
        file.addAction(settingsAct)
        file.addSeparator()
        file.addAction(exitAct)

        addCoinAct = QtGui.QAction(QtGui.QIcon('icons/add.png'), self.tr("Add"), self)
        addCoinAct.triggered.connect(self.addCoin)

        coin = menubar.addMenu(self.tr("Coin"))
        coin.addAction(addCoinAct)

        newCollectionAct = QtGui.QAction(self.tr("&New..."), self)
        newCollectionAct.triggered.connect(self.newCollectionEvent)

        style = QtGui.QApplication.style()
        icon = style.standardIcon(QtGui.QStyle.SP_DialogOpenButton)
        openCollectionAct = QtGui.QAction(icon, self.tr("&Open..."), self)
        openCollectionAct.setShortcut('Ctrl+O')
        openCollectionAct.triggered.connect(self.openCollectionEvent)

        backupCollectionAct = QtGui.QAction(self.tr("Backup"), self)
        backupCollectionAct.triggered.connect(self.backupCollectionEvent)

        collectionMenu = menubar.addMenu(self.tr("Collection"))
        collectionMenu.addAction(newCollectionAct)
        collectionMenu.addAction(openCollectionAct)
        collectionMenu.addAction(backupCollectionAct)
        collectionMenu.addSeparator()

        self.latestActions = []
        self.__updateLatest(collectionMenu)

        self.viewTab = TabView(self)
        
        actions = self.viewTab.actions()
        listMenu = menubar.addMenu(self.tr("List"))
        listMenu.addAction(actions['new'])
        listMenu.addMenu(actions['open'])
        listMenu.addAction(actions['rename'])
        listMenu.addSeparator()
        listMenu.addAction(actions['close'])
        listMenu.addAction(actions['remove'])

        self.referenceMenu = menubar.addMenu(self.tr("Reference"))

        toolBar = QtGui.QToolBar(self)
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
        if self.collection.open(latest.latest()):
            self.setCollection(self.collection)
        
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
            act.latestTriggered.connect(self.openCollection)
            self.__menu.addAction(act)
    
    def settingsEvent(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.reference.open(Settings().reference)

    def addCoin(self):
        model = self.viewTab.currentModel()
        model.addCoin(model.record(), self)

    def openCollectionEvent(self):
        dir_ = QtCore.QFileInfo(self.collection.fileName).absolutePath()
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                self.tr("Open collection"), dir_,
                self.tr("Collections (*.db)"))
        if fileName:
            self.openCollection(fileName)

    def newCollectionEvent(self):
        dir_ = QtCore.QFileInfo(self.collection.fileName).absolutePath()
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("New collection"), dir_,
                self.tr("Collections (*.db)"), QtGui.QFileDialog.DontConfirmOverwrite)
        if fileName:
            if self.collection.create(fileName):
                self.setCollection(self.collection)
    
    def backupCollectionEvent(self):
        file = QtCore.QFile(self.collection.fileName)
        folder = Settings().backupFolder
        backup = QtCore.QFileInfo(folder+'/'+self.collection.getCollectionName()+'_'+QtCore.QDateTime.currentDateTime().toString('yyMMddhhmm')+'.db')
        backupName = backup.absoluteFilePath()
        if not file.copy(backupName):
            QtGui.QMessageBox.critical(self, self.tr("Backup collection"), self.tr("Can't make a collection backup at %s") % backupName)

    def openCollection(self, fileName):
        if self.collection.open(fileName):
            self.setCollection(self.collection)
        else:
            # Remove wrong collection from latest collections list
            latest = LatestCollections(self)
            latest.delete(fileName)
            self.__updateLatest()
    
    def setCollection(self, collection):
        self.collectionFileLabel.setText(collection.getFileName())
        self.setWindowTitle(collection.getCollectionName() + ' - ' + version.AppName)

        latest = LatestCollections(self)
        latest.add(collection.getFileName())
        self.__updateLatest()
        
        self.viewTab.setCollection(collection)
        
        self.referenceMenu.clear()
        self.referenceMenu.addAction(self.collection.referenceMenu(self))
        
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

    QtCore.QCoreApplication.setOrganizationName(version.Company)
    QtCore.QCoreApplication.setApplicationName(version.AppName)

    settings = Settings()
    if settings.sendError:
        sys.excepthook = exceptHook
    
    locale = settings.language
    translator = QtCore.QTranslator()
    translator.load('lang_'+locale)
    app.installTranslator(translator)

    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

def exceptHook(type_, value, tback):
    import platform, sys, traceback
    
    stack = ''.join(traceback.format_exception(type_, value, tback))

    msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Information, "System error", "A system error occurred.\nDo you want to send an error message to the author?")
    msgBox.setDetailedText(stack)
    msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    if msgBox.exec_() == QtGui.QMessageBox.Yes:
        line = traceback.extract_tb(tback, 1)[0]
        subject = "[v%s] %s - %s:%d" % (version.Version, type_.__name__, line[0], line[1])
        
        errorMessage = []
        errorMessage.append("%s: %s" % (version.AppName, version.Version))
        errorMessage.append("OS: %s %s %s (%s)" % (platform.system(), platform.release(), platform.architecture()[0], platform.version()))
        errorMessage.append("Python: %s" % platform.python_version())
        errorMessage.append("Qt: %s" % QtCore.PYQT_VERSION_STR)
        errorMessage.append('')
        errorMessage.append(stack)

        url = QtCore.QUrl(version.Web + '/issues/entry')
        url.setQueryItems([('summary', subject), ('comment', '\n'.join(errorMessage))])

        executor = QtGui.QDesktopServices()
        executor.openUrl(url)
    
    # Call the default handler
    sys.__excepthook__(type, value, tback) 

if __name__ == '__main__':
    run()
