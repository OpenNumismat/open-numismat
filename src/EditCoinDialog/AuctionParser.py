# -*- coding: utf-8 -*-

import urllib.request, urllib.error
import lxml.html

from PyQt4 import QtGui, QtCore

class AuctionItem:
    def __init__(self, place):
        self.place = place

class AuctionParser(QtCore.QObject):
    def __init__(self, parent=None):
        super(AuctionParser, self).__init__(parent)
        
        self.html = ''
    
    def readHtmlPage(self, url, encoding='utf-8'):
        # TODO: Remove debug output
        print(url)
        try:
            data = urllib.request.urlopen(url).read()

            self.doc = str(data, encoding)
            self.html = lxml.html.fromstring(self.doc)
        except (ValueError, urllib.error.URLError):
            return False
        
        return True

class MolotokParser(AuctionParser):
    def __init__(self, url, parent=None):
        super(MolotokParser, self).__init__(parent)
        
        self.readHtmlPage(url)
    
    def parse(self):
        if len(self.html) == 0:
            return
        
        if self.html.get_element_by_id('itemBidInfo').cssselect('form.siBidFormOnce'):
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction item"),
                        self.tr("Auction not done yet"),
                        QtGui.QMessageBox.Ok)
            return
        
        auctionItem = AuctionItem('Молоток.Ру')
        
        content = self.html.get_element_by_id('itemBidInfo').find_class('sellerItemPadding')[0].text_content()
        parts = content.split()
        date = ' '.join(parts[1:4]) # convert '(Чтв 15 Сен 2011 22:33:47)' to '15 Сен 2011'
        auctionItem.date = QtCore.QDate.fromString(date, 'dd MMM yyyy').toString()
        
        saller = self.html.get_element_by_id('itemBidInfo').find_class('sellerInfo')[0].text_content()
        auctionItem.saller = saller.strip()
        buyer = self.html.get_element_by_id('itemBidInfo').find_class('itemBidder')[0].find_class('siBNPanel')[0].cssselect('span a')[0].text_content()
        auctionItem.buyer = buyer.strip()

        # Remove STYLE element
        for element in self.html.get_element_by_id('user_field').cssselect('style'):
            element.getparent().remove(element)
        info = self.html.get_element_by_id('user_field').text_content()
        auctionItem.info = info.strip()

        index = self.doc.find("$j('#galleryWrap').newGallery")
        bIndex = self.doc[index:].find("large:")+index
        bIndex = self.doc[bIndex:].find("[")+bIndex
        eIndex = self.doc[bIndex:].find("]")+bIndex
        images = self.doc[bIndex+1:eIndex].strip()
        images = images.replace('"', '')
        auctionItem.images = images.split(',')

        content = self.html.get_element_by_id('itemBidInfo').find_class('itemBidder')[0].find_class('siBNPanel')[0].cssselect('p strong')[1].text_content()
        auctionItem.price = self.contentToPrice(content)

        content = self.html.get_element_by_id('itemBidInfo').find_class('itemBidder')[0].find_class('shipmentShowHide')[0].cssselect('strong')[0].text_content()
        auctionItem.totalPayPrice = self.contentToPrice(content)
        
        auctionItem.totalSalePrice = self.totalSalePrice(auctionItem)
    
        return auctionItem
    
    def contentToPrice(self, content):
        price = ''
        for c in content:
            if c in '0123456789':
                price = price + c
            elif c in ' \t\n\r':
                continue
            else:
                break

        return int(price)
    
    def totalSalePrice(self, lot):
        price = int(lot.price)
        if price > 50000:
            excess = price - 50000
            commission = 1552.5 + (excess*2.5/100)
        elif price > 10000:
            excess = price - 10000
            commission = 352.5 + (excess*3/100)
        elif lot.price > 500:
            excess = price - 500
            commission = 20 + (excess*3.5/100)
        else:
            commission = price*4/100
        
        return str(price - commission)
