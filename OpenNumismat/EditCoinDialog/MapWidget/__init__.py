from enum import IntEnum

from .OSMWidget import OSMWidget
from .GMapsWidget import GMapsWidget, gmapsAvailable
from .MapboxWidget import MapboxWidget, mapboxAvailable
from .DAREWidget import DAREWidget


class MapType(IntEnum):
    OSM = 0
    GMaps = 1
    Mapbox = 2
    DARE = 3


def get_map_widget(parent, type_, global_, static=True):
    if type_ == MapType.GMaps and gmapsAvailable:
        return GMapsWidget(global_, static, parent)
    elif type_ == MapType.Mapbox and mapboxAvailable:
        return MapboxWidget(global_, static, parent)
    elif type_ == MapType.DARE:
        return DAREWidget(global_, static, parent)

    return OSMWidget(global_, static, parent)
