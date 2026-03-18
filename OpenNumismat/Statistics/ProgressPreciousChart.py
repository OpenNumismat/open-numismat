from datetime import datetime
from dateutil.relativedelta import relativedelta

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QLineSeries,
    QStackedBarSeries,
    QValueAxis,
    QXYLegendMarker,
)
from PySide6.QtCore import Qt, QLocale, QPoint
from PySide6.QtGui import QCursor, QColor, QPen
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Tools.Converters import stringToMoney, normalizeFineness
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartView


class LineSeries(QLineSeries):

    def __init__(self, parent):
        super().__init__(parent)

        self.hovered.connect(self.line_hover)

    def line_hover(self, point, state):
        if state:
            pos = int(point.x() + 0.5)
            value = self.at(pos).y()
            tooltip = f"{self.name()}: {value:.2f}"
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class ProgressPreciousChart(BaseChartView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setData(self, xx, yy):
        metals = list(set().union(*yy))
        self.xx = xx
        self.yy = yy

        series = QStackedBarSeries()
        series.hovered.connect(self.hover)

        barsets = {}

        for i, metal in enumerate(metals):
            lst = [0] * len(yy)
            for j, y in enumerate(yy):
                if metal in y:
                    lst[j] = y[metal]

            setY = QBarSet(metal)
            setY.append(lst)
            if self.use_blaf_palette:
                setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
            barsets[metal] = setY
            series.append(setY)

        self.chart().addSeries(series)

        self.lineseries = []
        for i, metal in enumerate(metals):
            line_series = LineSeries(self)
            line_series.setName(metal)
            pen = QPen(barsets[metal].color())
            pen.setWidth(2)
            line_series.setPen(pen)

            cur_y = 0
            for i, y in enumerate(yy):
                if metal in y:
                    cur_y += y[metal]
                line_series.append(i, cur_y)

            self.lineseries.append(line_series)

            self.chart().addSeries(line_series)

        markers = self.chart().legend().markers()
        for marker in markers:
            if isinstance(marker, QXYLegendMarker):
                marker.setVisible(False)

        axisX = QBarCategoryAxis()
        axisX.append(self.xLabels())
        self.chart().addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        for lineseries in self.lineseries:
            lineseries.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        for lineseries in self.lineseries:
            lineseries.attachAxis(axisY)
        series.attachAxis(axisY)
        axisY.setMin(0)
        axisY.applyNiceNumbers()

    def hover(self, status, index, barset):
        if status:
            y = barset.at(index)
            z = barset.label()

            metal_str = self.tr("Metal")
            locale = QLocale.system()
            weight_str = locale.toString(float(y), 'f', precision=2)
            tooltip = f"{metal_str}: {z}\n{self.label}: {weight_str}"
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


def progressPreciousChart(view):
    metals = (
        ("gold", view.tr("Gold").lower(), "au", "aurum"),
        ("silver", view.tr("Silver").lower(), "ag", "argentum"),
        ("platinum", view.tr("Platinum").lower(), "pt"),
        ("palladium", view.tr("Palladium").lower(), "pd"),
    )

    chart = ProgressPreciousChart(view)
    chart.setLabel(view.tr("Weight"))

    sql_field = "weight,quantity,fineness,material,paydate"

    period = view.periodSelector.currentData()
    if period == 'month':
        date_format = '%m'
        delta = relativedelta(months=1)
    elif period == 'week':
        date_format = '%W'
        delta = relativedelta(weeks=1)
    elif period == 'day':
        date_format = '%d'
        delta = relativedelta(days=1)
    else:
        date_format = '%Y'
        delta = relativedelta(years=1)

    sql_filters = ["status IN ('owned', 'ordered', 'sale', 'missing', 'duplicate', 'replacement')"]

    filter_ = view.model.filter()
    if filter_:
        sql_filters.append(filter_)

    sql_filters.append("material IS NOT NULL")
    sql_filters.append("material <> ''")
    sql_filters.append("paydate IS NOT NULL")
    sql_filters.append("paydate <> ''")
    if period == 'month':
        sql_filters.append("paydate >= datetime('now', 'start of month', '-11 months')")
    elif period == 'week':
        sql_filters.append("paydate > datetime('now', '-11 months')")
    elif period == 'day':
        sql_filters.append("paydate > datetime('now', '-1 month')")
    
    sql = "SELECT %s FROM coins"\
          " WHERE %s"\
          " ORDER BY paydate" % (
              sql_field, ' AND '.join(sql_filters))

    query = QSqlQuery(view.model.database())
    query.exec(sql)
    data = {}
    min_paydate = None
    max_paydate = None
    while query.next():
        record = query.record()

        weight = record.value('weight') or 0
        if isinstance(weight, str):
            weight = stringToMoney(weight)

        quantity = record.value('quantity') or 1

        fineness = record.value('fineness') or 0
        fineness = normalizeFineness(fineness)

        material = record.value('material').lower()
        metal = None
        for metal_titles in metals:
            if material in metal_titles:
                metal = metal_titles[1]
                break
        if not metal:
            continue

        paydate = record.value('paydate')
        paydate = datetime.strptime(paydate, '%Y-%m-%d')
        if not min_paydate:
            min_paydate = paydate
        max_paydate = paydate
        period_item = paydate.strftime(date_format)

        if period_item not in data:
            data[period_item] = {}

        total_weight = weight * fineness * quantity
        if metal in data[period_item]:
            data[period_item][metal] += total_weight
        else:
            data[period_item][metal] = total_weight

    current_date = min_paydate

    normalized_data = {}
    if data:
        while current_date <= max_paydate:
            period_item = current_date.strftime(date_format)
            if period_item in data:
                normalized_data[period_item] = data[period_item]
            else:
                normalized_data[period_item] = {}

            current_date = current_date + delta

    chart.setData(list(normalized_data), list(normalized_data.values()))
    chart.setLabelY(view.periodSelector.currentText())

    return chart
