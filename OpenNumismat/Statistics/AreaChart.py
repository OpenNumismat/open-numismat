import math
from datetime import date
from functools import cmp_to_key

from PySide6.QtCharts import (
    QAreaSeries,
    QBarCategoryAxis,
    QDateTimeAxis,
    QLineSeries,
    QValueAxis,
)
from PySide6.QtCore import (
    Qt,
    QDate,
    QDateTime,
    QPoint,
)
from PySide6.QtGui import QCursor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartModel, BaseChartView


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
    

class AreaChart(BaseChartView):
    
    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def updateChart(self):
        lineseries_bottom = QLineSeries(self)
        lineseries_bottom.append(0, 0)
        lineseries_bottom.append(len(self.model.x_data) - 1, 0)

        lines = {}
        for z in self.model.z_data:
            lineseries = QLineSeries(self)
            lines[z] = lineseries
        
        for z in self.model.z_data:
            n = 0
            for y in self.model.y_data:
                if z in y:
                    n += y[z]
                y[z] = n

        for i, y in enumerate(self.model.y_data):
            cur_y = 0
            for z in self.model.z_data:
                cur_y += y[z]
                lines[z].append(i, cur_y)
        
        serieses = []
        lineseries_prev = lineseries_bottom
        for i, z in enumerate(self.model.z_data):
            series = AreaSeries(lines[z], lineseries_prev)
            if self.use_blaf_palette:
                series.setColor(self.blafColor(i))
            lineseries_prev = lines[z]
            series.setName(z)
            series.hovered.connect(series.hover)
            serieses.append(series)

        serieses.reverse()
        for s in serieses:
            self.chart().addSeries(s)
            
        axisX = QBarCategoryAxis()
        axisX.append(self.model.x_data)
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


class AreaNiceChart(BaseChartView):

    def __init__(self, model, parent=None):
        super().__init__(model, parent)
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

    def updateChart(self):
        dates = list(self.model.x_data)

        lineseries_bottom = QLineSeries(self)
        if dates:
            date = self.val_to_date(dates[0])
            lineseries_bottom.append(float(date.toMSecsSinceEpoch()), 0)

            date = self.val_to_date(dates[-1])
            lineseries_bottom.append(float(date.toMSecsSinceEpoch()), 0)

        lines = {}
        for z in self.model.z_data:
            lines[z] = QLineSeries(self)

        for z in self.model.z_data:
            n = 0
            for y in self.model.y_data:
                if z in y:
                    n += y[z]
                y[z] = n

        for i, y in enumerate(self.model.y_data):
            cur_y = 0
            for z in self.model.z_data:
                cur_y += y[z]

                date = self.val_to_date(dates[i])
                lines[z].append(float(date.toMSecsSinceEpoch()), cur_y)

        serieses = []
        lineseries_prev = lineseries_bottom
        for i, z in enumerate(self.model.z_data):
            series = AreaNiceSeries(lines[z], lineseries_prev)
            if self.use_blaf_palette:
                series.setColor(self.blafColor(i))
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


class AreaChartModel(BaseChartModel):

    def __init__(self, db, filter_, parent=None):
        super().__init__(db, filter_, parent)

        self.z_data = []
        self.nice_years = Settings()['nice_years_chart']

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

    def loadData(self, field, area):
        if field == 'fineness':
            sql_field = "IFNULL(material,''),IFNULL(fineness,'')"
        elif field == 'unit':
            sql_field = "IFNULL(value,''),IFNULL(unit,'')"
        else:
            sql_field = "IFNULL(%s,'')" % field

        if area == 'paydate':
            sql_filters = ["status IN ('owned', 'ordered', 'sale', 'missing', 'duplicate', 'replacement')"]
        elif area == 'saledate':
            sql_filters = ["status='sold'"]
        else:
            sql_filters = ["1=1"]
    
        if self.filter:
            sql_filters.append(self.filter)

        if area in ('issuedate', 'paydate', 'saledate', 'createdat'):
            if self.nice_years:
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
        query = QSqlQuery(self.db)
        query.exec(sql)
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

        if not self.nice_years:
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

        if self.nice_years:
            self.x_data = {}
            for x, y in xx.items():
                try:
                    self.val_to_date(x)  # check that date is valid
                    self.x_data[x] = y  # store only valid dates
                except:
                    pass

            self.y_data = list(self.x_data.values())
        else:
            self.x_data = xx
            self.y_data = list(xx.values())

        self.z_data = zz
