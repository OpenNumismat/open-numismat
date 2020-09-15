from PyQt5.QtCore import Qt, QMargins
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Gui import getSaveFileName

ZOOM_IN_FACTOR = 1.25


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

        self.status = QStatusBar()

        self.sizeLabel = QLabel()
        self.status.addWidget(self.sizeLabel)

        self.zoomLabel = QLabel()
        self.status.addWidget(self.zoomLabel)

        layout = QVBoxLayout()
        layout.setMenuBar(self.menuBar)
        layout.addWidget(self.viewer)
        layout.addWidget(self.status)
        layout.setContentsMargins(QMargins())
        self.setLayout(layout)

        self.name = 'photo'
        self._pixmapHandle = None
        self.scale = 1
        self.minScale = 0.2
        self.isFitToWindow = True

        self.createActions()
        self.createMenus()

    def createActions(self):
        self.saveAct = QAction(self.tr("&Save As..."), self, shortcut="Ctrl+S", triggered=self.save)
#        self.printAct = QAction(self.tr("&Print..."), self, shortcut="Ctrl+P", enabled=False, triggered=self.print_)
        self.exitAct = QAction(self.tr("E&xit"), self, shortcut="Ctrl+Q", triggered=self.close)
#        self.fullScreenAct = QAction(self.tr("Full Screen"), self, shortcut="F11", triggered=self.fullScreen)
        self.zoomInAct = QAction(self.tr("Zoom &In (25%)"), self, shortcut="+", triggered=self.zoomIn)
        self.zoomOutAct = QAction(self.tr("Zoom &Out (25%)"), self, shortcut="-", triggered=self.zoomOut)
        self.normalSizeAct = QAction(self.tr("&Normal Size"), self, triggered=self.normalSize)
        self.fitToWindowAct = QAction(self.tr("&Fit to Window"), self, triggered=self.fitToWindow)
#        self.showTabBarAct = QAction(self.tr("Show Tab Bar"), self, checkable=True, triggered=self.showTabBar)

    def createMenus(self):
        self.fileMenu = QMenu(self.tr("&File"), self)
        self.fileMenu.addAction(self.saveAct)
#        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu(self.tr("&View"), self)
#        self.viewMenu.addAction(self.fullScreenAct)
#        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.fitToWindowAct)
#        self.viewMenu.addSeparator()
#        self.viewMenu.addAction(self.showTabBarAct)

        self.menuBar.addMenu(self.fileMenu)
        self.menuBar.addMenu(self.viewMenu)

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

        self.zoomLabel.setText("%d%%" % (self.scale * 100 + 0.5))

    def zoomIn(self):
        self.zoom(ZOOM_IN_FACTOR)

    def zoomOut(self):
        self.zoom(1 / ZOOM_IN_FACTOR)

    def zoom(self, scale):
        need_scale = self.scale * scale
        if need_scale < self.minScale:
            need_scale = self.minScale
            scale = need_scale / self.scale
        if need_scale > 5:
            need_scale = 5
            scale = need_scale / self.scale

        if need_scale > self.minScale:
            self.isFitToWindow = False
        else:
            self.isFitToWindow = True

        if need_scale != self.scale:
            self.scale = need_scale
            self.viewer.scale(scale, scale)

            sceneRect = self.viewer.sceneRect()
            imageRect = self.viewer.mapToScene(self.viewer.rect()).boundingRect()
            if imageRect.contains(sceneRect):
                self.viewer.setDragMode(QGraphicsView.NoDrag)
            else:
                self.viewer.setDragMode(QGraphicsView.ScrollHandDrag)

            self.zoomLabel.setText("%d%%" % (self.scale * 100 + 0.5))

    def updateViewer(self):
        self.minScale = (self.viewer.height() - 4) / self.viewer.sceneRect().height()
        if self.minScale > 1:
            self.minScale = 1

        if self.isFitToWindow:
            self.fitToWindow()
