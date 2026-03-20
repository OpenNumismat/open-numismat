import json

from PySide6.QtCore import QByteArray, QPoint
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QImage
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView as QWebView

from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartModel
from OpenNumismat.Tools.CachedPoolManager import CachedPoolManager
from OpenNumismat.Tools.Gui import ProgressDialog

try:
    from OpenNumismat.private_keys import MAPS_API_KEY
except ImportError:
    print('GeoChart does not support non-English country names')
    MAPS_API_KEY = ''


class GeoChart(QWebView):
    doubleClicked = pyqtSignal(QPoint)

    HTML = """
<html>
  <head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <meta charset="utf-8">
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {
        'packages':['geochart'],
        'language': '%s',
        'mapsApiKey': '%s'
      });
      google.charts.setOnLoadCallback(drawRegionsMap);

      var data;
      var chart;
      var element;
      var region = %s;

      function drawRegionsMap() {
        data = google.visualization.arrayToDataTable([
          %s
        ]);

        element = document.getElementById('regions_div');
        chart = new google.visualization.GeoChart(element);
        chart.draw(data, {region: region});
      }
      window.onresize = function(event) {
        width = element.style.width;
        height = element.style.height;
        chart.draw(data, {width: width, height: height, region: region});
      }
    </script>
  </head>
  <body>
    <div id="regions_div" style="width: 100%%; height: 100%%;"></div>
  </body>
</html>
    """

    def __init__(self, model, parent=None):
        super().__init__(parent)

        self.model = model

    def updateChart(self):
        data = ','.join(["['%s', %d]" % (x, y) for x, y in zip(self.model.x_data, self.model.y_data)])
        header = "['%s', '%s']" % (self.tr("Country"), self.tr("Quantity"))
        data = ','.join((header, data))
        locale = Settings()['locale']
        self.html_data = self.HTML % (locale, MAPS_API_KEY, self.model.region, data)
        self.setHtml(self.html_data)

    def filters(self):
        return (QApplication.translate('GeoChartCanvas', "Web page (*.htm *.html)"),
                QApplication.translate('GeoChartCanvas', "PNG image (*.png)"))

    def save(self, fileName, selectedFilter):
        if selectedFilter == self.filters()[1]:
            self.__fileName = fileName
            self.page().runJavaScript("chart.getImageURI()", self.saveResponse)
        else:
            with open(fileName, 'wb') as f:
                f.write(bytes(self.html_data, 'utf-8'))

    def saveResponse(self, img):
        if img:
            by = QByteArray.fromBase64(img[22:].encode('utf-8'))
            image = QImage.fromData(by, "PNG")
            image.save(self.__fileName)
        else:
            QMessageBox.warning(self.parent(),
                        self.tr("Saving"),
                        self.tr("Image not ready. Please try again later"))

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(event.position().toPoint())

    def contextMenuEvent(self, _event):
        pass


class GeoChartModel(BaseChartModel):

    def __init__(self, db, filter_, parent=None):
        super().__init__(db, filter_, parent)

        self.region = None
        self.http = CachedPoolManager(parent)

    def loadData(self, region):
        if self.filter:
            sql_filter = "WHERE %s" % filter
        else:
            sql_filter = ""

        sql = "SELECT sum(iif(quantity!='',quantity,1)), IFNULL(country,'') FROM coins %s GROUP BY IFNULL(country,'')" % sql_filter
        query = QSqlQuery(self.db)
        query.exec(sql)
        xx = []
        yy = []
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            xx.append(val)
            yy.append(count)
    
        self.x_data = self.translateCountries(xx)
        self.y_data = yy
        self.region = region

    def translateCountries(self, countries):
        progressDlg = ProgressDialog(self.tr("Translation of country names"),
                            self.tr("Cancel"), len(countries), self.parent())

        delay = 1  # maximum of 1 request per second
        for i, country in enumerate(countries):
            progressDlg.step()
            if progressDlg.wasCanceled():
                break

            if country:
                url = f"https://nominatim.openstreetmap.org/?q={country}&format=json&limit=1&accept-language=en"
                response_data = self.http.get(url, cache=30, delay=delay)
                if not response_data:
                    break

                data = json.loads(response_data.decode())
                if data and 'name' in data[0]:
                    countries[i] = data[0]['name']

        progressDlg.reset()

        return countries
