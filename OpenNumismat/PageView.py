from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import *

from OpenNumismat.ImageView import ImageView
from OpenNumismat.DetailsView import DetailsView
from OpenNumismat.ListView import ListView, CardView, IconView
from OpenNumismat.StatisticsView import StatisticsView
from OpenNumismat.TagsView import TagsView
from OpenNumismat.TreeView import TreeView
from OpenNumismat.Settings import Settings
from OpenNumismat.Collection.CollectionPages import CollectionPageTypes
from OpenNumismat.EditCoinDialog.MapWidget import get_map_widget


class Splitter(QSplitter):
    def __init__(self, title, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)

        self.title = title
        self.splitterMoved.connect(self.splitterPosChanged)

    def splitterPosChanged(self, _pos, _index):
        settings = QSettings()
        settings.setValue('pageview/splittersizes' + self.title, self.sizes())

    def showEvent(self, _e):
        settings = QSettings()
        sizes = settings.value('pageview/splittersizes' + self.title)
        if sizes:
            for i, size in enumerate(sizes):
                sizes[i] = int(size)

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)


class PageView(Splitter):
    def __init__(self, pageParam, parent=None):
        super().__init__('0', parent=parent)

        self.imagesAtBottom = pageParam.images_at_bottom

        self._model = None
        self.param = pageParam
        self.id = pageParam.id
        self.treeView = TreeView(pageParam.treeParam, self)
        self.tagsView = TagsView(self)
        if self.param.type == CollectionPageTypes.Card:
            self.listView = CardView(self.param.listParam, self)
        elif self.param.type == CollectionPageTypes.Icon:
            self.listView = IconView(self.param.listParam, self)
        else:
            self.listView = ListView(self.param.listParam, self)
        if self.imagesAtBottom:
            self.imageView = ImageView(QBoxLayout.LeftToRight, self)
            self.detailsView = DetailsView(QBoxLayout.TopToBottom, self)
        else:
            self.imageView = ImageView(QBoxLayout.TopToBottom, self)
            self.detailsView = DetailsView(QBoxLayout.LeftToRight, self)

        self.splitter1 = Splitter('1', Qt.Vertical, self)
        splitter2 = Splitter('2', parent=self.splitter1)
        splitter3 = Splitter('3', Qt.Vertical, parent=splitter2)
        splitter3.addWidget(self.treeView)
        splitter3.addWidget(self.tagsView)
        splitter2.addWidget(splitter3)
        splitter2.addWidget(self.listView)
        self.splitter1.addWidget(splitter2)
        if self.imagesAtBottom:
            self.splitter1.addWidget(self.imageView)
        else:
            self.splitter1.addWidget(self.detailsView)

        self.statisticsView = StatisticsView(pageParam.statisticsParam)
        self.statisticsView.setMinimumHeight(200)

        settings = Settings()
        self.mapView = get_map_widget(None, settings['map_type'], True)
        self.mapView.markerClicked.connect(self.setCurrentCoin)

        self.addWidget(self.splitter1)
        if self.imagesAtBottom:
            self.addWidget(self.detailsView)
        else:
            self.addWidget(self.imageView)

        self.splitterMoved.connect(self.splitterPosChanged)

    def setModel(self, model, reference):
        self._model = model

        self.treeView.setModel(model, reference)
        self.tagsView.setModel(model)
        self.listView.setModel(model)
        self.imageView.setModel(model)
        self.detailsView.setModel(model)
        self.statisticsView.setModel(model)
        self.mapView.setModel(model)
        self.prepareInfo()

        self.listView.rowChanged.connect(self.imageView.rowChangedEvent)
        self.listView.rowChanged.connect(self.treeView.rowChangedEvent)
        self.listView.rowChanged.connect(self.detailsView.rowChangedEvent)
        if model.settings['tags_used']:
            self.treeView.currentItemChanged.connect(self.tagsView.clearSelection)
            self.tagsView.currentItemChanged.connect(self.treeView.clearSelection)
            self._model.tagsChanged.connect(self.tagsView.tagsChanged)
        self._model.modelChanged.connect(self.modelChanged)

        if not model.settings['tags_used']:
            self.tagsView.hide()

    def model(self):
        return self._model

    def modelChanged(self):
        self.treeView.modelChanged()
        self.listView.modelChanged()
        if self.param.info_type == CollectionPageTypes.Statistics:
            self.statisticsView.modelChanged()
        elif self.param.info_type == CollectionPageTypes.Map:
            self.mapView.modelChanged()

    def prepareInfo(self):
        sizes = self.splitter1.sizes()

        if self.param.info_type == CollectionPageTypes.Map:
            self.splitter1.replaceWidget(1, self.mapView)
        elif self.param.info_type == CollectionPageTypes.Statistics:
            self.splitter1.replaceWidget(1, self.statisticsView)
        else:
            if self.imagesAtBottom:
                self.splitter1.replaceWidget(1, self.imageView)
            else:
                self.splitter1.replaceWidget(1, self.detailsView)

        if sizes[1] > 0:
            self.splitter1.setSizes(sizes)

    def showInfo(self, info_type):
        self.param.info_type = info_type
        self.prepareInfo()
        if self.param.info_type == CollectionPageTypes.Statistics:
            self.statisticsView.modelChanged()
        elif self.param.info_type == CollectionPageTypes.Map:
            self.mapView.modelChanged()

    def changeView(self, type_):
        index = self.listView.currentIndex()

        self.listView.rowChanged.disconnect(self.imageView.rowChangedEvent)
        self.listView.rowChanged.disconnect(self.treeView.rowChangedEvent)
        self.listView.rowChanged.disconnect(self.detailsView.rowChangedEvent)

        self.param.type = type_
        if self.param.type == CollectionPageTypes.Card:
            listView = CardView(self.param.listParam, self)
            self._model.setFilter('')
        elif self.param.type == CollectionPageTypes.Icon:
            listView = IconView(self.param.listParam, self)
            self._model.setFilter('')
        else:
            listView = ListView(self.param.listParam, self)

        splitter2 = self.splitter1.widget(0)
        old_widget = splitter2.replaceWidget(1, listView)
        old_widget.deleteLater()
        self.listView = listView

        self.listView.rowChanged.connect(self.imageView.rowChangedEvent)
        self.listView.rowChanged.connect(self.treeView.rowChangedEvent)
        self.listView.rowChanged.connect(self.detailsView.rowChangedEvent)

        self.listView.setModel(self._model)
        self.listView.modelChanged()

        if index.isValid():
            self.listView.setFocus()
            self.listView.scrollToIndex(index)

    def setCurrentCoin(self, coin_id):
        self.listView.selectedId = coin_id
        self.listView.modelChanged()
