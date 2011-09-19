from PyQt4 import QtGui

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

    def __createDefaultPage(self):
        label = self.tr("Coins")
        listView = ListView()
        listView.setModel(self.collection.model())
        self.addTab(listView, label)
        self.setCurrentWidget(listView)
        
        self.collection.pages().addPage(listView, label)
