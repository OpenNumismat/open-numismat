from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1024
IMAGE_FORMAT = 'jpg'

class ImageLabel(QtGui.QLabel):
    latestDir = QtCore.QDir.currentPath()
    # TODO: Uncomment default location in release 
    # latestDir = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.PicturesLocation)
    
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        
        self.__clearImage()
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)

    def contextMenu(self, pos):
        style = QtGui.QApplication.style()

        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        load = QtGui.QAction(icon, self.tr("Load..."), self)
        load.triggered.connect(self.openImage)

        paste = QtGui.QAction(self.tr("Paste"), self)
        paste.triggered.connect(self.pasteImage)

        copy = QtGui.QAction(self.tr("Copy"), self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)
        delete = QtGui.QAction(icon, self.tr("Delete"), self)
        delete.triggered.connect(self.deleteImage)
        delete.setDisabled(self.image.isNull())

        save = QtGui.QAction(self.tr("Save as..."), self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        separator = QtGui.QAction(self)
        separator.setSeparator(True)

        menu = QtGui.QMenu()
        menu.addAction(load)
        menu.setDefaultAction(load)
        menu.addAction(save)
        menu.addAction(separator)
        menu.addAction(paste)
        menu.addAction(copy)
        menu.addAction(delete)
        menu.exec_(self.mapToGlobal(pos))
    
    def mouseDoubleClickEvent(self, e):
        self.openImage()
        
    def openImage(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                self.tr("Open File"), ImageLabel.latestDir,
                self.tr("Images (*.bmp *.png *.jpg *.jpeg *.tiff *.gif);;All files (*.*)"))
        if fileName:
            ImageLabel.latestDir = QtCore.QDir(fileName).absolutePath()
            self.loadFromFile(fileName)

    def deleteImage(self):
        self.__clearImage()
    
    def saveImage(self):
        # TODO: Change latestDir to user's pictures dir
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                self.tr("Save File"), ImageLabel.latestDir,
                self.tr("Images (*.bmp *.png *.jpg *.jpeg *.tiff *.gif);;All files (*.*)"))
        if fileName:
            ImageLabel.latestDir = QtCore.QDir(fileName).absolutePath()
            self.image.save(fileName)
    
    def pasteImage(self):
        mime = QtGui.QApplication.clipboard().mimeData()
        if mime.hasUrls():
            fileName = mime.urls()[0]
            self.image.load(fileName)
        elif mime.hasImage():
            self.image = mime.imageData()
        elif mime.hasText():
            # Load image by URL
            import urllib.request
            url = mime.text()
            try:
                data = urllib.request.urlopen(url).read()
                self.image.loadFromData(data)
            except:
                return
        else:
            return

        self.__setImage()

    def copyImage(self):
        if not self.image.isNull():
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setImage(self.image)

    def __clearImage(self):
        self.image = QtGui.QImage()
        self.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.setText(self.tr("No image available\n(right-click to add an image)"))

    def __setImage(self):
        if self.image.isNull():
            return
        
        # Label not shown => can't get size for resizing image
        if not self.isVisible():
            return
            
        if self.image.width() > self.width() or self.image.height() > self.height():
            scaledImage = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaledImage = self.image
    
        pixmap = QtGui.QPixmap.fromImage(scaledImage)
        self.setPixmap(pixmap)
    
    def showEvent(self, e):
        self.__setImage()
    
    def loadFromFile(self, fileName):
        self.image.load(fileName)
        self.__setImage()
    
    def loadFromData(self, data):
        self.image.loadFromData(data)
        self.__setImage()
        
    def data(self):
        ba = QtCore.QByteArray() 
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.WriteOnly)

        # Resize big images for storing in DB
        if self.image.width() > MAX_IMAGE_WIDTH or self.image.height() > MAX_IMAGE_HEIGHT:
            scaledImage = self.image.scaled(MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaledImage = self.image
        scaledImage.save(buffer, IMAGE_FORMAT)
        return ba

if __name__ == '__main__':
    from main import run
    run()
