# -*- coding: utf-8 -*-

import json
import re
import urllib3

from PySide6.QtCore import Qt, QUrl, QMargins
from PySide6.QtGui import QDesktopServices, QImage
from PySide6.QtWidgets import QDialog, QVBoxLayout
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView as QWebView

from OpenNumismat import version
from OpenNumismat.Collection.Import import _Import2
from OpenNumismat.Collection.Import.Cache import Cache
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.Converters import numberToFraction
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator

numistaAvailable = True

try:
    from OpenNumismat.private_keys import NUMISTA_API_KEY
except ImportError:
    print('Importing from Numista not available')
    numistaAvailable = False


class WebEnginePage(QWebEnginePage):

    def acceptNavigationRequest(self, url, type_, isMainFrame):
        if type_ == QWebEnginePage.NavigationTypeLinkClicked:
            executor = QDesktopServices()
            executor.openUrl(QUrl(url))
            return False
        return super().acceptNavigationRequest(url, type_, isMainFrame)


@storeDlgSizeDecorator
class NumistaAuthentication(QDialog):

    def __init__(self, parent):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        if Settings()['locale'] in ('fr', 'es'):
            self.language = Settings()['locale']
        else:
            self.language = 'en'

        self.page = QWebView(self)
        self.page.setPage(WebEnginePage(self))
        self.page.urlChanged.connect(self.onUrlChanged)

        redirect_uri = 'local'  # Should normally be a URL to your application
        authorization_url = (f'https://{self.language}.numista.com/api/oauth_authorize.php'
                        '?response_type=code'
                        '&client_id=opennumismat'
                        f'&redirect_uri={redirect_uri}'
                        '&scope=view_collection')
        self.page.load(QUrl(authorization_url))

        layout = QVBoxLayout()
        layout.addWidget(self.page)
        layout.setContentsMargins(QMargins())
        self.setLayout(layout)

        self.setWindowTitle(self.tr("Numista"))

    def onLinkClicked(self, url):
        executor = QDesktopServices()
        executor.openUrl(QUrl(url))

    def onUrlChanged(self, url):
        url = self.page.url().toString()
        code_marker = 'api/local?code='
        if code_marker in url:
            start = url.find(code_marker) + len(code_marker)
            end = url.find('&', start)
            self.authorization_code = url[start:end]
            self.accept()
        elif 'api/local?state' in url:
            self.close()

    def onSslErrors(self, reply, errors):
        reply.ignoreSslErrors()

class ImportNumista(_Import2):
    ENDPOINT = 'https://api.numista.com/api/v3'
    CONNECTION_TIMEOUT = 10

    def __init__(self, parent=None):
        super().__init__(parent)

        settings = Settings()

        self.split_denomination = settings['numista_split_denomination']
        self.currency = settings['numista_currency']
        if settings['locale'] in ('fr', 'es'):
            self.language = settings['locale']
        else:
            self.language = 'en'

        urllib3.disable_warnings()
        timeout = urllib3.Timeout(connect=self.CONNECTION_TIMEOUT / 2,
                                  read=self.CONNECTION_TIMEOUT)
        self.http = urllib3.PoolManager(num_pools=2,
                                        headers={'User-Agent': version.AppName},
                                        timeout=timeout,
                                        cert_reqs="CERT_NONE")
        self.cache = Cache()

    @staticmethod
    def isAvailable():
        return numistaAvailable
    
    def _download_cache(self, url, get_image=False):
        raw_data = self.cache.get(url)
        is_cashed = bool(raw_data)
        if not is_cashed:
            try:
                headers = None
                if not get_image:
                    headers = {'Numista-API-Key': NUMISTA_API_KEY}
                resp = self.http.request("GET", url, headers=headers, retries=False)
                if resp.status == 200:
                    if not get_image:
                        raw_data = resp.data.decode()
                    else:
                        raw_data = resp.data
                else:
                    return None
            except:
                return None
        
        if not is_cashed:
            self.cache.set(url, raw_data)

        return raw_data

    def _connect(self, src):
        dialog = NumistaAuthentication(self.parent())

        result = dialog.exec()
        if result == QDialog.Accepted:
            url = (f"{self.ENDPOINT}/oauth_token?"
                   f"code={dialog.authorization_code}"
                   "&client_id=opennumismat"
                   f"&client_secret={NUMISTA_API_KEY}"
                   "&redirect_uri=local")
            try:
                resp = self.http.request("GET", url)
                raw_data = resp.data.decode()
            except:
                return False

            data = json.loads(raw_data)
            access_token = data['access_token']
            user_id = data['user_id']

            url = f"{self.ENDPOINT}/users/{user_id}/collected_items?lang={self.language}"
            try:
                headers = {'Numista-API-Key': NUMISTA_API_KEY,
                           'Authorization': f'Bearer {access_token}'}
                resp = self.http.request("GET", url, headers=headers)
                raw_data = resp.data.decode()
            except:
                return False

            self.coins_data = json.loads(raw_data)

            return True

        return False

    def _getRowsCount(self, connection):
        return len(self.coins_data['items'])

    def _setRecord(self, record, row):
        item = self.coins_data['items'][row]

        if 'issue' not in item:
            item['issue'] = {}
        if 'mintage' not in item['issue']:
            item['issue']['mintage'] = ''
        if 'comment' not in item['issue']:
            item['issue']['comment'] = ''
        if 'gregorian_year' in item['issue']:
            item['issue']['year'] = item['issue']['gregorian_year']
        if 'year' not in item['issue']:
            if 'min_year' in item['issue'] and 'max_year' in item['issue'] and item['issue']['min_year'] == item['issue']['max_year']:
                item['issue']['year'] = item['issue']['min_year']
            else:
                item['issue']['year'] = ''
        if 'mint_letter' not in item['issue']:
            item['issue']['mint_letter'] = ''
        if 'private_comment' not in item:
            item['private_comment'] = ''
        if 'public_comment' not in item:
            item['public_comment'] = ''
        if 'grade' not in item:
            item['grade'] = ''
        if 'price' not in item:
            item['price'] = {}
        if 'value' not in item['price']:
            item['price']['value'] = ''
        if 'issuer' not in item['type']:
            item['type']['issuer'] = {'name': ''}

        record.setValue('title', item['type']['title'])
        record.setValue('country', item['type']['issuer']['name'])
        record.setValue('features', '\n'.join((item['issue']['comment'], item['private_comment'], item['public_comment'])))
        if item['for_swap']:
            record.setValue('status', 'sale')
        else:
            record.setValue('status', 'owned')
        record.setValue('grade', item['grade'])
        record.setValue('year', item['issue']['year'])
        record.setValue('mintmark', item['issue']['mint_letter'])
        record.setValue('mintage', item['issue']['mintage'])
        record.setValue('quantity', item['quantity'])
        record.setValue('payprice', item['price']['value'])
        record.setValue('category', item['type']['category'])

        type_id = item['type']['id']
        url = f"{self.ENDPOINT}/types/{type_id}?lang={self.language}"
        raw_data = self._download_cache(url)
        if not raw_data:
            return

        item_data = json.loads(raw_data)

        if 'value' in item_data:
            if 'text' in item_data['value']:
                denomination = item_data['value']['text']
                if self.split_denomination:
                    parts = re.match(r'(^[0-9⅒⅛⅙⅕¼⅓½⅔¾,\.\s\-/⁄⅟]+)(.*)', denomination)
                    if parts:
                        value, unit = parts.groups()
                        record.setValue('value', numberToFraction(value.strip()))
                        record.setValue('unit', unit)
                    else:
                        record.setValue('unit', denomination)
                else:
                    record.setValue('unit', denomination)
            if 'currency' in item_data['value']:
                record.setValue('period', item_data['value']['currency']['full_name'])
        record.setValue('url', item_data['url'])
        if 'type' in item_data:
            record.setValue('type', item_data['type'])
        if 'series' in item_data:
            record.setValue('series', item_data['series'])
        if 'commemorated_topic' in item_data:
            record.setValue('subjectshort', item_data['commemorated_topic'])
        if 'ruler' in item_data:
            record.setValue('ruler', item_data['ruler'][0]['name'])
        if 'shape' in item_data:
            record.setValue('shape', item_data['shape'])
        if 'composition' in item_data:
            value = item_data['composition']['text']
            if '(.' in value:
                pos = value.find('(.')
                fineness = value[pos+2:-1]
                record.setValue('fineness', fineness)
                value = value[:pos].strip()
            record.setValue('material', value)
        if 'weight' in item_data:
            record.setValue('weight', item_data['weight'])
        if 'size' in item_data:
            record.setValue('diameter', item_data['size'])
        if 'thickness' in item_data:
            record.setValue('thickness', item_data['thickness'])
        if 'orientation' in item_data:
            record.setValue('obvrev', item_data['orientation'])
        if 'mints' in item_data:
            record.setValue('mint', item_data['mints'][0]['name'])
        elif 'printers' in item_data:
            record.setValue('mint', item_data['printers'][0]['name'])
        if 'min_year' in item_data and 'max_year' in item_data:
            if item_data['min_year'] != item_data['max_year']:
                record.setValue('dateemis', ' - '.join((str(item_data['min_year']), str(item_data['max_year']))))
        if 'references' in item_data:
            catalog_nums = item_data['references']
            for i, catalog_num in enumerate(catalog_nums[:4]):
                field = 'catalognum%d' % (i + 1)
                code = catalog_num['catalogue']['code'] + '# ' + catalog_num['number']
                record.setValue(field, code)
        if 'comments' in item_data:
            record.setValue('note', item_data['comments'])
        if 'technique' in item_data:
            record.setValue('technique', item_data['technique']['text'])

        if 'obverse' in item_data:
            if 'engravers' in item_data['obverse']:
                record.setValue('obverseengraver', ', '.join(item_data['obverse']['engravers']))
            if 'description' in item_data['obverse']:
                record.setValue('obversedesign', item_data['obverse']['description'])
            if 'picture' in item_data['obverse']:
                img_url = item_data['obverse']['picture']
                image = self._getImage(img_url)
                record.setValue('obverseimg', image)
        if 'reverse' in item_data:
            if 'engravers' in item_data['reverse']:
                record.setValue('reverseengraver', ', '.join(item_data['reverse']['engravers']))
            if 'description' in item_data['reverse']:
                record.setValue('reversedesign', item_data['reverse']['description'])
            if 'picture' in item_data['reverse']:
                img_url = item_data['reverse']['picture']
                image = self._getImage(img_url)
                record.setValue('reverseimg', image)
        if 'edge' in item_data:
            if 'description' in item_data['edge']:
                record.setValue('edge', item_data['edge']['description'])
            if 'lettering' in item_data['edge']:
                record.setValue('edgelabel', item_data['edge']['lettering'])
            if 'picture' in item_data['edge']:
                img_url = item_data['edge']['picture']
                image = self._getImage(img_url)
                record.setValue('edgeimg', image)

        if 'id' in item['issue']:
            issue_id = item['issue']['id']
            url = self.ENDPOINT + '/types/' + str(type_id) + '/issues/' + str(issue_id) + '/prices' + \
                '?lang=' + self.language + '&currency=' + self.currency
            raw_data = self._download_cache(url)
            if not raw_data:
                return

            prices_data = json.loads(raw_data)
    
            for price in prices_data['prices']:
                if price['grade'] == 'f':
                    record.setValue('price1', "%.2f" % price['price'])
                elif price['grade'] == 'vf':
                    record.setValue('price2', "%.2f" % price['price'])
                elif price['grade'] == 'xf':
                    record.setValue('price3', "%.2f" % price['price'])
                elif price['grade'] == 'unc':
                    record.setValue('price4', "%.2f" % price['price'])

    def _getImage(self, url):
        try:
            data = self._download_cache(url, True)
            if not data:
                return None

            image = QImage()
            image.loadFromData(data)
            return image
        except:
            return None

    def _close(self, connection):
        self.cache.close()
