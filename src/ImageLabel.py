from PyQt4 import QtGui, QtCore, QtNetwork
from PyQt4.QtCore import Qt

MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1024

class ImageLabel(QtGui.QLabel):
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        
        self.__clearImage()
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

    def contextMenu(self, pos):
        style = QtGui.QApplication.style()

        icon = style.standardIcon(QtGui.QStyle.SP_DirOpenIcon)
        open = QtGui.QAction(icon, 'Open...', self)
        open.triggered.connect(self.openImage)

        paste = QtGui.QAction('Paste', self)
        paste.triggered.connect(self.pasteImage)

        icon = style.standardIcon(QtGui.QStyle.SP_TrashIcon)
        delete = QtGui.QAction(icon, 'Delete', self)
        delete.triggered.connect(self.deleteImage)

        icon = style.standardIcon(QtGui.QStyle.SP_DriveFDIcon)
        save = QtGui.QAction(icon, 'Save as...', self)
        save.triggered.connect(self.saveImage)

        edit = QtGui.QAction('Edit...', self)
        edit.triggered.connect(self.editImage)

        menu = QtGui.QMenu()
        menu.addAction(open)
        menu.addAction(paste)
        menu.addAction(delete)
        if self.image.isNull():
            delete.setEnabled(False)
        menu.addAction(save)
        if self.image.isNull():
            save.setEnabled(False)
        menu.addAction(edit)
        if self.image.isNull():
            edit.setEnabled(False)
        menu.exec_(self.mapToGlobal(pos))
        
    def openImage(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,
                "Open File", QtCore.QDir.currentPath(),
                "Images (*.bmp *.png *.jpg *.jpeg *.tiff *.gif);;All files (*.*)")
        if fileName:
            self.loadFromFile(fileName)

    def deleteImage(self):
        self.__clearImage()
    
    def saveImage(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,
                "Save File", QtCore.QDir.currentPath(),
                "Images (*.bmp *.png *.jpg *.jpeg *.tiff *.gif);;All files (*.*)")
        if fileName:
            self.image.save(fileName)
    
    def pasteImage(self):
        mime = QtGui.QApplication.clipboard().mimeData()
        if mime.hasUrls():
            self.image.load(mime.urls()[0])
        elif mime.hasImage():
            self.image = mime.imageData()
        elif mime.hasText():
            # http://blog.mrcongwang.com/2009/07/21/applying-system-proxy-settings-to-qt-application/
            # http://www.erata.net/qt-boost/synchronous-http-request/
            url = QtCore.QUrl("http://www.stockmusic.com/uploads/wmm01-p.jpg");
            self.bytes = QtCore.QByteArray()
            buffer = QtCore.QBuffer(self.bytes)
            buffer.open(QtCore.QIODevice.WriteOnly);
            http = QtNetwork.QHttp(self)
            http.requestFinished.connect(self.requestFinished)
            http.setHost(url.host());
            self.Request=http.get(url.path(),buffer);
        else:
            return

        self.__setImage()
    
    def requestFinished(self, requestId, error):
        print(requestId, self.Request, error)
        if self.Request == requestId:
            self.image = QtGui.QImage()
            print(self.bytes)
            self.image.loadFromData(self.bytes);
            self.__setImage()

    def editImage(self):
        raise
    
    def __clearImage(self):
        self.image = QtGui.QImage()
        self.setPixmap(QtGui.QPixmap.fromImage(self.image))
        self.setText("No image available\n(right-click to add an image)")

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
        # Resize big images for storing in DB
        if self.image.width() > MAX_IMAGE_WIDTH or self.image.height() > MAX_IMAGE_HEIGHT:
            self.image = self.image.scaled(MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.__setImage()
    
    def loadFromData(self, data):
        self.image.loadFromData(data)
        self.__setImage()
        
    def loadFromUrl(self, url):
        raise
    
    def loadFromClipboard(self):
        raise
    
    def data(self):
        ba = QtCore.QByteArray() 
        buffer = QtCore.QBuffer(ba)
        buffer.open(QtCore.QIODevice.WriteOnly)
        self.image.save(buffer, "PNG")
        return ba

if __name__ == '__main__':
    import sys
    from main import MainWindow
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
