import json
import sys
from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QApplication

try:
    from OpenNumismat.private_keys import FINANCE_PROXY
except ImportError:
    pass


def versiontuple(v):
    try:
        return tuple(map(int, (v.split("."))))
    except:
        return tuple((99, 99, 99))  # It is a beta version and newer


def readImageFilters():
    supported_formats = QImageReader.supportedImageFormats()

    formats = "*.jpg *.jpeg *.png *.bmp *.tif *.tiff *.gif *.ico"
    if b'webp' in supported_formats:
        formats += " *.webp"
    if b'jp2' in supported_formats:
        formats += " *.jp2"
    if b'jxl' in supported_formats:
        formats += " *.jxl"
    if b'avif' in supported_formats:
        formats += " *.avif"

    if sys.platform == "linux":
        formats += " *.JPG *.JPEG"

    filters = (QApplication.translate('readImageFilters', "Images (%s)") % formats,
               QApplication.translate('readImageFilters', "All files (*.*)"))

    return filters


def saveImageFilters():
    supported_formats = QImageReader.supportedImageFormats()

    filters = []
    filters.append("JPG - JPEG (*.jpg *.jpeg)")
    filters.append("PNG - Portable Network Graphics (*.png)")
    if b'webp' in supported_formats:
        filters.append("WEBP - WebP (*.webp)")
    if b'jp2' in supported_formats:
        filters.append("JP2 - JPEG-2000 (*.jp2)")
    if b'jxl' in supported_formats:
        filters.append("JXL - JPEG XL (*.jxl)")
    if b'avif' in supported_formats:
        filters.append("AVIF - AVIF (*.avif)")
    filters.append("BMP - Windows Bitmaps (*.bmp)")
    filters.append("TIF - TIFF (*.tif *.tiff)")
    filters.append(QApplication.translate("saveImageFilters", "All files (*.*)"))

    return filters


def metalPrice(http, metal, currency, paydate=None):
    OZ_TO_GRAM = 31.1034768
    metal_finenesses = {
        'gold': 0.995,
        'silver': 0.999,
        'platinum': 0.9995,
        'palladium': 0.9995,
    }

    if not http.isAvailable():
        return None

    metal_url = f"{FINANCE_PROXY}/metal/{metal}_{currency}"
    cache = 1
    if paydate:
        metal_url += f"?date={paydate}"
        cache = 30

    response_data = http.get(metal_url, cache=cache)
    if not response_data:
        return None

    data = json.loads(response_data.decode())
    price_oz = data['price']
    price_gram = price_oz / OZ_TO_GRAM / metal_finenesses[metal]
    last_date = data['date']

    return price_gram, last_date
