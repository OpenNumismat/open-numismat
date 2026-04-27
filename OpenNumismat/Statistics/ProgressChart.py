from dateutil import parser
from dateutil.relativedelta import relativedelta

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QLineSeries,
    QStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QCursor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Settings import Settings
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

            total_str = self.tr("Total")
            locale = QLocale.system()
            count_str = locale.toString(int(count))
            tooltip = f"{total_str}: {count_str}"

            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.hideText()


class ProgressChartModel(BaseChartModel):

    def loadData(self, items, period):
        continuous_time = Settings()['continuous_time_chart']

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

        if period == 'month' and items != 'year':
            date_format = '%m'
            delta = relativedelta(months=1)
        elif period == 'week' and items != 'year':
            date_format = '%W'
            delta = relativedelta(weeks=1)
        elif period == 'day' and items != 'year':
            date_format = '%d'
            delta = relativedelta(days=1)
        else:
            date_format = '%Y'
            delta = relativedelta(years=1)

        if self.filter:
            sql_filters.append(self.filter)

        if items == 'createdat':
            sql = "SELECT %s, createdat FROM coins"\
                  " WHERE %s"\
                  " GROUP BY createdat ORDER BY createdat" % (
                      sql_field, ' AND '.join(sql_filters))
        elif items == 'issuedate':
            sql = "SELECT %s, issuedate FROM coins"\
                  " WHERE %s"\
                  " GROUP BY issuedate ORDER BY issuedate" % (
                      sql_field, ' AND '.join(sql_filters))
        elif items == 'year':
            sql = "SELECT %s, year FROM coins"\
                  " WHERE %s"\
                  " GROUP BY year ORDER BY year" % (
                      sql_field, ' AND '.join(sql_filters))
        else:
            sql = "SELECT %s, paydate FROM coins"\
                  " WHERE %s"\
                  " GROUP BY paydate ORDER BY paydate" % (
                      sql_field, ' AND '.join(sql_filters))
        query = QSqlQuery(self.db)
        query.exec(sql)
        xx = {}
        min_date = None
        max_date = None
        while query.next():
            record = query.record()
            count = record.value(0) or 0
            val = str(record.value(1))

            try:
                date = parser.parse(val)
            except parser.ParserError:
                pass
            else:
                if not min_date:
                    min_date = date
                max_date = date
                val = date.strftime(date_format)

            if val in xx:
                xx[val] += count
            else:
                xx[val] = count

        normalized_data = {}
        if continuous_time and min_date and max_date:
            current_date = min_date

            while current_date <= max_date:
                period_item = current_date.strftime(date_format)
                if period_item in xx:
                    normalized_data[period_item] = xx[period_item]
                else:
                    normalized_data[period_item] = 0

                current_date = current_date + delta
        else:
            normalized_data = xx

        self.x_data = list(normalized_data)
        self.y_data = list(normalized_data.values())
