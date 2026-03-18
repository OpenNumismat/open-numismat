from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QHorizontalBarSeries,
    QHorizontalStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from OpenNumismat.Statistics.BaseChart import BaseChartView


class BarHChart(BaseChartView):
    
    def updateChart(self, xx, yy):
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
        axisY.setTitleText(self.label_y)
        axisY.append(self.xLabels())
        self.chart().addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)


def barHChart(view):
    chart = BarHChart(view)
    view.fillBarChart(chart)
    return chart
