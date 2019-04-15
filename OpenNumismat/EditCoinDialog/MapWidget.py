import json
import urllib.request

from PyQt5.QtCore import pyqtSignal, QSettings, QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QDesktopServices

from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings
from OpenNumismat import version

importedQtWebKit = True
try:
    from PyQt5.QtWebKitWidgets import QWebView, QWebPage
except ImportError:
    print('PyQt5.QtWebKitWidgets module missed. Google Maps not available')
    importedQtWebKit = False

    class QWebView:
        pass


class BaseMapWidget(QWebView):
    ZOOM_KEY = 'maps/zoom'
    POSITION_KEY = 'maps/position'
    mapReady = pyqtSignal()
    mapMoved = pyqtSignal(float, float)
    mapZoomed = pyqtSignal(int)
    mapClicked = pyqtSignal(float, float)
    markerMoved = pyqtSignal(float, float, bool)
    markerRemoved = pyqtSignal()

    def __init__(self, is_static, parent):
        super().__init__(parent)

        self.language = Settings()['locale']

        self.is_static = is_static
        self.lat = None
        self.lng = None
        self.initialized = False
        self.loadFinished.connect(self.onLoadFinished)
        self.page().mainFrame().addToJavaScriptWindowObject(
            "qtWidget", self)

        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.page().linkClicked.connect(self.linkClicked)

    def linkClicked(self, url):
        executor = QDesktopServices()
        executor.openUrl(QUrl(url))

    def _getParams(self):
        zoom = QSettings().value(self.ZOOM_KEY, 4, type=int)
        position = QSettings().value(self.POSITION_KEY)
        if not position:
            position = (59.957, 30.375)
        if self.is_static:
            draggable = 'false'
        else:
            draggable = 'true'
        params = {"DRAGGABLE": draggable,
                  "ZOOM": str(zoom),
                  "LATITUDE": str(position[0]),
                  "LONGITUDE": str(position[1])}
        return params

    def activate(self):
        if not self.initialized:
            self.mapMoved.connect(self.mapIsMoved)
            self.mapZoomed.connect(self.mapIsZoomed)
            self.mapReady.connect(self.mapIsReady)

            if not self.is_static:
                self.mapClicked.connect(self.mapIsClicked)
                self.markerRemoved.connect(self.markerIsRemoved)

            params = self._getParams()
            html = self.HTML
            for key, val in params.items():
                html = html.replace(key, val)
            self.setHtml(html)

    def showEvent(self, e):
        self.activate()
        super().showEvent(e)

    def onLoadFinished(self, ok):
        if not ok:
            self.initialized = True

    @waitCursorDecorator
    def waitUntilReady(self):
        while not self.initialized:
            QApplication.processEvents()

    def runScript(self, script):
        return self.page().mainFrame().evaluateJavaScript(script)

    def mapIsReady(self):
        self.moveMarker(self.lat, self.lng)
        self.initialized = True

    def mapIsMoved(self, lat, lng):
        QSettings().setValue(self.POSITION_KEY, (lat, lng))

    def mapIsZoomed(self, zoom):
        if zoom < 2:
            zoom = 2
        elif zoom > 15:
            zoom = 15

        QSettings().setValue(self.ZOOM_KEY, zoom)

    def moveMarker(self, lat, lng):
        if lat and lng:
            self.lat = lat
            self.lng = lng
            self.runScript("gmap_moveMarker(%f, %f)" % (self.lat, self.lng))
            self.mapIsMoved(self.lat, self.lng)
        else:
            self.runScript("gmap_deleteMarker()")

    def setMarker(self, lat, lng):
        self.lat = lat
        self.lng = lng

        if self.initialized:
            self.moveMarker(self.lat, self.lng)

    def mapIsClicked(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.runScript("gmap_addMarker(%f, %f)" % (self.lat, self.lng))
        self.markerMoved.emit(self.lat, self.lng, True)

    def markerIsRemoved(self):
        self.lat = None
        self.lng = None
        self.runScript("gmap_deleteMarker()")

    @waitCursorDecorator
    def geocode(self, address):
        self.runScript('gmap_geocode("{}")'.format(address))

    def reverseGeocode(self, lat, lng):
        raise NotImplementedError
