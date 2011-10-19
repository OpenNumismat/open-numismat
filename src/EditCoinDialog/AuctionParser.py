# -*- coding: utf-8 -*-

import urllib.request, urllib.error, urllib.parse
import lxml.html

from PyQt4 import QtGui, QtCore

class AuctionItem:
    def __init__(self, place):
        self.place = place
        self.saller = ''
        self.info = ''
        self.grade = ''

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
            self.url = url
        except (ValueError, urllib.error.URLError):
            return False
        
        return True

class MolotokParser(AuctionParser):
    HostName = 'molotok.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == MolotokParser.HostName)
    
    def __init__(self, url, parent=None):
        super(MolotokParser, self).__init__(parent)
        
        self.readHtmlPage(url)
    
    def parse(self):
        if len(self.doc) == 0:
            return
        
        if self.html.get_element_by_id('itemBidInfo').cssselect('form.siBidFormOnce'):
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction not done yet"),
                        QtGui.QMessageBox.Ok)
            return
        if not self.html.get_element_by_id('itemBidInfo').find_class('itemBidder')[0].find_class('siBNPanel')[0].cssselect('span a'):
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction canceled"),
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
        auctionItem.info = info.strip() + '\n' + self.url
        
        if len(self.html.find_class('bidHistoryList')[0].cssselect('tr')) - 1 < 2: 
            QtGui.QMessageBox.information(self.parent(), self.tr("Parse auction lot"),
                                self.tr("Only 1 bid"),
                                QtGui.QMessageBox.Ok)

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
            elif c in '.,':
                price = price + '.'
            elif c in ' \t\n\r':
                continue
            else:
                break

        return float(price)
    
    def totalSalePrice(self, lot):
        price = float(lot.price)
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

class AuctionSpbParser(AuctionParser):
    HostName = 'www.auction.spb.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == AuctionSpbParser.HostName)
    
    def __init__(self, url, parent=None):
        super(AuctionSpbParser, self).__init__(parent)
        
        self.readHtmlPage(url, 'windows-1251')
    
    def parse(self):
        if len(self.doc) == 0:
            return
        
        if self.html.cssselect('table tr')[4].cssselect('table td')[0].text_content().find("Торги по лоту завершились") < 0:
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction not done yet"),
                        QtGui.QMessageBox.Ok)
            return
        
        auctionItem = AuctionItem('АукционЪ.СПб')
        
        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('b')[0].text_content()
        date = content.split()[1] # convert '12:00:00 05-12-07' to '05-12-07'
        date = QtCore.QDate.fromString(date, 'dd-MM-yy')
        if date.year() < 1960:
            date = date.addYears(100)
        auctionItem.date = date.toString()
        
        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('strong')[2].text_content()
        auctionItem.buyer = content.split()[-1]

        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('strong')[1].text_content()
        grade = content.split()[1]
        grade = grade.replace('.', '')  # remove end dot
        auctionItem.grade = self.contentToGrade(grade)

        auctionItem.info = self.url
        
        if len(self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('table tr')) - 1 < 2:
            QtGui.QMessageBox.information(self.parent(), self.tr("Parse auction lot"),
                                self.tr("Only 1 bid"),
                                QtGui.QMessageBox.Ok)

        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('strong')[2].text_content()
        auctionItem.price = self.contentToPrice(content)

        price = float(auctionItem.price)
        auctionItem.totalPayPrice = str(price + price*10/100)
        
        auctionItem.totalSalePrice = self.totalSalePrice(auctionItem)
        
        auctionItem.images = []
        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('a')[0]
        href = content.attrib['href']
        href = urllib.parse.urljoin(self.url, href)
        auctionItem.images.append(href)

        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('a')[1]
        href = content.attrib['href']
        href = urllib.parse.urljoin(self.url, href)
        auctionItem.images.append(href)

        return auctionItem
    
    def contentToPrice(self, content):
        valueBegan = False
        price = ''
        for c in content:
            if c in '0123456789':
                price = price + c
                valueBegan = True
            elif c in '.,':
                price = price + '.'
            elif c in ' \t\n\r':
                continue
            else:
                if valueBegan:
                    break

        return float(price)

    def totalSalePrice(self, lot):
        price = float(lot.price)
        commission = price*15/100
        if commission < 25:
            commission = 25
        
        totalPrice = price - commission
        if totalPrice < 0:
            totalPrice = 0
        
        return str(totalPrice)

    def contentToGrade(self, content):
        # Parse VF-XF and XF/AU
        grade = ''
        for c in content:
            if c in '-+/':
                break
            else:
                grade = grade + c
            
        return grade

class ConrosParser(AuctionParser):
    HostName = 'auction.conros.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == ConrosParser.HostName)
    
    def __init__(self, url, parent=None):
        super(ConrosParser, self).__init__(parent)
        
        self.readHtmlPage(url, 'windows-1251')
    
    def parse(self):
        if len(self.doc) == 0:
            return
        
        if self.html.cssselect('form center')[1].text_content().find("Торги по этому лоту завершены") < 0:
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction not done yet"),
                        QtGui.QMessageBox.Ok)
            return
        
        auctionItem = AuctionItem('Конрос')
        
        content = self.html.cssselect('form center')[1].text_content()
        date = content.split()[5] # extract date
        auctionItem.date = QtCore.QDate.fromString(date, 'dd.MM.yyyy').toString()
        
        content = self.html.cssselect('form table tr')[1].cssselect('table tr')[3].text_content().strip()
        content = content.split('\n')[1]
        auctionItem.buyer = content.split()[-1]

        content = self.html.cssselect('form table tr')[1].cssselect('table tr')[2].text_content()
        grade = content.split()[1]
        auctionItem.grade = self.contentToGrade(grade)

        index = content.find("Особенности")
        auctionItem.info = '\n'.join([content[:index], content[index:], self.url])
        
        content = self.html.cssselect('form table tr')[1].cssselect('table tr')[3].text_content().strip()
        content = content.split('\n')[2]
        if int(content.split()[-1]) < 2:
            QtGui.QMessageBox.information(self.parent(), self.tr("Parse auction lot"),
                                self.tr("Only 1 bid"),
                                QtGui.QMessageBox.Ok)

        content = self.html.cssselect('form table tr')[1].cssselect('table tr')[3].text_content().strip()
        content = content.split('\n')[0]
        auctionItem.price = self.contentToPrice(content)

        price = float(auctionItem.price)
        auctionItem.totalPayPrice = str(price + price*10/100)
        
        price = float(auctionItem.price)
        auctionItem.totalSalePrice = str(price - price*15/100)
        
        auctionItem.images = []
        for tag in self.html.cssselect('form table tr')[1].cssselect('table tr')[1].cssselect('a'):
            href = tag.attrib['href']
            href = urllib.parse.urljoin(self.url, href)
            auctionItem.images.append(href)

        return auctionItem
    
    def contentToPrice(self, content):
        valueBegan = False
        price = ''
        for c in content:
            if c in '0123456789':
                price = price + c
                valueBegan = True
            elif c in '.,':
                price = price + '.'
            elif c in ' \t\n\r':
                continue
            else:
                if valueBegan:
                    break

        return float(price)
    
    def contentToGrade(self, content):
        # Parse VF-XF and XF/AU
        grade = ''
        for c in content:
            if c in '-+/':
                break
            else:
                grade = grade + c
            
        return grade

class WolmarParser(AuctionParser):
    HostName = 'www.wolmar.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == WolmarParser.HostName)
    
    def __init__(self, url, parent=None):
        super(WolmarParser, self).__init__(parent)
        
        self.readHtmlPage(url, 'windows-1251')
    
    def parse(self):
        if len(self.doc) == 0:
            return
        
        if self.html.find_class('item')[0].text_content().find("Лот закрыт") < 0:
            QtGui.QMessageBox.warning(self.parent(), self.tr("Parse auction lot"),
                        self.tr("Auction not done yet"),
                        QtGui.QMessageBox.Ok)
            return
        
        auctionItem = AuctionItem('Волмар')
        
        content = self.html.find_class('item')[0].find_class('values')[1].text_content()
        bIndex = content.find("Лидер")
        bIndex = content[bIndex:].find(":")+bIndex
        eIndex = content[bIndex:].find("Количество ставок")+bIndex
        auctionItem.buyer = content[bIndex+1:eIndex].strip()

        content = self.html.find_class('item')[0].find_class('values')[0].text_content()
        bIndex = content.find("Состояние")
        bIndex = content[bIndex:].find(":")+bIndex
        grade = content[bIndex+1:].strip()
        auctionItem.grade = self.contentToGrade(grade)

        auctionItem.info = self.url
        
        content = self.html.find_class('item')[0].find_class('values')[1].text_content()
        bIndex = content.find("Количество ставок")
        bIndex = content[bIndex:].find(":")+bIndex
        eIndex = content[bIndex:].find("Лот закрыт")+bIndex
        content = content[bIndex+1:eIndex].strip()
        if int(content) < 2:
            QtGui.QMessageBox.information(self.parent(), self.tr("Parse auction lot"),
                                self.tr("Only 1 bid"),
                                QtGui.QMessageBox.Ok)

        content = self.html.find_class('item')[0].find_class('values')[1].text_content()
        bIndex = content.find("Ставка")
        bIndex = content[bIndex:].find(":")+bIndex
        eIndex = content[bIndex:].find("Лидер")+bIndex
        content = content[bIndex+1:eIndex].strip()
        auctionItem.price = self.contentToPrice(content)

        price = float(auctionItem.price)
        auctionItem.totalPayPrice = str(price + price*10/100)
        
        price = float(auctionItem.price)
        auctionItem.totalSalePrice = str(price - price*10/100)
        
        storedUrl = self.url
        
        auctionItem.images = []
        for tag in self.html.find_class('item')[0].cssselect('a'):
            href = tag.attrib['href']
            url = urllib.parse.urljoin(storedUrl, href)
            self.readHtmlPage(url, 'windows-1251')
            content = self.html.cssselect('div')[0]
            for tag in content.cssselect('div'):
                tag.drop_tree()
            content = content.cssselect('img')[0]
            src = content.attrib['src']
            href = urllib.parse.urljoin(self.url, src)
            auctionItem.images.append(href)

        # Extract date from parent page
        url = urllib.parse.urljoin(storedUrl, '.')[:-1]
        self.readHtmlPage(url, 'windows-1251')
        content = self.html.find_class('content')[0]
        content = self.html.find_class('content')[0].cssselect('h1 span')[0].text_content()
        date = content.split()[1] # convert '(Закрыт 29.09.2011 12:30)' to '29.09.2011'
        auctionItem.date = QtCore.QDate.fromString(date, 'dd.MM.yyyy').toString()
        
        return auctionItem
    
    def contentToPrice(self, content):
        valueBegan = False
        price = ''
        for c in content:
            if c in '0123456789':
                price = price + c
                valueBegan = True
            elif c in '.,':
                price = price + '.'
            elif c in ' \t\n\r':
                continue
            else:
                if valueBegan:
                    break

        return float(price)
    
    def contentToGrade(self, content):
        # Parse VF-XF and XF/AU
        grade = ''
        for c in content:
            if c in '-+/':
                break
            else:
                grade = grade + c
            
        return grade

def getParser(url, parent=None):
    if MolotokParser.verifyDomain(url):
        return MolotokParser(url, parent)
    elif AuctionSpbParser.verifyDomain(url):
        return AuctionSpbParser(url, parent)
    elif ConrosParser.verifyDomain(url):
        return ConrosParser(url, parent)
    elif WolmarParser.verifyDomain(url):
        return WolmarParser(url, parent)
    return WolmarParser('http://www.wolmar.ru/auction/466/369651?category=9', parent)
