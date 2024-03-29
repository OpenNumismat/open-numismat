import json
import urllib.request

from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from .MapWidget import BaseMapWidget

gmapsAvailable = True

try:
    from OpenNumismat.private_keys import MAPS_API_KEY
except ImportError:
    gmapsAvailable = False


class GMapsWidget(BaseMapWidget):
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
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
var map;
var geocoder;
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
    qtWidget.mapIsMoved(center.lat(), center.lng());
  });
  map.addListener('zoom_changed', function() {
    zoom = map.getZoom();
    qtWidget.mapIsZoomed(zoom);
  });
  map.addListener('click', function (ev) {
    if (marker === null) {
      lat = ev.latLng.lat();
      lng = ev.latLng.lng();
      qtWidget.mapIsClicked(lat, lng)
    }
  });
  qtWidget.mapIsReady();
}
function gmap_addMarker(lat, lng) {
  var position = {lat: lat, lng: lng};
  marker = new google.maps.Marker({
    position: position,
    map: map,
    draggable: DRAGGABLE
  });

  marker.addListener('dragend', function () {
    qtWidget.markerIsMoved(marker.position.lat(), marker.position.lng(), true);
  });
  marker.addListener('click', function () {
    qtWidget.markerIsMoved(marker.position.lat(), marker.position.lng(), true);
  });
  marker.addListener('rightclick', function () {
    qtWidget.markerIsRemoved();
    gmap_deleteMarker();
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
function gmap_addStaticMarker(lat, lng, coin_id, status) {
  var position = new google.maps.LatLng(lat, lng);
  var marker = new google.maps.Marker({
    position: position,
    map: map,
    icon: 'qrc:/' + status + '.png',
  });
  marker.coin_id = coin_id;
  marker.addListener('click', function () {
    qtWidget.markerIsClicked(marker.coin_id);
  });
  markers.push(marker);
}
function gmap_clearStaticMarkers() {
  for (var i = 0; i < markers.length; i++ ) {
    markers[i].setMap(null);
  }
  markers.length = 0;
}
function gmap_fitBounds() {
  var bounds = new google.maps.LatLngBounds();
  for (var i = 0; i < markers.length; i++) {
    bounds.extend(markers[i].getPosition());
  }
  map.fitBounds(bounds);
  var zoom = map.getZoom();
  if (zoom > 15)
    map.setZoom(15);
}
function gmap_geocode(address) {
  geocoder.geocode({'address': address}, function(results, status) {
    if (status === 'OK') {
      lat = results[0].geometry.location.lat();
      lng = results[0].geometry.location.lng();
      gmap_moveMarker(lat, lng);
      qtWidget.markerIsMoved(lat, lng, false);
    }
  });
}
    </script>
    <script async defer
            src="https://maps.googleapis.com/maps/api/js?key=API_KEY&callback=onload&language=LANGUAGE"
            type="text/javascript"></script>
</head>
<body>
<div id="map"></div>
</body>
</html>
'''

    def _getParams(self):
        params = super()._getParams()
        params['API_KEY'] = MAPS_API_KEY
        params['LANGUAGE'] = self.language
        return params

    @waitCursorDecorator
    def reverseGeocode(self, lat, lng):
        url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=%f,%f&key=%s&language=%s" % (lat, lng, MAPS_API_KEY, self.language)

        try:
            req = urllib.request.Request(url)
            data = urllib.request.urlopen(req, timeout=10).read()
            json_data = json.loads(data.decode())
            return json_data['results'][0]['formatted_address']
        except:
            return ''
