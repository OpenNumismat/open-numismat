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
    if b'avif' in supported_formats:
        filters.append("AVIF - AVIF (*.avif)")
    filters.append("BMP - Windows Bitmaps (*.bmp)")
    filters.append("TIF - TIFF (*.tif *.tiff)")
    filters.append(QApplication.translate("saveImageFilters", "All files (*.*)"))

    return filters
