from PyQt4 import QtCore, QtGui, QtWebKit
from PyQt4.QtCore import Qt


class PreviewDialog(QtGui.QPrintPreviewDialog):
    def __init__(self, html, baseUrl, parent=None):
        super(PreviewDialog, self).__init__(parent,
                        Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint)

        self.html = html
        self.baseUrl = QtCore.QUrl.fromLocalFile(baseUrl + '/')

        self.webView = QtWebKit.QWebView(self)
        self.webView.setVisible(False)

        self.paintRequested.connect(self.paintRequest)

    def paintRequest(self, printer):
        self.webView.print_(printer)

    def exec_(self):
        self.webView.loadFinished.connect(self.loadFinished)
        self.webView.setHtml(self.html, self.baseUrl)

    def loadFinished(self, ok):
        super(PreviewDialog, self).exec_()
