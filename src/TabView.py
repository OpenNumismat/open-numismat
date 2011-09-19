from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

from ListView import ListView

class TabView(QtGui.QTabWidget):
    def __init__(self, parent):
        super(TabView, self).__init__(parent)

        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closePage)
    
    def setCollection(self, collection):
        self.collection = collection
        
        for _ in range(self.count()):
            self.removeTab(0)

        for pageParam in collection.pages().pagesParam():
            if pageParam.isopen:
                listView = ListView()
                listView.setModel(self.collection.model())
                listView.id = pageParam.id
                self.addTab(listView, pageParam.title)
        
        # If no pages exists => create default page
        if self.count() == 0:
            self.__createDefaultPage()
        
        self.__updateOpenPageMenu()

    def newList(self):
        label, ok = QtGui.QInputDialog.getText(self, self.tr("New list"), self.tr("Enter list title"))
        if ok and label:
            listView = ListView()
            listView.setModel(self.collection.model())
            self.addTab(listView, label)
            self.setCurrentWidget(listView)
            
            self.collection.pages().addPage(listView, label)

    def renamePage(self):
        index = self.currentIndex()
        oldLabel = self.tabText(index)
        label, ok = QtGui.QInputDialog.getText(self, self.tr("Rename list"), self.tr("Enter new list title"), text=oldLabel)
        if ok and label:
            self.setTabText(index, label)
            page = self.widget(index)
            self.collection.pages().renamePage(page, label)

    def closePage(self, index=None):
        if not index:
            index = self.currentIndex()
        page = self.widget(index)
        self.removeTab(index)
        self.collection.pages().closePage(page)
        
        self.__updateOpenPageMenu()

    def removePage(self):
        index = self.currentIndex()
        result = QtGui.QMessageBox.question(self, self.tr("Remove page"),
                        self.tr("Remove the page '%s' permanently?") % self.tabText(index),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if result == QtGui.QMessageBox.Yes:
            page = self.widget(index)
            self.removeTab(index)
            self.collection.pages().removePage(page)

    def savePagePositions(self):
        pages = []
        for i in range(self.count()):
            pages.append(self.widget(i))
        self.collection.pages().savePositions(pages)
    
    def openPage(self, pageParam):
        listView = ListView()
        listView.id = pageParam.id
        listView.setModel(self.collection.model())
        self.addTab(listView, pageParam.title)
        self.setCurrentWidget(listView)
        
        self.collection.pages().openPage(listView)
            
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

    def __createDefaultPage(self):
        label = self.tr("Coins")
        listView = ListView()
        listView.setModel(self.collection.model())
        self.addTab(listView, label)
        self.setCurrentWidget(listView)
        
        self.collection.pages().addPage(listView, label)

class OpenPageAction(QtGui.QAction):
    openPageTriggered = pyqtSignal(object)
    
    def __init__(self, pageParam, parent=None):
        super(OpenPageAction, self).__init__(pageParam.title, parent)

        self.pageParam = pageParam
        self.triggered.connect(self.trigger)
    
    def trigger(self):
        self.openPageTriggered.emit(self.pageParam)
