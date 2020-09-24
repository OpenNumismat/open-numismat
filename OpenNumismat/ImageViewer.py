from PyQt5.QtCore import Qt, QMargins, QSettings, QObject, QPointF, QRectF, QRect, pyqtSignal, QMimeData, QLineF, QPoint
from PyQt5.QtGui import QPixmap, QPen, QTransform, QImage, QKeySequence, QColor, QPolygonF
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator, storeDlgPositionDecorator
from OpenNumismat.Tools.Gui import createIcon, getSaveFileName

ZOOM_IN_FACTOR = 1.25
ZOOM_MAX = 5


@storeDlgPositionDecorator
class CropDialog(QDialog):
    currentToolChanged = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.tr("Crop"))

        settings = QSettings()
        cropTool = settings.value('crop_dialog/crop_tool', 0)
        self.tab = QTabWidget(self)
        self.tab.addTab(QWidget(), createIcon('shape_handles.png'), '')
        self.tab.addTab(QWidget(), createIcon('shape_handles_free.png'), '')
        self.tab.currentChanged.connect(self.tabChanged)
        self.tab.setCurrentIndex(cropTool)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.tab)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def showEvent(self, _e):
        self.setFixedSize(self.size())

    def tabChanged(self, index):
        settings = QSettings()
        settings.setValue('crop_dialog/crop_tool', self.currentTool())

        self.currentToolChanged.emit(index)

    def currentTool(self):
        return self.tab.currentIndex()


@storeDlgPositionDecorator
class RotateDialog(QDialog):
    valueChanged = pyqtSignal(float)

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.tr("Rotate"))

        angelLabel = QLabel(self.tr("Angel:"))

        angelSlider = QSlider(Qt.Horizontal)
        angelSlider.setRange(-180, 180)
        angelSlider.setTickInterval(10)
        angelSlider.setTickPosition(QSlider.TicksAbove)
        angelSlider.setMinimumWidth(200)

        self.angelSpin = QDoubleSpinBox()
        self.angelSpin.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.angelSpin.setRange(-180, 180)
        self.angelSpin.setSingleStep(0.1)
        self.angelSpin.setAccelerated(True)
        self.angelSpin.setKeyboardTracking(False)

        angelSlider.valueChanged.connect(self.angelSpin.setValue)
        self.angelSpin.valueChanged.connect(angelSlider.setValue)
        self.angelSpin.valueChanged.connect(self.valueChanged.emit)

        angelLayout = QHBoxLayout()
        angelLayout.addWidget(angelLabel)
        angelLayout.addWidget(angelSlider)
        angelLayout.addWidget(self.angelSpin)

        settings = QSettings()
        autoCropEnabled = settings.value('rotate_dialog/auto_crop', False, type=bool)
        self.autoCrop = QCheckBox(self.tr("Auto crop"))
        self.autoCrop.stateChanged.connect(self.autoCropChanged)
        self.autoCrop.setChecked(autoCropEnabled)

        gridEnabled = settings.value('rotate_dialog/grid', False, type=bool)
        self.gridShown = QCheckBox(self.tr("Show grid"))
        self.gridShown.stateChanged.connect(self.gridChanged)
        self.gridShown.setChecked(gridEnabled)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(angelLayout)
        layout.addWidget(self.autoCrop)
        layout.addWidget(self.gridShown)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def showEvent(self, _e):
        self.setFixedSize(self.size())

    def autoCropChanged(self, state):
        settings = QSettings()
        settings.setValue('rotate_dialog/auto_crop', state)

        self.valueChanged.emit(self.angelSpin.value())

    def isAutoCrop(self):
        return self.autoCrop.isChecked()

    def gridChanged(self, state):
        settings = QSettings()
        settings.setValue('rotate_dialog/grid', state)

        self.valueChanged.emit(self.angelSpin.value())

    def isGridShown(self):
        return self.gridShown.isChecked()


class BoundingPointItem(QGraphicsRectItem):
    SIZE = 4
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_RIGHT = 2
    BOTTOM_LEFT = 3

    def __init__(self, bounding, width, height, corner, fixed):
        self.bounding = bounding
        self.width = width
        self.height = height
        self.corner = corner
        self.fixed = fixed

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
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
#        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return self.bounding.update(self, value)

        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.corner in (self.TOP_LEFT, self.BOTTOM_RIGHT):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.SizeBDiagCursor)

        super().hoverEnterEvent(event)


class BoundingLineItem(QGraphicsLineItem):

    def __init__(self, bounding, fixed):
        self.bounding = bounding
        self.fixed = fixed

        super().__init__()

        self.setPen(QPen(Qt.DashLine))
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        if self.fixed:
            self.setFlag(QGraphicsItem.ItemIsMovable)
            self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
#            self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
            self.setAcceptHoverEvents(True)

    def _isHorizontal(self):
        angle = self.line().angle()
        return (angle in (0, 180))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            return self.bounding.update(self, value)

        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self._isHorizontal():
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeHorCursor)

        super().hoverEnterEvent(event)


class GraphicsBoundingItem(QObject):

    def __init__(self, width, height, scale, fixed):
        super().__init__()

        self.width = width
        self.height = height
        self.scale = scale
        self.fixed = fixed

        point1 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP_LEFT, self.fixed)
        point2 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP_RIGHT, self.fixed)
        point3 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM_RIGHT, self.fixed)
        point4 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM_LEFT, self.fixed)

        self.points = [point1, point2, point3, point4]

        line1 = BoundingLineItem(self, self.fixed)
        line2 = BoundingLineItem(self, self.fixed)
        line3 = BoundingLineItem(self, self.fixed)
        line4 = BoundingLineItem(self, self.fixed)

        self.lines = [line1, line2, line3, line4]

        self.updateRect()

    def update(self, obj, pos):
        p1 = self.points[BoundingPointItem.TOP_LEFT]
        p2 = self.points[BoundingPointItem.TOP_RIGHT]
        p3 = self.points[BoundingPointItem.BOTTOM_RIGHT]
        p4 = self.points[BoundingPointItem.BOTTOM_LEFT]

        for item in self.items():
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)

        if obj in self.lines:
            line = obj
            if line in (self.lines[0], self.lines[2]):
                pos.setX(0)
            else:
                pos.setY(0)

            newPos = line.line().p1() / self.scale + pos
            if line == self.lines[0]:  # --
                if newPos.y() < 0:
                    newPos.setY(0)
                oppositePos = p3.pos()
                if newPos.y() > oppositePos.y() - BoundingPointItem.SIZE:
                    newPos.setY(oppositePos.y() - BoundingPointItem.SIZE)

                p1.setY(newPos.y())
                p2.setY(newPos.y())
                x1 = self.lines[1].line().x1()
                x2 = self.lines[1].line().x2()
                self.lines[1].setLine(x1, p2.y() * self.scale,
                                      x2, p3.y() * self.scale)
                x1 = self.lines[3].line().x1()
                x2 = self.lines[3].line().x2()
                self.lines[3].setLine(x1, p4.y() * self.scale,
                                      x2, p1.y() * self.scale)
            elif line == self.lines[1]:  # |
                if newPos.x() > self.width:
                    newPos.setX(self.width)
                oppositePos = p1.pos()
                if newPos.x() < oppositePos.x() + BoundingPointItem.SIZE:
                    newPos.setX(oppositePos.x() + BoundingPointItem.SIZE)

                p2.setX(newPos.x())
                p3.setX(newPos.x())
                y1 = self.lines[0].line().y1()
                y2 = self.lines[0].line().y2()
                self.lines[0].setLine(p1.x() * self.scale, y1,
                                      p2.x() * self.scale, y2)
                y1 = self.lines[2].line().y1()
                y2 = self.lines[2].line().y2()
                self.lines[2].setLine(p3.x() * self.scale, y1,
                                      p4.x() * self.scale, y2)
            elif line == self.lines[2]:  # --
                if newPos.y() > self.height:
                    newPos.setY(self.height)
                oppositePos = p1.pos()
                if newPos.y() < oppositePos.y() + BoundingPointItem.SIZE:
                    newPos.setY(oppositePos.y() + BoundingPointItem.SIZE)

                p3.setY(newPos.y())
                p4.setY(newPos.y())
                x1 = self.lines[1].line().x1()
                x2 = self.lines[1].line().x2()
                self.lines[1].setLine(x1, p2.y() * self.scale,
                                      x2, p3.y() * self.scale)
                x1 = self.lines[3].line().x1()
                x2 = self.lines[3].line().x2()
                self.lines[3].setLine(x1, p4.y() * self.scale,
                                      x2, p1.y() * self.scale)
            else:
                if newPos.x() < 0:
                    newPos.setX(0)
                oppositePos = p2.pos()
                if newPos.x() > oppositePos.x() - BoundingPointItem.SIZE:
                    newPos.setX(oppositePos.x() - BoundingPointItem.SIZE)

                p1.setX(newPos.x())
                p4.setX(newPos.x())
                y1 = self.lines[0].line().y1()
                y2 = self.lines[0].line().y2()
                self.lines[0].setLine(p1.x() * self.scale, y1,
                                      p2.x() * self.scale, y2)
                y1 = self.lines[2].line().y1()
                y2 = self.lines[2].line().y2()
                self.lines[2].setLine(p3.x() * self.scale, y1,
                                      p4.x() * self.scale, y2)

            pos = newPos - line.line().p1() / self.scale
        elif obj in self.points:
            point = obj
            newPos = pos
            if point.corner == point.TOP_LEFT:
                if newPos.x() < 0:
                    newPos.setX(0)
                if newPos.y() < 0:
                    newPos.setY(0)

                oppositePos = p2.scenePos()
                if newPos.x() > oppositePos.x() - point.SIZE:
                    newPos.setX(oppositePos.x() - point.SIZE)
                oppositePos = p4.scenePos()
                if newPos.y() > oppositePos.y() - point.SIZE:
                    newPos.setY(oppositePos.y() - point.SIZE)

                if self.fixed:
                    self.points[point.BOTTOM_LEFT].setX(newPos.x())
                    self.points[point.TOP_RIGHT].setY(newPos.y())
            elif point.corner == point.TOP_RIGHT:
                if newPos.x() > self.width:
                    newPos.setX(self.width)
                if newPos.y() < 0:
                    newPos.setY(0)

                oppositePos = p1.scenePos()
                if newPos.x() < oppositePos.x() + point.SIZE:
                    newPos.setX(oppositePos.x() + point.SIZE)
                oppositePos = p3.scenePos()
                if newPos.y() > oppositePos.y() - point.SIZE:
                    newPos.setY(oppositePos.y() - point.SIZE)

                if self.fixed:
                    self.points[point.BOTTOM_RIGHT].setX(newPos.x())
                    self.points[point.TOP_LEFT].setY(newPos.y())
            elif point.corner == point.BOTTOM_RIGHT:
                if newPos.x() > self.width:
                    newPos.setX(self.width)
                if newPos.y() > self.height:
                    newPos.setY(self.height)

                oppositePos = p4.scenePos()
                if newPos.x() < oppositePos.x() + point.SIZE:
                    newPos.setX(oppositePos.x() + point.SIZE)
                oppositePos = p2.scenePos()
                if newPos.y() < oppositePos.y() + point.SIZE:
                    newPos.setY(oppositePos.y() + point.SIZE)

                if self.fixed:
                    self.points[point.BOTTOM_LEFT].setY(newPos.y())
                    self.points[point.TOP_RIGHT].setX(newPos.x())
            else:  # self.corner == self.BOTTOM_LEFT
                if newPos.x() < 0:
                    newPos.setX(0)
                if newPos.y() > self.height:
                    newPos.setY(self.height)

                oppositePos = p3.scenePos()
                if newPos.x() > oppositePos.x() - point.SIZE:
                    newPos.setX(oppositePos.x() - point.SIZE)
                oppositePos = p1.scenePos()
                if newPos.y() < oppositePos.y() + point.SIZE:
                    newPos.setY(oppositePos.y() + point.SIZE)

                if self.fixed:
                    self.points[point.BOTTOM_RIGHT].setY(newPos.y())
                    self.points[point.TOP_LEFT].setX(newPos.x())

            self.updateRect()
            pos = newPos

        for item in self.items():
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        return pos

    def updateRect(self):
        p1 = self.points[BoundingPointItem.TOP_LEFT]
        p2 = self.points[BoundingPointItem.TOP_RIGHT]
        p3 = self.points[BoundingPointItem.BOTTOM_RIGHT]
        p4 = self.points[BoundingPointItem.BOTTOM_LEFT]
        self.lines[0].setLine(p1.x() * self.scale, p1.y() * self.scale,
                              p2.x() * self.scale, p2.y() * self.scale)
        self.lines[1].setLine(p2.x() * self.scale, p2.y() * self.scale,
                              p3.x() * self.scale, p3.y() * self.scale)
        self.lines[2].setLine(p3.x() * self.scale, p3.y() * self.scale,
                              p4.x() * self.scale, p4.y() * self.scale)
        self.lines[3].setLine(p4.x() * self.scale, p4.y() * self.scale,
                              p1.x() * self.scale, p1.y() * self.scale)

    def setScale(self, scale):
        self.scale = scale

        self.updateRect()

    def items(self):
        return self.lines + self.points

    def cropPoints(self):
        return [p.pos() for p in self.points]


class GraphicsGridItem(QObject):
    STEP = 40

    def __init__(self, width, height, scale):
        super().__init__()

        self.width = width * scale - 1
        self.height = height * scale - 1

        self.v_lines = []
        for i in range(int(self.width / self.STEP) + 1):
            line = QGraphicsLineItem()
            line.setPen(QPen(QColor(Qt.red)))
            line.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            line.setLine(i * self.STEP, 0, i * self.STEP, self.height)

            self.v_lines.append(line)

        self.h_lines = []
        for i in range(int(self.height / self.STEP) + 1):
            line = QGraphicsLineItem()
            line.setPen(QPen(QColor(Qt.red)))
            line.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self.h_lines.append(line)

            line.setLine(0, i * self.STEP, self.width, i * self.STEP)

    def items(self):
        return self.v_lines + self.h_lines


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
        self.rotateDlg = None
        self.grid = None
        self.bounding = None
        self.isFullScreen = False
        self.name = 'photo'
        self._pixmapHandle = None
        self._origPixmap = None
        self._startPixmap = None
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
        self.rotateAct = QAction(self.tr("Rotate..."), self, checkable=True, triggered=self.rotate)
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
        self.editMenu.addAction(self.rotateAct)
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

        self.viewer.setSceneRect(QRectF(pixmap.rect()))
        self.updateViewer()

        self.sizeLabel.setText("%dx%d" % (image.width(), image.height()))

    def saveAs(self):
        filters = (self.tr("Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif)"),
                   self.tr("All files (*.*)"))
        fileName, _selectedFilter = getSaveFileName(
            self, 'save_image', self.name, OpenNumismat.IMAGE_PATH, filters)
        if fileName:
            self._pixmapHandle.pixmap().save(fileName)

    def done(self, r):
        if self.cropDlg and self.cropDlg.isVisible():
            self.cropDlg.close()
            return
        if self.rotateDlg and self.rotateDlg.isVisible():
            self.rotateDlg.close()
            return

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

        self._updateGrid()
        if self.bounding:
            self.bounding.setScale(self.scale)

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

            self._updateGrid()
            if self.bounding:
                self.bounding.setScale(self.scale)

        self._updateZoomActions()

    def updateViewer(self):
        if not self.hasImage():
            return

        self.minScale = (self.viewer.height() - 4) / self.viewer.sceneRect().height()
        if self.minScale > 1:
            self.minScale = 1

        if self.isFitToWindow:
            self.fitToWindow()

        self._updateGrid()
        if self.bounding:
            self.bounding.setScale(self.scale)

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
        pixmap = pixmap.transformed(trans)
        self.setImage(pixmap)

        self.isChanged = True
        self._updateEditActions()

    def rotateRight(self):
        transform = QTransform()
        trans = transform.rotate(90)
        pixmap = self._pixmapHandle.pixmap()
        pixmap = pixmap.transformed(trans)
        self.setImage(pixmap)

        self.isChanged = True
        self._updateEditActions()

    def _updateGrid(self):
        if self.grid:
            for item in self.grid.items():
                self.scene.removeItem(item)

        if self.rotateDlg and self.rotateDlg.isVisible():
            if self.rotateDlg.isGridShown():
                sceneRect = self.viewer.sceneRect()
                w = sceneRect.width()
                h = sceneRect.height()
                self.grid = GraphicsGridItem(w, h, self.scale)
                for item in self.grid.items():
                    self.scene.addItem(item)
            else:
                self.grid = None
        else:
            self.grid = None

    def rotate(self, checked):
        if checked:
            self.rotateDlg = RotateDialog(self)
            self.rotateDlg.valueChanged.connect(self.rotateChanged)
            self.rotateDlg.finished.connect(self.closeRotate)
            self.rotateDlg.show()
            self._startPixmap = self._pixmapHandle.pixmap()

            self._updateEditActions()
        else:
            self.rotateDlg.close()
            self.rotateDlg = None

        self._updateGrid()

    def rotateChanged(self, value):
        transform = QTransform()
        trans = transform.rotate(value)
        pixmap = self._startPixmap.transformed(trans, Qt.SmoothTransformation)
        if self.rotateDlg.isAutoCrop():
            if (-45 < value and value < 45) or value < -135 or 135 < value:
                xoffset = (pixmap.width() - self._startPixmap.width()) / 2
                yoffset = (pixmap.height() - self._startPixmap.height()) / 2
                rect = QRect(xoffset, yoffset, self._startPixmap.width(), self._startPixmap.height())
            else:
                xoffset = (pixmap.width() - self._startPixmap.height()) / 2
                yoffset = (pixmap.height() - self._startPixmap.width()) / 2
                rect = QRect(xoffset, yoffset, self._startPixmap.height(), self._startPixmap.width())
            pixmap = pixmap.copy(rect)

        self.setImage(pixmap)

        self._updateGrid()

    def closeRotate(self, result):
        self._updateGrid()

        if result:
            self.isChanged = True
        else:
            self.setImage(self._startPixmap)

        self._startPixmap = None

        self.rotateAct.setChecked(False)
        self._updateEditActions()

    def crop(self, checked):
        if checked:
            self.cropDlg = CropDialog(self)
            self.cropDlg.finished.connect(self.closeCrop)
            self.cropDlg.currentToolChanged.connect(self.cropToolChanged)
            self.cropDlg.show()

            self.cropToolChanged(self.cropDlg.currentTool())

            self._updateEditActions()
        else:
            self.cropDlg.close()
            self.cropDlg = None

    def cropToolChanged(self, _index):
        if self.bounding:
            for item in self.bounding.items():
                self.scene.removeItem(item)
            self.bounding = None

        sceneRect = self.viewer.sceneRect()
        w = sceneRect.width()
        h = sceneRect.height()

        fixed_bounding = (self.cropDlg.currentTool() == 0)
        self.bounding = GraphicsBoundingItem(w, h, self.scale, fixed_bounding)
        for item in self.bounding.items():
            self.scene.addItem(item)

    def closeCrop(self, result):
        points = self.bounding.cropPoints()

        for item in self.bounding.items():
            self.scene.removeItem(item)
        self.bounding = None

        if result:
            if self.cropDlg.currentTool() == 0:
                rect = QRectF(points[0], points[2]).toRect()

                pixmap = self._pixmapHandle.pixmap()
                pixmap = pixmap.copy(rect)
                self.setImage(pixmap)

                self.isChanged = True
            else:
                topLine = QLineF(points[0], points[1])
                bottomLine = QLineF(points[2], points[3])
                leftLine = QLineF(points[1], points[2])
                rightLine = QLineF(points[3], points[0])

                if topLine.length() > bottomLine.length():
                    width = topLine.length()
                else:
                    width = bottomLine.length()
                if leftLine.length() > rightLine.length():
                    height = leftLine.length()
                else:
                    height = rightLine.length()

                poly1 = QPolygonF(points)

                poly2 = QPolygonF()
                poly2.append(QPointF(0, 0))
                poly2.append(QPointF(width, 0))
                poly2.append(QPointF(width, height))
                poly2.append(QPointF(0, height))

                transform = QTransform()
                res = QTransform.quadToQuad(poly1, poly2, transform)
                if res:
                    rect = self._pixmapHandle.pixmap().rect()
                    tl = transform.map(QPoint(0, 0))
                    bl = transform.map(QPoint(0, rect.height()))
                    tr = transform.map(QPoint(rect.width(), 0))

                    if -tl.x() > -bl.x():
                        x = -tl.x()
                    else:
                        x = -bl.x()

                    if -tr.y() > -tl.y():
                        y = -tr.y()
                    else:
                        y = -tl.y()

                    pixmap = self._pixmapHandle.pixmap().transformed(transform, Qt.SmoothTransformation)
                    pixmap = pixmap.copy(x, y, width, height)
                    self.setImage(pixmap)

                    self.isChanged = True

        self.cropAct.setChecked(False)
        self._updateEditActions()

    def _updateEditActions(self):
        inCrop = self.cropAct.isChecked()
        inRotate = self.rotateAct.isChecked()
        self.rotateLeftAct.setDisabled(inCrop or inRotate)
        self.rotateRightAct.setDisabled(inCrop or inRotate)
        self.rotateAct.setDisabled(inCrop)
        self.cropAct.setDisabled(inRotate)

        self.saveAct.setEnabled(self.isChanged)

    def save(self):
        if self.isChanged:
            self._origPixmap = self._pixmapHandle.pixmap()
            self.imageSaved.emit(self.getImage())

        self.isChanged = False
        self._updateEditActions()

    def getImage(self):
        return self._origPixmap.toImage()
