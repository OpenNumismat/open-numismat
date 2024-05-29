from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QKeySequence, QIcon, QAction
from PySide6.QtWidgets import (
    QInputDialog,
    QMenu,
    QMessageBox,
    QTabBar,
    QTabWidget,
)

from OpenNumismat.PageView import PageView
from OpenNumismat.Collection.CollectionPages import CollectionPageTypes


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

        removeAllAct = QAction(QIcon(':/cross.png'),
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

        removeListAct = QAction(QIcon(':/cross.png'),
                                self.tr("Remove"), self)
        removeListAct.triggered.connect(self.removePage)
        self.__actions['remove'] = removeListAct

        cancelFilteringAct = QAction(QIcon(':/funnel_clear.png'),
                                     self.tr("Clear all filters"), self)
        cancelFilteringAct.triggered.connect(self.cancelFiltering)
        self.__actions['cancel_filtering'] = cancelFilteringAct

        cancelSortingAct = QAction(QIcon(':/sort_clear.png'),
                                   self.tr("Clear sort order"), self)
        cancelSortingAct.triggered.connect(self.cancelSorting)
        self.__actions['cancel_sorting'] = cancelSortingAct

        saveSortingAct = QAction(QIcon(':/sort_save.png'),
                                   self.tr("Save sort order"), self)
        saveSortingAct.triggered.connect(self.saveSorting)
        self.__actions['save_sorting'] = saveSortingAct

        customizeTreeAct = QAction(self.tr("Customize tree..."), self)
        customizeTreeAct.triggered.connect(self.customizeTree)
        self.__actions['customize_tree'] = customizeTreeAct

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

        pageView = self.__createPage(pageParam)
        self.collection.pages().openPage(pageView)

    def clearStatusBar(self):
        if self.oldPage:
            statusBar = self.parent().statusBar()
            statusBar.removeWidget(self.oldPage.listView.listCountLabel)
            self.oldPage.listView.listCountLabel.hide()
            statusBar.removeWidget(self.oldPage.listView.listSelectedLabel)
            self.oldPage.listView.listSelectedLabel.hide()

    def updatePage(self, page):
        parent = self.parent()
        statusBar = parent.statusBar()
        statusBar.addPermanentWidget(page.listView.listCountLabel)
        page.listView.listCountLabel.show()
        statusBar.addPermanentWidget(page.listView.listSelectedLabel)
        page.listView.listSelectedLabel.show()

        type_ = page.param.type
        if type_ == CollectionPageTypes.Card:
            parent.viewButton.setDefaultAction(parent.cardViewAct)
        elif type_ == CollectionPageTypes.Icon:
            parent.viewButton.setDefaultAction(parent.iconViewAct)
        else:
            parent.viewButton.setDefaultAction(parent.tableViewAct)

        self.__actions['select'].setEnabled(type_ == CollectionPageTypes.List)

        mode = page.listView.isDragMode()
        parent.enableDragAct.setChecked(mode)

    def activatedPage(self, index):
        enabled = (index >= 0)
        self.__actions['rename'].setEnabled(enabled)
        self.__actions['close'].setEnabled(enabled)
        self.__actions['remove'].setEnabled(enabled)
        self.__actions['cancel_filtering'].setEnabled(enabled)
        self.__actions['cancel_sorting'].setEnabled(enabled)
        self.__actions['save_sorting'].setEnabled(enabled)
        self.__actions['customize_tree'].setEnabled(enabled)

        if index >= 0:
            page = self.widget(index)
            page.model().select()

            self.parent().updateInfoType(page.param.info_type)
            self.parent().quickSearch.setText(page.listView.searchText)

            self.clearStatusBar()
            self.updatePage(page)

            self.oldPage = page
        else:
            self.parent().quickSearch.clear()
            self.oldPage = None

    def clear(self):
        self.currentChanged.disconnect(self.activatedPage)
        while self.count():
            w = self.widget(0)
            self.removeTab(0)
            w.deleteLater()
        self.currentChanged.connect(self.activatedPage)
        
        self.clearStatusBar()

    def setCollection(self, collection):
        self.collection = collection

        self.currentChanged.disconnect(self.activatedPage)

        for pageParam in collection.pages().pagesParam():
            if pageParam.isopen:
                self.__createPage(pageParam)

        self.currentChanged.connect(self.activatedPage)

        settings = self.collection.settings
        self.setCurrentIndex(settings['current_page'])
        if self.count() == 1:
            self.activatedPage(0)

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

    def selectColumns(self):
        listView = self.currentListView()
        listView.selectColumns()

    def cancelFiltering(self):
        self.parent().quickSearch.clear()

        listView = self.currentListView()
        listView.clearAllFilters()

    def cancelSorting(self):
        listView = self.currentListView()
        listView.clearSorting()

    def saveSorting(self):
        listView = self.currentListView()
        listView.saveSorting()

    def customizeTree(self):
        treeView = self.currentPageView().treeView
        treeView.customizeTree()

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

        # Save latest opened page
        settings = self.collection.settings
        settings['current_page'] = self.currentIndex()
        settings.save()

    def openPage(self, pageParam):
        pageView = self.__createPage(pageParam)
        self.collection.pages().openPage(pageView)

    def openPageEvent(self):
        pageParam = self.sender().data()
        self.openPage(pageParam)

    def updateOpenPageMenu(self):
        menu = self.__actions['open']
        menu.clear()
        closedPages = self.collection.pages().closedPages()
        hasClosedPages = len(closedPages)
        menu.setEnabled(hasClosedPages)
        if hasClosedPages:
            for pageParam in closedPages:
                act = QAction(pageParam.title, self)
                act.setData(pageParam)
                act.triggered.connect(self.openPageEvent)
                menu.addAction(act)

            menu.addSeparator()
            menu.addAction(self.__actions['removeAll'])

    def currentListView(self):
        return self.currentWidget().listView

    def currentPageView(self):
        return self.currentWidget()

    def __createListPage(self, title):
        pageParam = self.collection.pages().addPage(title)
        self.__createPage(pageParam)

    def __createPage(self, pageParam):
        settings = self.collection.settings
        pageParam.images_at_bottom = settings['images_at_bottom']
        pageParam.treeParam.convert_fraction = settings['convert_fraction']

        pageView = PageView(pageParam, self)
        pageView.setModel(self.collection.model(), self.collection.reference)
        self.addTab(pageView, pageParam.title)
        self.setCurrentWidget(pageView)

        return pageView
