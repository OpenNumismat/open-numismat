from PyQt4 import QtCore, QtGui

import urllib.request, urllib.error, urllib.parse
try:
    import lxml.html
except ImportError:
    print('lxml module missed. Auction parsing not available')

class _NotDoneYetError(Exception):
    pass

class _CanceledError(Exception):
    pass

class AuctionItem:
    def __init__(self, place):
        self.place = place
        self.saller = ''
        self.info = ''
        self.grade = ''

class _AuctionParser(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        
        self.html = ''
    
    def parse(self, url):
        self.readHtmlPage(url, self._encoding())
        
        if len(self.doc) == 0:
            return
        
        try:
            return self._parse()
        except _NotDoneYetError:
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction not done yet"),
                        QtGui.QMessageBox.Ok)
        except _CanceledError:
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction canceled"),
                        QtGui.QMessageBox.Ok)
    
    def readHtmlPage(self, url, encoding='utf-8'):
        # TODO: Remove debug output
        print(url)
        try:
            data = urllib.request.urlopen(url).read()

            self.doc = str(data, encoding)
            self.html = lxml.html.fromstring(self.doc)
            self.url = url
        except (ValueError, urllib.error.URLError):
            return False
        
        return True
    
    def _encoding(self):
        return 'utf-8'
    
    def _parse(self):
        raise NotImplementedError

from EditCoinDialog.Auctions.AuctionParser import MolotokParser
from EditCoinDialog.Auctions.AuctionParser import AuctionSpbParser
from EditCoinDialog.Auctions.AuctionParser import ConrosParser
from EditCoinDialog.Auctions.AuctionParser import WolmarParser

def getParser(url, parent=None):
    if MolotokParser.verifyDomain(url):
        return MolotokParser(parent)
    elif AuctionSpbParser.verifyDomain(url):
        return AuctionSpbParser(parent)
    elif ConrosParser.verifyDomain(url):
        return ConrosParser(parent)
    elif WolmarParser.verifyDomain(url):
        return WolmarParser(parent)
