from textwrap import wrap

from PyQt5.QtCore import Qt, QPoint, QMargins, QSize, QDateTime, QUrl, QByteArray
from PyQt5.QtGui import QImage
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Gui import createIcon, getSaveFileName, ProgressDialog
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings

statisticsAvailable = True

try:
    import numpy
    import matplotlib
    matplotlib.use('Qt5Agg')

    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator
    import matplotlib.pyplot as plt
    from OpenNumismat import PRJ_PATH
    plt.style.use(PRJ_PATH + '/opennumismat.mplstyle')
    # plt.style.use('seaborn-paper')
except ImportError:
    print('matplotlib or nympy module missed. Statistics not available')
    statisticsAvailable = False

    class FigureCanvas:
        pass
except ValueError:
    print('matplotlib is old version. Statistics not available')
    statisticsAvailable = False

    class FigureCanvas:
        pass

importedQtWebKit = True
try:
    from PyQt5.QtWebKitWidgets import QWebView
except ImportError:
    print('PyQt5.QtWebKitWidgets module missed. GeoChart not available')
    importedQtWebKit = False

    class QWebView:
        pass


class GeoChartCanvas(QWebView):
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
        'mapsApiKey': 'AIzaSyCtPThA7-xGhB54LbcUYlpgOO25ccYegMY'
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

    def __init__(self, parent=None):
        super().__init__(parent)

    def setData(self, xx, yy, region):
        data = ','.join(["['%s', %d]" % (x, y) for x, y in zip(xx, yy)])
        header = "['%s', '%s']" % (self.tr("Country"), self.tr("Number of coins"))
        data = ','.join((header, data))
        locale = Settings()['locale']
        self.html_data = self.HTML % (locale, region, data)
        self.setHtml(self.html_data, QUrl.fromLocalFile(OpenNumismat.PRJ_PATH))

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


class BaseCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.mpl_connect("motion_notify_event", self.hover)

        self.label = QApplication.translate('BaseCanvas', "Number of coins")

        self.colors = None
        self.multicolors = (
            '#336699', '#99CCFF', '#999933', '#666699', '#CC9933', '#006666',
            '#3399FF', '#993300', '#CCCC99', '#666666', '#FFCC66', '#6699CC',
            '#663366', '#9999CC', '#CCCCCC', '#669999', '#CCCC66', '#CC6600',
            '#9999FF', '#0066CC', '#99CCCC', '#999999', '#FFCC00', '#009999',
            '#99CC33', '#FF9900', '#999966', '#66CCCC', '#339966', '#CCCC33')

    def setMulticolor(self, multicolor=False):
        if multicolor:
            self.colors = self.multicolors
        else:
            self.colors = None

    def setLabel(self, text):
        self.label = text

    def setLabelY(self, text):
        self.label_y = text

    def hover(self, event):
        if not event.inaxes:
            QToolTip.showText(QPoint(), "")
            return

        for pos, figure in enumerate(self.figures):
            if figure.contains(event)[0]:
                point = QPoint(event.x, self.parent().height() - event.y)
                QToolTip.showText(self.parent().mapToGlobal(point), self.tooltip(pos))
                return

        QToolTip.showText(QPoint(), "")

    def tooltip(self, pos):
        x = self.xx[pos]
        y = self.yy[pos]
        return "%s: %s\n%s: %d" % (self.label_y, x, self.label, y)

    filters = (QApplication.translate('BaseCanvas', "PNG image (*.png)"),
               QApplication.translate('BaseCanvas', "PDF file (*.pdf)"),
               QApplication.translate('BaseCanvas', "SVG image (*.svg)"),
               QApplication.translate('BaseCanvas', "PostScript (*.ps)"),
               QApplication.translate('BaseCanvas', "Encapsulated PostScript (*.eps)"))

    def save(self, fileName, selectedFilter):
        # TODO: Matplotlib 2.1.0 needs file name in latin-1 for PS and EPS
        if selectedFilter in self.filters[3:5]:
            fileName = fileName.encode("latin-1", "ignore")
        self.fig.savefig(fileName)


class BarCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy

        self.axes.cla()

        x = range(len(yy))
        self.figures = self.axes.bar(x, yy, color=self.colors)
        self.axes.set_xticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_xticklabels(keys)

        self.axes.set_ylabel(self.label)
        ya = self.axes.get_yaxis()
        ya.set_major_locator(MaxNLocator(integer=True))

        self.draw()


class BarHCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.axes.cla()

        xx = xx[::-1]  # xx.reverse()
        yy = yy[::-1]  # yy.reverse()

        self.xx = xx
        self.yy = yy

        x = range(len(yy))
        self.figures = self.axes.barh(x, yy, color=self.colors)
        self.axes.set_yticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_yticklabels(keys)

        self.axes.set_xlabel(self.label)
        xa = self.axes.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        self.draw()


class PieCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy

        self.axes.cla()

        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.figures = self.axes.pie(yy, labels=keys, colors=self.multicolors)[0]
        self.axes.axis('equal')

        self.draw()


class StackedBarCanvas(BaseCanvas):

    def setLabelZ(self, text):
        self.label_z = text

    @waitCursorDecorator
    def setData(self, xx, yy, zz):
        self.xx = xx
        self.yy = yy
        self.zz = zz

        self.axes.cla()

        x = range(len(xx))

        self.figures = []
        lines = []
        prev_y = [0 * len(xx)]
        progressDlg = ProgressDialog(self.tr("Building chart"),
                                self.tr("Cancel"), len(yy), self)
        progressDlg.setMinimumDuration(2000)
        for i, y in enumerate(yy):
            progressDlg.step()
            if progressDlg.wasCanceled():
                return

            color = self.multicolors[i % len(self.multicolors)]
            bars = self.axes.barh(x, y, left=prev_y, color=color)
            for bar in bars:
                self.figures.append(bar)
            prev_y = numpy.add(prev_y, y)
            lines.append(bars[0])

        progressDlg.setLabelText(self.tr("Drawing chart"))

        self.axes.set_yticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_yticklabels(keys)

        self.axes.set_xlabel(self.label)
        xa = self.axes.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        self.axes.legend(lines, zz, frameon=True)

        self.draw()

        progressDlg.reset()

    def tooltip(self, pos):
        x = self.xx[pos % len(self.xx)]
        y = self.yy[pos // len(self.xx)][pos % len(self.xx)]
        z = self.zz[pos // len(self.xx)]
        s = sum([yy[pos % len(self.xx)] for yy in self.yy])
        return "%s: %s\n%s: %s\n%s: %d/%d" % (self.label_y, x, self.label_z, z,
                                              self.label, y, s)


class ProgressCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy

        self.axes.cla()

        x = range(len(yy))
        self.figures = self.axes.bar(x, yy, color=self.colors)
        self.axes.plot(x, numpy.cumsum(yy), color='red')

        self.axes.set_xticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_xticklabels(keys)

        self.axes.set_ylabel(self.label)
        ya = self.axes.get_yaxis()
        ya.set_major_locator(MaxNLocator(integer=True))

        self.draw()


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
        if importedQtWebKit:
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
        self.regionSelector.addItem(self.tr("All"), 'null')
        self.regionSelector.addItem(self.tr("Europe"), "'150'")
        self.regionSelector.addItem(self.tr("Africa"), "'002'")
        self.regionSelector.addItem(self.tr("Americas"), "'019'")
        self.regionSelector.addItem(self.tr("Asia"), "'142'")
        self.regionSelector.addItem(self.tr("Oceania"), "'009'")
        ctrlLayout.addWidget(self.regionSelector)

        saveButton = QPushButton()
        icon = createIcon("save.png")
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

    def clear(self):
        pass

    def modelChanged(self):
        self.chartLayout.removeWidget(self.chart)
        chart = self.chartSelector.currentData()
        if chart == 'geochart':
            self.chart = GeoChartCanvas(self)
        elif chart == 'barh':
            self.chart = BarHCanvas(self)
        elif chart == 'pie':
            self.chart = PieCanvas(self)
        elif chart == 'stacked':
            self.chart = StackedBarCanvas(self)
        elif chart == 'progress':
            self.chart = ProgressCanvas(self)
        else:
            self.chart = BarCanvas(self)
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
            elif items == 'count':
                sql_field = 'count(*)'
                self.chart.setLabel(self.tr("Number of coins"))
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
                sql_filters = ["status IN ('owned', 'ordered', 'sale', 'missing')"]

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
