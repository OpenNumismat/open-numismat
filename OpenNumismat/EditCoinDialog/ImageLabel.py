from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QApplication

from OpenNumismat.Tools import TemporaryDir


class ImageLabel(QtGui.QLabel):
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)

        self.clear()

        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Ignored,
                           QtGui.QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)

    def mouseDoubleClickEvent(self, e):
        tmpDir = QtCore.QDir(TemporaryDir.path())
        file = QtCore.QTemporaryFile(tmpDir.absoluteFilePath("img_XXXXXX.jpg"))
        file.setAutoRemove(False)
        file.open()

        fileName = QtCore.QFileInfo(file).absoluteFilePath()
        self.image.save(fileName)

        executor = QtGui.QDesktopServices()
        executor.openUrl(QtCore.QUrl.fromLocalFile(fileName))

    def clear(self):
        self.image = QtGui.QImage()
        self.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self._data = None

    def resizeEvent(self, e):
        self._showImage()

    def showEvent(self, e):
        self._showImage()

    def loadFromData(self, data):
        self._data = data

        image = QtGui.QImage()
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

        pixmap = QtGui.QPixmap.fromImage(scaledImage)
        self.setPixmap(pixmap)


class ImageEdit(ImageLabel):
    latestDir = QtGui.QDesktopServices.storageLocation(
                                    QtGui.QDesktopServices.PicturesLocation)

    def __init__(self, name, parent=None):
        super(ImageEdit, self).__init__(parent)

        self.name = name or 'photo'

        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

        self.changed = False

    def contextMenu(self, pos):
        style = QtGui.QApplication.style()

        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        text = QApplication.translate('ImageEdit', "Load...")
        load = QtGui.QAction(icon, text, self)
        load.triggered.connect(self.openImage)

        text = QApplication.translate('ImageEdit', "Paste")
        paste = QtGui.QAction(text, self)
        paste.triggered.connect(self.pasteImage)

        text = QApplication.translate('ImageEdit', "Copy")
        copy = QtGui.QAction(text, self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)
        text = QApplication.translate('ImageEdit', "Delete")
        delete = QtGui.QAction(icon, text, self)
        delete.triggered.connect(self.deleteImage)
        delete.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Save as...")
        save = QtGui.QAction(text, self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        menu = QtGui.QMenu()
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
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                caption, ImageEdit.latestDir,
                filter_)
        if fileName:
            file_info = QtCore.QFileInfo(fileName)
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
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                caption, ImageEdit.latestDir + '/' + self.name,
                filter_)
        if fileName:
            dir_ = QtCore.QDir(fileName)
            dir_.cdUp()
            ImageEdit.latestDir = dir_.absolutePath()

            self.image.save(fileName)

    def pasteImage(self):
        mime = QtGui.QApplication.clipboard().mimeData()
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
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setImage(self.image)

    def clear(self):
        super(ImageEdit, self).clear()
        text = QApplication.translate('ImageEdit',
                        "No image available\n(right-click to add an image)")
        self.setText(text)

    def loadFromFile(self, fileName):
        image = QtGui.QImage()
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
                                    headers={'User-Agent': "OpenNumismat"})
            data = urllib.request.urlopen(req).read()
            image = QtGui.QImage()
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
        fixedImage = QtGui.QImage(image.size(), QtGui.QImage.Format_RGB32)
        fixedImage.fill(QtGui.QColor(Qt.white).rgb())
        painter = QtGui.QPainter(fixedImage)
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
                matrix = QtGui.QMatrix()
                matrix.rotate(90)
                image = image.transformed(matrix, Qt.SmoothTransformation)

        super(EdgeImageEdit, self)._setImage(image)
