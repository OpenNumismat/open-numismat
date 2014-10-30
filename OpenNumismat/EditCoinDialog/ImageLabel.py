from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from OpenNumismat.Tools import TemporaryDir
from OpenNumismat import version


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)

        self.clear()

        self.setBackgroundRole(QPalette.Base)
        self.setSizePolicy(QSizePolicy.Ignored,
                           QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)

    def mouseDoubleClickEvent(self, e):
        tmpDir = QDir(TemporaryDir.path())
        file = QTemporaryFile(tmpDir.absoluteFilePath("img_XXXXXX.jpg"))
        file.setAutoRemove(False)
        file.open()

        fileName = QFileInfo(file).absoluteFilePath()
        self.image.save(fileName)

        executor = QDesktopServices()
        executor.openUrl(QUrl.fromLocalFile(fileName))

    def clear(self):
        self._data = None

        self.image = QImage()
        pixmap = QPixmap.fromImage(self.image)
        self.setPixmap(pixmap)

    def resizeEvent(self, e):
        self._showImage()

    def showEvent(self, e):
        self._showImage()

    def loadFromData(self, data):
        self._data = data

        image = QImage()
        result = image.loadFromData(data)
        if result:
            self._setImage(image)

        return result

    def _setImage(self, image):
        self.image = image
        self._showImage()

    def _showImage(self):
        if self.image.isNull():
            return

        # Label not shown => can't get size for resizing image
        if not self.isVisible():
            return

        if self.image.width() > self.width() or \
                                        self.image.height() > self.height():
            scaledImage = self.image.scaled(self.size(),
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaledImage = self.image

        pixmap = QPixmap.fromImage(scaledImage)
        self.setPixmap(pixmap)


class ImageEdit(ImageLabel):
    latestDir = QStandardPaths.displayName(
                                    QStandardPaths.PicturesLocation)

    def __init__(self, name, parent=None):
        super(ImageEdit, self).__init__(parent)

        self.name = name or 'photo'

        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

        self.changed = False

    def contextMenu(self, pos):
        style = QApplication.style()

        icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        text = QApplication.translate('ImageEdit', "Load...")
        load = QAction(icon, text, self)
        load.triggered.connect(self.openImage)

        text = QApplication.translate('ImageEdit', "Paste")
        paste = QAction(text, self)
        paste.triggered.connect(self.pasteImage)

        text = QApplication.translate('ImageEdit', "Copy")
        copy = QAction(text, self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        icon = style.standardIcon(QStyle.SP_TrashIcon)
        text = QApplication.translate('ImageEdit', "Delete")
        delete = QAction(icon, text, self)
        delete.triggered.connect(self.deleteImage)
        delete.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Save as...")
        save = QAction(text, self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        menu = QMenu()
        menu.addAction(load)
        menu.setDefaultAction(load)
        menu.addAction(save)
        menu.addSeparator()
        menu.addAction(paste)
        menu.addAction(copy)
        menu.addAction(delete)
        menu.exec_(self.mapToGlobal(pos))

    def mouseDoubleClickEvent(self, e):
        if self.image.isNull():
            self.openImage()
        else:
            super(ImageEdit, self).mouseDoubleClickEvent(e)

    def openImage(self):
        caption = QApplication.translate('ImageEdit', "Open File")
        filter_ = QApplication.translate('ImageEdit',
                            "Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif);;"
                            "All files (*.*)")
        fileName = QFileDialog.getOpenFileName(self,
                caption, ImageEdit.latestDir,
                filter_)
        if fileName:
            file_info = QFileInfo(fileName)
            ImageEdit.latestDir = file_info.absolutePath()

            self.loadFromFile(fileName)

    def deleteImage(self):
        self.clear()
        self.changed = True

    def saveImage(self):
        caption = QApplication.translate('ImageEdit', "Save File")
        filter_ = QApplication.translate('ImageEdit',
                            "Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif);;"
                            "All files (*.*)")
        # TODO: Set default name to coin title + field name
        fileName = QFileDialog.getSaveFileName(self,
                caption, ImageEdit.latestDir + '/' + self.name,
                filter_)
        if fileName:
            dir_ = QDir(fileName)
            dir_.cdUp()
            ImageEdit.latestDir = dir_.absolutePath()

            self.image.save(fileName)

    def pasteImage(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())
        elif mime.hasImage():
            self._setNewImage(mime.imageData())
        elif mime.hasText():
            # Load image by URL
            self.loadFromUrl(mime.text())

    def copyImage(self):
        if not self.image.isNull():
            clipboard = QApplication.clipboard()
            clipboard.setImage(self.image)

    def clear(self):
        super(ImageEdit, self).clear()
        text = QApplication.translate('ImageEdit',
                        "No image available\n(right-click to add an image)")
        self.setText(text)

    def loadFromFile(self, fileName):
        image = QImage()
        result = image.load(fileName)
        if result:
            self._setNewImage(image)

        return result

    def loadFromUrl(self, url):
        result = False

        import urllib.request
        try:
            # Wikipedia require any header
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req).read()
            image = QImage()
            result = image.loadFromData(data)
            if result:
                self._setNewImage(image)
        except:
            pass

        return result

    def data(self):
        if self.changed:
            return self.image
        return self._data

    def _setNewImage(self, image):
        # Fill transparent color if present
        fixedImage = QImage(image.size(), QImage.Format_RGB32)
        fixedImage.fill(QColor(Qt.white).rgb())
        painter = QPainter(fixedImage)
        painter.drawImage(0, 0, image)
        painter.end()

        self._setImage(fixedImage)
        self.changed = True


class EdgeImageEdit(ImageEdit):
    def __init__(self, name, parent=None):
        super(EdgeImageEdit, self).__init__(name, parent)

    def _setImage(self, image):
        if not image.isNull():
            if image.width() < image.height():
                matrix = QTransform()
                matrix.rotate(90)
                image = image.transformed(matrix, Qt.SmoothTransformation)

        super(EdgeImageEdit, self)._setImage(image)
