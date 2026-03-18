from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from OpenNumismat.Statistics.BaseChart import BaseChartView


class BarChart(BaseChartView):
    
    def updateChart(self):
        if self.colors:
            series = QStackedBarSeries()
        else:
            series = QBarSeries()
        series.hovered.connect(self.hover)

        if self.colors:
            for i, y in enumerate(self.model.y_data):
                lst = [0] * len(self.model.y_data)
                lst[i] = y
                setY = QBarSet(self.label_y)
                setY.append(lst)
                if self.use_blaf_palette:
                    setY.setColor(QColor(self.BLAF_PALETTE[i % len(self.BLAF_PALETTE)]))
                series.append(setY)
        else:
            setY = QBarSet(self.label_y)
            setY.append(self.model.y_data)
            series.append(setY)

        self.chart().addSeries(series)

        axisX = QBarCategoryAxis()
        axisX.setTitleText(self.label_y)
        axisX.append(self.xLabels())
        self.chart().addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText(self.label)
        axisY.setLabelFormat("%d")
        self.chart().addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        axisY.applyNiceNumbers()
