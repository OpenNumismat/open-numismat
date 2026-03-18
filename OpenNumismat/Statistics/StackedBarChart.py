from functools import cmp_to_key

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QHorizontalStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QColor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartView


class StackedBarChart(BaseChartView):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setLabelZ(self, text):
        self.label_z = text

    def xLabels(self):
        if Settings()['tree_counter']:
            labels = []
            for i, x in enumerate(self.xx):
                s = sum([yy[i] for yy in self.yy])
                labels.append(f"{x} [{s}]")
            return labels
        else:
            return self.xx

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
        axisY.setTitleText(self.label_y)
        axisY.append(self.xLabels())
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


def stackedBarChart(view):
    fieldId = view.fieldSelector.currentData()
    field = view.model.fields.field(fieldId).name
    if field == 'fineness':
        sql_field = "IFNULL(material,''),IFNULL(fineness,'')"
    elif field == 'unit':
        sql_field = "IFNULL(value,''),IFNULL(unit,'')"
    else:
        sql_field = "IFNULL(%s,'')" % field

    filter_ = view.model.filter()
    if filter_:
        sql_filter = "WHERE %s" % filter_
    else:
        sql_filter = ""
    
    subfieldId = view.subfieldSelector.currentData()
    subfield = view.model.fields.field(subfieldId).name
    sql = "SELECT count(IFNULL(%s,'')), IFNULL(%s,''), %s FROM coins"\
          " %s GROUP BY %s, IFNULL(%s,'')" % (
                    subfield, subfield, sql_field, sql_filter, sql_field, subfield)
    query = QSqlQuery(view.model.database())
    query.exec(sql)
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
        xx = sorted(xx, key=cmp_to_key(view.sortYears), reverse=True)
    else:
        xx = sorted(xx, key=cmp_to_key(view.sortStrings), reverse=True)

    if subfield == 'status':
        pass
    elif subfield == 'year':
        zz = sorted(zz, key=cmp_to_key(view.sortYears), reverse=True)
    else:
        zz = sorted(zz, key=cmp_to_key(view.sortStrings))

    for i, val in enumerate(xx):
        for j, subval in enumerate(zz):
            try:
                yy[j][i] = vv[val][subval]
            except KeyError:
                pass

    chart = StackedBarChart(view)
    chart.setData(xx, yy, zz)
    chart.setLabelY(view.fieldSelector.currentText())
    chart.setLabelZ(view.subfieldSelector.currentText())
    
    return chart
