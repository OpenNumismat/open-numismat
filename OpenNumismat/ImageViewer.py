from PyQt5.QtCore import Qt, QMargins, QSettings, QObject, QPointF, QRectF, QRect, pyqtSignal, QMimeData, QLineF, QPoint
from PyQt5.QtGui import QPixmap, QPen, QTransform, QImage, QKeySequence, QColor, QPolygonF, QPainter, QBitmap
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator, storeDlgPositionDecorator
from OpenNumismat.Tools.Gui import createIcon, getSaveFileName

ZOOM_IN_FACTOR = 1.25
ZOOM_MAX = 5


@storeDlgPositionDecorator
class CropDialog(QDialog):
    currentToolChanged = pyqtSignal(int)
    cropChanged = pyqtSignal()

    def __init__(self, width, height, parent):
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.tr("Crop"))

        self.xSpin = QSpinBox()
        self.xSpin.setMaximum(width)
        self.xSpin.valueChanged.connect(self.cropChanged.emit)
        self.ySpin = QSpinBox()
        self.ySpin.setMaximum(height)
        self.ySpin.valueChanged.connect(self.cropChanged.emit)
        self.widthSpin = QSpinBox()
        self.widthSpin.setMaximum(width)
        self.widthSpin.valueChanged.connect(self.cropChanged.emit)
        self.heightSpin = QSpinBox()
        self.heightSpin.setMaximum(height)
        self.heightSpin.valueChanged.connect(self.cropChanged.emit)

        rectLayout = QGridLayout()
        rectLayout.addWidget(QLabel(self.tr("X")), 0, 0)
        rectLayout.addWidget(self.xSpin, 0, 1)
        rectLayout.addWidget(QLabel(self.tr("Y")), 0, 2)
        rectLayout.addWidget(self.ySpin, 0, 3)
        rectLayout.addWidget(QLabel(self.tr("Width")), 1, 0)
        rectLayout.addWidget(self.widthSpin, 1, 1)
        rectLayout.addWidget(QLabel(self.tr("Height")), 1, 2)
        rectLayout.addWidget(self.heightSpin, 1, 3)

        rectWidget = QWidget()
        rectWidget.setLayout(rectLayout)

        self.x1Spin = QSpinBox()
        self.x1Spin.setMaximum(width)
        self.x1Spin.valueChanged.connect(self.cropChanged.emit)
        self.y1Spin = QSpinBox()
        self.y1Spin.setMaximum(height)
        self.y1Spin.valueChanged.connect(self.cropChanged.emit)
        self.x2Spin = QSpinBox()
        self.x2Spin.setMaximum(width)
        self.x2Spin.valueChanged.connect(self.cropChanged.emit)
        self.y2Spin = QSpinBox()
        self.y2Spin.setMaximum(height)
        self.y2Spin.valueChanged.connect(self.cropChanged.emit)
        self.x3Spin = QSpinBox()
        self.x3Spin.setMaximum(width)
        self.x3Spin.valueChanged.connect(self.cropChanged.emit)
        self.y3Spin = QSpinBox()
        self.y3Spin.setMaximum(height)
        self.y3Spin.valueChanged.connect(self.cropChanged.emit)
        self.x4Spin = QSpinBox()
        self.x4Spin.setMaximum(width)
        self.x4Spin.valueChanged.connect(self.cropChanged.emit)
        self.y4Spin = QSpinBox()
        self.y4Spin.setMaximum(height)
        self.y4Spin.valueChanged.connect(self.cropChanged.emit)

        quadLayout = QGridLayout()
        quadLayout.addWidget(QLabel(self.tr("X1")), 0, 0)
        quadLayout.addWidget(self.x1Spin, 0, 1)
        quadLayout.addWidget(QLabel(self.tr("Y1")), 0, 2)
        quadLayout.addWidget(self.y1Spin, 0, 3)
        quadLayout.addWidget(QLabel(self.tr("X2")), 0, 4)
        quadLayout.addWidget(self.x2Spin, 0, 5)
        quadLayout.addWidget(QLabel(self.tr("Y2")), 0, 6)
        quadLayout.addWidget(self.y2Spin, 0, 7)
        quadLayout.addWidget(QLabel(self.tr("X3")), 1, 0)
        quadLayout.addWidget(self.x3Spin, 1, 1)
        quadLayout.addWidget(QLabel(self.tr("Y3")), 1, 2)
        quadLayout.addWidget(self.y3Spin, 1, 3)
        quadLayout.addWidget(QLabel(self.tr("X4")), 1, 4)
        quadLayout.addWidget(self.x4Spin, 1, 5)
        quadLayout.addWidget(QLabel(self.tr("Y4")), 1, 6)
        quadLayout.addWidget(self.y4Spin, 1, 7)

        quadWidget = QWidget()
        quadWidget.setLayout(quadLayout)

        self.xCircleSpin = QSpinBox()
        self.xCircleSpin.setMaximum(width)
        self.xCircleSpin.valueChanged.connect(self.cropChanged.emit)
        self.yCircleSpin = QSpinBox()
        self.yCircleSpin.setMaximum(height)
        self.yCircleSpin.valueChanged.connect(self.cropChanged.emit)
        self.widthCircleSpin = QSpinBox()
        self.widthCircleSpin.setMaximum(width)
        self.widthCircleSpin.valueChanged.connect(self.cropChanged.emit)
        self.heightCircleSpin = QSpinBox()
        self.heightCircleSpin.setMaximum(height)
        self.heightCircleSpin.valueChanged.connect(self.cropChanged.emit)

        circleLayout = QGridLayout()
        circleLayout.addWidget(QLabel(self.tr("X")), 0, 0)
        circleLayout.addWidget(self.xCircleSpin, 0, 1)
        circleLayout.addWidget(QLabel(self.tr("Y")), 0, 2)
        circleLayout.addWidget(self.yCircleSpin, 0, 3)
        circleLayout.addWidget(QLabel(self.tr("Width")), 1, 0)
        circleLayout.addWidget(self.widthCircleSpin, 1, 1)
        circleLayout.addWidget(QLabel(self.tr("Height")), 1, 2)
        circleLayout.addWidget(self.heightCircleSpin, 1, 3)

        circleWidget = QWidget()
        circleWidget.setLayout(circleLayout)

        settings = QSettings()
        cropTool = settings.value('crop_dialog/crop_tool', 0)
        self.tab = QTabWidget(self)
        self.tab.addTab(rectWidget, createIcon('shape_handles.png'), None)
        self.tab.setTabToolTip(0, self.tr("Rect"))
        self.tab.addTab(circleWidget, createIcon('shape_handles_free.png'), None)
        self.tab.setTabToolTip(1, self.tr("Circle"))
        self.tab.addTab(quadWidget, createIcon('shape_handles_free.png'), None)
        self.tab.setTabToolTip(2, self.tr("Quad"))
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

        angelLabel = QLabel(self.tr("Angel"))

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
    TOP = 4
    RIGHT = 5
    BOTTOM = 6
    LEFT = 7

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
        elif corner == self.BOTTOM_LEFT:
            x = 0
            y = height
        elif corner == self.TOP:
            x = width / 2
            y = 0
        elif corner == self.RIGHT:
            x = width
            y = height / 2
        elif corner == self.BOTTOM:
            x = width / 2
            y = height
        else:
            x = 0
            y = height / 2

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
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.bounding.updateRect()

        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if self.corner in (self.TOP_LEFT, self.BOTTOM_RIGHT):
            self.setCursor(Qt.SizeFDiagCursor)
        elif self.corner in (self.TOP_RIGHT, self.BOTTOM_LEFT):
            self.setCursor(Qt.SizeBDiagCursor)
        elif self.corner in (self.TOP, self.BOTTOM):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.SizeHorCursor)

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
    rectChanged = pyqtSignal()

    def __init__(self, width, height, scale, fixed):
        super().__init__()

        self.width = width
        self.height = height
        self.scale = scale
        self.fixed = fixed

        point1 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP_LEFT)
        point2 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP_RIGHT)
        point3 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM_RIGHT)
        point4 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM_LEFT)

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

            pos = newPos

        for item in self.items():
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.rectChanged.emit()

        return pos

    def updateRect(self):
        p1 = self.points[BoundingPointItem.TOP_LEFT]
        p2 = self.points[BoundingPointItem.TOP_RIGHT]
        p3 = self.points[BoundingPointItem.BOTTOM_RIGHT]
        p4 = self.points[BoundingPointItem.BOTTOM_LEFT]
        self.lines[0].setLine(p1.x() * self.scale,
                              (p1.y() - self.lines[0].pos().y()) * self.scale,
                              p2.x() * self.scale,
                              (p2.y() - self.lines[0].pos().y()) * self.scale)
        self.lines[1].setLine((p2.x() - self.lines[1].pos().x()) * self.scale,
                              p2.y() * self.scale,
                              (p3.x() - self.lines[1].pos().x()) * self.scale,
                              p3.y() * self.scale)
        self.lines[2].setLine(p3.x() * self.scale,
                              (p3.y() - self.lines[2].pos().y()) * self.scale,
                              p4.x() * self.scale,
                              (p4.y() - self.lines[2].pos().y()) * self.scale)
        self.lines[3].setLine((p4.x() - self.lines[3].pos().x()) * self.scale,
                              p4.y() * self.scale,
                              (p1.x() - self.lines[3].pos().x()) * self.scale,
                              p1.y() * self.scale)

    def setScale(self, scale):
        self.scale = scale

        self.updateRect()

    def items(self):
        return self.lines + self.points

    def cropPoints(self):
        return [p.pos() for p in self.points]


class BoundingCircleItem(QGraphicsEllipseItem):

    def __init__(self, bounding):
        self.bounding = bounding

        super().__init__()

        self.setPen(QPen(Qt.DashLine))
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)


class GraphicsCircleBoundingItem(QObject):
    rectChanged = pyqtSignal()

    def __init__(self, width, height, scale, _fixed):
        super().__init__()

        self.width = width
        self.height = height
        self.scale = scale

        point1 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.TOP)
        point2 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.RIGHT)
        point3 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.BOTTOM)
        point4 = BoundingPointItem(self, self.width, self.height,
                                   BoundingPointItem.LEFT)

        self.points = [point1, point2, point3, point4]

        self.circle = BoundingCircleItem(self)

        self.updateRect()

    def update(self, obj, pos):
        p1 = self.points[0]
        p2 = self.points[1]
        p3 = self.points[2]
        p4 = self.points[3]

        for item in self.items():
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)

        if obj in self.points:
            point = obj
            newPos = pos
            if point.corner == point.TOP:
                newPos.setX(point.x())
                if newPos.y() < 0:
                    newPos.setY(0)

                oppositePos = p3.scenePos()
                if newPos.y() > oppositePos.y() - point.SIZE:
                    newPos.setY(oppositePos.y() - point.SIZE)
                oppositePos = p2.scenePos()
                if newPos.x() > oppositePos.x() - point.SIZE:
                    newPos.setX(oppositePos.x() - point.SIZE)
                oppositePos = p4.scenePos()
                if newPos.x() < oppositePos.x() + point.SIZE:
                    newPos.setX(oppositePos.x() + point.SIZE)

                halfY = newPos.y() + (p3.y() - newPos.y()) / 2
                p2.setY(halfY)
                p4.setY(halfY)
            elif point.corner == point.RIGHT:
                newPos.setY(point.y())
                if newPos.x() > self.width:
                    newPos.setX(self.width)

                oppositePos = p4.scenePos()
                if newPos.x() < oppositePos.x() + point.SIZE:
                    newPos.setX(oppositePos.x() + point.SIZE)
                oppositePos = p1.scenePos()
                if newPos.y() < oppositePos.y() + point.SIZE:
                    newPos.setY(oppositePos.y() + point.SIZE)
                oppositePos = p3.scenePos()
                if newPos.y() > oppositePos.y() - point.SIZE:
                    newPos.setY(oppositePos.y() - point.SIZE)

                halfX = newPos.x() - (newPos.x() - p4.x()) / 2
                p1.setX(halfX)
                p3.setX(halfX)
            elif point.corner == point.BOTTOM:
                newPos.setX(point.x())
                if newPos.y() > self.height:
                    newPos.setY(self.height)

                oppositePos = p1.scenePos()
                if newPos.y() < oppositePos.y() + point.SIZE:
                    newPos.setY(oppositePos.y() + point.SIZE)
                oppositePos = p2.scenePos()
                if newPos.x() > oppositePos.x() - point.SIZE:
                    newPos.setX(oppositePos.x() - point.SIZE)
                oppositePos = p4.scenePos()
                if newPos.x() < oppositePos.x() + point.SIZE:
                    newPos.setX(oppositePos.x() + point.SIZE)

                halfY = newPos.y() - (newPos.y() - p1.y()) / 2
                p2.setY(halfY)
                p4.setY(halfY)
            else:  # self.corner == self.LEFT
                newPos.setY(point.y())
                if newPos.x() < 0:
                    newPos.setX(0)

                oppositePos = p2.scenePos()
                if newPos.x() > oppositePos.x() - point.SIZE:
                    newPos.setX(oppositePos.x() - point.SIZE)
                oppositePos = p1.scenePos()
                if newPos.y() < oppositePos.y() + point.SIZE:
                    newPos.setY(oppositePos.y() + point.SIZE)
                oppositePos = p3.scenePos()
                if newPos.y() > oppositePos.y() - point.SIZE:
                    newPos.setY(oppositePos.y() - point.SIZE)

                halfX = newPos.x() + (p2.x() - newPos.x()) / 2
                p1.setX(halfX)
                p3.setX(halfX)

            pos = newPos

        for item in self.items():
            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

        self.rectChanged.emit()

        return pos

    def updateRect(self):
        p1 = self.points[0]
        p2 = self.points[1]
        p3 = self.points[2]
        p4 = self.points[3]

        self.circle.setRect(p4.x() * self.scale, p1.y() * self.scale,
                            (p2.x() - p4.x()) * self.scale, (p3.y() - p1.y()) * self.scale)

    def setScale(self, scale):
        self.scale = scale

        self.updateRect()

    def items(self):
        return [self.circle] + self.points

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
        self.pasteAct = QAction(createIcon('page_paste.png'), self.tr("Paste"), self, shortcut=QKeySequence.Paste, triggered=self.paste)

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
        self.editMenu.addAction(self.pasteAct)
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

    def paste(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasImage():
            self.setImage(mime.imageData())
            self.isChanged = True
        elif mime.hasUrls():
            url = mime.urls()[0]
            image = QImage()
            result = image.load(url.toLocalFile())
            if result:
                self.setImage(image)
                self.isChanged = True
        self._updateEditActions()

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
            self.rotateDlg.finished.connect(self.rotateClose)
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

    def rotateClose(self, result):
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
            sceneRect = self.viewer.sceneRect()
            w = sceneRect.width()
            h = sceneRect.height()

            self.cropDlg = CropDialog(w, h, self)
            self.cropDlg.finished.connect(self.cropClose)
            self.cropDlg.currentToolChanged.connect(self.cropToolChanged)
            self.cropDlg.cropChanged.connect(self.cropDlgChanged)
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

        if self.cropDlg.currentTool() in (0, 2):
            fixed_bounding = (self.cropDlg.currentTool() == 0)
            self.bounding = GraphicsBoundingItem(w, h, self.scale, fixed_bounding)
        else:
            self.bounding = GraphicsCircleBoundingItem(w, h, self.scale, False)
        for item in self.bounding.items():
            self.scene.addItem(item)

        self.bounding.rectChanged.connect(self.cropChanged)
        self.cropChanged()

    def cropChanged(self):
        points = self.bounding.cropPoints()

        self.cropDlg.cropChanged.disconnect(self.cropDlgChanged)
        if self.cropDlg.currentTool() == 0:
            self.cropDlg.xSpin.setValue(points[0].x())
            self.cropDlg.ySpin.setValue(points[0].y())
            self.cropDlg.widthSpin.setValue(points[2].x() - points[0].x())
            self.cropDlg.heightSpin.setValue(points[2].y() - points[0].y())
        elif self.cropDlg.currentTool() == 1:
            self.cropDlg.xCircleSpin.setValue(points[3].x())
            self.cropDlg.yCircleSpin.setValue(points[0].y())
            self.cropDlg.widthCircleSpin.setValue(points[1].x() - points[3].x())
            self.cropDlg.heightCircleSpin.setValue(points[2].y() - points[0].y())
        else:
            self.cropDlg.x1Spin.setValue(points[0].x())
            self.cropDlg.y1Spin.setValue(points[0].y())
            self.cropDlg.x2Spin.setValue(points[1].x())
            self.cropDlg.y2Spin.setValue(points[1].y())
            self.cropDlg.x3Spin.setValue(points[2].x())
            self.cropDlg.y3Spin.setValue(points[2].y())
            self.cropDlg.x4Spin.setValue(points[3].x())
            self.cropDlg.y4Spin.setValue(points[3].y())
        self.cropDlg.cropChanged.connect(self.cropDlgChanged)

    def cropDlgChanged(self):
        self.bounding.rectChanged.disconnect(self.cropChanged)
        if self.cropDlg.currentTool() == 0:
            self.bounding.points[0].setX(self.cropDlg.xSpin.value())
            self.bounding.points[0].setY(self.cropDlg.ySpin.value())
            self.bounding.points[2].setX(self.cropDlg.xSpin.value() + self.cropDlg.widthSpin.value())
            self.bounding.points[2].setY(self.cropDlg.ySpin.value() + self.cropDlg.heightSpin.value())
            self.cropChanged()
        elif self.cropDlg.currentTool() == 1:
            self.bounding.points[3].setX(self.cropDlg.xCircleSpin.value())
            self.bounding.points[0].setY(self.cropDlg.yCircleSpin.value())
            self.bounding.points[1].setX(self.cropDlg.xCircleSpin.value() + self.cropDlg.widthCircleSpin.value())
            self.bounding.points[2].setY(self.cropDlg.yCircleSpin.value() + self.cropDlg.heightCircleSpin.value())
            self.cropChanged()
        else:
            self.bounding.points[0].setX(self.cropDlg.x1Spin.value())
            self.bounding.points[0].setY(self.cropDlg.y1Spin.value())
            self.bounding.points[1].setX(self.cropDlg.x2Spin.value())
            self.bounding.points[1].setY(self.cropDlg.y2Spin.value())
            self.bounding.points[2].setX(self.cropDlg.x3Spin.value())
            self.bounding.points[2].setY(self.cropDlg.y3Spin.value())
            self.bounding.points[3].setX(self.cropDlg.x4Spin.value())
            self.bounding.points[3].setY(self.cropDlg.y4Spin.value())
            self.cropChanged()
        self.bounding.rectChanged.connect(self.cropChanged)

    def cropClose(self, result):
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
            elif self.cropDlg.currentTool() == 1:
                rect = QRectF(points[3].x(), points[0].y(),
                              points[1].x() - points[3].x(),
                              points[2].y() - points[0].y()).toRect()

                pixmap = self._pixmapHandle.pixmap()
                mask = QBitmap(pixmap.size())
                mask.fill(Qt.white)
                painter = QPainter()
                painter.begin(mask)
                painter.setBrush(Qt.black)
                painter.drawEllipse(rect)
                painter.end()
                pixmap.setMask(mask)

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
        self.exitAct.setDisabled(inCrop or inRotate)
        self.saveAsAct.setDisabled(inCrop or inRotate)
        self.copyAct.setDisabled(inCrop or inRotate)
        self.pasteAct.setDisabled(inCrop or inRotate)
        self.rotateLeftAct.setDisabled(inCrop or inRotate)
        self.rotateRightAct.setDisabled(inCrop or inRotate)
        self.rotateAct.setDisabled(inCrop)
        self.cropAct.setDisabled(inRotate)

        if inCrop or inRotate:
            self.saveAct.setDisabled(True)
        else:
            self.saveAct.setEnabled(self.isChanged)

    def save(self):
        if self.isChanged:
            self._origPixmap = self._pixmapHandle.pixmap()
            self.imageSaved.emit(self.getImage())

        self.isChanged = False
        self._updateEditActions()

    def getImage(self):
        return self._origPixmap.toImage()
