from PySide6.QtCore import QSettings, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtCore import Slot as pyqtSlot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings


class WebEnginePage(QWebEnginePage):
    def acceptNavigationRequest(self, url, type_, isMainFrame):
        if type_ == QWebEnginePage.NavigationTypeLinkClicked:
            executor = QDesktopServices()
            executor.openUrl(QUrl(url))
            return False
        return super().acceptNavigationRequest(url, type_, isMainFrame)


class QWebView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPage(WebEnginePage(self))

    def contextMenuEvent(self, _event):
        pass


class BaseMapWidget(QWebView):
    ZOOM_KEY = 'maps/zoom'
    POSITION_KEY = 'maps/position'
    markerMoved = pyqtSignal(float, float, bool)
    markerRemoved = pyqtSignal()
    markerClicked = pyqtSignal(int)

    def __init__(self, global_, static, parent):
        super().__init__(parent)

        self.language = Settings()['locale']
        self.is_static = static
        self.is_global = global_
        self.lat = None
        self.lng = None
        self.points = []
        self.activated = False
        self.initialized = False

        self.loadFinished.connect(self.onLoadFinished)

        channel = QWebChannel(self.page())
        channel.registerObject("qtWidget", self)
        self.page().setWebChannel(channel)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setModel(self, model):
        self.model = model

    def modelChanged(self):
        self.points = []
        sql = "SELECT latitude, longitude, id, status FROM coins WHERE ifnull(latitude,'')<>'' AND ifnull(longitude,'')<>''"
        filter_ = self.model.filter()
        if filter_:
            sql += " AND " + filter_
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        while query.next():
            record = query.record()
            lat = record.value(0)
            lng = record.value(1)
            coin_id = record.value(2)
            status = record.value(3)
            self.addMarker(lat, lng, coin_id, status)

        self.showMarkers()

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
        if not self.activated:
            params = self._getParams()
            html = self.HTML
            for key, val in params.items():
                html = html.replace(key, val)
            self.setHtml(html)

            self.activated = True

    def showEvent(self, e):
        self.activate()
        super().showEvent(e)

    def onLoadFinished(self, ok):
        if not ok:
            self.initialized = True

    def runScript(self, script):
        return self.page().runJavaScript(script)

    @pyqtSlot()
    def mapIsReady(self):
        self.initialized = True
        self.moveMarker(self.lat, self.lng)
        self.showMarkers()

    @pyqtSlot(float, float)
    def mapIsMoved(self, lat, lng):
        if not self.is_global:
            QSettings().setValue(self.POSITION_KEY, (lat, lng))

    @pyqtSlot(int)
    def mapIsZoomed(self, zoom):
        if not self.is_global:
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

    def addMarker(self, lat, lng, coin_id, status):
        self.points.append((lat, lng, coin_id, status))

    def showMarkers(self):
        if self.initialized:
            self.runScript("gmap_clearStaticMarkers()")
            if self.points:
                for point in self.points:
                    self.runScript("gmap_addStaticMarker(%f, %f, %d, '%s')" % (point[0], point[1], point[2], point[3]))
                self.runScript("gmap_fitBounds()")

    @pyqtSlot(float, float)
    def mapIsClicked(self, lat, lng):
        if not self.is_static:
            self.lat = lat
            self.lng = lng
            self.runScript("gmap_addMarker(%f, %f)" % (self.lat, self.lng))
            self.markerMoved.emit(self.lat, self.lng, True)

    @pyqtSlot(float, float, bool)
    def markerIsMoved(self, lat, lng, address_changed):
        self.lat = lat
        self.lng = lng
        self.markerMoved.emit(lat, lng, address_changed)

    @pyqtSlot(int)
    def markerIsClicked(self, coin_id):
        self.markerClicked.emit(coin_id)

    @pyqtSlot()
    def markerIsRemoved(self):
        if not self.is_static:
            self.lat = None
            self.lng = None
            self.markerRemoved.emit()

    @waitCursorDecorator
    def geocode(self, address):
        self.runScript('gmap_geocode("{}")'.format(address))

    def reverseGeocode(self, lat, lng):
        raise NotImplementedError
