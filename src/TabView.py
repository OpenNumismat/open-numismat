from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal

from PageView import PageView

class TabBar(QtGui.QTabBar):
    doubleClicked = pyqtSignal(int)
    
    def __init__(self, parent):
        super(TabBar, self).__init__(parent)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    
    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        self.doubleClicked.emit(index)

class TabView(QtGui.QTabWidget):
    def __init__(self, parent):
        super(TabView, self).__init__(parent)
        
        tabBar = TabBar(self)
        self.setTabBar(tabBar)
        
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closePage)
        self.currentChanged.connect(self.activatedPage)
        self.tabBar().customContextMenuRequested.connect(self.tabBarContextMenuEvent)
        self.tabBar().doubleClicked.connect(self.tabDClicked)
        self.oldPage = None
        
        self.__createActions()
    
    def tabDClicked(self, index):
        self.renamePage(index)
    
    def actions(self):
        return self.__actions
    
    def __createActions(self):
        self.__actions = {}
        
        newListAct = QtGui.QAction(self.tr("&New..."), self)
        newListAct.triggered.connect(self.newList)
        self.__actions['new'] = newListAct
        
        cloneListAct = QtGui.QAction(self.tr("Clone"), self)
        cloneListAct.triggered.connect(self._clone)
        self.__actions['clone'] = cloneListAct
        
        openPageMenu = QtGui.QMenu(self.tr("Open"), self)
        openPageMenu.aboutToShow.connect(self.__updateOpenPageMenu)
        self.__actions['open'] = openPageMenu
        
        removeAllAct = QtGui.QAction(QtGui.QIcon('icons/cross.png'), self.tr("Remove all"), self)
        removeAllAct.triggered.connect(self.removeClosedPages)
        self.__actions['removeAll'] = removeAllAct
        
        renameListAct = QtGui.QAction(self.tr("Rename..."), self)
        renameListAct.triggered.connect(self.renamePage)
        self.__actions['rename'] = renameListAct
        
        closeListAct = QtGui.QAction(self.tr("Close"), self)
        closeListAct.setShortcut(QtGui.QKeySequence.Close)
        closeListAct.triggered.connect(self.closePage)
        self.__actions['close'] = closeListAct
        
        removeListAct = QtGui.QAction(QtGui.QIcon('icons/cross.png'), self.tr("Remove"), self)
        removeListAct.triggered.connect(self.removePage)
        self.__actions['remove'] = removeListAct

    def tabBarContextMenuEvent(self, pos):
        index = self.tabBar().tabAt(pos)
        self.setCurrentIndex(index)
        
        menu = QtGui.QMenu(self)
        menu.addAction(self.__actions['rename'])
        menu.setDefaultAction(self.__actions['rename'])
        menu.addAction(self.__actions['clone'])
        menu.addSeparator()
        menu.addAction(self.__actions['remove'])
        menu.exec_(self.mapToGlobal(pos))
    
    def _clone(self):
        index = self.currentIndex()
        oldLabel = self.tabText(index)
        oldWidget = self.widget(index)

        pageParam = self.collection.pages().addPage(oldLabel + self.tr(" (clone)"))
        pageParam.listParam = oldWidget.listView.listParam.clone()
        pageParam.listParam.pageId = pageParam.id
        pageParam.listParam.save()

        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model())
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)
        
        self.collection.pages().openPage(pageView)
    
    def activatedPage(self, index):
        enabled = (index >= 0)
        self.__actions['rename'].setEnabled(enabled)
        self.__actions['close'].setEnabled(enabled)
        self.__actions['remove'].setEnabled(enabled)

        if self.oldPage:
            self.parent().statusBar().removeWidget(self.oldPage.listView.listCountLabel)
            self.parent().statusBar().removeWidget(self.oldPage.listView.listSelectedLabel)

        if index >= 0:
            page = self.widget(index)
            page.model().select()

            self.parent().statusBar().addPermanentWidget(page.listView.listCountLabel)
            page.listView.listCountLabel.show()
            self.parent().statusBar().addPermanentWidget(page.listView.listSelectedLabel)
            page.listView.listSelectedLabel.show()

            self.oldPage = page
    
    def setCollection(self, collection):
        self.collection = collection
        
        for _ in range(self.count()):
            self.removeTab(0)

        for pageParam in collection.pages().pagesParam():
            if pageParam.isopen:
                pageView = PageView(pageParam, self)
                pageView.setModel(self.collection.model())
                self.addTab(pageView, pageParam.title)
        
        # If no pages exists => create default page
        if self.count() == 0:
            self.__createListPage(self.tr("Coins"))

    def currentModel(self):
        index = self.currentIndex()
        page = self.widget(index)
        return page.model()

    def newList(self):
        label, ok = QtGui.QInputDialog.getText(self, self.tr("New list"), self.tr("Enter list title"), text=self.tr("New list"))
        if ok and label:
            self.__createListPage(label)
    
    def renamePage(self, index=None):
        index = self.currentIndex()
        oldLabel = self.tabText(index)
        label, ok = QtGui.QInputDialog.getText(self, self.tr("Rename list"), self.tr("Enter new list title"), text=oldLabel)
        if ok and label:
            self.setTabText(index, label)
            page = self.widget(index)
            self.collection.pages().renamePage(page, label)
            self.setCurrentIndex(index)

    def closePage(self, index=None):
        if not index:
            index = self.currentIndex()
        page = self.widget(index)
        self.removeTab(index)
        self.collection.pages().closePage(page)
    
    def removePage(self):
        index = self.currentIndex()
        result = QtGui.QMessageBox.question(self, self.tr("Remove page"),
                        self.tr("Remove the page '%s' permanently?") % self.tabText(index),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result == QtGui.QMessageBox.Yes:
            page = self.widget(index)
            self.removeTab(index)
            self.collection.pages().removePage(page)

    def removeClosedPages(self):
        result = QtGui.QMessageBox.question(self, self.tr("Remove pages"),
                        self.tr("Remove all closed pages permanently?"),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result == QtGui.QMessageBox.Yes:
            closedPages = self.collection.pages().closedPages()
            for pageParam in closedPages:
                self.collection.pages().removePage(pageParam)

    def savePagePositions(self):
        pages = []
        for i in range(self.count()):
            pages.append(self.widget(i))
        self.collection.pages().savePositions(pages)
    
    def openPage(self, pageParam):
        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model())
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)
        
        self.collection.pages().openPage(pageView)

    def __updateOpenPageMenu(self):
        menu = self.__actions['open']
        menu.clear()
        closedPages = self.collection.pages().closedPages()
        if len(closedPages) > 0:
            for param in closedPages:
                act = OpenPageAction(param, self)
                act.openPageTriggered.connect(self.openPage)
                menu.addAction(act)
            
            menu.addSeparator()
            menu.addAction(self.__actions['removeAll'])
        else:
            menu.setDisabled(True)

    def __createListPage(self, title):
        pageParam = self.collection.pages().addPage(title)

        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model())
        self.addTab(pageView, title)
        self.setCurrentWidget(pageView)

class OpenPageAction(QtGui.QAction):
    openPageTriggered = pyqtSignal(object)
    
    def __init__(self, pageParam, parent=None):
        super(OpenPageAction, self).__init__(pageParam.title, parent)

        self.pageParam = pageParam
        self.triggered.connect(self.trigger)
    
    def trigger(self):
        self.openPageTriggered.emit(self.pageParam)
