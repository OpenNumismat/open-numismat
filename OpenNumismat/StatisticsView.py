import math
from functools import cmp_to_key

from PySide6.QtCharts import (
    QAreaSeries,
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QDateTimeAxis,
    QHorizontalBarSeries,
    QHorizontalStackedBarSeries,
    QLineSeries,
    QPieSeries,
    QStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import (
    Qt,
    QByteArray,
    QCollator,
    QDate,
    QDateTime,
    QLocale,
    QMargins,
    QPoint,
    QSize,
)
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QImage, QIcon, QCursor, QPainter, QColor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineWidgets import QWebEngineView as QWebView

import OpenNumismat
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Collection.CollectionFields import StatisticsFields
from OpenNumismat.Tools.Gui import getSaveFileName
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Tools.misc import saveImageFilters
from OpenNumismat.Settings import Settings

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

    def setData(self, xx, yy, region):
        data = ','.join(["['%s', %d]" % (x, y) for x, y in zip(xx, yy)])
        header = "['%s', '%s']" % (self.tr("Country"), self.tr("Quantity"))
        data = ','.join((header, data))
        locale = Settings()['locale']
        self.html_data = self.HTML % (locale, MAPS_API_KEY, region, data)
        self.setHtml(self.html_data)

    def filters(self):
        return (QApplication.translate('GeoChartCanvas', "Web page (*.htm *.html)"),
                QApplication.translate('GeoChartCanvas', "PNG image (*.png)"))

    def save(self, fileName, selectedFilter):
        if selectedFilter == self.filters()[1]:
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
            with open(fileName, 'wb') as f:
                f.write(bytes(self.html_data, 'utf-8'))

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(event.position().toPoint())

    def contextMenuEvent(self, _event):
        pass


class BaseChart(QChartView):
    doubleClicked = pyqtSignal(QPoint)
    
    BLAF_PALETTE = (
            '#336699', '#99CCFF', '#999933', '#666699', '#CC9933', '#006666',
            '#3399FF', '#993300', '#CCCC99', '#666666', '#FFCC66', '#6699CC',
            '#663366', '#9999CC', '#CCCCCC', '#669999', '#CCCC66', '#CC6600',
            '#9999FF', '#0066CC', '#99CCCC', '#999999', '#FFCC00', '#009999',
            '#99CC33', '#FF9900', '#999966', '#66CCCC', '#339966', '#CCCC33')

    def __init__(self, parent=None):
        chart = QChart()
        theme = QChart.ChartTheme(Settings()['chart_theme'])
        chart.setTheme(theme)
        chart.legend().hide()
        chart.layout().setContentsMargins(0, 0, 0, 0)
        chart.setBackgroundRoundness(0)
        
        self.label = QApplication.translate('BaseCanvas', "Quantity")
        self.label_y = ''
        self.colors = Settings()['multicolor_chart']
        self.use_blaf_palette = Settings()['use_blaf_palette']
        
        super().__init__(chart, parent)

        self.setRenderHint(QPainter.Antialiasing)

    def setLabel(self, text):
        self.label = text

    def setLabelY(self, text):
        self.label_y = text

    def hover(self, status, index, _barset):
        if status:
            QToolTip.showText(QCursor.pos(), self.tooltip(index))
        else:
            QToolTip.showText(QPoint(), "")

    def tooltip(self, pos):
        x = self.xx[pos]
        y = self.yy[pos]
        return "%s: %s\n%s: %d" % (self.label_y, x, self.label, y)

    def filters(self):
        return saveImageFilters()

    def save(self, fileName, _selectedFilter):
        self.grab().save(fileName)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(event.position().toPoint())


class BarChart(BaseChart):
    
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

        self.chart().addSeries(series)

        axisX = QBarCategoryAxis()
        axisX.append(xx)
        self.chart().addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        axisY.applyNiceNumbers()


class BarHChart(BaseChart):
    
    def setData(self, xx, yy):
        xx.reverse()
        yy.reverse()

        self.xx = xx
        self.yy = yy
        
        if self.colors:
            series = QHorizontalStackedBarSeries()
        else:
            series = QHorizontalBarSeries()
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

        self.chart().addSeries(series)

        axisX = QValueAxis()
        axisX.setTitleText(self.label)
        axisX.setLabelFormat("%d")
        self.chart().addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        axisX.applyNiceNumbers()

        axisY = QBarCategoryAxis()
        axisY.append(xx)
        self.chart().addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)


class PieChart(BaseChart):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.legend = Settings['show_chart_legend']
        if self.legend:
            self.chart().legend().show()
            self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

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

        self.chart().addSeries(series)
        if not self.legend:
            series.setLabelsVisible(True)

    def hover(self, slice_, state):
        if state:
            tooltip = "%s: %s\n%s: %d" % (self.label_y, slice_.label(),
                                          self.label, slice_.value())
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class StackedBarChart(BaseChart):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setLabelZ(self, text):
        self.label_z = text

    def setData(self, xx, yy, zz):
        self.xx = xx
        self.yy = yy
        self.zz = zz
        
        series = QHorizontalStackedBarSeries()
        series.hovered.connect(self.hover)

        for i, (y, z) in enumerate(zip(yy, zz)):
            setY = QBarSet(z)
            setY.append(y)
            if self.use_blaf_palette:
                setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            series.append(setY)

        self.chart().addSeries(series)

        axisX = QValueAxis()
        axisX.setTitleText(self.label)
        axisX.setLabelFormat("%d")
        self.chart().addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        axisX.applyNiceNumbers()

        axisY = QBarCategoryAxis()
        axisY.append(xx)
        self.chart().addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

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

        if self.colors and len(yy) < 500:
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

        self.chart().addSeries(series)

        self.lineseries = QLineSeries(self)
        self.lineseries.setName(self.tr("Trend"))
        self.lineseries.hovered.connect(self.line_hover)
        
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y
            self.lineseries.append(i, cur_y)

        self.chart().addSeries(self.lineseries)

        axisX = QBarCategoryAxis()
        axisX.append(xx)
        self.chart().addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        self.lineseries.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        self.lineseries.attachAxis(axisY)
        series.attachAxis(axisY)
        axisY.setMin(0)
        axisY.applyNiceNumbers()
        
    def line_hover(self, point, state):
        if state:
            pos = int(point.x() + 0.5)
            count = self.lineseries.at(pos).y()
            tooltip = "%s: %d" % (self.tr("Total"), count)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class AreaStatusChart(BaseChart):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setData(self, xx, yy):
        self.xx = xx
        self.yy = yy

        lineseries_bottom = QLineSeries(self)
        lineseries_bottom.append(0, 0)
        lineseries_bottom.append(len(xx)-1, 0)
        
        serieses = []

        lineseries_total = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y[0]
            lineseries_total.append(i, cur_y)

        series = QAreaSeries(lineseries_total, lineseries_bottom)
        series.setName(self.tr("Total"))
        serieses.append(series)

        lineseries_owned = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y[1]
            lineseries_owned.append(i, cur_y)

        series = QAreaSeries(lineseries_owned, lineseries_bottom)
        series.setName(Statuses['owned'])
        serieses.append(series)

        lineseries_sold = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y[2]
            lineseries_sold.append(i, cur_y)

        if cur_y:
            series = QAreaSeries(lineseries_sold, lineseries_bottom)
            series.setName(Statuses['sold'])
            serieses.append(series)

        for i, series in enumerate(serieses):
            if self.use_blaf_palette:
                series.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            series.setOpacity(0.5)
            series.hovered.connect(self.hover)
            self.chart().addSeries(series)
        
        axisX = QBarCategoryAxis()
        axisX.append(xx)
        self.chart().addAxis(axisX, Qt.AlignBottom)
        for series in serieses:
            series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        for series in serieses:
            series.attachAxis(axisY)
        axisY.setMin(0)
        axisY.applyNiceNumbers()

    def hover(self, point, state):
        if state:
            pos = int(point.x() + 0.5)
            total = 0
            owned = 0
            sold = 0
            for i in range(pos+1):
                total += self.yy[i][0]
                owned += self.yy[i][1]
                sold += self.yy[i][2]
            owned -= sold
            tooltip = "%s: %d\n%s: %d" % (self.tr("Total"), total,
                                          Statuses['owned'], owned)
            if sold:
                tooltip += "\n%s: %d" % (Statuses['sold'], sold)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class AreaNiceStatusChart(BaseChart):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def val_to_date(self, val):
        year = int(val[0:4])
        if len(val) >= 7:
            month = int(val[5:7])
        else:
            month = 1
        if len(val) >= 10:
            day = int(val[8:10])
        else:
            day = 1
        date = QDateTime()
        date.setDate(QDate(year, month, day))

        return date

    def setData(self, xx, yy):
        self.xx = list(xx)
        self.yy = yy

        dates = []
        for x in self.xx:
            try:
                self.val_to_date(x)  # check that date is valid
                dates.append(x)  # store only valid dates
            except:
                pass

        lineseries_bottom = QLineSeries(self)
        if dates:
            date = self.val_to_date(dates[0])
            lineseries_bottom.append(float(date.toMSecsSinceEpoch()), 0)

            date = self.val_to_date(dates[-1])
            lineseries_bottom.append(float(date.toMSecsSinceEpoch()), 0)

        serieses = []

        lineseries_total = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y[0]

            try:
                date = self.val_to_date(self.xx[i])
                lineseries_total.append(float(date.toMSecsSinceEpoch()), cur_y)
            except:
                pass

        series = QAreaSeries(lineseries_total, lineseries_bottom)
        series.setName(self.tr("Total"))
        serieses.append(series)

        lineseries_owned = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y[1]

            try:
                date = self.val_to_date(self.xx[i])
                lineseries_owned.append(float(date.toMSecsSinceEpoch()), cur_y)
            except:
                pass

        series = QAreaSeries(lineseries_owned, lineseries_bottom)
        series.setName(Statuses['owned'])
        serieses.append(series)

        lineseries_sold = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(yy):
            cur_y += y[2]

            try:
                date = self.val_to_date(self.xx[i])
                lineseries_sold.append(float(date.toMSecsSinceEpoch()), cur_y)
            except:
                pass

        if cur_y:
            series = QAreaSeries(lineseries_sold, lineseries_bottom)
            series.setName(Statuses['sold'])
            serieses.append(series)

        for i, series in enumerate(serieses):
            if self.use_blaf_palette:
                series.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            series.setOpacity(0.5)
            series.hovered.connect(self.hover)
            self.chart().addSeries(series)

        min_year = self.val_to_date(dates[0]).date().year()
        max_year = self.val_to_date(dates[-1]).date().year()
        ticks = min(max_year - min_year, 12) + 1
        axisX = QDateTimeAxis()
        axisX.setFormat("yyyy")
        axisX.setTickCount(ticks)
        self.chart().addAxis(axisX, Qt.AlignBottom)
        for series in serieses:
            series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        for series in serieses:
            series.attachAxis(axisY)
        axisY.setMin(0)
        axisY.applyNiceNumbers()

    def hover(self, point, state):
        if state:
            pos = int(point.x() + 5 * 24 * 60 * 60 * 1000)
            date = QDateTime()
            date.setMSecsSinceEpoch(pos)
            tooltip = date.toString("yyyy/MM")

            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class AreaSeries(QAreaSeries):
    
    def hover(self, point, state):
        axisX = self.attachedAxes()[0]
        if state:
            pos = int(point.x() + 0.5)
            max_y = 0
            for series in self.chart().series():
                max_y = max(max_y, series.upperSeries().at(pos).y())

            cur_y = self.upperSeries().at(pos).y() - self.lowerSeries().at(pos).y()
            # TODO: Why cur_y may be negative or NaN on long period?
            if math.isnan(cur_y) or cur_y < 0:
                cur_y = 0

            tooltip = "%s %s: %d\n%s: %d" % (self.name(), axisX.at(pos),
                                             cur_y, self.tr("Total"), max_y)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")
    

class AreaChart(BaseChart):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setData(self, xx, zz):
        self.xx = xx
        self.yy = list(xx.values())
        self.zz = zz

        lineseries_bottom = QLineSeries(self)
        lineseries_bottom.append(0, 0)
        lineseries_bottom.append(len(xx)-1, 0)

        lines = {}
        for z in self.zz:
            lineseries = QLineSeries(self)
            lines[z] = lineseries
        
        for z in self.zz:
            n = 0
            for y in self.yy:
                if z in y:
                    n += y[z]
                y[z] = n

        for i, y in enumerate(self.yy):
            cur_y = 0
            for z in self.zz:
                cur_y += y[z]
                lines[z].append(i, cur_y)
        
        serieses = []
        lineseries_prev = lineseries_bottom
        for i, z in enumerate(self.zz):
            series = AreaSeries(lines[z], lineseries_prev)
            if self.use_blaf_palette:
                series.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            lineseries_prev = lines[z]
            series.setName(z)
            series.hovered.connect(series.hover)
            serieses.append(series)

        serieses.reverse()
        for s in serieses:
            self.chart().addSeries(s)
            
        axisX = QBarCategoryAxis()
        axisX.append(xx)
        self.chart().addAxis(axisX, Qt.AlignBottom)
        for s in serieses:
            s.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        for s in serieses:
            s.attachAxis(axisY)
        axisY.setMin(0)
        axisY.applyNiceNumbers()


class AreaNiceSeries(QAreaSeries):

    def hover(self, point, state):
        if state:
            pos = int(point.x() + 5 * 24 * 60 * 60 * 1000)
            date = QDateTime()
            date.setMSecsSinceEpoch(pos)
            max_y = 0
            for series in self.chart().series():
                point = self.getPoint(series.upperSeries(), pos)
                max_y = max(max_y, point.y())

            cur_y = self.getPoint(self.upperSeries(), pos).y() - self.getPoint(self.lowerSeries(), pos).y()
            # TODO: Why cur_y may be negative or NaN on long period?
            if math.isnan(cur_y) or cur_y < 0:
                cur_y = 0

            tooltip = "%s %s: %d\n%s: %d" % (self.name(), date.toString("yyyy/MM"),
                                             cur_y, self.tr("Total"), max_y)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")

    def getPoint(self, series, pos):
        prev_point = series.points()[0]
        for point in series.points():
            if point.x() >= pos:
                break
            prev_point = point

        return prev_point


class AreaNiceChart(BaseChart):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def val_to_date(self, val):
        year = int(val[0:4])
        if len(val) >= 7:
            month = int(val[5:7])
        else:
            month = 1
        if len(val) >= 10:
            day = int(val[8:10])
        else:
            day = 1
        date = QDateTime()
        date.setDate(QDate(year, month, day))

        return date

    def setData(self, xx, zz):
        self.zz = zz

        self.xx = {}
        for x, y in xx.items():
            try:
                self.val_to_date(x)  # check that date is valid
                self.xx[x] = y  # store only valid dates
            except:
                pass

        self.yy = list(self.xx.values())
        dates = list(self.xx)

        lineseries_bottom = QLineSeries(self)
        if dates:
            date = self.val_to_date(dates[0])
            lineseries_bottom.append(float(date.toMSecsSinceEpoch()), 0)

            date = self.val_to_date(dates[-1])
            lineseries_bottom.append(float(date.toMSecsSinceEpoch()), 0)

        lines = {}
        for z in self.zz:
            lines[z] = QLineSeries(self)

        for z in self.zz:
            n = 0
            for y in self.yy:
                if z in y:
                    n += y[z]
                y[z] = n

        for i, y in enumerate(self.yy):
            cur_y = 0
            for z in self.zz:
                cur_y += y[z]

                date = self.val_to_date(dates[i])
                lines[z].append(float(date.toMSecsSinceEpoch()), cur_y)

        serieses = []
        lineseries_prev = lineseries_bottom
        for i, z in enumerate(self.zz):
            series = AreaNiceSeries(lines[z], lineseries_prev)
            if self.use_blaf_palette:
                series.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            lineseries_prev = lines[z]
            series.setName(z)
            series.hovered.connect(series.hover)
            serieses.append(series)

        serieses.reverse()
        for s in serieses:
            self.chart().addSeries(s)

        axisX = QDateTimeAxis()
        axisX.setFormat("yyyy")
        if dates:
            min_year = self.val_to_date(dates[0]).date().year()
            max_year = self.val_to_date(dates[-1]).date().year()
            ticks = min(max_year - min_year, 12) + 1
            axisX.setTickCount(ticks)
        self.chart().addAxis(axisX, Qt.AlignBottom)
        for s in serieses:
            s.attachAxis(axisX)
        self.axisX = axisX

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        for s in serieses:
            s.attachAxis(axisY)
        axisY.setMin(0)
        axisY.applyNiceNumbers()


class StatisticsView(QWidget):
    def __init__(self, statisticsParam, parent=None):
        super().__init__(parent)

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

        self.statisticsParam = statisticsParam

        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins())
        layout.setAlignment(Qt.AlignTop)

        ctrlLayout = QVBoxLayout()
        ctrlLayout.setAlignment(Qt.AlignTop)
        ctrlLayout.setContentsMargins(QMargins(10, 10, 0, 10))
        layout.addLayout(ctrlLayout)

        self.chart = QWidget(self)
        self.scroll = QScrollArea(self)

        self.chartSelector = QComboBox(self)
        self.chartSelector.addItem(self.tr("Bar"), 'bar')
        self.chartSelector.addItem(self.tr("Horizontal bar"), 'barh')
        self.chartSelector.addItem(self.tr("Pie"), 'pie')
        self.chartSelector.addItem(self.tr("Stacked bar"), 'stacked')
        self.chartSelector.addItem(self.tr("Progress"), 'progress')
        self.chartSelector.addItem(self.tr("Area"), 'area')
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
        ctrlLayout.addWidget(self.itemsSelector)

        self.areaLabel = QLabel(self.tr("Items:"))
        ctrlLayout.addWidget(self.areaLabel)
        self.areaSelector = QComboBox(self)
        self.areaSelector.addItem(self.tr("Status changing"), 'status')
        ctrlLayout.addWidget(self.areaSelector)

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
        saveButton.setIcon(QIcon(':/save.png'))
        saveButton.setToolTip(self.tr("Save chart"))
        saveButton.setFixedWidth(25)
        saveButton.clicked.connect(self.save)

        settingsButton = QPushButton()
        settingsButton.setIcon(QIcon(':/cog.png'))
        settingsButton.setToolTip(self.tr("Settings"))
        settingsButton.setFixedWidth(25)
        settingsButton.clicked.connect(self.settings)

        self.zoomInButton = QPushButton()
        self.zoomInButton.setIcon(QIcon(':/zoom_in.png'))
        self.zoomInButton.setToolTip(self.tr("Zoom In (25%)"))
        self.zoomInButton.setFixedWidth(25)
        self.zoomInButton.clicked.connect(self.zoomIn)

        self.zoomOutButton = QPushButton()
        self.zoomOutButton.setIcon(QIcon(':/zoom_out.png'))
        self.zoomOutButton.setToolTip(self.tr("Zoom Out (25%)"))
        self.zoomOutButton.setFixedWidth(25)
        self.zoomOutButton.clicked.connect(self.zoomOut)

        button_layout = QHBoxLayout()
        button_layout.addWidget(saveButton)
        button_layout.addWidget(settingsButton)
        button_layout.addWidget(self.zoomInButton, alignment=Qt.AlignRight)
        button_layout.addWidget(self.zoomOutButton)

        ctrlLayout.addSpacing(1000)
        ctrlLayout.addLayout(button_layout)

        self.setLayout(layout)
        layout.addWidget(self.scroll)

    def setModel(self, model):
        self.model = model

        default_subfieldid = 0
        for field in self.model.fields.userFields:
            if field.name in StatisticsFields:
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

            if field.name in ('issuedate', 'year', 'createdat'):
                self.areaSelector.addItem(field.title, field.name)
            elif field.name == 'paydate':
                self.areaSelector.addItem(self.tr("Pay date"), field.name)
            elif field.name == 'saledate':
                self.areaSelector.addItem(self.tr("Sale date"), field.name)

            if field.name in ('issuedate', 'createdat', 'payprice', 'year', 'totalpayprice'):
                self.itemsSelector.addItem(field.title, field.name)
            elif field.name == 'paydate':
                self.itemsSelector.addItem(self.tr("Pay date"), field.name)

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

        # TODO: Store selected area in separate field
        area = self.statisticsParam['items']
        index = self.areaSelector.findData(area)
        if index >= 0:
            self.areaSelector.setCurrentIndex(index)

        period = self.statisticsParam['period']
        index = self.periodSelector.findData(period)
        if index >= 0:
            self.periodSelector.setCurrentIndex(index)

        self.showConfig(chart)
        self.chartSelector.currentIndexChanged.connect(self.chartChaged)
        self.fieldSelector.currentIndexChanged.connect(self.fieldChaged)
        self.subfieldSelector.currentIndexChanged.connect(self.subfieldChaged)
        self.periodSelector.currentIndexChanged.connect(self.periodChaged)
        self.itemsSelector.currentIndexChanged.connect(self.itemsChaged)
        self.areaSelector.currentIndexChanged.connect(self.areaChaged)
        self.regionSelector.currentIndexChanged.connect(self.regionChanged)

    def modelChanged(self):
        chart = self.chartSelector.currentData()
        if chart == 'geochart':
            self.chart = self.geoChart()
        elif chart == 'barh':
            self.chart = self.barHChart()
        elif chart == 'pie':
            self.chart = self.pieChart()
        elif chart == 'stacked':
            self.chart = self.stackedChart()
        elif chart == 'progress':
            self.chart = self.progressChart()
        elif chart == 'area':
            area = self.areaSelector.currentData()
            if area == 'status':
                self.chart = self.areaStatusChart()
            else:
                self.chart = self.areaChart()
        else:
            self.chart = self.barChart()

        self.scroll.setWidget(self.chart)
        self.chart.doubleClicked.connect(self.zoomInPos)

        self.resizeEvent(None)

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
        self.fieldSelector.setVisible(chart not in ('progress', 'geochart'))
        self.fieldLabel.setVisible(chart not in ('progress', 'geochart'))
        self.periodSelector.setVisible(chart == 'progress')
        self.periodLabel.setVisible(chart == 'progress')
        self.itemsSelector.setVisible(chart == 'progress')
        self.itemsLabel.setVisible(chart == 'progress')
        self.areaSelector.setVisible(chart == 'area')
        self.areaLabel.setVisible(chart == 'area')
        if chart == 'area':
            area = self.areaSelector.currentData()
            self.fieldSelector.setDisabled(area == 'status')
        else:
            self.fieldSelector.setDisabled(False)
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

    def areaChaged(self, _text):
        area = self.areaSelector.currentData()
        self.statisticsParam['items'] = area

        self.fieldSelector.setDisabled(area == 'status')

        self.modelChanged()

    def regionChanged(self, _text):
        # region = self.itemsSelector.currentData()
        # self.statisticsParam['region'] = region

        self.modelChanged()
    
    def fillBarChart(self, chart):
        fieldId = self.fieldSelector.currentData()
        field = self.model.fields.field(fieldId).name
        if field == 'fineness':
            sql_field = "IFNULL(material,''),IFNULL(fineness,'')"
        elif field == 'unit':
            sql_field = "IFNULL(value,''),IFNULL(unit,'')"
        else:
            sql_field = "IFNULL(%s,'')" % field

        filter_ = self.model.filter()
        if filter_:
            sql_filter = "WHERE %s" % filter_
        else:
            sql_filter = ""
        
        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins %s GROUP BY %s" % (
            sql_field, sql_filter, sql_field)
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        zz = {}
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            if field == 'unit':
                val = numberWithFraction(val)[0] + ' ' + str(record.value(2))
            elif field == 'fineness':
                val += ' ' + str(record.value(2))
            zz[val] = count

        if field == 'status':
            sorted_zz = dict(sorted(zz.items(), key=lambda x: Statuses.order(x[0])))
            zz = {}
            for key, val in sorted_zz.items():
                zz[Statuses[key]] = val
        elif field == 'year':
            pass
        else:
            zz = dict(sorted(zz.items(), key=cmp_to_key(self.sortStrings)))

        chart.setData(list(zz), list(zz.values()))
        chart.setLabelY(self.fieldSelector.currentText())

        return chart
    
    def barChart(self):
        chart = BarChart(self)
        self.fillBarChart(chart)
        return chart
    
    def barHChart(self):
        chart = BarHChart(self)
        self.fillBarChart(chart)
        return chart

    def pieChart(self):
        chart = PieChart(self)
        self.fillBarChart(chart)
        return chart

    def stackedChart(self):
        fieldId = self.fieldSelector.currentData()
        field = self.model.fields.field(fieldId).name
        if field == 'fineness':
            sql_field = "IFNULL(material,''),IFNULL(fineness,'')"
        elif field == 'unit':
            sql_field = "IFNULL(value,''),IFNULL(unit,'')"
        else:
            sql_field = "IFNULL(%s,'')" % field

        filter_ = self.model.filter()
        if filter_:
            sql_filter = "WHERE %s" % filter_
        else:
            sql_filter = ""
        
        subfieldId = self.subfieldSelector.currentData()
        subfield = self.model.fields.field(subfieldId).name
        sql = "SELECT count(IFNULL(%s,'')), IFNULL(%s,''), %s FROM coins"\
              " %s GROUP BY %s, IFNULL(%s,'')" % (
                        subfield, subfield, sql_field, sql_filter, sql_field, subfield)
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
            elif field == 'unit':
                val = numberWithFraction(val)[0] + ' ' + str(record.value(3))
            elif field == 'fineness':
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

        if field == 'status':
            xx.reverse()
        elif field == 'year':
            xx = sorted(xx, key=cmp_to_key(self.sortYears), reverse=True)
        else:
            xx = sorted(xx, key=cmp_to_key(self.sortStrings), reverse=True)

        if subfield == 'status':
            pass
        elif subfield == 'year':
            zz = sorted(zz, key=cmp_to_key(self.sortYears), reverse=True)
        else:
            zz = sorted(zz, key=cmp_to_key(self.sortStrings))

        for i, val in enumerate(xx):
            for j, subval in enumerate(zz):
                try:
                    yy[j][i] = vv[val][subval]
                except KeyError:
                    pass

        chart = StackedBarChart(self)
        chart.setData(xx, yy, zz)
        chart.setLabelY(self.fieldSelector.currentText())
        chart.setLabelZ(self.subfieldSelector.currentText())
        
        return chart

    def progressChart(self):
        chart = ProgressChart(self)

        items = self.itemsSelector.currentData()
        if items == 'payprice':
            sql_field = 'sum(payprice)'
            chart.setLabel(self.tr("Total price"))
        elif items == 'totalpayprice':
            sql_field = 'sum(totalpayprice)'
            chart.setLabel(self.tr("Total paid"))
        else:
            sql_field = "sum(iif(quantity!='',quantity,1))"
            chart.setLabel(self.tr("Quantity"))

        period = self.periodSelector.currentData()
        if items == 'createdat':
            if period == 'month':
                sql_filters = ["createdat >= datetime('now', 'start of month', '-11 months')"]
            elif period == 'week':
                sql_filters = ["createdat > datetime('now', '-11 months')"]
            elif period == 'day':
                sql_filters = ["createdat > datetime('now', '-1 month')"]
            else:  # year
                sql_filters = ["1=1"]
        elif items == 'issuedate':
            if period == 'month':
                sql_filters = ["issuedate >= datetime('now', 'start of month', '-11 months')"]
            elif period == 'week':
                sql_filters = ["issuedate > datetime('now', '-11 months')"]
            elif period == 'day':
                sql_filters = ["issuedate > datetime('now', '-1 month')"]
            else:  # year
                sql_filters = ["1=1"]
        elif items == 'year':
            sql_filters = ["1=1"]
        else:
            sql_filters = ["status IN ('owned', 'ordered', 'sale', 'missing', 'duplicate', 'replacement')"]

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

        filter_ = self.model.filter()
        if filter_:
            sql_filters.append(filter_)

        if items == 'createdat':
            sql = "SELECT %s, strftime('%s', createdat) FROM coins"\
                  " WHERE %s"\
                  " GROUP BY strftime('%s', createdat) ORDER BY createdat" % (
                      sql_field, date_format, ' AND '.join(sql_filters),
                      date_format)
        elif items == 'issuedate':
            sql = "SELECT %s, strftime('%s', issuedate) FROM coins"\
                  " WHERE %s"\
                  " GROUP BY strftime('%s', issuedate) ORDER BY issuedate" % (
                      sql_field, date_format, ' AND '.join(sql_filters),
                      date_format)
        elif items == 'year':
            sql = "SELECT %s, year FROM coins"\
                  " WHERE %s"\
                  " GROUP BY year" % (
                      sql_field, ' AND '.join(sql_filters))
        else:
            sql = "SELECT %s, strftime('%s', paydate) FROM coins"\
                  " WHERE %s"\
                  " GROUP BY strftime('%s', paydate) ORDER BY paydate" % (
                      sql_field, date_format, ' AND '.join(sql_filters),
                      date_format)
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        xx = {}
        while query.next():
            record = query.record()
            count = record.value(0) or 0
            val = str(record.value(1))
            xx[val] = count

        if period == 'year':
            years = []
            for year in xx.keys():
                try:
                    years.append(int(year))
                except ValueError:
                    pass

            if len(years) > 2:
                for x in range(int(min(years)), int(max(years))):
                    if str(x) not in xx:
                        xx[str(x)] = 0

            xx = dict(sorted(xx.items()))

        chart.setData(list(xx), list(xx.values()))
        chart.setLabelY(self.periodSelector.currentText())

        return chart

    def areaChart(self):
        nice_years = Settings()['nice_years_chart']
        fieldId = self.fieldSelector.currentData()
        field = self.model.fields.field(fieldId).name
        if field == 'fineness':
            sql_field = "IFNULL(material,''),IFNULL(fineness,'')"
        elif field == 'unit':
            sql_field = "IFNULL(value,''),IFNULL(unit,'')"
        else:
            sql_field = "IFNULL(%s,'')" % field

        area = self.areaSelector.currentData()
        if area == 'paydate':
            sql_filters = ["status IN ('owned', 'ordered', 'sale', 'missing', 'duplicate', 'replacement')"]
        elif area == 'saledate':
            sql_filters = ["status='sold'"]
        else:
            sql_filters = ["1=1"]

        filter_ = self.model.filter()
        if filter_:
            sql_filters.append(filter_)
        
        if area in ('issuedate', 'paydate', 'saledate', 'createdat'):
            if nice_years:
                date_field = "strftime('%%Y-%%m', %s)" % area
            else:
                date_field = "strftime('%%Y', %s)" % area
        else:
            date_field = area
        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s, %s FROM coins"\
              " WHERE %s"\
              " GROUP BY %s, %s" % (
                    date_field, sql_field,
                    ' AND '.join(sql_filters),
                    date_field, sql_field)
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        xx = {}
        zz = []
        while query.next():
            record = query.record()
            count = record.value(0)
            year = str(record.value(1))
            val = str(record.value(2))

            if field == 'status':
                val = Statuses[val]
            elif field == 'unit':
                val = numberWithFraction(val)[0] + ' ' + str(record.value(3))
            elif field == 'fineness':
                val += ' ' + str(record.value(3))

            if val not in zz:
                zz.append(val)

            if year not in xx:
                xx[year] = {}
            xx[year][val] = count

        if not nice_years:
            years = []
            for year in xx.keys():
                try:
                    years.append(int(year))
                except ValueError:
                    pass

            if len(years) > 2:
                for x in range(int(min(years)), int(max(years))):
                    if str(x) not in xx:
                        xx[str(x)] = {}

            xx = dict(sorted(xx.items(), key=cmp_to_key(self.sortYears)))

        if field == 'status':
            zz = sorted(zz, key=cmp_to_key(self.sortStatuses), reverse=True)
        elif field == 'year':
            zz = sorted(zz, key=cmp_to_key(self.sortYears))
        else:
            zz = sorted(zz, key=cmp_to_key(self.sortStrings), reverse=True)

        if nice_years:
            chart = AreaNiceChart(self)
        else:
            chart = AreaChart(self)
        chart.setData(xx, zz)
        chart.setLabelY(self.fieldSelector.currentText())

        return chart

    def areaStatusChart(self):
        nice_years = Settings()['nice_years_chart']

        filter_ = self.model.filter()
        if filter_:
            sql_filter = "WHERE %s" % filter_
        else:
            sql_filter = ""

        if nice_years:
            date_field = "strftime('%Y-%m', createdat)"
        else:
            date_field = "strftime('%Y', createdat)"

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins"\
              " %s"\
              " GROUP BY %s" % (date_field, sql_filter, date_field)
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        xx = {}
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            xx[val] = [count, 0, 0]

        sql_filters = ["status IN ('owned', 'ordered', 'sale', 'sold', 'missing', 'duplicate', 'replacement')"]
        if filter_:
            sql_filters.append(filter_)

        if nice_years:
            date_field = "strftime('%Y-%m', paydate)"
        else:
            date_field = "strftime('%Y', paydate)"

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins"\
              " WHERE %s"\
              " GROUP BY %s" % (date_field, ' AND '.join(sql_filters), date_field)
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            if val in xx:
                xx[val][1] = count
            else:
                xx[val] = [0, count, 0]

        sql_filters = ["status='sold'"]
        if filter_:
            sql_filters.append(filter_)

        if nice_years:
            date_field = "strftime('%Y-%m', saledate)"
        else:
            date_field = "strftime('%Y', saledate)"

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins"\
              " WHERE %s"\
              " GROUP BY %s" % (date_field, ' AND '.join(sql_filters), date_field)
        query = QSqlQuery(self.model.database())
        query.exec_(sql)
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            if val in xx:
                xx[val][2] = count
            else:
                xx[val] = [0, 0, count]

        if nice_years:
            chart = AreaNiceStatusChart(self)
        else:
            keys = list(xx)
            if '' in keys:
                keys.remove('')
            if len(keys) > 2:
                for x in range(int(min(keys)), int(max(keys))):
                    if str(x) not in xx:
                        xx[str(x)] = [0, 0, 0]

            chart = AreaStatusChart(self)

        xx = dict(sorted(xx.items()))
        chart.setData(xx.keys(), list(xx.values()))

        return chart

    def geoChart(self):
        filter_ = self.model.filter()
        if filter_:
            sql_filter = "WHERE %s" % filter_
        else:
            sql_filter = ""

        sql = "SELECT sum(iif(quantity!='',quantity,1)), IFNULL(country,'') FROM coins %s GROUP BY IFNULL(country,'')" % sql_filter
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

        chart = GeoChart(self)
        chart.setData(xx, yy, self.regionSelector.currentData())
        
        return chart

    def save(self):
        defaultFileName = "%s_%s" % (self.chartSelector.currentText(),
                                     QDateTime.currentDateTime().toString('yyyyMMdd'))

        fileName, selectedFilter = getSaveFileName(
            self, 'export_statistics', defaultFileName,
            OpenNumismat.HOME_PATH, self.chart.filters())
        if fileName:
            self.chart.save(fileName, selectedFilter)

    def settings(self):
        dialog = SettingsDialog(self)
        dialog.applyClicked.connect(self.applySettings)
        res = dialog.exec_()
        if res == QDialog.Accepted:
            self.applySettings()

    def applySettings(self):
        self.modelChanged()

    def resizeEvent(self, _e):
        scroll_size = self.scroll.size() - QSize(2, 2)
        chart_size = self.chart.size()

        if scroll_size.height() >= chart_size.height() or \
                scroll_size.width() >= chart_size.width():
            self.chart.resize(scroll_size)
            self.zoomOutButton.setDisabled(True)
            self.zoomInButton.setEnabled(True)

    def zoomInPos(self, point):
        if not self.zoomInButton.isEnabled():
            return

        scroll_size = self.scroll.size() - QSize(2, 2)
        target_size = self.chart.size() * 1.5

        old_pos_h = (self.scroll.horizontalScrollBar().value() + point.x()) * 1.5
        old_pos_v = (self.scroll.verticalScrollBar().value() + point.y()) * 1.5

        if scroll_size.height() * 5 <= target_size.height() or \
                scroll_size.width() * 5 <= target_size.width():
            self.zoomInButton.setDisabled(True)
        self.zoomOutButton.setEnabled(True)

        self.chart.resize(target_size)

        self.scroll.horizontalScrollBar().setValue((old_pos_h - point.x()))
        self.scroll.verticalScrollBar().setValue((old_pos_v - point.y()))

    def zoomIn(self):
        old_size = self.chart.size()
        scroll_size = self.scroll.size() - QSize(2, 2)
        target_size = self.chart.size() * 1.25

        if scroll_size.height() * 5 <= target_size.height() or \
                scroll_size.width() * 5 <= target_size.width():
            self.zoomInButton.setDisabled(True)
        self.zoomOutButton.setEnabled(True)

        self.chart.resize(target_size)

        w = target_size.width() - old_size.width()
        pos = self.scroll.horizontalScrollBar().value()
        self.scroll.horizontalScrollBar().setValue(pos + w // 2)

        h = target_size.height() - old_size.height()
        pos = self.scroll.verticalScrollBar().value()
        self.scroll.verticalScrollBar().setValue(pos + h // 2)

    def zoomOut(self):
        old_size = self.chart.size()
        scroll_size = self.scroll.size() - QSize(2, 2)
        target_size = self.chart.size() / 1.25

        old_pos_h = self.scroll.horizontalScrollBar().value()
        old_pos_v = self.scroll.verticalScrollBar().value()

        if scroll_size.height() >= target_size.height() or \
                scroll_size.width() >= target_size.width():
            self.chart.resize(scroll_size)
            self.zoomOutButton.setDisabled(True)
        else:
            self.chart.resize(target_size)
        self.zoomInButton.setEnabled(True)

        w1 = target_size.width() - scroll_size.width()
        if w1:
            w2 = old_size.width() - scroll_size.width()
            scale = w2 / w1
            self.scroll.horizontalScrollBar().setValue(old_pos_h / scale)

        h1 = target_size.height() - scroll_size.height()
        if h1:
            h2 = old_size.height() - scroll_size.height()
            scale = h2 / h1
            self.scroll.verticalScrollBar().setValue(old_pos_v / scale)

    def sortStrings(self, leftData, rightData):
        if type(leftData) is tuple:
            leftData = leftData[0]
        if type(rightData) is tuple:
            rightData = rightData[0]

        return self.collator.compare(leftData, rightData)

    def sortStatuses(self, leftData, rightData):
        if type(leftData) is tuple:
            leftData = leftData[0]
        if type(rightData) is tuple:
            rightData = rightData[0]

        leftData = Statuses.reverse(leftData)
        rightData = Statuses.reverse(rightData)

        return Statuses.compare(leftData, rightData)

    def sortYears(self, leftData, rightData):
        if type(leftData) is tuple:
            leftData = leftData[0]
        if type(rightData) is tuple:
            rightData = rightData[0]

        try:
            leftData = int(leftData)
            rightData = int(rightData)
        except ValueError:
            leftData = str(leftData)
            rightData = str(rightData)

        if leftData < rightData:
            return -1
        elif leftData > rightData:
            return 1
        else:
            return 0


class SettingsDialog(QDialog):
    applyClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        settings = Settings()

        self.setWindowTitle(self.tr("Chart settings"))

        formLayout = QFormLayout()
        formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.chartThemeSelector = QComboBox(self)
        self.chartThemeSelector.addItem(self.tr("Light"),
                                        QChart.ChartThemeLight.value)
        self.chartThemeSelector.addItem(self.tr("Blue Cerulean"),
                                        QChart.ChartThemeBlueCerulean.value)
        self.chartThemeSelector.addItem(self.tr("Dark"),
                                        QChart.ChartThemeDark.value)
        self.chartThemeSelector.addItem(self.tr("Brown Sand"),
                                        QChart.ChartThemeBrownSand.value)
        self.chartThemeSelector.addItem(self.tr("Blue Ncs"),
                                        QChart.ChartThemeBlueNcs.value)
        self.chartThemeSelector.addItem(self.tr("High Contrast"),
                                        QChart.ChartThemeHighContrast.value)
        self.chartThemeSelector.addItem(self.tr("Blue Icy"),
                                        QChart.ChartThemeBlueIcy.value)
        self.chartThemeSelector.addItem(self.tr("Qt"),
                                        QChart.ChartThemeQt.value)
        index = self.chartThemeSelector.findData(settings['chart_theme'])
        if index >= 0:
            self.chartThemeSelector.setCurrentIndex(index)
        self.chartThemeSelector.setSizePolicy(QSizePolicy.Fixed,
                                              QSizePolicy.Fixed)
        formLayout.addRow(self.tr("Chart theme"), self.chartThemeSelector)

        self.colorCheck = QCheckBox(self.tr("Multicolor"), self)
        self.colorCheck.setChecked(settings['multicolor_chart'])
        formLayout.addRow(self.colorCheck)

        self.useBlafPalette = QCheckBox(
                        self.tr("Use BLAF palette"), self)
        self.useBlafPalette.setChecked(settings['use_blaf_palette'])
        formLayout.addRow(self.useBlafPalette)

        self.legendCheck = QCheckBox(self.tr("Show legend (Pie)"), self)
        self.legendCheck.setChecked(settings['show_chart_legend'])
        formLayout.addRow(self.legendCheck)

        self.legendPosSelector = QComboBox(self)
        self.legendPosSelector.addItem(self.tr("Top"), Qt.AlignTop.value)
        self.legendPosSelector.addItem(self.tr("Right"), Qt.AlignRight.value)
        self.legendPosSelector.addItem(self.tr("Bottom"), Qt.AlignBottom.value)
        self.legendPosSelector.addItem(self.tr("Left"), Qt.AlignLeft.value)
        index = self.legendPosSelector.findData(settings['chart_legend_pos'])
        if index >= 0:
            self.legendPosSelector.setCurrentIndex(index)
        self.legendPosSelector.setSizePolicy(QSizePolicy.Fixed,
                                             QSizePolicy.Fixed)
        formLayout.addRow(self.tr("Legend position"), self.legendPosSelector)

        self.niceYearsCheck = QCheckBox(self.tr("Nice years (Area)"), self)
        self.niceYearsCheck.setChecked(settings['nice_years_chart'])
        formLayout.addRow(self.niceYearsCheck)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        applyButton = buttonBox.addButton(QDialogButtonBox.Apply)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)
        applyButton.clicked.connect(self.apply)

        layout = QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        self.save_settings()
        self.accept()

    def apply(self):
        self.save_settings()
        self.applyClicked.emit()

    def save_settings(self):
        settings = Settings()

        settings['use_blaf_palette'] = self.useBlafPalette.isChecked()
        settings['chart_theme'] = self.chartThemeSelector.currentData()
        settings['multicolor_chart'] = self.colorCheck.isChecked()
        settings['show_chart_legend'] = self.legendCheck.isChecked()
        settings['chart_legend_pos'] = self.legendPosSelector.currentData()
        settings['nice_years_chart'] = self.niceYearsCheck.isChecked()

        settings.save()
