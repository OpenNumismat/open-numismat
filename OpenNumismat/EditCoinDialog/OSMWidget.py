import json
import urllib.request

from PyQt5.QtCore import pyqtSignal, QSettings
from PyQt5.QtWidgets import QApplication

from OpenNumismat.private_keys import MAPS_API_KEY
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings
from OpenNumismat import version

importedQtWebKit = True
try:
    from PyQt5.QtWebKitWidgets import QWebView
except ImportError:
    print('PyQt5.QtWebKitWidgets module missed. Google Maps not available')
    importedQtWebKit = False

    class QWebView:
        pass

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.4.0/dist/leaflet.css" integrity="sha512-puBpdR0798OZvTTbP4A8Ix/l+A4dHDD0DGqYW6RQ+9jxkRFclaxxQb/SJAWZfWAkuyeQUytO7+7N4QKrDh+drA==" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.4.0/dist/leaflet.js" integrity="sha512-QVftwZFqvtRNi0ZyCtsznlKSWOStnDORoefr1enyq5mVL4tmKB3S/EnC3rRJcxCPavG10IcrVGSmPh6Qw5lwrg==" crossorigin=""></script>
    <style type="text/css">
        html {
            height: 100%;
        }
        body {
            height: 100%;
            margin: 0;
            padding: 0
        }
        #map {
            height: 100%
        }
    </style>
    <script>
var map;
var marker = null;

function initialize() {
  var osmUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      osmAttrib = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      osm = L.tileLayer(osmUrl, {attribution: osmAttrib});

  map = L.map('map').setView([LATITUDE, LONGITUDE], ZOOM).addLayer(osm);

  map.on('moveend', function (e) {
    var center = map.getCenter();
    qtWidget.mapMoved(center.lat, center.lng);
  });
  map.on('zoomend', function() {
    zoom = map.getZoom();
    qtWidget.mapZoomed(zoom);
  });
  map.on('click', function (ev) {
    if (marker === null) {
      lat = ev.latlng.lat;
      lng = ev.latlng.lng;
      qtWidget.mapClicked(lat, lng)
    }
  });
  qtWidget.mapReady();
}
function gmap_addMarker(lat, lng) {
  marker = L.marker([lat, lng], {draggable: DRAGGABLE}).addTo(map);

  marker.on('dragend', function () {
    position = marker.getLatLng();
    qtWidget.markerMoved(position.lat, position.lng, true);
  });
  marker.on('click', function () {
    position = marker.getLatLng();
    qtWidget.markerMoved(position.lat, position.lng, true);
  });
  marker.on('contextmenu', function () {
    qtWidget.markerRemoved();
  });
}
function gmap_deleteMarker() {
  map.removeLayer(marker);
  delete marker;
  marker = null;
}
function gmap_moveMarker(lat, lng) {
  var coords = new L.LatLng(lat, lng);
  if (marker === null) {
    gmap_addMarker(lat, lng);
  }
  else {
    marker.setLatLng(coords);
  }
  map.panTo(coords);
}
function gmap_geocode(address) {
  url = "https://nominatim.openstreetmap.org/?addressdetails=1&format=json&limit=1&q=" + address;
  var xmlHttp = new XMLHttpRequest();
  xmlHttp.open("GET", url, false);
  xmlHttp.send(null);
  if (xmlHttp.status == 200) {
      results = JSON.parse(xmlHttp.responseText);
      lat = parseFloat(results[0]['lat']);
      lng = parseFloat(results[0]['lon']);
      gmap_moveMarker(lat, lng);
      qtWidget.markerMoved(lat, lng, false);
  }
}
    </script>
</head>
<body onload="initialize()">
<div id="map"></div>
</body>
</html>
'''


class BaseOSMWidget(QWebView):
    ZOOM_KEY = 'maps/zoom'
    POSITION_KEY = 'maps/position'
    DRAGGABLE = 'false'
    mapReady = pyqtSignal()
    mapMoved = pyqtSignal(float, float)
    mapZoomed = pyqtSignal(int)
    mapClicked = pyqtSignal(float, float)
    markerMoved = pyqtSignal(float, float, bool)
    markerRemoved = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self.language = Settings()['locale']

        self.lat = None
        self.lng = None
        self.initialized = False
        self.loadFinished.connect(self.onLoadFinished)
        self.page().mainFrame().addToJavaScriptWindowObject(
            "qtWidget", self)

    def activate(self):
        if not self.initialized:
            self.mapMoved.connect(self.mapIsMoved)
            self.mapZoomed.connect(self.mapIsZoomed)
            self.mapReady.connect(self.mapIsReady)

            zoom = QSettings().value(self.ZOOM_KEY, 4, type=int)
            position = QSettings().value(self.POSITION_KEY)
            if not position:
                position = (59.957, 30.375)
            params = {"DRAGGABLE": self.DRAGGABLE,
                      "ZOOM": str(zoom),
                      "LATITUDE": str(position[0]),
                      "LONGITUDE": str(position[1])}
            html = HTML
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


class OSMWidget(BaseOSMWidget):
    DRAGGABLE = 'true'

    def activate(self):
        if not self.initialized:
            self.mapClicked.connect(self.mapIsClicked)
            self.markerRemoved.connect(self.markerIsRemoved)

        super().activate()

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
    def reverseGeocode(self, lat, lng):
        url = "https://nominatim.openstreetmap.org/reverse?format=json&lat=%f&lon=%f&zoom=18&addressdetails=0&accept-language=%s" % (lat, lng, self.language)

        try:
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req).read()
            json_data = json.loads(data.decode())
            return json_data['display_name']
        except:
            return ''

    @waitCursorDecorator
    def geocode(self, address):
        self.runScript('gmap_geocode("{}")'.format(address))


class StaticOSMWidget(BaseOSMWidget):
    pass
