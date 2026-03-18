from PySide6.QtCharts import QPieSeries, QPieSlice
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartView


class PieSlice(QPieSlice):

    def __init__(self, label, value, parent=None):
        self.tooltip_label = label
        if Settings()['tree_counter']:
            label = f"{label} [{value}]"
        super().__init__(label, value, parent)

    def tooltipLabel(self):
        return self.tooltip_label


class PieChart(BaseChartView):
    
    def __init__(self, model, parent=None):
        super().__init__(model, parent)

        self.legend = Settings()['show_chart_legend']
        if self.legend:
            self.chart().legend().show()
            self.chart().legend().setAlignment(Qt.Alignment(Settings()['chart_legend_pos']))

    def updateChart(self):
        series = QPieSeries()
        series.hovered.connect(self.hover)

        if self.use_blaf_palette:
            for i, (x, y) in enumerate(zip(self.model.x_data, self.model.y_data)):
                _slice = PieSlice(x, y)
                _slice.setBrush(self.blafColor(i))
                series.append(_slice)
        else:
            for x, y in zip(self.model.x_data, self.model.y_data):
                _slice = PieSlice(x, y)
                series.append(_slice)

        self.chart().addSeries(series)
        if not self.legend:
            series.setLabelsVisible(True)
        self.chart().setTitle(self.label_y)

    def hover(self, slice_, state):
        if state:
            tooltip = "%s: %s\n%s: %d" % (self.label_y, slice_.tooltipLabel(),
                                          self.label, slice_.value())
            QToolTip.showText(QCursor.pos(), tooltip)
        else:
            QToolTip.showText(QPoint(), "")
