from collections import Counter
from textwrap import wrap

import matplotlib
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
plt.style.use('seaborn-whitegrid')
# plt.style.use('seaborn-paper')

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from OpenNumismat.Settings import Settings


class BaseCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class BarCanvas(BaseCanvas):
    def setData(self, data):
        self.axes.cla()

        xx = range(len(data.values()))
        self.axes.bar(xx, data.values())
        self.axes.set_xticks(xx)
        keys = ['\n'.join(wrap(l, 20)) for l in data.keys()]
        self.axes.set_xticklabels(keys)

        self.axes.set_ylabel(self.tr("Number of coins"))
        ya = self.axes.get_yaxis()
        ya.set_major_locator(MaxNLocator(integer=True))

        self.draw()


class StatisticsView(QWidget):
    def __init__(self, parent=None):
        super(StatisticsView, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.imageLayout = QVBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        self.bc = BarCanvas(self)
        self.imageLayout.addWidget(self.bc)

        ctrlLayout = QHBoxLayout()
        ctrlLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(ctrlLayout)
        widget.setSizePolicy(QSizePolicy.Preferred,
                             QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.fieldSelector = QComboBox(self)
        self.fieldSelector.currentIndexChanged.connect(self.fieldChaged)
        ctrlLayout.addWidget(self.fieldSelector)

        self.setLayout(layout)

    def setModel(self, model):
        self.model = model

        for field in self.model.fields.userFields:
            if field.name in ('region', 'country', 'year', 'period', 'ruler',
                              'mint', 'type', 'series', 'status', 'material',
                              'grade', 'saller', 'payplace', 'buyer',
                              'saleplace', 'storage'):
                self.fieldSelector.addItem(field.title, field.name)

    def clear(self):
        pass

    def modelChanged(self):
        cnt = Counter()
        field = self.fieldSelector.currentData()
        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            value = str(record.value(field))
            cnt[value] += 1

        self.bc.setData(cnt)

    def fieldChaged(self, _text):
        self.modelChanged()

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget
