from datetime import date

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
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartModel, BaseChartView


class AreaStatusChart(BaseChartView):
    
    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def updateChart(self):
        lineseries_bottom = QLineSeries(self)
        lineseries_bottom.append(0, 0)
        lineseries_bottom.append(len(self.model.x_data) - 1, 0)
        
        serieses = []

        lineseries_total = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(self.model.y_data):
            cur_y += y[0]
            lineseries_total.append(i, cur_y)

        series = QAreaSeries(lineseries_total, lineseries_bottom)
        series.setName(self.tr("Total"))
        serieses.append(series)

        lineseries_owned = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(self.model.y_data):
            cur_y += y[1]
            lineseries_owned.append(i, cur_y)

        series = QAreaSeries(lineseries_owned, lineseries_bottom)
        series.setName(Statuses['owned'])
        serieses.append(series)

        lineseries_sold = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(self.model.y_data):
            cur_y += y[2]
            lineseries_sold.append(i, cur_y)

        if cur_y:
            series = QAreaSeries(lineseries_sold, lineseries_bottom)
            series.setName(Statuses['sold'])
            serieses.append(series)

        for i, series in enumerate(serieses):
            if self.use_blaf_palette:
                series.setColor(self.blafColor(i))
            series.setOpacity(0.5)
            series.hovered.connect(self.hover)
            self.chart().addSeries(series)
        
        axisX = QBarCategoryAxis()
        axisX.append(self.model.x_data)
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
                total += self.model.y_data[i][0]
                owned += self.model.y_data[i][1]
                sold += self.model.y_data[i][2]
            owned -= sold
            tooltip = "%s: %d\n%s: %d" % (self.tr("Total"), total,
                                          Statuses['owned'], owned)
            if sold:
                tooltip += "\n%s: %d" % (Statuses['sold'], sold)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class AreaNiceStatusChart(BaseChartView):

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
        dates = []
        for x in self.model.x_data:
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
        for i, y in enumerate(self.model.y_data):
            cur_y += y[0]

            try:
                date = self.val_to_date(self.model.x_data[i])
                lineseries_total.append(float(date.toMSecsSinceEpoch()), cur_y)
            except:
                pass

        series = QAreaSeries(lineseries_total, lineseries_bottom)
        series.setName(self.tr("Total"))
        serieses.append(series)

        lineseries_owned = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(self.model.y_data):
            cur_y += y[1]

            try:
                date = self.val_to_date(self.model.x_data[i])
                lineseries_owned.append(float(date.toMSecsSinceEpoch()), cur_y)
            except:
                pass

        series = QAreaSeries(lineseries_owned, lineseries_bottom)
        series.setName(Statuses['owned'])
        serieses.append(series)

        lineseries_sold = QLineSeries(self)
        cur_y = 0
        for i, y in enumerate(self.model.y_data):
            cur_y += y[2]

            try:
                date = self.val_to_date(self.model.x_data[i])
                lineseries_sold.append(float(date.toMSecsSinceEpoch()), cur_y)
            except:
                pass

        if cur_y:
            series = QAreaSeries(lineseries_sold, lineseries_bottom)
            series.setName(Statuses['sold'])
            serieses.append(series)

        for i, series in enumerate(serieses):
            if self.use_blaf_palette:
                series.setColor(self.blafColor(i))
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


class AreaStatusChartModel(BaseChartModel):

    def __init__(self, db, filter_, parent=None):
        super().__init__(db, filter_, parent)

        self.nice_years = Settings()['nice_years_chart']

    def loadData(self):
        if self.filter:
            sql_filter = "WHERE %s" % self.filter
        else:
            sql_filter = ""

        if self.nice_years:
            date_field = "strftime('%Y-%m', createdat)"
        else:
            date_field = "strftime('%Y', createdat)"

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins"\
              " %s"\
              " GROUP BY %s" % (date_field, sql_filter, date_field)
        query = QSqlQuery(self.db)
        query.exec(sql)
        xx = {}
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            xx[val] = [count, 0, 0]

        sql_filters = ["status IN ('owned', 'ordered', 'sale', 'sold', 'missing', 'duplicate', 'replacement')"]
        if self.filter:
            sql_filters.append(self.filter)

        if self.nice_years:
            date_field = "strftime('%Y-%m', paydate)"
        else:
            date_field = "strftime('%Y', paydate)"

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins"\
              " WHERE %s"\
              " GROUP BY %s" % (date_field, ' AND '.join(sql_filters), date_field)
        query = QSqlQuery(self.db)
        query.exec(sql)
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            if val in xx:
                xx[val][1] = count
            else:
                xx[val] = [0, count, 0]

        sql_filters = ["status='sold'"]
        if self.filter:
            sql_filters.append(self.filter)

        if self.nice_years:
            date_field = "strftime('%Y-%m', saledate)"
        else:
            date_field = "strftime('%Y', saledate)"

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins"\
              " WHERE %s"\
              " GROUP BY %s" % (date_field, ' AND '.join(sql_filters), date_field)
        query = QSqlQuery(self.db)
        query.exec(sql)
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            if val in xx:
                xx[val][2] = count
            else:
                xx[val] = [0, 0, count]

        if not self.nice_years:
            keys = list(xx)
            if '' in keys:
                keys.remove('')
            if len(keys) > 2:
                for x in range(int(min(keys)), int(max(keys))):
                    if str(x) not in xx:
                        xx[str(x)] = [0, 0, 0]

        xx = dict(sorted(xx.items()))

        self.x_data = list(xx.keys())
        self.y_data = list(xx.values())
