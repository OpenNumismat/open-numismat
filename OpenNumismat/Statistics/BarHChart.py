from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QHorizontalBarSeries,
    QHorizontalStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from OpenNumismat.Statistics.BaseChart import BaseChartModel, BaseChartView


class BarHChart(BaseChartView):
    
    def updateChart(self):
        if self.colors:
            series = QHorizontalStackedBarSeries()
        else:
            series = QHorizontalBarSeries()
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


class BarHChartModel(BaseChartModel):

    def loadData(self, field):
        super().loadData(field)

        self.x_data.reverse()
        self.y_data.reverse()
