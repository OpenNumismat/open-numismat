import json
import urllib.request

from PyQt5.QtCore import Qt, QUrl, QMargins
from PyQt5.QtGui import QImage, QPixmap, QDesktopServices
from PyQt5.QtWidgets import *

from OpenNumismat.Collection.Import import _Import2
from OpenNumismat.Settings import Settings
from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator

importedQtWebKit = True
numistaAvailable = True
try:
    from PyQt5.QtWebKitWidgets import QWebView, QWebPage
except ImportError:
    print('PyQt5.QtWebKitWidgets module missed. Importing from Numista not available')
    importedQtWebKit = False
    numistaAvailable = False

    class QWebView:
        pass

try:
    from OpenNumismat.private_keys import NUMISTA_API_KEY
except ImportError:
    print('Importing from Numista not available')
    numistaAvailable = False


@storeDlgSizeDecorator
class NumistaAuthentication(QDialog):

    def __init__(self, parent):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        if Settings()['locale'] == 'fr':
            self.language = Settings()['locale']
        else:
            self.language = 'en'

        self.page = QWebView(self)
        self.page.linkClicked.connect(self.onLinkClicked)
        self.page.urlChanged.connect(self.onUrlChanged)
        self.page.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)

        redirect_uri = 'local'  # Should normally be a URL to your application
        url_template = ('https://{language}.numista.com/api/oauth_authorize.php'
                        '?response_type=code'
                        '&client_id={client_id}'
                        '&redirect_uri={redirect_uri}'
                        '&scope={scope}')
        authorization_url = url_template.format(
          language=self.language,
          client_id='opennumismat',
          redirect_uri=redirect_uri,
          scope='view_collection')
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


class ImportNumista(_Import2):

    @staticmethod
    def isAvailable():
        return numistaAvailable

    def _connect(self, src):
        dialog = NumistaAuthentication(self.parent())

        result = dialog.exec_()
        if result == QDialog.Accepted:
            endpoint = 'https://api.numista.com/api/v1'

            url = endpoint + '/oauth_token?' + \
                'code=' + dialog.authorization_code + \
                '&client_id=opennumismat' + \
                '&client_secret=' + NUMISTA_API_KEY + \
                '&redirect_uri=local'
            try:
                req = urllib.request.Request(url)
                raw_data = urllib.request.urlopen(req).read().decode()
                print(raw_data)
            except:
                return False

            data = json.loads(raw_data)
            access_token = data['access_token']
            user_id = data['user_id']

            if Settings()['locale'] == 'fr':
                language = Settings()['locale']
            else:
                language = 'en'

            url = endpoint + '/users/' + str(user_id) + '/collected_coins?' +\
                'lang=' + language
            try:
                req = urllib.request.Request(url,
                        headers={'Numista-API-Key': NUMISTA_API_KEY,
                                 'Authorization': 'Bearer ' + access_token})
                raw_data = urllib.request.urlopen(req).read().decode()
                print(raw_data)
            except:
                return False

            self.coin_data = json.loads(raw_data)

            return True

        return False

    def _getRowsCount(self, connection):
        return len(self.coin_data['collected_coins'])

    def _setRecord(self, record, row):
        item = self.coin_data['collected_coins'][row]

        if 'issue' not in item:
            item['issue'] = {}
        if 'mintLetter' not in item['issue']:
            item['issue']['mintLetter'] = ''
        if 'comment' not in item['issue']:
            item['issue']['comment'] = ''
        if 'private_comment' not in item:
            item['private_comment'] = ''
        if 'public_comment' not in item:
            item['public_comment'] = ''
        if 'public_comment' not in item:
            item['public_comment'] = ''
        if 'grade' not in item:
            item['grade'] = ''
        if 'price' not in item:
            item['price'] = {}
        if 'value' not in item['price']:
            item['price']['value'] = ''

        record.setValue('title', item['coin']['title'])
        record.setValue('country', item['coin']['issuer']['name'])
        record.setValue('features', '\n'.join((item['issue']['comment'], item['private_comment'], item['public_comment'])))
        if item['for_swap']:
            record.setValue('status', 'sale')
        else:
            record.setValue('status', 'owned')
        record.setValue('grade', item['grade'])
        record.setValue('year', item['issue']['year'])
        record.setValue('mintmark', item['issue']['mintLetter'])
        record.setValue('quantity', item['quantity'])
        record.setValue('payprice', item['price']['value'])
