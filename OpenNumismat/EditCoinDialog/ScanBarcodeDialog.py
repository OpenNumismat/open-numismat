from PIL import ImageQt

from PySide6.QtCore import QTimer, QThread, QSettings, Qt, QRectF
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QIcon, QPen, QImage, QBrush, QPainter, QBitmap, QPixmap, QColor
from PySide6.QtMultimedia import QCamera, QImageCapture, QMediaCaptureSession, QMediaDevices
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QComboBox, QDialog, QMessageBox, QVBoxLayout
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsPixmapItem

from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.dependencies import HAS_ZXING

if HAS_ZXING:
    import zxingcpp

MASK_OPACITY = 0.3
QR_SIZE = 0.7  # Size of rectangle for QR capture


class WorkerThread(QThread):
    resultReady = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.image = None

    def setImage(self, image):
        self.image = image

    def run(self):
        if self.image:
            img = ImageQt.fromqimage(self.image)
            results = zxingcpp.read_barcodes(img)

            if results:
                self.resultReady.emit(results[0].text)
                return

        self.resultReady.emit(None)


class MaskRectangleItem(QGraphicsPixmapItem):

    def __init__(self):
        super().__init__()

        self.setOpacity(MASK_OPACITY)

    def setRect(self, width, height, x, y, w, h):
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.black)

        brush = QBrush(Qt.white)
        painter = QPainter(image)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(x, y, w, h)
        painter.end()

        mask = image.createMaskFromColor(QColor(Qt.white).rgb())
        bitmap = QBitmap.fromImage(mask)
        pixmap = QPixmap.fromImage(image)
        pixmap.setMask(bitmap)
        self.setPixmap(pixmap)


@storeDlgSizeDecorator
class ScanBarcodeDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowIcon(QIcon(':/webcam.png'))

        self.rectangle = None
        self.mask = None
        self.barcode = None
        self.camera = QCamera(self)
        self.camera.errorOccurred.connect(self.displayCameraError)
        self.captureSession = QMediaCaptureSession()
        self.worker = WorkerThread(self)
        self.worker.resultReady.connect(self.resultReady)

        # To check camera blocked by antivirus
        self.first_capture = True
        self.first_capture_timer = QTimer(self)
        self.first_capture_timer.timeout.connect(self.firstCaptureTimeout)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        # self.view.setMinimumSize(120, 60)
        self.view.setFrameStyle(0)
        self.viewfinder = QGraphicsVideoItem()

        self.scene.addItem(self.viewfinder)

        self.viewfinder.nativeSizeChanged.connect(self.video_size_changed)

        self.cameraSelector = QComboBox()
        for cameraDevice in QMediaDevices.videoInputs():
            self.cameraSelector.addItem(cameraDevice.description(), cameraDevice.id())
        self.cameraSelector.setCurrentIndex(-1)
        self.cameraSelector.currentIndexChanged.connect(self.cameraChanged)

        layout = QVBoxLayout()
        layout.addWidget(self.cameraSelector)
        layout.addWidget(self.view)
        self.setLayout(layout)

        settings = QSettings()
        default_camera_id = settings.value('default_camera')
        camera_index = -1
        if default_camera_id:
            camera_index = self.cameraSelector.findData(default_camera_id)
            if camera_index == -1:
                defaultDevice = QMediaDevices.defaultVideoInput()
                camera_index = self.cameraSelector.findData(defaultDevice.id())
        else:
            defaultDevice = QMediaDevices.defaultVideoInput()
            camera_index = self.cameraSelector.findData(defaultDevice.id())

        if camera_index == -1:
            QMessageBox.warning(self.parent(), self.tr("Scan barcode"),
                                self.tr("Camera not available"))
        else:
            self.cameraSelector.setCurrentIndex(camera_index)

    def video_size_changed(self, _size):
        self.resizeEvent(None)

    def resizeEvent(self, _event):
        if self.rectangle:
            self.scene.removeItem(self.rectangle)
        if self.mask:
            self.scene.removeItem(self.mask)

        bounds = self.scene.itemsBoundingRect()
        self.view.fitInView(bounds, Qt.KeepAspectRatio)
        square = self.calculate_center_square(bounds)

        pen = QPen(Qt.green)
        pen.setWidth(0)
        pen.setStyle(Qt.DotLine)
        self.rectangle = self.scene.addRect(square, pen)

        offsetX = bounds.x()
        offsetY = bounds.y()

        self.mask = MaskRectangleItem()
        self.mask.setRect(bounds.width(), bounds.height(),
                          square.x() - offsetX, square.y() - offsetY,
                          square.width(), square.height())
        self.mask.setX(offsetX)
        self.mask.setY(offsetY)
        self.scene.addItem(self.mask)

        self.view.centerOn(0, 0)
        self.view.raise_()

    def calculate_center_square(self, img_rect):
        a = QR_SIZE * min(img_rect.height(), img_rect.width())  # Size of square side
        x = (img_rect.width() - a) / 2  # Postion of the square inside rectangle
        y = (img_rect.height() - a) / 2
        if type(img_rect) != QImage:  # if we have a bounding rectangle, not an image
            x += img_rect.left()  # then we need to shift our square inside this rectangle
            y += img_rect.top()
        return QRectF(x, y, a, a)

    def cameraChanged(self, _index):
        cameraId = self.cameraSelector.currentData()
        for cameraDevice in QMediaDevices.videoInputs():
            if cameraDevice.id() == cameraId:
                self.setCamera(cameraDevice)

                settings = QSettings()
                settings.setValue('default_camera', cameraId)

                break

    def setCamera(self, cameraDevice):
        self.setWindowTitle(cameraDevice.description())

        if self.camera.isActive():
            self.camera.stop()

        self.camera.setCameraDevice(cameraDevice)
        if self.camera.isFocusModeSupported(QCamera.FocusModeAutoNear):
            self.camera.setFocusMode(QCamera.FocusModeAutoNear)
        if self.camera.isExposureModeSupported(QCamera.ExposureBarcode):
            self.camera.setExposureMode(QCamera.ExposureBarcode)
        self.captureSession.setCamera(self.camera)

        self.imageCapture = QImageCapture()
        self.captureSession.setImageCapture(self.imageCapture)
        self.imageCapture.readyForCaptureChanged.connect(self.readyForCapture)
        self.imageCapture.imageCaptured.connect(self.processCapturedImage)
        self.imageCapture.errorOccurred.connect(self.displayCaptureError)

        self.captureSession.setVideoOutput(self.viewfinder)

        self.camera.start()

    def done(self, r):
        if self.camera.isActive():
            self.camera.stop()

        if self.worker.isRunning():
            self.worker.terminate()

        super().done(r)

    def readyForCapture(self, ready):
        if ready:
            if self.first_capture:
                self.first_capture = False
                self.first_capture_timer.start(2500)
                self.first_capture_timer.setSingleShot(True)

            self.imageCapture.capture()

    def processCapturedImage(self, _requestId, img):
        self.first_capture_timer.stop()

        if not self.worker.isRunning():
            img = img.copy(self.calculate_center_square(img).toRect())
            self.worker.setImage(img)
            self.worker.start()

    def resultReady(self, barcode):
        if barcode:
            self.barcode = barcode
            self.accept()

    def firstCaptureTimeout(self):
        QMessageBox.warning(self, self.tr("Scan barcode"),
            self.tr("Camera not available or disabled by antivirus"))

    def displayCameraError(self):
        if self.camera.error() != QCamera.NoError:
            QMessageBox.warning(self, self.tr("Camera Error"),
                                self.camera.errorString())

    def displayCaptureError(self, _id, _error, errorString):
        QMessageBox.warning(self, "Image Capture Error", errorString)
