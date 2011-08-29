from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1024

class ImageLabel(QtGui.QLabel):
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        
        self.image = QtGui.QImage()

        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
        self.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Plain)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

    def __setImage(self):
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
