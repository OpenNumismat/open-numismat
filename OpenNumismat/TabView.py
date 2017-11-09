from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import *

from OpenNumismat.PageView import PageView
from OpenNumismat.Tools.Gui import createIcon


class TabBar(QTabBar):
    doubleClicked = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

    def mouseDoubleClickEvent(self, event):
        index = self.tabAt(event.pos())
        self.doubleClicked.emit(index)


class TabView(QTabWidget):
    def __init__(self, parent):
        super().__init__(parent)

        tabBar = TabBar(self)
        self.setTabBar(tabBar)

        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closePage)
        self.currentChanged.connect(self.activatedPage)
        self.tabBar().customContextMenuRequested.connect(
                                                self.tabBarContextMenuEvent)
        self.tabBar().doubleClicked.connect(self.tabDClicked)
        self.tabBar().tabMoved.connect(self.tabMoved)
        self.oldPage = None
        self.__pages_changed = False

        self.__createActions()

    def mouseDoubleClickEvent(self, _event):
        self.newList()

    def tabDClicked(self, index):
        self.renamePage(index)

    def tabMoved(self, _from, _to):
        self.__pages_changed = True

    def actions(self):
        return self.__actions

    def __createActions(self):
        self.__actions = {}

        newListAct = QAction(self.tr("&New..."), self)
        newListAct.triggered.connect(self.newList)
        self.__actions['new'] = newListAct

        cloneListAct = QAction(self.tr("Clone"), self)
        cloneListAct.triggered.connect(self._clone)
        self.__actions['clone'] = cloneListAct

        openPageMenu = QMenu(self.tr("Open"), self)
        self.__actions['open'] = openPageMenu

        removeAllAct = QAction(createIcon('cross.png'),
                               self.tr("Remove all"), self)
        removeAllAct.triggered.connect(self.removeClosedPages)
        self.__actions['removeAll'] = removeAllAct

        renameListAct = QAction(self.tr("Rename..."), self)
        renameListAct.triggered.connect(self.renamePage)
        self.__actions['rename'] = renameListAct

        selectColumnsAct = QAction(self.tr("Select columns..."), self)
        selectColumnsAct.triggered.connect(self.selectColumns)
        self.__actions['select'] = selectColumnsAct

        closeListAct = QAction(self.tr("Close"), self)
        closeListAct.setShortcut(QKeySequence.Close)
        closeListAct.triggered.connect(self.closePage)
        self.__actions['close'] = closeListAct

        removeListAct = QAction(createIcon('cross.png'),
                                self.tr("Remove"), self)
        removeListAct.triggered.connect(self.removePage)
        self.__actions['remove'] = removeListAct

    def tabBarContextMenuEvent(self, pos):
        index = self.tabBar().tabAt(pos)
        self.setCurrentIndex(index)

        menu = QMenu(self)
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

        pageTitle = oldLabel + self.tr(" (clone)")
        pageParam = self.collection.pages().addPage(pageTitle)
        pageParam.listParam = oldWidget.listView.listParam.clone()
        pageParam.listParam.page.id = pageParam.id
        pageParam.listParam.save()

        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model(), self.collection.reference)
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)

        self.collection.pages().openPage(pageView)

    def activatedPage(self, index):
        enabled = (index >= 0)
        self.__actions['rename'].setEnabled(enabled)
        self.__actions['close'].setEnabled(enabled)
        self.__actions['remove'].setEnabled(enabled)

        statusBar = self.parent().statusBar()

        if self.oldPage:
            statusBar.removeWidget(self.oldPage.listView.listCountLabel)
            statusBar.removeWidget(self.oldPage.listView.listSelectedLabel)

        if index >= 0:
            page = self.widget(index)
            page.model().select()

            statusBar.addPermanentWidget(page.listView.listCountLabel)
            page.listView.listCountLabel.show()
            statusBar.addPermanentWidget(page.listView.listSelectedLabel)
            page.listView.listSelectedLabel.show()

            self.oldPage = page

            self.parent().updateStatisticsAct(page.statisticsShowed)

    def setCollection(self, collection):
        self.collection = collection

        for _ in range(self.count()):
            self.removeTab(0)

        for pageParam in collection.pages().pagesParam():
            if pageParam.isopen:
                pageView = PageView(pageParam, self)
                pageView.setModel(self.collection.model(), self.collection.reference)
                self.addTab(pageView, pageParam.title)

        # If no pages exists => create default page
        if self.count() == 0:
            self.__createListPage(self.tr("Coins"))

    def currentModel(self):
        index = self.currentIndex()
        page = self.widget(index)
        return page.model()

    def newList(self):
        label, ok = QInputDialog.getText(self, self.tr("New list"),
                self.tr("Enter list title"), text=self.tr("New list"),
                flags=(Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint))
        if ok and label:
            self.__createListPage(label)

    def renamePage(self, index=None):
        index = self.currentIndex()
        oldLabel = self.tabText(index)
        label, ok = QInputDialog.getText(self, self.tr("Rename list"),
                self.tr("Enter new list title"), text=oldLabel,
                flags=(Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint))
        if ok and label:
            self.setTabText(index, label)
            page = self.widget(index)
            self.collection.pages().renamePage(page, label)
            self.setCurrentIndex(index)

    def selectColumns(self, index=None):
        listView = self.currentListView()
        listView.selectColumns()

    def closePage(self, index=None):
        if self.count() <= 1:
            QMessageBox.information(self, self.tr("Remove page"),
                    self.tr("Can't close latest opened page.\n"
                            "Add a new one first."))
            return

        if index is None:
            index = self.currentIndex()
        page = self.widget(index)
        self.removeTab(index)
        self.collection.pages().closePage(page)

    def removePage(self):
        if self.count() <= 1:
            QMessageBox.information(self, self.tr("Remove page"),
                    self.tr("Can't remove latest opened page.\n"
                            "Add a new one first."))
            return

        index = self.currentIndex()
        pageTitle = self.tabText(index)
        result = QMessageBox.question(self, self.tr("Remove page"),
                self.tr("Remove the page '%s' permanently?") % pageTitle,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if result == QMessageBox.Yes:
            page = self.widget(index)
            self.removeTab(index)
            self.collection.pages().removePage(page.param)

    def removeClosedPages(self):
        result = QMessageBox.question(self, self.tr("Remove pages"),
                self.tr("Remove all closed pages permanently?"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if result == QMessageBox.Yes:
            closedPages = self.collection.pages().closedPages()
            for pageParam in closedPages:
                self.collection.pages().removePage(pageParam)

    def savePagePositions(self, only_if_changed=False):
        if not only_if_changed or self.__pages_changed:
            pages = []
            for i in range(self.count()):
                pages.append(self.widget(i))
            self.collection.pages().savePositions(pages)

            self.__pages_changed = False

    def openPage(self, pageParam):
        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model(), self.collection.reference)
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)

        self.collection.pages().openPage(pageView)

    def updateOpenPageMenu(self):
        menu = self.__actions['open']
        menu.clear()
        closedPages = self.collection.pages().closedPages()
        hasClosedPages = len(closedPages)
        menu.setEnabled(hasClosedPages)
        if hasClosedPages:
            for param in closedPages:
                act = OpenPageAction(param, self)
                act.openPageTriggered.connect(self.openPage)
                menu.addAction(act)

            menu.addSeparator()
            menu.addAction(self.__actions['removeAll'])

    def currentListView(self):
        return self.currentWidget().listView

    def currentPageView(self):
        return self.currentWidget()

    def __createListPage(self, title):
        pageParam = self.collection.pages().addPage(title)

        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model(), self.collection.reference)
        self.addTab(pageView, title)
        self.setCurrentWidget(pageView)


class OpenPageAction(QAction):
    openPageTriggered = pyqtSignal(object)

    def __init__(self, pageParam, parent=None):
        super().__init__(pageParam.title, parent)

        self.pageParam = pageParam
        self.triggered.connect(self.trigger)

    def trigger(self):
        self.openPageTriggered.emit(self.pageParam)
