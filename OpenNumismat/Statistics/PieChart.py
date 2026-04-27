from PySide6.QtCharts import QPieSeries, QPieSlice
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QToolTip

from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartView


class PieSlice(QPieSlice):

    def __init__(self, label, value, parent=None):
        self.tooltip_label = label
        super().__init__(label, value, parent)

    def tooltipLabel(self):
        return self.tooltip_label


class PieChart(BaseChartView):
    
    def __init__(self, model, parent=None):
        super().__init__(model, parent)

        settings = Settings()
        self.tree_counter = settings['tree_counter']
        self.legend = settings['show_chart_legend']
        if self.legend:
            self.chart().legend().show()
            self.chart().legend().setAlignment(Qt.Alignment(settings['chart_legend_pos']))

    def updateChart(self):
        series = QPieSeries()
        series.hovered.connect(self.hover)

        for i, (x, y) in enumerate(zip(self.model.x_data, self.model.y_data)):
            _slice = PieSlice(x, y)
            if self.tree_counter:
                _slice.setLabel(f"{x} [{y}]")
            if self.use_blaf_palette:
                _slice.setBrush(self.blafColor(i))
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
            QToolTip.hideText()
