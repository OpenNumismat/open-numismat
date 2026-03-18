from functools import cmp_to_key

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QHorizontalStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartModel, BaseChartView


class StackedBarChart(BaseChartView):
    
    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self.chart().legend().show()
        self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def setLabelZ(self, text):
        self.label_z = text

    def xLabels(self):
        if Settings()['tree_counter']:
            labels = []
            for i, x in enumerate(self.model.x_data):
                s = sum([yy[i] for yy in self.model.y_data])
                labels.append(f"{x} [{s}]")
            return labels
        else:
            return self.model.x_data

    def updateChart(self):
        series = QHorizontalStackedBarSeries()
        series.hovered.connect(self.hover)

        for i, (y, z) in enumerate(zip(self.model.y_data, self.model.z_data)):
            setY = QBarSet(z)
            setY.append(y)
            if self.use_blaf_palette:
                setY.setColor(self.blafColor(i))
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
            x = self.model.x_data[index]
            y = barset.at(index)
            z = barset.label()
            s = sum([yy[index] for yy in self.model.y_data])
            tooltip = "%s: %s\n%s: %s\n%s: %d/%d" % (self.label_y, x, self.label_z, z,
                                                     self.label, y, s)
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")


class StackedBarChartModel(BaseChartModel):

    def __init__(self, db, filter_, parent=None):
        super().__init__(db, filter_, parent)

        self.z_data = []

    def loadData(self, field, subfield):
        if field == 'fineness':
            sql_field = "IFNULL(material,''),IFNULL(fineness,'')"
        elif field == 'unit':
            sql_field = "IFNULL(value,''),IFNULL(unit,'')"
        else:
            sql_field = "IFNULL(%s,'')" % field

        if self.filter:
            sql_filter = "WHERE %s" % self.filter
        else:
            sql_filter = ""

        sql = "SELECT count(IFNULL(%s,'')), IFNULL(%s,''), %s FROM coins"\
              " %s GROUP BY %s, IFNULL(%s,'')" % (
                        subfield, subfield, sql_field, sql_filter, sql_field, subfield)
        query = QSqlQuery(self.db)
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

        self.x_data = xx
        self.y_data = yy
        self.z_data = zz
