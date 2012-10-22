# -*- coding: utf-8 -*-

import urllib.parse

from PyQt4 import QtGui, QtCore

from EditCoinDialog.Auctions import AuctionItem, _AuctionParser, _NotDoneYetError, _CanceledError
from Tools.Converters import stringToMoney

class MolotokParser(_AuctionParser):
    HostName = 'molotok.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == MolotokParser.HostName)
    
    def __init__(self, url, parent=None):
        super(MolotokParser, self).__init__(parent)
    
    def _parse(self):
        try:
            self.html.get_element_by_id('siBidForm2')
            raise _NotDoneYetError()
        except KeyError:
            pass
        # TODO: Update for new Molotok design
#        if not self.html.get_element_by_id('siBidForm2').find_class('itemBidder')[0].find_class('siBNPanel')[0].cssselect('span a'):
#            raise _CanceledError()
        
        auctionItem = AuctionItem('Молоток.Ру')
        
        content = self.html.get_element_by_id('siWrapper').find_class('timeInfo')[0].text_content()
        begin = content.find('(')
        end = content.find(',')
        date = content[begin+1:end] # convert 'завершен (19 Январь, 00:34:14)' to '19 Январь'
        tmpDate = QtCore.QDate.fromString(date, 'dd MMMM')
        currentDate = QtCore.QDate.currentDate()
        auctionItem.date = QtCore.QDate(currentDate.year(), tmpDate.month(), tmpDate.day()).toString(QtCore.Qt.ISODate)
        
        saller = self.html.find_class('sellerDetails')[0].cssselect('dl dt')[0].text_content()
        auctionItem.saller = saller.split()[0].strip()
        buyer = self.html.get_element_by_id('siWrapper').find_class('buyerInfo')[0].cssselect('strong')[1].text_content()
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

        index = self.doc.find("$j('.galleryWrap').newGallery")
        bIndex = self.doc[index:].find("large:")+index
        bIndex = self.doc[bIndex:].find("[")+bIndex
        eIndex = self.doc[bIndex:].find("]")+bIndex
        images = self.doc[bIndex+1:eIndex].strip()
        images = images.replace('"', '')
        auctionItem.images = images.split(',')

        content = self.html.get_element_by_id('itemFinishBox2').cssselect('strong')[0].text_content()
        auctionItem.price = stringToMoney(content)

        element = self.html.get_element_by_id('paymentShipment').cssselect('dd strong')
        if element:
            content = element[0].text_content()
            shipmentPrice = stringToMoney(content)
            auctionItem.totalPayPrice = str(auctionItem.price + shipmentPrice)
        else:
            auctionItem.totalPayPrice = auctionItem.price
        
        auctionItem.totalSalePrice = self.totalSalePrice(auctionItem)
    
        return auctionItem
    
    def totalSalePrice(self, lot):
        price = float(lot.price)
        if price > 50000:
            excess = price - 50000
            commission = 1557.5 + (excess*2.5/100)
        elif price > 10000:
            excess = price - 10000
            commission = 357.5 + (excess*3/100)
        elif lot.price > 500:
            excess = price - 500
            commission = 25 + (excess*3.5/100)
        else:
            commission = price*5/100
        
        if commission > 3999:
            commission = 3999
        
        return str(price - commission)

class AuctionSpbParser(_AuctionParser):
    HostNames = ('www.auction.spb.ru', 'auction.spb.ru')
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname in AuctionSpbParser.HostNames)
    
    def __init__(self, url, parent=None):
        super(AuctionSpbParser, self).__init__(parent)
        
    def _encoding(self):
        return 'windows-1251'
    
    def _parse(self):
        if self.html.cssselect('table tr')[4].cssselect('table td')[0].text_content().find("Торги по лоту завершились") < 0:
            raise _NotDoneYetError()
        
        auctionItem = AuctionItem('АукционЪ.СПб')
        
        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('b')[0].text_content()
        date = content.split()[1] # convert '12:00:00 05-12-07' to '05-12-07'
        date = QtCore.QDate.fromString(date, 'dd-MM-yy')
        if date.year() < 1960:
            date = date.addYears(100)
        auctionItem.date = date.toString(QtCore.Qt.ISODate)
        
        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('strong')[2].text_content()
        auctionItem.buyer = content.split()[-1]

        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('strong')[1].text_content()
        grade = content.split()[1]
        grade = grade.replace('.', '')  # remove end dot
        auctionItem.grade = _stringToGrade(grade)

        auctionItem.info = self.url
        
        if len(self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('table tr')) - 1 < 2:
            QtGui.QMessageBox.information(self.parent(), self.tr("Parse auction lot"),
                                self.tr("Only 1 bid"),
                                QtGui.QMessageBox.Ok)

        content = self.html.cssselect('table tr')[4].cssselect('table td')[0].cssselect('strong')[2].text_content()
        auctionItem.price = stringToMoney(content)

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
    
    def totalSalePrice(self, lot):
        price = float(lot.price)
        commission = price*15/100
        if commission < 35:
            commission = 35
        
        totalPrice = price - commission
        if totalPrice < 0:
            totalPrice = 0
        
        return str(totalPrice)

class ConrosParser(_AuctionParser):
    HostName = 'auction.conros.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == ConrosParser.HostName)
    
    def __init__(self, parent=None):
        super(ConrosParser, self).__init__(parent)
        
    def _encoding(self):
        return 'windows-1251'
    
    def _parse(self):
        if self.html.cssselect('div#your_rate')[0].text_content().find("Торги по этому лоту завершены") < 0:
            raise _NotDoneYetError()
        
        auctionItem = AuctionItem('Конрос')
        
        content = self.html.cssselect('p#lot_state.lot_info_box')[0].text_content()
        date = content.split()[9] # extract date
        auctionItem.date = QtCore.QDate.fromString(date, 'dd.MM.yyyy').toString(QtCore.Qt.ISODate)
        
        content = self.html.cssselect('p#lot_state.lot_info_box')[0].cssselect('#leader')[0].text_content()
        auctionItem.buyer = content

        content = self.html.cssselect('div#lot_information')[0].cssselect('p')[1].text_content()
        grade = content.split()[1]
        auctionItem.grade = _stringToGrade(grade)

        index = content.find("Особенности")
        auctionItem.info = '\n'.join([content[:index], content[index:], self.url])
        
        content = self.html.cssselect('p#lot_state.lot_info_box')[0].cssselect('#rate_count')[0].text_content()
        if int(content) < 2:
            QtGui.QMessageBox.information(self.parent(), self.tr("Parse auction lot"),
                                self.tr("Only 1 bid"),
                                QtGui.QMessageBox.Ok)

        content = self.html.cssselect('p#lot_state.lot_info_box')[0].cssselect('#price')[0].text_content()
        auctionItem.price = stringToMoney(content)

        price = float(auctionItem.price)
        auctionItem.totalPayPrice = str(price + price*10/100)
        
        price = float(auctionItem.price)
        auctionItem.totalSalePrice = str(price - price*15/100)
        
        auctionItem.images = []
        for tag in self.html.cssselect('div#lot_information')[0].cssselect('a'):
            href = tag.attrib['href']
            href = urllib.parse.urljoin(self.url, href)
            auctionItem.images.append(href)

        return auctionItem

class WolmarParser(_AuctionParser):
    HostName = 'www.wolmar.ru'
    
    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname == WolmarParser.HostName)
    
    def __init__(self, parent=None):
        super(WolmarParser, self).__init__(parent)
    
    def _encoding(self):
        return 'windows-1251'
    
    def _parse(self):
        if self.html.find_class('item')[0].text_content().find("Лот закрыт") < 0:
            raise _NotDoneYetError()
        
        auctionItem = AuctionItem('Wolmar')
        
        content = self.html.find_class('item')[0].find_class('values')[1].text_content()
        bIndex = content.find("Лидер")
        bIndex = content[bIndex:].find(":")+bIndex
        eIndex = content[bIndex:].find("Количество ставок")+bIndex
        auctionItem.buyer = content[bIndex+1:eIndex].strip()

        content = self.html.find_class('item')[0].find_class('values')[0].text_content()
        bIndex = content.find("Состояние")
        bIndex = content[bIndex:].find(":")+bIndex
        grade = content[bIndex+1:].strip()
        auctionItem.grade = _stringToGrade(grade)

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
        auctionItem.price = stringToMoney(content)

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
        content = self.html.find_class('content')[0].cssselect('h1 span')[0].text_content()
        date = content.split()[1] # convert '(Закрыт 29.09.2011 12:30)' to '29.09.2011'
        auctionItem.date = QtCore.QDate.fromString(date, 'dd.MM.yyyy').toString(QtCore.Qt.ISODate)
        
        return auctionItem

def _stringToGrade(string):
    # Parse VF-XF and XF/AU
    grade = ''
    for c in string:
        if c in '-+/':
            break
        else:
            grade = grade + c
        
    return grade
