from PIL import ImageQt
import zxingcpp

from PySide6.QtCore import QTimer, QThread
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import QComboBox, QDialog, QMessageBox, QVBoxLayout
from PySide6.QtMultimedia import QCamera, QImageCapture, QMediaCaptureSession, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget

from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


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
#            for result in results:
#                print('Found barcode:'
#                    f'\n Text:    "{result.text}"'
#                    f'\n Format:   {result.format}'
#                    f'\n Content:  {result.content_type}'
#                    f'\n Position: {result.position}')

            if results:
                self.resultReady.emit(results[0].text)
                return

        self.resultReady.emit(None)


@storeDlgSizeDecorator
class ScanBarcodeDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.barcode = None
        self.captureSession = QMediaCaptureSession()
        self.camera = None
        self.worker = WorkerThread(self)
        self.worker.resultReady.connect(self.resultReady)

        # To check camera blocked by antivirus
        self.first_capture = True
        self.first_capture_timer = QTimer(self)
        self.first_capture_timer.timeout.connect(self.firstCaptureTimeout)

        self.viewfinder = QVideoWidget()

        self.cameraSelector = QComboBox()
        for cameraDevice in QMediaDevices.videoInputs():
            self.cameraSelector.addItem(cameraDevice.description(), cameraDevice.id())
        defaultDevice = QMediaDevices.defaultVideoInput()
        self.cameraSelector.findData(defaultDevice.id())
        self.cameraSelector.currentIndexChanged.connect(self.cameraChanged)

        layout = QVBoxLayout()
        layout.addWidget(self.cameraSelector)
        layout.addWidget(self.viewfinder)
        self.setLayout(layout)

        if defaultDevice.isNull():
            QMessageBox.warning(self.parent(), self.tr("Scan barcode"),
                                self.tr("Camera not available"))

        self.setCamera(defaultDevice)

    def cameraChanged(self, _index):
        cameraId = self.cameraSelector.currentData()
        for cameraDevice in QMediaDevices.videoInputs():
            if cameraDevice.id() == cameraId:
                self.setCamera(cameraDevice)
                break

    def setCamera(self, cameraDevice):
        self.setWindowTitle(cameraDevice.description())

        if self.camera:
            self.camera.stop()

        self.camera = QCamera(cameraDevice)
#        self.camera.setFocusMode(QCamera.FocusModeAutoNear)
#        self.camera.setExposureMode(QCamera.ExposureBarcode)
        self.captureSession.setCamera(self.camera)

        self.camera.errorOccurred.connect(self.displayCameraError)

        self.imageCapture = QImageCapture()
        self.captureSession.setImageCapture(self.imageCapture)
        self.imageCapture.readyForCaptureChanged.connect(self.readyForCapture)
        self.imageCapture.imageCaptured.connect(self.processCapturedImage)
        self.imageCapture.errorOccurred.connect(self.displayCaptureError)

        self.captureSession.setVideoOutput(self.viewfinder)

        self.camera.start()

    def done(self, r):
        self.camera.stop()
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
