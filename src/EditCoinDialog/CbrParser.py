# -*- coding: utf-8 -*-

import urllib.parse

from PyQt4 import QtGui, QtCore

from EditCoinDialog.Auctions import AuctionItem
from EditCoinDialog.Auctions import _AuctionParser
from Tools.Converters import stringToMoney


class CbrParser(_AuctionParser):
    HostNames = ('www.cbr.ru', 'cbr.ru')

    @staticmethod
    def verifyDomain(url):
        return (urllib.parse.urlparse(url).hostname in CbrParser.HostNames)

    def __init__(self, url, parent=None):
        super(CbrParser, self).__init__(parent)

    def _encoding(self):
        return 'windows-1251'

    def _parse(self):
        auctionItem = AuctionItem(None)

        auctionItem.url = self.url

        tables = self.html.cssselect('table')

        start_tbl_index = 1
        if len(tables[3].cssselect('table')[0].cssselect('tr')) < 3:
            start_tbl_index = 2

        header_parts = tables[start_tbl_index].text_content().splitlines()
        auctionItem.series = ''
        for part in header_parts:
            start = part.find('Серия:')
            if start >= 0:
                series = part[start + 6:].strip()
                if series and series[-1] == '.':
                    series = series[:-1]
                auctionItem.series = series
            start = part.find('Дата выпуска:')
            if start >= 0:
                subjectshort = part[:start].strip()
                if subjectshort and subjectshort[-1] == '.':
                    subjectshort = subjectshort[:-1]
                auctionItem.subjectshort = subjectshort
                date = part[(start + 14):(start + 24)]
                auctionItem.issuedate = QtCore.QDate.fromString(date, 'dd.MM.yyyy').toString(QtCore.Qt.ISODate)
                auctionItem.year = date[6:10]
            start = part.find('Каталожный номер:')
            if start >= 0:
                auctionItem.catalognum1 = part[start + 17:].strip()

        table_element = tables[start_tbl_index + 2].cssselect('table')[0]
        header_table = table_element.cssselect('tr')[1]
        body_table = table_element.cssselect('tr')[2]
        auctionItem.thickness = ''
        auctionItem.fineness = ''
        auctionItem.weight = ''
        for i, e in enumerate(header_table.cssselect('td')):
            head = e.text_content().strip()
            value = body_table.cssselect('td')[i].text_content().strip()
            if head.startswith('Номинал'):
                auctionItem.value = int(value.split()[0])
                auctionItem.title = value
            elif head.startswith('Качество'):
                auctionItem.quality = value
            elif head.startswith('Сплав'):
                auctionItem.material = value.title()
            elif head.startswith('Материал'):
                auctionItem.material = value.title()
            elif head.startswith('Металл'):
                auctionItem.material = value.split()[0].title()
                auctionItem.fineness = value.split()[-1].split('/')[0]
            elif head.startswith('Масса'):
                auctionItem.weight = stringToMoney(value)
            elif head.startswith('Диаметр'):
                auctionItem.diameter = stringToMoney(value)
            elif head.startswith('Толщина'):
                auctionItem.thickness = stringToMoney(value)
            elif head.startswith('Тираж'):
                auctionItem.mintage = int(value)

        auctionItem.images = []

        obverse_element = tables[start_tbl_index + 4].cssselect('tr')[0]
        tag = obverse_element.cssselect('img')[0]
        href = tag.attrib['src']
        href = urllib.parse.urljoin(self.url, href)
        auctionItem.images.append(href)
        value = obverse_element.cssselect('td')[3].text_content()
        auctionItem.obversedesign = value.strip()

        reverse_element = tables[start_tbl_index + 4].cssselect('tr')[1]
        tag = reverse_element.cssselect('img')[0]
        href = tag.attrib['src']
        href = urllib.parse.urljoin(self.url, href)
        auctionItem.images.append(href)
        value = reverse_element.cssselect('td')[2].text_content()
        auctionItem.reversedesign = value.strip()

        parts = tables[start_tbl_index + 4].cssselect('tr')[2].text_content().splitlines()
        auctionItem.obversedesigner = ''
        auctionItem.reversedesigner = ''
        auctionItem.edgelabel = ''
        auctionItem.mintmark = ''
        auctionItem.mint = ''
        for part in parts:
            if part and part[-1] == '.':
                part = part[:-1]
            start = part.find('Художник:')
            if start >= 0:
                designer = part[start + 9:].strip()
                if ',' in designer:
                    parts = designer.split(',')
                    if parts[1].find('(реверс)') >= 0:
                        auctionItem.reversedesigner = parts[1].split('(')[0].strip()
                        auctionItem.obversedesigner = parts[0].split('(')[0].strip()
                    elif parts[1].find('(аверс)') >= 0:
                        auctionItem.reversedesigner = parts[0].split('(')[0].strip()
                        auctionItem.obversedesigner = parts[1].split('(')[0].strip()
                    else:
                        auctionItem.reversedesigner = parts[0].strip()
                else:
                    auctionItem.reversedesigner = designer
            start = part.find('Художник и скульптор:')
            if start >= 0:
                auctionItem.reversedesigner = part[start + 22:].strip()
            start = part.find('Оформление гурта')
            if start >= 0:
                auctionItem.edgelabel = part[start + 18:].strip()
            start = part.find('Чеканка:')
            if start >= 0:
                t = part[start + 8:].strip()
                p = t.split('(')
                if '(' in t:
                    auctionItem.mintmark = p[1].replace(')', '')
                auctionItem.mint = p[0].strip()

        auctionItem.subject = ''
        if tables[0].text_content().strip():
            url = 'http://www.cbr.ru/bank-notes_coins/base_of_memorable_coins/his/%s.htm' % auctionItem.catalognum1
            if self.readHtmlPage(url, 'utf-8'):
                content = self.html.cssselect('table')[0]
                auctionItem.subject = content.text_content().strip().replace('\t', '')
        else:
            subject_element = tables[5].cssselect('tr')[3]
            value = subject_element.text_content()
            auctionItem.subject = value.strip()

        if auctionItem.year:
            auctionItem.title = auctionItem.title + ' ' + auctionItem.year
        if auctionItem.subjectshort:
            auctionItem.title = auctionItem.title + ' ' + auctionItem.subjectshort
        if auctionItem.mintmark:
            auctionItem.title = auctionItem.title + ' ' + auctionItem.mintmark

        return auctionItem
