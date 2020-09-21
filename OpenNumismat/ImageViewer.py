from PyQt5.QtCore import Qt, QMargins, QSettings, QObject, QPointF, QRectF, QRect, pyqtSignal, QMimeData
from PyQt5.QtGui import QPixmap, QPen, QTransform, QImage, QKeySequence
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator, storeDlgPositionDecorator
from OpenNumismat.Tools.Gui import createIcon, getSaveFileName

ZOOM_IN_FACTOR = 1.25
ZOOM_MAX = 5


@storeDlgPositionDecorator
class CropDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.tr("Crop"))

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
#        layout.addWidget(tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def showEvent(self, _e):
        self.setFixedSize(self.size())


class BoundingPointItem(QGraphicsRectItem):
    SIZE = 4
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_RIGHT = 2
    BOTTOM_LEFT = 3

    def __init__(self, bounding, width, height, corner):
        self.bounding = bounding
        self.width = width
        self.height = height
        self.corner = corner

        if corner == self.TOP_LEFT:
            x = 0
            y = 0
        elif corner == self.TOP_RIGHT:
            x = width
            y = 0
        elif corner == self.BOTTOM_RIGHT:
            x = width
            y = height
        else:  # corner == self.BOTTOM_LEFT
            x = 0
            y = height

        super().__init__(-self.SIZE / 2, -self.SIZE / 2, self.SIZE, self.SIZE)
        self.setPos(QPointF(x, y))

        self.setBrush(Qt.white)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
#        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            newPos = value
            if self.corner == self.TOP_LEFT:
                if newPos.x() < 0:
                    newPos.setX(0)
                if newPos.y() < 0:
                    newPos.setY(0)

                oppositePoint = self.bounding.points[self.BOTTOM_RIGHT]
                oppositePos = oppositePoint.scenePos()
                if newPos.x() > oppositePos.x() - self.SIZE:
                    newPos.setX(oppositePos.x() - self.SIZE)
                if newPos.y() > oppositePos.y() - self.SIZE:
                    newPos.setY(oppositePos.y() - self.SIZE)

                self.bounding.points[self.BOTTOM_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.TOP_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.BOTTOM_LEFT].setX(newPos.x())
                self.bounding.points[self.TOP_RIGHT].setY(newPos.y())
                self.bounding.points[self.BOTTOM_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
                self.bounding.points[self.TOP_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)

                self.bounding.rect.setRect(QRectF(newPos, oppositePos).normalized())
            elif self.corner == self.TOP_RIGHT:
                if newPos.x() > self.width:
                    newPos.setX(self.width)
                if newPos.y() < 0:
                    newPos.setY(0)

                oppositePoint = self.bounding.points[self.BOTTOM_LEFT]
                oppositePos = oppositePoint.scenePos()
                if newPos.x() < oppositePos.x() + self.SIZE:
                    newPos.setX(oppositePos.x() + self.SIZE)
                if newPos.y() > oppositePos.y() - self.SIZE:
                    newPos.setY(oppositePos.y() - self.SIZE)

                self.bounding.points[self.BOTTOM_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.TOP_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.BOTTOM_RIGHT].setX(newPos.x())
                self.bounding.points[self.TOP_LEFT].setY(newPos.y())
                self.bounding.points[self.BOTTOM_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
                self.bounding.points[self.TOP_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)

                self.bounding.rect.setRect(QRectF(newPos, oppositePos).normalized())
            elif self.corner == self.BOTTOM_RIGHT:
                if newPos.x() > self.width:
                    newPos.setX(self.width)
                if newPos.y() > self.height:
                    newPos.setY(self.height)

                oppositePoint = self.bounding.points[self.TOP_LEFT]
                oppositePos = oppositePoint.scenePos()
                if newPos.x() < oppositePos.x() + self.SIZE:
                    newPos.setX(oppositePos.x() + self.SIZE)
                if newPos.y() < oppositePos.y() + self.SIZE:
                    newPos.setY(oppositePos.y() + self.SIZE)

                self.bounding.points[self.BOTTOM_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.TOP_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.BOTTOM_LEFT].setY(newPos.y())
                self.bounding.points[self.TOP_RIGHT].setX(newPos.x())
                self.bounding.points[self.BOTTOM_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
                self.bounding.points[self.TOP_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)

                self.bounding.rect.setRect(QRectF(newPos, oppositePos).normalized())
            else:  # self.corner == self.BOTTOM_LEFT
                if newPos.x() < 0:
                    newPos.setX(0)
                if newPos.y() > self.height:
                    newPos.setY(self.height)

                oppositePoint = self.bounding.points[self.TOP_RIGHT]
                oppositePos = oppositePoint.scenePos()
                if newPos.x() > oppositePos.x() - self.SIZE:
                    newPos.setX(oppositePos.x() - self.SIZE)
                if newPos.y() < oppositePos.y() + self.SIZE:
                    newPos.setY(oppositePos.y() + self.SIZE)

                self.bounding.points[self.BOTTOM_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.TOP_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                self.bounding.points[self.BOTTOM_RIGHT].setY(newPos.y())
                self.bounding.points[self.TOP_LEFT].setX(newPos.x())
                self.bounding.points[self.BOTTOM_RIGHT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
                self.bounding.points[self.TOP_LEFT].setFlag(QGraphicsItem.ItemSendsGeometryChanges)

                self.bounding.rect.setRect(QRectF(newPos, oppositePos).normalized())

            return newPos

        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.corner in (self.TOP_LEFT, self.BOTTOM_RIGHT):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.SizeBDiagCursor)

        super().hoverEnterEvent(event)


class GraphicsBoundingItem(QObject):

    def __init__(self, width, height):
        super().__init__()

        self.width = width
        self.height = height

        point1 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP_LEFT)
        point2 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP_RIGHT)
        point3 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM_RIGHT)
        point4 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM_LEFT)

        self.rect = QGraphicsRectItem(0, 0, self.width, self.height)
        self.rect.setPen(QPen(Qt.DashLine))

        self.points = [point1, point2, point3, point4]

    def items(self):
        return [self.rect] + self.points


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
    imageSaved = pyqtSignal(QImage)

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

        self.isChanged = False
        self.cropDlg = None
        self.bounding = None
        self.isFullScreen = False
        self.name = 'photo'
        self._pixmapHandle = None
        self._origPixmap = None
        self.scale = 1
        self.minScale = 0.2
        self.isFitToWindow = True

        self.createActions()
        self.createMenus()
        self.createToolBar()

    def createActions(self):
        self.saveAsAct = QAction(self.tr("&Save As..."), self, shortcut=QKeySequence.SaveAs, triggered=self.saveAs)
#        self.printAct = QAction(self.tr("&Print..."), self, shortcut=QKeySequence.Print, enabled=False, triggered=self.print_)
        self.exitAct = QAction(self.tr("E&xit"), self, shortcut=QKeySequence.Quit, triggered=self.close)
        self.fullScreenAct = QAction(self.tr("Full Screen"), self, shortcut=QKeySequence.FullScreen, triggered=self.fullScreen)
        self.zoomInAct = QAction(createIcon('zoom_in.png'), self.tr("Zoom &In (25%)"), self, triggered=self.zoomIn)
        self.zoomInShortcut = QShortcut(Qt.Key_Plus, self, self.zoomIn)
        self.zoomOutAct = QAction(createIcon('zoom_out.png'), self.tr("Zoom &Out (25%)"), self, triggered=self.zoomOut)
        self.zoomOutShortcut = QShortcut(Qt.Key_Minus, self, self.zoomOut)
        self.normalSizeAct = QAction(createIcon('arrow_out.png'), self.tr("&Normal Size"), self, triggered=self.normalSize)
        self.fitToWindowAct = QAction(createIcon('arrow_in.png'), self.tr("&Fit to Window"), self, triggered=self.fitToWindow)
        self.showToolBarAct = QAction(self.tr("Show Tool Bar"), self, checkable=True, triggered=self.showToolBar)
        self.showStatusBarAct = QAction(self.tr("Show Status Bar"), self, checkable=True, triggered=self.showStatusBar)
        self.rotateLeftAct = QAction(createIcon('arrow_rotate_anticlockwise.png'), self.tr("Rotate to Left"), self, triggered=self.rotateLeft)
        self.rotateRightAct = QAction(createIcon('arrow_rotate_clockwise.png'), self.tr("Rotate to Right"), self, triggered=self.rotateRight)
        self.cropAct = QAction(createIcon('shape_handles.png'), self.tr("Crop"), self, checkable=True, triggered=self.crop)
        self.saveAct = QAction(createIcon('save.png'), self.tr("Save"), self, shortcut=QKeySequence.Save, triggered=self.save)
        self.saveAct.setDisabled(True)
        self.copyAct = QAction(createIcon('page_copy.png'), self.tr("Copy"), self, shortcut=QKeySequence.Copy, triggered=self.copy)

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
        self.fileMenu.addAction(self.saveAsAct)
#        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = QMenu(self.tr("&Edit"), self)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.rotateLeftAct)
        self.editMenu.addAction(self.rotateRightAct)
        self.editMenu.addAction(self.cropAct)

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
        self.menuBar.addMenu(self.editMenu)
        self.menuBar.addMenu(self.viewMenu)

    def createToolBar(self):
        self.toolBar.addAction(self.zoomInAct)
        self.toolBar.addAction(self.zoomOutAct)
        self.toolBar.addAction(self.normalSizeAct)
        self.toolBar.addAction(self.fitToWindowAct)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.rotateLeftAct)
        self.toolBar.addAction(self.rotateRightAct)
        self.toolBar.addAction(self.cropAct)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.saveAct)

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
        if type(image) is QPixmap:
            pixmap = image
        else:
            pixmap = QPixmap.fromImage(image)

        if self.hasImage():
            self._pixmapHandle.setPixmap(pixmap)
        else:
            self._origPixmap = pixmap
            self._pixmapHandle = self.scene.addPixmap(pixmap)

        self.sizeLabel.setText("%dx%d" % (image.width(), image.height()))

    def saveAs(self):
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
            if self.isChanged:
                result = QMessageBox.warning(
                    self, self.tr("Save"),
                    self.tr("Image was changed. Save changes?"),
                    QMessageBox.Save | QMessageBox.No, QMessageBox.No)
                if result == QMessageBox.Save:
                    self.save()

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

    def copy(self):
        image = self._pixmapHandle.pixmap().toImage()
        mime = QMimeData()
        mime.setImageData(image)

        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime)

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

        self._updateZoomActions()

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

    def rotateLeft(self):
        transform = QTransform()
        trans = transform.rotate(-90)
        pixmap = self._pixmapHandle.pixmap()
        pixmap = QPixmap(pixmap.transformed(trans))
        self.setImage(pixmap)
        self.viewer.setSceneRect(QRectF(pixmap.rect()))

        self.isChanged = True
        self._updateEditActions()

    def rotateRight(self):
        transform = QTransform()
        trans = transform.rotate(90)
        pixmap = self._pixmapHandle.pixmap()
        pixmap = QPixmap(pixmap.transformed(trans))
        self.setImage(pixmap)
        self.viewer.setSceneRect(QRectF(pixmap.rect()))

        self.isChanged = True
        self._updateEditActions()

    def crop(self, checked):
        if checked:
            sceneRect = self.viewer.sceneRect()
            w = sceneRect.width()
            h = sceneRect.height()

            self.bounding = GraphicsBoundingItem(w, h)
            for item in self.bounding.items():
                self.scene.addItem(item)

            self.cropDlg = CropDialog(self)
            self.cropDlg.finished.connect(self.closeCrop)
            self.cropDlg.show()

            self._updateEditActions()
        else:
            self.cropDlg.close()
            self.cropDlg = None

    def closeCrop(self, result):
        pixmap = self._pixmapHandle.pixmap()
        if result:
            rect = self.bounding.rect.rect().toRect()
            pixmap = pixmap.copy(rect)
            self.setImage(pixmap)

            self.isChanged = True

        for item in self.bounding.items():
            self.scene.removeItem(item)
        self.bounding = None

        self.viewer.setSceneRect(QRectF(pixmap.rect()))

        self.cropAct.setChecked(False)
        self._updateEditActions()

    def _updateEditActions(self):
        inCrop = self.cropAct.isChecked()
        self.rotateLeftAct.setDisabled(inCrop)
        self.rotateRightAct.setDisabled(inCrop)

        self.saveAct.setEnabled(self.isChanged)

    def save(self):
        if self.isChanged:
            self._origPixmap = self._pixmapHandle.pixmap()
            self.imageSaved.emit(self.getImage())

        self.isChanged = False
        self._updateEditActions()

    def getImage(self):
        return self._origPixmap.toImage()
