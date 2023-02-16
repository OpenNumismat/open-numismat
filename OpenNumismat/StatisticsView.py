from textwrap import wrap

from PySide6.QtCore import Qt, QPoint, QMargins, QSize, QDateTime, QByteArray
from PySide6.QtGui import QImage, QIcon, QCursor, QPainter, QColor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import *
from PySide6.QtCharts import QBarSet, QBarSeries, QChart, QChartView, QBarCategoryAxis, QValueAxis, QHorizontalBarSeries, QPieSeries, QHorizontalStackedBarSeries, QLineSeries, QStackedBarSeries
from PySide6.QtWebEngineWidgets import QWebEngineView as QWebView

import OpenNumismat
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Gui import getSaveFileName, ProgressDialog
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings

gmapsAvailable = True

try:
    from OpenNumismat.private_keys import MAPS_API_KEY
except ImportError:
    print('GMaps not available')
    gmapsAvailable = False


class GeoChart(QWebView):
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

    def setData(self, xx, yy, region):
        data = ','.join(["['%s', %d]" % (x, y) for x, y in zip(xx, yy)])
        header = "['%s', '%s']" % (self.tr("Country"), self.tr("Number of coins"))
        data = ','.join((header, data))
        locale = Settings()['locale']
        self.html_data = self.HTML % (locale, MAPS_API_KEY, region, data)
        self.setHtml(self.html_data)

    def setMulticolor(self, multicolor=False):
        pass

    filters = (QApplication.translate('GeoChartCanvas', "Web page (*.htm *.html)"),
               QApplication.translate('GeoChartCanvas', "PNG image (*.png)"))

    def save(self, fileName, selectedFilter):
        if selectedFilter == self.filters[1]:
            img = self.page().mainFrame().evaluateJavaScript("chart.getImageURI()")
            if img:
                ba = QByteArray()
                ba.append(img[22:])
                by = QByteArray.fromBase64(ba)
                image = QImage.fromData(by, "PNG")
                image.save(fileName)
            else:
                QMessageBox.warning(self.parent(),
                            self.tr("Saving"),
                            self.tr("Image not ready. Please try again later"))
        else:
            if selectedFilter == self.filters[0]:
                with open(fileName, 'wb') as f:
                    f.write(bytes(self.html_data, 'utf-8'))


class BaseChart(QChartView):
    
    BLAF_PALETTE = (
            '#336699', '#99CCFF', '#999933', '#666699', '#CC9933', '#006666',
            '#3399FF', '#993300', '#CCCC99', '#666666', '#FFCC66', '#6699CC',
            '#663366', '#9999CC', '#CCCCCC', '#669999', '#CCCC66', '#CC6600',
            '#9999FF', '#0066CC', '#99CCCC', '#999999', '#FFCC00', '#009999',
            '#99CC33', '#FF9900', '#999966', '#66CCCC', '#339966', '#CCCC33')

    def __init__(self, parent=None):
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.layout().setContentsMargins(0, 0, 0, 0)
        self.chart.setBackgroundRoundness(0)
        
        self.label = QApplication.translate('BaseCanvas', "Number of coins")
        self.label_y = ''
        self.colors = False
        self.use_blaf_palette = True    # TODO: Move to settings
        
        super().__init__(self.chart, parent)

        self.setRenderHint(QPainter.Antialiasing)

    def setMulticolor(self, multicolor=False):
        self.colors = multicolor

    def setLabel(self, text):
        self.label = text

    def setLabelY(self, text):
        self.label_y = text

    def hover(self, status, index, barset):
        if status:
            QToolTip.showText(QCursor.pos(), self.tooltip(index))
        else:
            QToolTip.showText(QPoint(), "")

    def tooltip(self, pos):
        x = self.xx[pos]
        y = self.yy[pos]
        return "%s: %s\n%s: %d" % (self.label_y, x, self.label, y)

    filters = (QApplication.translate('BaseCanvas', "Images (*.png *.jpg *.jpeg *.bmp *.tiff *.gif)"),
               QApplication.translate('BaseCanvas', "All files (*.*)"))

    def save(self, fileName, selectedFilter):
        self.grab().save(fileName)


class BarChart(BaseChart):
    
    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy
        
        if self.colors:
            series = QStackedBarSeries()
        else:
            series = QBarSeries()
        series.hovered.connect(self.hover)

        axisX = QBarCategoryAxis()
        axisX.append(xx)
        series.attachAxis(axisX)
        self.chart.addAxis(axisX, Qt.AlignBottom)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        if yy:
            axisY.setRange(0, max(yy))
        axisY.setLabelFormat("%d")
        series.attachAxis(axisY)
        self.chart.addAxis(axisY, Qt.AlignLeft)

        if self.colors:
            for i, y in enumerate(yy):
                lst = [0] * len(yy)
                lst[i] = y
                setY = QBarSet(self.label_y)
                setY.append(lst)
                if self.use_blaf_palette:
                    setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
                series.append(setY)
        else:
            setY = QBarSet(self.label_y)
            setY.append(yy)
            series.append(setY)

        self.chart.addSeries(series)


class BarHChart(BaseChart):
    
    def setData(self, xx, yy):
        xx = xx[::-1]  # xx.reverse()
        yy = yy[::-1]  # yy.reverse()

        self.xx = xx
        self.yy = yy
        
        if self.colors:
            series = QHorizontalStackedBarSeries()
        else:
            series = QHorizontalBarSeries()
        series.hovered.connect(self.hover)

        axisY = QBarCategoryAxis()
        axisY.append(xx)
        series.attachAxis(axisY)
        self.chart.addAxis(axisY, Qt.AlignLeft)

        axisX = QValueAxis()
        axisX.setTitleText(self.label)
        if yy:
            axisX.setRange(0, max(yy))
        axisX.setLabelFormat("%d")
        series.attachAxis(axisX)
        self.chart.addAxis(axisX, Qt.AlignBottom)

        if self.colors:
            for i, y in enumerate(yy):
                lst = [0] * len(yy)
                lst[i] = y
                setY = QBarSet(self.label_y)
                setY.append(lst)
                if self.use_blaf_palette:
                    setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
                series.append(setY)
        else:
            setY = QBarSet(self.label_y)
            setY.append(yy)
            series.append(setY)

        self.chart.addSeries(series)


class PieChart(BaseChart):
    
#    def __init__(self, parent=None):
#        super().__init__(parent)
#        self.chart.legend().show()
#        self.chart.legend().setAlignment(Qt.AlignRight)

    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy
        
        series = QPieSeries()
        series.hovered.connect(self.hover)

        if self.use_blaf_palette:
            for i, (x, y) in enumerate(zip(xx, yy)):
                _slice = series.append(x, y)
                _slice.setBrush(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
        else:
            for x, y in zip(xx, yy):
                series.append(x, y)

        self.chart.addSeries(series)
        series.setLabelsVisible(True)

    def hover(self, slice, state):
        if state:
            tooltip = "%s: %s\n%s: %d" % (self.label_y, slice.label(), self.label, slice.value())
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class StackedBarChart(BaseChart):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart.legend().show()

    def setLabelZ(self, text):
        self.label_z = text

    @waitCursorDecorator
    def setData(self, xx, yy, zz):
        self.xx = xx
        self.yy = yy
        self.zz = zz
        
        series = QHorizontalStackedBarSeries()
        series.hovered.connect(self.hover)

        axisY = QBarCategoryAxis()
        axisY.append(xx)
        series.attachAxis(axisY)
        self.chart.addAxis(axisY, Qt.AlignLeft)

        axisX = QValueAxis()
        axisX.setTitleText(self.label)
        if yy:
            sums = []
            for i in range(len(yy[0])):
                sums.append(sum(y[i] for y in yy))
            axisX.setRange(0, max(sums))
        axisX.setLabelFormat("%d")
        series.attachAxis(axisX)
        self.chart.addAxis(axisX, Qt.AlignBottom)

        for i, (y, z) in enumerate(zip(yy, zz)):
            setY = QBarSet(z)
            setY.append(y)
            if self.use_blaf_palette:
                setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            series.append(setY)

        self.chart.addSeries(series)

    def hover(self, status, index, barset):
        if status:
            x = self.xx[index]
            y = barset.at(index)
            z = barset.label()
            s = sum([yy[index] for yy in self.yy])
            tooltip = "%s: %s\n%s: %s\n%s: %d/%d" % (self.label_y, x, self.label_z, z,
                                                     self.label, y, s)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class ProgressChart(BaseChart):
    
    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy
        
        if self.colors:
            series = QStackedBarSeries()
        else:
            series = QBarSeries()
        series.hovered.connect(self.hover)

        if self.colors:
            for i, y in enumerate(yy):
                lst = [0] * len(yy)
                lst[i] = y
                setY = QBarSet(self.label_y)
                setY.append(lst)
                if self.use_blaf_palette:
                    setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
                series.append(setY)
        else:
            setY = QBarSet(self.label_y)
            setY.append(yy)
            series.append(setY)

        self.chart.addSeries(series)

        lineseries = QLineSeries()
        lineseries.setName(self.tr("Trend"))
        
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y
            lineseries.append(QPoint(i, cur_y))

        self.chart.addSeries(lineseries)

        axisX = QBarCategoryAxis()
        axisX.append(xx)
        self.chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        lineseries.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setLabelFormat("%d")
        axisY.setRange(0, cur_y)
        self.chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        lineseries.attachAxis(axisY)
        

class StatisticsView(QWidget):
    def __init__(self, statisticsParam, parent=None):
        super().__init__(parent)

        self.statisticsParam = statisticsParam

        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins())
        layout.setAlignment(Qt.AlignTop)

        ctrlLayout = QVBoxLayout()
        ctrlLayout.setAlignment(Qt.AlignTop)
        widget = self.__layoutToWidget(ctrlLayout)
        widget.setSizePolicy(QSizePolicy.Fixed,
                             QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.chartLayout = QVBoxLayout()
        self.chartLayout.setContentsMargins(QMargins())
        layout.addWidget(self.__layoutToWidget(self.chartLayout))

        self.chart = QWidget(self)
        self.chartLayout.addWidget(self.chart)

        self.chartSelector = QComboBox(self)
        self.chartSelector.addItem(self.tr("Bar"), 'bar')
        self.chartSelector.addItem(self.tr("Horizontal bar"), 'barh')
        self.chartSelector.addItem(self.tr("Pie"), 'pie')
        self.chartSelector.addItem(self.tr("Stacked bar"), 'stacked')
        self.chartSelector.addItem(self.tr("Progress"), 'progress')
        if gmapsAvailable:
            self.chartSelector.addItem(self.tr("GeoChart"), 'geochart')
        ctrlLayout.addWidget(QLabel(self.tr("Chart:")))
        ctrlLayout.addWidget(self.chartSelector)

        self.fieldLabel = QLabel(self.tr("Field:"))
        ctrlLayout.addWidget(self.fieldLabel)
        self.fieldSelector = QComboBox(self)
        ctrlLayout.addWidget(self.fieldSelector)

        self.subfieldLabel = QLabel(self.tr("Additional field:"))
        ctrlLayout.addWidget(self.subfieldLabel)
        self.subfieldSelector = QComboBox(self)
        ctrlLayout.addWidget(self.subfieldSelector)

        self.periodLabel = QLabel(self.tr("Sum per:"))
        ctrlLayout.addWidget(self.periodLabel)
        self.periodSelector = QComboBox(self)
        self.periodSelector.addItem(self.tr("Year"), 'year')
        self.periodSelector.addItem(self.tr("Month"), 'month')
        self.periodSelector.addItem(self.tr("Week"), 'week')
        self.periodSelector.addItem(self.tr("Day"), 'day')
        ctrlLayout.addWidget(self.periodSelector)

        self.itemsLabel = QLabel(self.tr("Items:"))
        ctrlLayout.addWidget(self.itemsLabel)
        self.itemsSelector = QComboBox(self)
        self.itemsSelector.addItem(self.tr("Count"), 'count')
        self.itemsSelector.addItem(self.tr("Price"), 'price')
        self.itemsSelector.addItem(self.tr("Total price"), 'totalprice')
        self.itemsSelector.addItem(self.tr("Created"), 'created')
        ctrlLayout.addWidget(self.itemsSelector)

        self.colorCheck = QCheckBox(self.tr("Multicolor"), self)
        ctrlLayout.addWidget(self.colorCheck)

        self.regionLabel = QLabel(self.tr("Region:"))
        ctrlLayout.addWidget(self.regionLabel)
        self.regionSelector = QComboBox(self)
        self.regionSelector.addItem(self.tr("All"), "'world'")
        self.regionSelector.addItem(self.tr("Europe"), "'150'")
        self.regionSelector.addItem(self.tr("Africa"), "'002'")
        self.regionSelector.addItem(self.tr("Americas"), "'019'")
        self.regionSelector.addItem(self.tr("Asia"), "'142'")
        self.regionSelector.addItem(self.tr("Oceania"), "'009'")
        ctrlLayout.addWidget(self.regionSelector)

        saveButton = QPushButton()
        icon = QIcon(':/save.png')
        saveButton.setIcon(icon)
        saveButton.setIconSize(QSize(16, 16))
        saveButton.setToolTip(self.tr("Save chart"))
        saveButton.setFixedWidth(25)
        ctrlLayout.addSpacing(1000)
        ctrlLayout.addWidget(saveButton)
        saveButton.clicked.connect(self.save)

        self.setLayout(layout)

    def setModel(self, model):
        self.model = model

        default_subfieldid = 0
        for field in self.model.fields.userFields:
            if field.name in ('region', 'country', 'year', 'period', 'ruler',
                              'mint', 'type', 'series', 'status', 'material',
                              'grade', 'saller', 'payplace', 'buyer',
                              'saleplace', 'storage', 'fineness', 'unit'):
                if field.name == 'fineness':
                    title = self.model.fields.material.title + '+' + field.title
                    self.fieldSelector.addItem(title, field.id)
                elif field.name == 'unit':
                    title = self.model.fields.value.title + '+' + field.title
                    self.fieldSelector.addItem(title, field.id)
                else:
                    self.fieldSelector.addItem(field.title, field.id)
                    self.subfieldSelector.addItem(field.title, field.id)
                if field.name == 'status':
                    default_subfieldid = field.id

        # TODO: Store field name instead field ID
        fieldid = self.statisticsParam['fieldid']
        index = self.fieldSelector.findData(fieldid)
        if index >= 0:
            self.fieldSelector.setCurrentIndex(index)

        subfieldid = self.statisticsParam['subfieldid']
        index = self.subfieldSelector.findData(subfieldid)
        if index >= 0:
            self.subfieldSelector.setCurrentIndex(index)
        elif default_subfieldid:
            index = self.subfieldSelector.findData(default_subfieldid)
            self.subfieldSelector.setCurrentIndex(index)

        chart = self.statisticsParam['chart']
        index = self.chartSelector.findData(chart)
        if index >= 0:
            self.chartSelector.setCurrentIndex(index)

        items = self.statisticsParam['items']
        index = self.itemsSelector.findData(items)
        if index >= 0:
            self.itemsSelector.setCurrentIndex(index)

        period = self.statisticsParam['period']
        index = self.periodSelector.findData(period)
        if index >= 0:
            self.periodSelector.setCurrentIndex(index)

        color = self.statisticsParam['color']
        self.colorCheck.setChecked(color)

        self.showConfig(chart)
        self.chartSelector.currentIndexChanged.connect(self.chartChaged)
        self.fieldSelector.currentIndexChanged.connect(self.fieldChaged)
        self.subfieldSelector.currentIndexChanged.connect(self.subfieldChaged)
        self.periodSelector.currentIndexChanged.connect(self.periodChaged)
        self.itemsSelector.currentIndexChanged.connect(self.itemsChaged)
        self.colorCheck.stateChanged.connect(self.colorChanged)
        self.regionSelector.currentIndexChanged.connect(self.regionChanged)

    def modelChanged(self):
        self.chartLayout.removeWidget(self.chart)
        self.chart.deleteLater()
        chart = self.chartSelector.currentData()
        if chart == 'geochart':
            self.chart = GeoChart(self)
        elif chart == 'barh':
            self.chart = BarHChart(self)
        elif chart == 'pie':
            self.chart = PieChart(self)
        elif chart == 'stacked':
            self.chart = StackedBarChart(self)
        elif chart == 'progress':
            self.chart = ProgressChart(self)
        else:
            self.chart = BarChart(self)
        self.chart.setMulticolor(self.colorCheck.checkState() == Qt.Checked)
        self.chartLayout.addWidget(self.chart)

        fieldId = self.fieldSelector.currentData()
        field = self.model.fields.field(fieldId).name
        if field == 'fineness':
            field = 'material,fineness'
        elif field == 'unit':
            field = 'value,unit'
        filter_ = self.model.filter()
        if filter_:
            sql_filter = "WHERE %s" % filter_
        else:
            sql_filter = ""

        if chart == 'geochart':
            sql = "SELECT count(*), country FROM coins %s GROUP BY country" % sql_filter
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(1))
                xx.append(val)
                yy.append(count)

            self.chart.setData(xx, yy, self.regionSelector.currentData())
        elif chart == 'stacked':
            subfieldId = self.subfieldSelector.currentData()
            subfield = self.model.fields.field(subfieldId).name
            sql = "SELECT count(%s), %s, %s FROM coins %s GROUP BY %s, %s" % (
                subfield, subfield, field, sql_filter, field, subfield)
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            zz = []
            vv = {}
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(2))
                if field == 'status':
                    val = Statuses[val]
                elif field == 'value,unit':
                    val = numberWithFraction(val)[0] + ' ' + str(record.value(3))
                elif ',' in field:
                    val += ' ' + str(record.value(3))
                subval = str(record.value(1))
                if subfield == 'status':
                    subval = Statuses[subval]

                if val not in xx:
                    xx.append(val)
                if subval not in zz:
                    zz.append(subval)
                if val not in vv:
                    vv[val] = {}
                vv[val][subval] = count

            for _ in range(len(zz)):
                yy.append([0] * len(xx))

            xx = xx[::-1]
            for i, val in enumerate(xx):
                for j, subval in enumerate(zz):
                    try:
                        yy[j][i] = vv[val][subval]
                    except KeyError:
                        pass

            self.chart.setData(xx, yy, zz)
            self.chart.setLabelY(self.fieldSelector.currentText())
            self.chart.setLabelZ(self.subfieldSelector.currentText())
        elif chart == 'progress':
            items = self.itemsSelector.currentData()
            if items == 'price':
                sql_field = 'sum(payprice)'
                self.chart.setLabel(self.tr("Paid"))
            elif items == 'totalprice':
                sql_field = 'sum(totalpayprice)'
                self.chart.setLabel(self.tr("Total paid"))
            else:
                sql_field = 'count(*)'
                self.chart.setLabel(self.tr("Number of coins"))

            period = self.periodSelector.currentData()
            if items == 'created':
                if period == 'month':
                    sql_filters = ["createdat >= datetime('now', 'start of month', '-11 months')"]
                elif period == 'week':
                    sql_filters = ["createdat > datetime('now', '-11 months')"]
                elif period == 'day':
                    sql_filters = ["createdat > datetime('now', '-1 month')"]
                else:  # year
                    sql_filters = ["1=1"]
            else:
                sql_filters = ["status IN ('owned', 'ordered', 'sale', 'missing', 'duplicate')"]

                if period == 'month':
                    sql_filters.append("paydate >= datetime('now', 'start of month', '-11 months')")
                elif period == 'week':
                    sql_filters.append("paydate > datetime('now', '-11 months')")
                elif period == 'day':
                    sql_filters.append("paydate > datetime('now', '-1 month')")

            if period == 'month':
                date_format = '%m'
            elif period == 'week':
                date_format = '%W'
            elif period == 'day':
                date_format = '%d'
            else:
                date_format = '%Y'

            if filter_:
                sql_filters.append(filter_)

            if items == 'created':
                sql = "SELECT %s, strftime('%s', createdat) FROM coins"\
                      " WHERE %s"\
                      " GROUP BY strftime('%s', createdat) ORDER BY createdat" % (
                          sql_field, date_format, ' AND '.join(sql_filters),
                          date_format)
            else:
                sql = "SELECT %s, strftime('%s', paydate) FROM coins"\
                      " WHERE %s"\
                      " GROUP BY strftime('%s', paydate) ORDER BY paydate" % (
                          sql_field, date_format, ' AND '.join(sql_filters),
                          date_format)
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(1))
                xx.append(val)
                yy.append(count)

            self.chart.setData(xx, yy)
            self.chart.setLabelY(self.periodSelector.currentText())
        else:
            sql = "SELECT count(*), %s FROM coins %s GROUP BY %s" % (
                field, sql_filter, field)
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(1))
                if field == 'status':
                    val = Statuses[val]
                elif field == 'value,unit':
                    val = numberWithFraction(val)[0] + ' ' + str(record.value(2))
                elif ',' in field:
                    val += ' ' + str(record.value(2))
                xx.append(val)
                yy.append(count)

            self.chart.setData(xx, yy)
            self.chart.setLabelY(self.fieldSelector.currentText())

    def fieldChaged(self, _text):
        fieldId = self.fieldSelector.currentData()
        self.statisticsParam['fieldid'] = fieldId

        self.modelChanged()

    def subfieldChaged(self, _text):
        subfieldId = self.fieldSelector.currentData()
        self.statisticsParam['subfieldid'] = subfieldId

        self.modelChanged()

    def chartChaged(self, _text):
        chart = self.chartSelector.currentData()
        self.statisticsParam['chart'] = chart

        self.showConfig(chart)

        self.modelChanged()

    def showConfig(self, chart):
        self.subfieldSelector.setVisible(chart == 'stacked')
        self.subfieldLabel.setVisible(chart == 'stacked')
        self.fieldSelector.setVisible(chart != 'progress' and chart != 'geochart')
        self.fieldLabel.setVisible(chart != 'progress' and chart != 'geochart')
        self.periodSelector.setVisible(chart == 'progress')
        self.periodLabel.setVisible(chart == 'progress')
        self.itemsSelector.setVisible(chart == 'progress')
        self.itemsLabel.setVisible(chart == 'progress')
        self.colorCheck.setVisible(chart != 'stacked' and chart != 'pie' and chart != 'geochart')
        self.regionLabel.setVisible(chart == 'geochart')
        self.regionSelector.setVisible(chart == 'geochart')

    def periodChaged(self, _text):
        period = self.periodSelector.currentData()
        self.statisticsParam['period'] = period

        self.modelChanged()

    def itemsChaged(self, _text):
        items = self.itemsSelector.currentData()
        self.statisticsParam['items'] = items

        self.modelChanged()

    def colorChanged(self, state):
        self.statisticsParam['color'] = state

        self.modelChanged()

    def regionChanged(self, _text):
#        region = self.itemsSelector.currentData()
#        self.statisticsParam['region'] = region

        self.modelChanged()

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget

    def save(self):
        defaultFileName = "%s_%s" % (self.chartSelector.currentText(),
                                     QDateTime.currentDateTime().toString('yyyyMMdd'))

        fileName, selectedFilter = getSaveFileName(
            self, 'export_statistics', defaultFileName,
            OpenNumismat.HOME_PATH, self.chart.filters)
        if fileName:
            self.chart.save(fileName, selectedFilter)
