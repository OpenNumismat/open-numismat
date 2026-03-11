import json
import sys
from PySide6.QtGui import QImageReader
from PySide6.QtWidgets import QApplication


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
    metal_urls = {
        'gold': "https://api.db.nomics.world/v22/series/LBMA/gold_D/gold_D_USD_AM?observations=1",
        'silver': "https://api.db.nomics.world/v22/series/LBMA/silver_D/silver_D_USD?observations=1",
        'platinum': "https://api.db.nomics.world/v22/series/LBMA/platinum_D/platinum_D_USD_AM?observations=1",
        'palladium': "https://api.db.nomics.world/v22/series/LBMA/palladium_D/palladium_D_USD_AM?observations=1",
    }
    metal_finenesses = {
        'gold': 0.995,
        'silver': 0.999,
        'platinum': 0.9995,
        'palladium': 0.9995,
    }

    if not http.isAvailable():
        return None

    response_data = http.get(metal_urls[metal], cache=1)
    if not response_data:
        return None

    data = json.loads(response_data.decode())

    series = data['series']['docs'][0]
    dates = series['period']
    values = series['value']

    if paydate:
        for i, date in enumerate(dates):
            if paydate < date:
                break
            last_date = date
            price_oz = values[i]
    else:
        last_date = dates[-1]
        price_oz = values[-1]
    price_gram = price_oz / OZ_TO_GRAM / metal_finenesses[metal]

    if currency == 'USD':
        return price_gram

    currency_url = f"https://theratesapi.com/api/{last_date}/?base=USD&symbols={currency}"
    response_data = http.get(currency_url, cache=30)
    if not response_data:
        return None

    data = json.loads(response_data.decode())

    rates = data['rates']
    rate = rates[currency]

    price_gram = price_gram * rate

    return price_gram
