import json
import urllib.request

from PyQt5.QtCore import pyqtSignal, QSettings, QUrl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QDesktopServices

from OpenNumismat.private_keys import MAPS_API_KEY
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings

importedQtWebKit = True
try:
    from PyQt5.QtWebKitWidgets import QWebView, QWebPage
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
var geocoder;
var marker = null;

function initialize() {
  var position = {lat: LATITUDE, lng: LONGITUDE};
  map = new google.maps.Map(
  document.getElementById('map'), {
    zoom: ZOOM,
    center: position,
    streetViewControl: false,
    fullscreenControl: false,
    styles: [
        {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "off" }]
        },
        {
            featureType: "transit.station",
            stylers: [{ visibility: "off" }]
        }
    ]
  });

  geocoder = new google.maps.Geocoder();

  map.addListener('dragend', function () {
    var center = map.getCenter();
    qtWidget.mapMoved(center.lat(), center.lng());
  });
  map.addListener('zoom_changed', function() {
    zoom = map.getZoom();
    qtWidget.mapZoomed(zoom);
  });
  map.addListener('click', function (ev) {
    if (marker === null) {
      lat = ev.latLng.lat();
      lng = ev.latLng.lng();
      qtWidget.mapClicked(lat, lng)
    }
  });
  qtWidget.mapReady();
}
function gmap_addMarker(lat, lng) {
  var position = {lat: lat, lng: lng};
  marker = new google.maps.Marker({
    position: position,
    map: map,
    draggable: DRAGGABLE
  });

  marker.addListener('dragend', function () {
    qtWidget.markerMoved(marker.position.lat(), marker.position.lng(), true);
  });
  marker.addListener('click', function () {
    qtWidget.markerMoved(marker.position.lat(), marker.position.lng(), true);
  });
  marker.addListener('rightclick', function () {
    qtWidget.markerRemoved();
  });
}
function gmap_deleteMarker() {
  marker.setMap(null);
  delete marker;
  marker = null;
}
function gmap_moveMarker(lat, lng) {
  var coords = new google.maps.LatLng(lat, lng);
  if (marker === null) {
    gmap_addMarker(lat, lng);
  }
  else {
    marker.setPosition(coords);
  }
  map.setCenter(coords);
}
function gmap_geocode(address) {
  geocoder.geocode({'address': address}, function(results, status) {
    if (status === 'OK') {
      lat = results[0].geometry.location.lat();
      lng = results[0].geometry.location.lng();
      gmap_moveMarker(lat, lng);
      qtWidget.markerMoved(lat, lng, false);
    }
  });
}
    </script>
    <script async defer
            src="https://maps.googleapis.com/maps/api/js?key=API_KEY&callback=initialize&language=LANGUAGE"
            type="text/javascript"></script>
</head>
<body>
<div id="map"></div>
</body>
</html>
'''


class BaseGMapsWidget(QWebView):
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

        self.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.page().linkClicked.connect(self.linkClicked)

    def linkClicked(self, url):
        executor = QDesktopServices()
        executor.openUrl(QUrl(url))

    def activate(self):
        if not self.initialized:
            self.mapMoved.connect(self.mapIsMoved)
            self.mapZoomed.connect(self.mapIsZoomed)
            self.mapReady.connect(self.mapIsReady)

            zoom = QSettings().value(self.ZOOM_KEY, 4, type=int)
            position = QSettings().value(self.POSITION_KEY)
            if not position:
                position = (59.957, 30.375)
            params = {"API_KEY": MAPS_API_KEY,
                      "LANGUAGE": self.language,
                      "DRAGGABLE": self.DRAGGABLE,
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


class GMapsWidget(BaseGMapsWidget):
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
        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%f,%f&key=%s&language=%s" % (lat, lng, MAPS_API_KEY, self.language)

        try:
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(req).read()
            json_data = json.loads(data.decode())
            return json_data['results'][0]['formatted_address']
        except:
            return ''

    @waitCursorDecorator
    def geocode(self, address):
        self.runScript('gmap_geocode("{}")'.format(address))


class StaticGMapsWidget(BaseGMapsWidget):
    pass
