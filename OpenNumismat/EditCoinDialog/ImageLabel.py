import urllib.request

from PySide6.QtCore import (
    QDir,
    QFileInfo,
    QMimeData,
    QSettings,
    QTemporaryFile,
    QUrl,
)
from PySide6.QtGui import (
    Qt,
    QAction,
    QDesktopServices,
    QImage,
    QPainter,
    QPalette,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QInputDialog,
    QLabel,
    QMenu,
    QSizePolicy,
    QStyle,
)
from PySide6.QtCore import Signal as pyqtSignal

import OpenNumismat
from OpenNumismat.ImageEditor import ImageEditorDialog
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools import TemporaryDir
from OpenNumismat.Tools.Gui import getSaveFileName
from OpenNumismat import version
from OpenNumismat.Tools.misc import readImageFilters, saveImageFilters


class ImageLabel(QLabel):
    MimeType = 'num/image'
    imageEdited = pyqtSignal(QLabel)

    def __init__(self, field=None, title=None, parent=None):
        super().__init__(parent)

        self.parent = parent
        self.field = field
        self.title = title or 'photo'
        self._data = None
        self.image = QImage()
        self.readonly = False

        self.clear()

        self.setBackgroundRole(QPalette.Base)
        self.setSizePolicy(QSizePolicy.Ignored,
                           QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumWidth(100)

    def contextMenuEvent(self, event):
        open_ = QAction(self.tr("Open"), self)
        open_.triggered.connect(self.openImage)
        open_.setDisabled(self.image.isNull())

        use_external_viewer = not Settings()['built_in_viewer']
        if use_external_viewer:
            edit = QAction(self.tr("Edit..."), self)
            edit.triggered.connect(self.editImage)
            edit.setDisabled(self.image.isNull())

        copy = QAction(self.tr("Copy"), self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        save = QAction(self.tr("Save as..."), self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        menu = QMenu(self)
        menu.addAction(open_)
        menu.setDefaultAction(open_)
        if use_external_viewer:
            menu.addAction(edit)
        menu.addAction(save)
        menu.addSeparator()
        menu.addAction(copy)
        menu.exec(self.mapToGlobal(event.pos()))

    def openImage(self):
        if Settings()['built_in_viewer']:
            self.editImage()
        else:
            fileName = self._saveTmpImage()

            executor = QDesktopServices()
            executor.openUrl(QUrl.fromLocalFile(fileName))

    def editImage(self):
        if isinstance(self, ImageEdit):
            viewer = ImageEditorDialog(self)
            viewer.setImage(self.image)
            viewer.imageSaved.connect(self.imageSaved)
        else:
            if self.readonly:
                viewer = ImageEditorDialog(self.parent, readonly=True)
                viewer.setImage(self.image)
            else:
                proxy = self.parent.getImageProxy()
                proxy.setCurrent(self.field)
                viewer = ImageEditorDialog(self.parent, scrollpanel=True)
                viewer.setImageProxy(proxy)

        viewer.setTitle(self.title)
        viewer.exec()
        viewer.deleteLater()

    def imageSaved(self, image):
        self._setImage(image)
        self.imageEdited.emit(self)

    def mouseDoubleClickEvent(self, _e):
        if not self.image.isNull():
            self.openImage()

    def clear(self):
        self._data = None

        self.image = QImage()
        pixmap = QPixmap.fromImage(self.image)
        self.setPixmap(pixmap)

    def resizeEvent(self, _e):
        self._showImage()

    def showEvent(self, _e):
        self._showImage()

    def loadFromData(self, data):
        if not data:
            data = None

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

    def _saveTmpImage(self):
        tmpDir = QDir(TemporaryDir.path())
        if self.image.format() == QImage.Format.Format_ARGB32:
            file_name_template = "img_XXXXXX.webp"
        else:
            file_name_template = "img_XXXXXX.jpg"
        file = QTemporaryFile(tmpDir.absoluteFilePath(file_name_template))
        file.setAutoRemove(False)
        file.open()

        fileName = QFileInfo(file).absoluteFilePath()
        self.image.save(fileName)

        return fileName

    def saveImage(self):
        # TODO: Set default name to coin title + field name
        fileName, _selectedFilter = getSaveFileName(
            self, 'images', self.title, OpenNumismat.IMAGE_PATH, saveImageFilters())
        if fileName:
            self.image.save(fileName)

    def copyImage(self):
        if not self.image.isNull():
            mime = QMimeData()
            mime.setImageData(self.image)
            mime.setData(ImageLabel.MimeType, self._data)

            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime)

    def setReadonly(self, readonly):
        self.readonly = readonly


class ImageEdit(ImageLabel):
    imageChanged = pyqtSignal(QLabel)

    def __init__(self, field=None, label=None, parent=None):
        super().__init__(None, field, parent)

        self.label = label
        self.title = field

        if label:
            self.label.mouseDoubleClickEvent = self.renameImageEvent

        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        text = QApplication.translate('ImageEdit', "Exchange with")
        self.exchangeMenu = QMenu(text, self)

        self.changed = False

    def setTitle(self, title):
        self.title = title
        self.label.setText(title)

    def contextMenuEvent(self, event):
        style = QApplication.style()

        icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        text = QApplication.translate('ImageEdit', "Load...")
        load_act = QAction(icon, text, self)
        load_act.triggered.connect(self.loadImage)

        text = QApplication.translate('ImageEdit', "Open")
        open_act = QAction(text, self)
        open_act.triggered.connect(self.openImage)
        open_act.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Paste")
        paste_act = QAction(text, self)
        paste_act.triggered.connect(self.pasteImage)

        text = QApplication.translate('ImageEdit', "Copy")
        copy_act = QAction(text, self)
        copy_act.triggered.connect(self.copyImage)
        copy_act.setDisabled(self.image.isNull())

        icon = style.standardIcon(QStyle.SP_TrashIcon)
        text = QApplication.translate('ImageEdit', "Delete")
        delete_act = QAction(icon, text, self)
        delete_act.triggered.connect(self.deleteImage)
        delete_act.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Save as...")
        save_act = QAction(text, self)
        save_act.triggered.connect(self.saveImage)
        save_act.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Rename...")
        rename_act = QAction(text, self)
        rename_act.triggered.connect(self.renameImage)

        menu = QMenu(self)
        menu.addAction(load_act)
        menu.addAction(open_act)
        if self.image.isNull():
            menu.setDefaultAction(load_act)
        else:
            menu.setDefaultAction(open_act)
        menu.addAction(save_act)
        if self.label:
            menu.addSeparator()
            menu.addAction(rename_act)
            menu.addMenu(self.exchangeMenu)
        menu.addSeparator()
        menu.addAction(copy_act)
        menu.addAction(paste_act)
        menu.addAction(delete_act)
        menu.exec(self.mapToGlobal(event.pos()))

    def mouseDoubleClickEvent(self, _e):
        if self.image.isNull():
            self.loadImage()
        else:
            self.openImage()

    def loadImage(self):
        settings = QSettings()
        last_dir = settings.value('images/last_dir', OpenNumismat.IMAGE_PATH)

        caption = QApplication.translate('ImageEdit', "Open File")
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                caption, last_dir, ';;'.join(readImageFilters()))
        if fileName:
            file_info = QFileInfo(fileName)
            settings = QSettings()
            settings.setValue('images/last_dir', file_info.absolutePath())

            self.loadFromFile(fileName)

    def deleteImage(self):
        self.clear()

    def copyImage(self):
        if not self.image.isNull():
            mime = QMimeData()
            mime.setImageData(self.image)
            if not self.changed:
                mime.setData(ImageLabel.MimeType, self._data)

            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime)

    def pasteImage(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasFormat(ImageLabel.MimeType):
            self.loadFromData(mime.data(ImageLabel.MimeType))
        elif mime.hasImage():
            self._setNewImage(mime.imageData())
        elif mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())
        elif mime.hasText():
            # Load image by URL
            self.loadFromUrl(mime.text())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())

    def clear(self):
        super().clear()
        self.changed = False
        self.imageChanged.emit(self)

        text = QApplication.translate('ImageEdit',
                        "No image available\n"
                        "(double-click, right-click or\n"
                        "drag-n-drop to add an image)")
        self.setText(text)

    def loadFromFile(self, fileName):
        image = QImage()
        result = image.load(fileName)
        if result:
            self._setNewImage(image)

        return result

    def loadFromUrl(self, url):
        result = False

        try:
            # Wikipedia require any header
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req, timeout=30).read()
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

    def exchangeImageEvent(self):
        image = self.sender().data()

        original_data = self.data()

        if isinstance(image.data(), QImage):
            self._setImage(image.data())
            self.changed = True
        else:
            if image.data():
                self.loadFromData(image.data())
                self.changed = False
            else:
                self.clear()

        if isinstance(original_data, QImage):
            image._setImage(original_data)
            image.changed = True
        else:
            if original_data:
                image.loadFromData(original_data)
                image.changed = False
            else:
                image.clear()

    def connectExchangeAct(self, image, title):
        act = QAction(title, self)
        act.setData(image)
        act.triggered.connect(self.exchangeImageEvent)
        self.exchangeMenu.addAction(act)

    def renameImageEvent(self, _event):
        self.renameImage()

    def renameImage(self):
        title, ok = QInputDialog.getText(self, self.tr("Rename image"),
                self.tr("Enter new image name"), text=self.title,
                flags=(Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint))
        if ok:
            self.title = title
            self.label.setText(title)

    def imageSaved(self, image):
        self._setNewImage(image)
        self.imageEdited.emit(self)

    def _setNewImage(self, image):
        if image.hasAlphaChannel() and not Settings()['transparent_store']:
            # Fill transparent color if present
            color = Settings()['transparent_color']
            fixedImage = QImage(image.size(), QImage.Format_RGB32)
            fixedImage.fill(color)
            painter = QPainter(fixedImage)
            painter.drawImage(0, 0, image)
            painter.end()
        else:
            fixedImage = image

        self._setImage(fixedImage)
        self.changed = True
        self.imageChanged.emit(self)

    def loadFromData(self, data):
        result = super().loadFromData(data)
        self.imageChanged.emit(self)
        return result
