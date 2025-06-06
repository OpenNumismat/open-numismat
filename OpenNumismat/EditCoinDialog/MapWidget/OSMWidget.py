import json
import urllib.request

from OpenNumismat import version
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from .MapWidget import BaseMapWidget

class OSMWidget(BaseMapWidget):
    HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="initial-scale=1.0, user-scalable=no"/>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
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
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
var map;
var marker = null;
var markers = [];

function onload() {
  if (typeof qtWidget !== 'undefined') {
    initialize();
  }
  else {
    new QWebChannel(qt.webChannelTransport, function(channel) {
      window.qtWidget = channel.objects.qtWidget;
      initialize();
    });
  }
}

function initialize() {
  var osmUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      osmAttrib = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      osm = L.tileLayer(osmUrl, {attribution: osmAttrib});

  map = L.map('map').setView([LATITUDE, LONGITUDE], ZOOM).addLayer(osm);

  map.on('moveend', function (e) {
    var center = map.getCenter();
    qtWidget.mapIsMoved(center.lat, center.lng);
  });
  map.on('zoomend', function() {
    zoom = map.getZoom();
    qtWidget.mapIsZoomed(zoom);
  });
  map.on('click', function (ev) {
    if (marker === null) {
      lat = ev.latlng.lat;
      lng = ev.latlng.lng;
      qtWidget.mapIsClicked(lat, lng)
    }
  });
  qtWidget.mapIsReady();
}
function gmap_addMarker(lat, lng) {
  marker = L.marker([lat, lng], {draggable: DRAGGABLE}).addTo(map);

  marker.on('dragend', function () {
    position = marker.getLatLng();
    qtWidget.markerIsMoved(position.lat, position.lng, true);
  });
  marker.on('click', function () {
    position = marker.getLatLng();
    qtWidget.markerIsMoved(position.lat, position.lng, true);
  });
  marker.on('contextmenu', function () {
    qtWidget.markerIsRemoved();
    gmap_deleteMarker();
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
function gmap_addStaticMarker(lat, lng, coin_id, status) {
  var coords = new L.LatLng(lat, lng);
  var icon = L.icon({
    iconUrl: 'qrc:/' + status + '.png',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
  var marker = L.marker(coords, {icon: icon}).addTo(map);
  marker.coin_id = coin_id;
  marker.on('click', function () {
    qtWidget.markerIsClicked(marker.coin_id);
  });
  markers.push(marker);
}
function gmap_clearStaticMarkers() {
  for (var i = 0; i < markers.length; i++ ) {
    map.removeLayer(markers[i]);
  }
  markers.length = 0;
}
function gmap_fitBounds() {
  var bounds = new L.latLngBounds();
  for (var i = 0; i < markers.length; i++) {
    bounds.extend(markers[i].getLatLng());
  }
  map.fitBounds(bounds);
  var zoom = map.getZoom();
  if (zoom > 15)
    map.setZoom(15);
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
      qtWidget.markerIsMoved(lat, lng, false);
  }
}
    </script>
</head>
<body onload="onload()">
<div id="map"></div>
</body>
</html>
'''

    @waitCursorDecorator
    def reverseGeocode(self, lat, lng):
        url = "https://nominatim.openstreetmap.org/reverse?format=json&lat=%f&lon=%f&zoom=18&addressdetails=0&accept-language=%s" % (lat, lng, self.language)

        try:
            req = urllib.request.Request(url,
                                         headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req, timeout=10).read()
            json_data = json.loads(data.decode())
            return json_data['display_name']
        except:
            return ''
