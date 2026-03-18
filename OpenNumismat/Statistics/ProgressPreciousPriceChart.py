# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
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
from PySide6.QtGui import QCursor, QColor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Tools.Converters import stringToMoney, normalizeFineness
from OpenNumismat.Tools.misc import metalPrice
from OpenNumismat.Tools.CachedPoolManager import CachedPoolManager
from OpenNumismat.Tools.CursorDecorators import waitCursorDecorator
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartView


class ProgressPreciousPriceChart(BaseChartView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setData(self, xx, yy, zz):
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

        self.lineseries = QLineSeries(self)
        self.lineseries.setName(self.tr("Trend"))
        self.lineseries.hovered.connect(self.line_hover)

        for i, z in enumerate(zz):
            self.lineseries.append(i, z)

        self.chart().addSeries(self.lineseries)

        markers = self.chart().legend().markers()
        for marker in markers:
            if isinstance(marker, QXYLegendMarker):
                marker.setVisible(False)

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

    def hover(self, status, index, barset):
        if status:
            y = barset.at(index)
            z = barset.label()

            metal_str = self.tr("Metal")
            locale = QLocale.system()
            price_str = locale.toString(float(y), 'f', precision=2)
            tooltip = f"{metal_str}: {z}\n{self.label}: {price_str}"
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")

    def line_hover(self, point, state):
        if state:
            pos = int(point.x() + 0.5)
            count = self.lineseries.at(pos).y()
            total_str = self.tr("Total")
            locale = QLocale.system()
            price_str = locale.toString(float(count), 'f', precision=2)
            tooltip = f"{total_str}: {price_str}"
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


@waitCursorDecorator
def progressPreciousPriceChart(view):
    metals = (
        ("gold", view.tr("Gold").lower(), "au", "aurum"),
        ("silver", view.tr("Silver").lower(), "ag", "argentum"),
        ("platinum", view.tr("Platinum").lower(), "pt"),
        ("palladium", view.tr("Palladium").lower(), "pd"),
    )
    currency_symbols = {
        'USD': "$",
        'EUR': "€",
        'GBP': "£",
        'RUB': "₽",
        'PLN': "zł",
    }

    dbnomicsCurrency = Settings()['dbnomics_currency']

    if dbnomicsCurrency in currency_symbols:
        symbol = currency_symbols[dbnomicsCurrency]
    else:
        symbol = dbnomicsCurrency

    title = view.tr("Price")
    chart = ProgressPreciousPriceChart(view)
    chart.setLabel(f"{title}, {symbol}")

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
                metal = metal_titles[0]
                break
        if not metal:
            continue

        paydate_raw = record.value('paydate')
        paydate = datetime.strptime(paydate_raw, '%Y-%m-%d')

        if period == 'month':
            paydate_start = date(paydate.year, paydate.month, 1)
        elif period == 'week':
            paydate_start = paydate - timedelta(days=paydate.weekday())
        elif period == 'day':
            paydate_start = paydate
        else:
            paydate_start = date(paydate.year, 1, 1)
        period_item = paydate_start.strftime('%Y-%m-%d')

        if not min_paydate:
            min_paydate = paydate_start
        max_paydate = paydate_start

        if period_item not in data:
            data[period_item] = {}

        total_weight = weight * fineness * quantity

        if metal in data[period_item]:
            data[period_item][metal] += total_weight
        else:
            data[period_item][metal] = total_weight

    current_date = min_paydate

    normalized_data = {}
    normalized_linear_data = {}
    if data:
        http = CachedPoolManager(chart)

        total_weight = {'gold': 0, 'silver': 0, 'platinum': 0, 'palladium': 0}

        while current_date <= max_paydate:
            period_item = current_date.strftime('%Y-%m-%d')
            normalized_period_item = current_date.strftime(date_format)

            total_price = 0
            for metal, weight in total_weight.items():
                if weight > 0:
                    price = metalPrice(http, metal, dbnomicsCurrency, period_item)
                    if price:
                        total_price += weight * price
            normalized_linear_data[normalized_period_item] = total_price

            if period_item in data:
                item_data = {}
                for metal, weight in data[period_item].items():
                    price = metalPrice(http, metal, dbnomicsCurrency, period_item)
                    if price:
                        metal_title = view.tr(metal.capitalize())
                        item_data[metal_title] = weight * price
                    total_weight[metal] += weight
                normalized_data[normalized_period_item] = item_data

                normalized_linear_data[normalized_period_item] += sum(item_data.values())
            else:
                normalized_data[normalized_period_item] = {}

            current_date = current_date + delta

        http.close()

    chart.setData(list(normalized_data), list(normalized_data.values()),
                  list(normalized_linear_data.values()))
    chart.setLabelY(view.periodSelector.currentText())

    return chart
