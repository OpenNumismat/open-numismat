from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal

from PageView import PageView

class TabView(QtGui.QTabWidget):
    def __init__(self, parent):
        super(TabView, self).__init__(parent)

        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closePage)
        self.currentChanged.connect(self.activatedPage)
        self.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self.tabBarContextMenuEvent)
        self.oldPage = None
        
        self.__createActions()
        self._pos = None
    
    def actions(self):
        return self.__actions
    
    def __createActions(self):
        self.__actions = {}
        
        newListAct = QtGui.QAction(self.tr("New..."), self)
        newListAct.triggered.connect(self.newList)
        self.__actions['new'] = newListAct
        
        openPageMenu = QtGui.QMenu(self.tr("Open"), self)
        self.setOpenPageMenu(openPageMenu)
        self.__actions['open'] = openPageMenu
        
        renameListAct = QtGui.QAction(self.tr("Rename..."), self)
        renameListAct.triggered.connect(self.renamePage)
        self.__actions['rename'] = renameListAct
        
        closeListAct = QtGui.QAction(self.tr("Close"), self)
        closeListAct.triggered.connect(self.closePage)
        self.__actions['close'] = closeListAct
        
        removeListAct = QtGui.QAction(self.tr("Remove"), self)
        removeListAct.triggered.connect(self.removePage)
        self.__actions['remove'] = removeListAct

    def tabBarContextMenuEvent(self, pos):
        self._pos = pos  # store pos for action
        menu = QtGui.QMenu(self)
        menu.addAction(self.tr("Clone"), self._clone)
        menu.addAction(self.__actions['rename'])
        menu.addSeparator()
        menu.addAction(self.__actions['remove'])
        menu.exec_(self.mapToGlobal(pos))
        self._pos = None
    
    def _clone(self):
        index = self.tabBar().tabAt(self._pos)
        oldLabel = self.tabText(index)
        oldWidget = self.widget(index)

        pageParam = self.collection.pages().addPage(oldLabel + self.tr(" (clone)"))
        pageParam.listParam = oldWidget.listView.listParam
        pageParam.listParam.pageId = pageParam.id
        pageParam.listParam.save()

        pageView = PageView(pageParam.listParam)
        pageView.id = pageParam.id
        pageView.setModel(self.collection.model())
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)
        
        self.collection.pages().openPage(pageView)
    
    def activatedPage(self, index):
        if self.oldPage:
            self.parent().statusBar().removeWidget(self.oldPage.listView.listCountLabel)
            self.parent().statusBar().removeWidget(self.oldPage.listView.listSelectedLabel)

        page = self.widget(index)
        if page:
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
                pageView = PageView(pageParam.listParam)
                pageView.id = pageParam.id
                pageView.setModel(self.collection.model())
                self.addTab(pageView, pageParam.title)
        
        # If no pages exists => create default page
        if self.count() == 0:
            self.__createListPage(self.tr("Coins"))
        
        self.__updateOpenPageMenu()

    def currentModel(self):
        index = self.currentIndex()
        page = self.widget(index)
        return page.model()

    def newList(self):
        label, ok = QtGui.QInputDialog.getText(self, self.tr("New list"), self.tr("Enter list title"), text=self.tr("New list"))
        if ok and label:
            self.__createListPage(label)
    
    def renamePage(self):
        if self._pos:
            index = self.tabBar().tabAt(self._pos)
        else:
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
        
        self.__updateOpenPageMenu()
    
    def removePage(self):
        if self._pos:
            index = self.tabBar().tabAt(self._pos)
        else:
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
            
            self.__updateOpenPageMenu()

    def savePagePositions(self):
        pages = []
        for i in range(self.count()):
            pages.append(self.widget(i))
        self.collection.pages().savePositions(pages)
    
    def openPage(self, pageParam):
        pageView = PageView(pageParam.listParam)
        pageView.id = pageParam.id
        pageView.setModel(self.collection.model())
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)
        
        self.collection.pages().openPage(pageView)
        
        self.__updateOpenPageMenu()

    def setOpenPageMenu(self, menu):
        self.openPageMenu = menu
    
    def __updateOpenPageMenu(self):
        if hasattr(self, 'openPageMenu'):
            closedPages = self.collection.pages().closedPages()
            self.openPageMenu.clear()
            self.openPageMenu.setEnabled(len(closedPages) > 0)
            for param in closedPages:
                act = OpenPageAction(param, self)
                act.openPageTriggered.connect(self.openPage)
                self.openPageMenu.addAction(act)
            self.openPageMenu.addSeparator()
            act = QtGui.QAction(self.tr("Remove all"), self)
            act.triggered.connect(self.removeClosedPages)
            self.openPageMenu.addAction(act)

    def __createListPage(self, title):
        pageParam = self.collection.pages().addPage(title)

        pageView = PageView(pageParam.listParam)
        pageView.setModel(self.collection.model())
        pageView.id = pageParam.id
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
