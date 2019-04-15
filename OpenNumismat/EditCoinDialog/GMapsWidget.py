import json
import urllib.request

from OpenNumismat.private_keys import MAPS_API_KEY
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.EditCoinDialog.MapWidget import BaseMapWidget


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

    def __init__(self, parent):
        super().__init__(False, parent)

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
            data = urllib.request.urlopen(req).read()
            json_data = json.loads(data.decode())
            return json_data['results'][0]['formatted_address']
        except:
            return ''


class StaticGMapsWidget(GMapsWidget):

    def __init__(self, parent):
        super(GMapsWidget, self).__init__(True, parent)
