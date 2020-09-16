from PyQt5.QtCore import Qt, QMargins, QSettings
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import createIcon, getSaveFileName

ZOOM_IN_FACTOR = 1.25
ZOOM_MAX = 5


class GraphicsView(QGraphicsView):

    def __init__(self, scene, parent):
        super().__init__(scene, parent)

        self.setStyleSheet("border: 0px;")

    def wheelEvent(self, event):
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
#        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        oldPos = self.mapToScene(event.pos())

        if event.angleDelta().y() > 0:
            self.parent().zoomIn()
        else:
            self.parent().zoomOut()

        # Get the new position
        newPos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())


@storeDlgSizeDecorator
class ImageViewer(QDialog):

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowSystemMenuHint |
                         Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.scene = QGraphicsScene()
        self.viewer = GraphicsView(self.scene, self)

        self.viewer.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viewer.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.viewer.installEventFilter(self)
        self.viewer.setResizeAnchor(QGraphicsView.AnchorViewCenter)

        self.menuBar = QMenuBar()

        self.toolBar = QToolBar()

        self.statusBar = QStatusBar()

        self.sizeLabel = QLabel()
        self.statusBar.addWidget(self.sizeLabel)

        self.zoomLabel = QLabel()
        self.statusBar.addWidget(self.zoomLabel)

        layout = QVBoxLayout()
        layout.setMenuBar(self.menuBar)
        layout.addWidget(self.toolBar)
        layout.addWidget(self.viewer)
        layout.addWidget(self.statusBar)
        layout.setContentsMargins(QMargins())
        layout.setSpacing(0)
        self.setLayout(layout)

        self.isFullScreen = False
        self.name = 'photo'
        self._pixmapHandle = None
        self.scale = 1
        self.minScale = 0.2
        self.isFitToWindow = True

        self.createActions()
        self.createMenus()
        self.createToolBar()

    def createActions(self):
        self.saveAct = QAction(self.tr("&Save As..."), self, shortcut="Ctrl+S", triggered=self.save)
#        self.printAct = QAction(self.tr("&Print..."), self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.exitAct = QAction(self.tr("E&xit"), self, shortcut="Ctrl+Q", triggered=self.close)
        self.fullScreenAct = QAction(self.tr("Full Screen"), self, shortcut="F11", triggered=self.fullScreen)
        self.zoomInAct = QAction(createIcon('zoom_in.png'), self.tr("Zoom &In (25%)"), self, triggered=self.zoomIn)
        self.zoomInShortcut = QShortcut(Qt.Key_Plus, self, self.zoomIn)
        self.zoomOutAct = QAction(createIcon('zoom_out.png'), self.tr("Zoom &Out (25%)"), self, triggered=self.zoomOut)
        self.zoomOutShortcut = QShortcut(Qt.Key_Minus, self, self.zoomOut)
        self.normalSizeAct = QAction(createIcon('arrow_out.png'), self.tr("&Normal Size"), self, triggered=self.normalSize)
        self.fitToWindowAct = QAction(createIcon('arrow_in.png'), self.tr("&Fit to Window"), self, triggered=self.fitToWindow)
        self.showToolBarAct = QAction(self.tr("Show Tool Bar"), self, checkable=True, triggered=self.showToolBar)
        self.showStatusBarAct = QAction(self.tr("Show Status Bar"), self, checkable=True, triggered=self.showStatusBar)

        settings = QSettings()
        toolBarShown = settings.value('image_viewer/tool_bar', True, type=bool)
        self.showToolBarAct.setChecked(toolBarShown)
        self.toolBar.setVisible(toolBarShown)
        statusBarShown = settings.value('image_viewer/status_bar', True, type=bool)
        self.showStatusBarAct.setChecked(statusBarShown)
        self.statusBar.setVisible(statusBarShown)

    def createMenus(self):
        self.fileMenu = QMenu(self.tr("&File"), self)
        self.fileMenu.addAction(self.saveAct)
#        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu(self.tr("&View"), self)
        self.viewMenu.addAction(self.fullScreenAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.fitToWindowAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.showToolBarAct)
        self.viewMenu.addAction(self.showStatusBarAct)

        self.menuBar.addMenu(self.fileMenu)
        self.menuBar.addMenu(self.viewMenu)

    def createToolBar(self):
        self.toolBar.addAction(self.zoomInAct)
        self.toolBar.addAction(self.zoomOutAct)
        self.toolBar.addAction(self.normalSizeAct)
        self.toolBar.addAction(self.fitToWindowAct)

    def showToolBar(self, status):
        settings = QSettings()
        settings.setValue('image_viewer/tool_bar', status)
        self.toolBar.setVisible(status)

    def showStatusBar(self, status):
        settings = QSettings()
        settings.setValue('image_viewer/status_bar', status)
        self.statusBar.setVisible(status)

    def hasImage(self):
        return self._pixmapHandle is not None

    def clearImage(self):
        if self.hasImage():
            self.scene.removeItem(self._pixmapHandle)
            self._pixmapHandle = None

    def pixmap(self):
        if self.hasImage():
            return self._pixmapHandle.pixmap()
        return None

    def showEvent(self, _e):
        self.updateViewer()

    def resizeEvent(self, _e):
        if self.isVisible():
            self.updateViewer()

    def setImage(self, image):
        pixmap = QPixmap.fromImage(image)

        if self.hasImage():
            self._pixmapHandle.setPixmap(pixmap)
        else:
            self._pixmapHandle = self.scene.addPixmap(pixmap)

        self.sizeLabel.setText("%dx%d" % (image.width(), image.height()))

    def save(self):
        filters = (self.tr("Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif)"),
                   self.tr("All files (*.*)"))
        fileName, _selectedFilter = getSaveFileName(
            self, 'save_image', self.name, OpenNumismat.IMAGE_PATH, filters)
        if fileName:
            self._pixmapHandle.pixmap().save(fileName)

    def done(self, r):
        if self.isFullScreen:
            self.isFullScreen = False

            self.menuBar.show()
            self.toolBar.setVisible(self.showToolBarAct.isChecked())
            self.statusBar.setVisible(self.showStatusBarAct.isChecked())

            self.showNormal()
        else:
            super().done(r)

    def fullScreen(self):
        self.isFullScreen = True

        self.menuBar.hide()
        self.toolBar.hide()
        self.statusBar.hide()

        self.showFullScreen()

    def normalSize(self):
        self.viewer.setTransformationAnchor(QGraphicsView.AnchorViewCenter)

        self.zoom(1 / self.scale)
        self.scale = 1

    def fitToWindow(self):
        self.isFitToWindow = True

        sceneRect = self.viewer.sceneRect()
        if sceneRect.width() > self.viewer.width() or \
                sceneRect.height() > self.viewer.height():
            self.viewer.fitInView(sceneRect, Qt.KeepAspectRatio)
            self.scale = (self.viewer.height() - 4) / sceneRect.height()
        else:
            self.viewer.resetTransform()
            self.scale = 1

        self._updateZoomActions()

    def zoomIn(self):
        self.zoom(ZOOM_IN_FACTOR)

    def zoomOut(self):
        self.zoom(1 / ZOOM_IN_FACTOR)

    def zoom(self, scale):
        need_scale = self.scale * scale
        if need_scale < self.minScale:
            need_scale = self.minScale
            scale = need_scale / self.scale
        if need_scale > ZOOM_MAX:
            need_scale = ZOOM_MAX
            scale = need_scale / self.scale

        if need_scale > self.minScale:
            self.isFitToWindow = False
        else:
            self.isFitToWindow = True

        if need_scale != self.scale:
            self.scale = need_scale
            self.viewer.scale(scale, scale)

        self._updateZoomActions()

    def updateViewer(self):
        if not self.hasImage():
            return

        self.minScale = (self.viewer.height() - 4) / self.viewer.sceneRect().height()
        if self.minScale > 1:
            self.minScale = 1

        if self.isFitToWindow:
            self.fitToWindow()

    def _updateZoomActions(self):
        sceneRect = self.viewer.sceneRect()
        imageRect = self.viewer.mapToScene(self.viewer.rect()).boundingRect()
        if imageRect.contains(sceneRect):
            self.viewer.setDragMode(QGraphicsView.NoDrag)
        else:
            self.viewer.setDragMode(QGraphicsView.ScrollHandDrag)

        self.zoomInAct.setDisabled(self.scale >= ZOOM_MAX)
        self.zoomOutAct.setDisabled(self.scale <= self.minScale)
        self.fitToWindowAct.setDisabled(self.isFitToWindow)
        self.normalSizeAct.setDisabled(self.scale == 1)

        self.zoomLabel.setText("%d%%" % (self.scale * 100 + 0.5))
