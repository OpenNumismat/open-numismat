from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QLineSeries,
    QStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Statistics.BaseChart import BaseChartModel, BaseChartView


class ProgressChart(BaseChartView):
    
    def updateChart(self):
        if self.colors:
            series = QStackedBarSeries()
        else:
            series = QBarSeries()
        series.hovered.connect(self.hover)

        if self.colors and len(self.model.y_data) < 500:
            for i, y in enumerate(self.model.y_data):
                lst = [0] * len(self.model.y_data)
                lst[i] = y
                setY = QBarSet(self.label_y)
                setY.append(lst)
                if self.use_blaf_palette:
                    setY.setColor(self.blafColor(i))
                series.append(setY)
        else:
            setY = QBarSet(self.label_y)
            setY.append(self.model.y_data)
            series.append(setY)

        self.chart().addSeries(series)

        self.lineseries = QLineSeries(self)
        self.lineseries.setName(self.tr("Trend"))
        self.lineseries.hovered.connect(self.line_hover)
        
        cur_y = 0
        for i, y in enumerate(self.model.y_data):
            cur_y += y
            self.lineseries.append(i, cur_y)

        self.chart().addSeries(self.lineseries)

        axisX = QBarCategoryAxis()
        axisX.append(self.xLabels())
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


class ProgressChartModel(BaseChartModel):

    def loadData(self, items, period):
        if items == 'payprice':
            sql_field = 'sum(payprice)'
        elif items == 'totalpayprice':
            sql_field = 'sum(totalpayprice)'
        else:
            sql_field = "sum(iif(quantity!='',quantity,1))"

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

        if self.filter:
            sql_filters.append(self.filter)

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
        query = QSqlQuery(self.db)
        query.exec(sql)
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

        self.x_data = list(xx)
        self.y_data = list(xx.values())
