from textwrap import wrap

statisticsAvailable = True

try:
    import numpy
    import matplotlib
    matplotlib.use('Qt5Agg')

    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.ticker import MaxNLocator
    import matplotlib.pyplot as plt
    from OpenNumismat import PRJ_PATH
    plt.style.use(PRJ_PATH + '/opennumismat.mplstyle')
    # plt.style.use('seaborn-paper')
except ImportError:
    print('matplotlib or nympy module missed. Statistics not available')
    statisticsAvailable = False

    class FigureCanvas:
        pass

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import *

from OpenNumismat.Collection.CollectionFields import Statuses


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
    def setData(self, xx, yy):
        self.axes.cla()

        x = range(len(yy))
        self.axes.bar(x, yy)
        self.axes.set_xticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_xticklabels(keys)

        self.axes.set_ylabel(self.tr("Number of coins"))
        ya = self.axes.get_yaxis()
        ya.set_major_locator(MaxNLocator(integer=True))

        self.draw()


class BarHCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.axes.cla()

        xx = xx[::-1]  # xx.reverse()
        yy = yy[::-1]  # yy.reverse()

        x = range(len(yy))
        self.axes.barh(x, yy)
        self.axes.set_yticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_yticklabels(keys)

        self.axes.set_xlabel(self.tr("Number of coins"))
        xa = self.axes.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        self.draw()


class PieCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.axes.cla()

        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.pie(yy, labels=keys)
        self.axes.axis('equal')

        self.draw()


class StackedBarCanvas(BaseCanvas):
    def setData(self, xx, yy, zz):
        self.axes.cla()

        x = range(len(xx))

        lines = []
        prev_y = [0 * len(xx)]
        for y in yy:
            bars = self.axes.barh(x, y, left=prev_y)
            prev_y = numpy.add(prev_y, y)
            lines.append(bars[0])

        self.axes.set_yticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_yticklabels(keys)

        self.axes.set_xlabel(self.tr("Number of coins"))
        xa = self.axes.get_xaxis()
        xa.set_major_locator(MaxNLocator(integer=True))

        self.axes.legend(lines, zz, frameon=True)

        self.draw()


class ProgressCanvas(BaseCanvas):
    def setData(self, xx, yy):
        self.axes.cla()

        x = range(len(yy))
        self.axes.bar(x, yy)
        self.axes.plot(x, numpy.cumsum(yy), color='red')

        self.axes.set_xticks(x)
        keys = ['\n'.join(wrap(l, 17)) for l in xx]
        self.axes.set_xticklabels(keys)

        self.axes.set_ylabel(self.tr("Number of coins"))
        ya = self.axes.get_yaxis()
        ya.set_major_locator(MaxNLocator(integer=True))

        self.draw()


class StatisticsView(QWidget):
    def __init__(self, statisticsParam, parent=None):
        super().__init__(parent)

        self.statisticsParam = statisticsParam

        layout = QVBoxLayout(self)

        self.imageLayout = QVBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        self.chart = QWidget(self)
        self.imageLayout.addWidget(self.chart)

        ctrlLayout = QHBoxLayout()
        ctrlLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(ctrlLayout)
        widget.setSizePolicy(QSizePolicy.Preferred,
                             QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.chartSelector = QComboBox(self)
        self.chartSelector.addItem(self.tr("bar"), 'bar')
        self.chartSelector.addItem(self.tr("horizontal bar"), 'barh')
        self.chartSelector.addItem(self.tr("pie"), 'pie')
        self.chartSelector.addItem(self.tr("stacked bar"), 'stacked')
        self.chartSelector.addItem(self.tr("progress"), 'progress')
        ctrlLayout.addWidget(self.chartSelector)

        self.fieldSelector = QComboBox(self)
        ctrlLayout.addWidget(self.fieldSelector)

        self.subfieldSelector = QComboBox(self)
        ctrlLayout.addWidget(self.subfieldSelector)

        self.periodSelector = QComboBox(self)
        ctrlLayout.addWidget(self.periodSelector)
        self.periodSelector.addItem(self.tr("year"), 'year')
        self.periodSelector.addItem(self.tr("month"), 'month')
        self.periodSelector.addItem(self.tr("week"), 'week')
        self.periodSelector.addItem(self.tr("day"), 'day')

        self.setLayout(layout)

    def setModel(self, model):
        self.model = model

        default_subfieldid = 0
        for field in self.model.fields.userFields:
            if field.name in ('region', 'country', 'year', 'period', 'ruler',
                              'mint', 'type', 'series', 'status', 'material',
                              'grade', 'saller', 'payplace', 'buyer',
                              'saleplace', 'storage'):
                self.fieldSelector.addItem(field.title, field.id)
                self.subfieldSelector.addItem(field.title, field.id)
                if field.name == 'status':
                    default_subfieldid = field.id

        fieldid = self.statisticsParam.params()['fieldid']
        index = self.fieldSelector.findData(fieldid)
        if index >= 0:
            self.fieldSelector.setCurrentIndex(index)

        subfieldid = self.statisticsParam.params()['subfieldid']
        index = self.subfieldSelector.findData(subfieldid)
        if index >= 0:
            self.subfieldSelector.setCurrentIndex(index)
        elif default_subfieldid:
            index = self.subfieldSelector.findData(default_subfieldid)
            self.subfieldSelector.setCurrentIndex(index)

        chart = self.statisticsParam.params()['chart']
        index = self.chartSelector.findData(chart)
        if index >= 0:
            self.chartSelector.setCurrentIndex(index)

        self.chartSelector.currentIndexChanged.connect(self.chartChaged)
        self.fieldSelector.setVisible(chart != 'progress')
        self.fieldSelector.currentIndexChanged.connect(self.fieldChaged)
        self.subfieldSelector.setVisible(chart == 'stacked')
        self.subfieldSelector.currentIndexChanged.connect(self.subfieldChaged)
        self.periodSelector.setVisible(chart == 'progress')
        self.periodSelector.currentIndexChanged.connect(self.periodChaged)

    def clear(self):
        pass

    def modelChanged(self):
        self.imageLayout.removeWidget(self.chart)
        chart = self.chartSelector.currentData()
        if chart == 'barh':
            self.chart = BarHCanvas(self)
        elif chart == 'pie':
            self.chart = PieCanvas(self)
        elif chart == 'stacked':
            self.chart = StackedBarCanvas(self)
        elif chart == 'progress':
            self.chart = ProgressCanvas(self)
        else:
            self.chart = BarCanvas(self)
        self.imageLayout.addWidget(self.chart)

        fieldId = self.fieldSelector.currentData()
        field = self.model.fields.field(fieldId).name
        filter_ = self.model.filter()
        if filter_:
            sql_filter = "WHERE %s" % filter_
        else:
            sql_filter = ""

        if chart == 'stacked':
            subfieldId = self.subfieldSelector.currentData()
            subfield = self.model.fields.field(subfieldId).name
            sql = "SELECT count(%s), %s, %s FROM coins %s GROUP BY %s, %s" % (
                subfield, field, subfield, sql_filter, field, subfield)
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            zz = []
            vv = {}
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(1))
                if field == 'status':
                    val = Statuses[val]
                subval = str(record.value(2))
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

            xx = xx[::-1]
            for i, val in enumerate(xx):
                for j, subval in enumerate(zz):
                    try:
                        yy[j][i] = vv[val][subval]
                    except KeyError:
                        pass

            self.chart.setData(xx, yy, zz)
        elif chart == 'progress':
            period = self.periodSelector.currentData()
            if filter_:
                sql_filter = "%s AND" % filter_
            else:
                sql_filter = ""
            if period == 'month':
                sql = "SELECT count(*), strftime('%%m', paydate) FROM coins"\
                      " WHERE %s status IN ('owned', 'ordered', 'sold', 'sale')"\
                      " AND paydate > datetime('now', '-11 month')"\
                      " GROUP BY strftime('%%m', paydate) ORDER BY paydate" % sql_filter
            elif period == 'week':
                sql = "SELECT count(*), strftime('%%W', paydate) FROM coins"\
                      " WHERE %s status IN ('owned', 'ordered', 'sold', 'sale')"\
                      " AND paydate > datetime('now', '-11 month')"\
                      " GROUP BY strftime('%%W', paydate) ORDER BY paydate" % sql_filter
            elif period == 'day':
                sql = "SELECT count(*), strftime('%%d', paydate) FROM coins"\
                      " WHERE %s status IN ('owned', 'ordered', 'sold', 'sale')"\
                      " AND paydate > datetime('now', '-1 month')"\
                      " GROUP BY strftime('%%d', paydate) ORDER BY paydate" % sql_filter
            else:
                sql = "SELECT count(*), strftime('%%Y', paydate) FROM coins"\
                      " WHERE %s status IN ('owned', 'ordered', 'sold', 'sale')"\
                      " GROUP BY strftime('%%Y', paydate)" % sql_filter
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(1))
                xx.append(val)
                yy.append(count)

            self.chart.setData(xx, yy)
        else:
            sql = "SELECT count(%s), %s FROM coins %s GROUP BY %s" % (
                field, field, sql_filter, field)
            query = QSqlQuery(self.model.database())
            query.exec_(sql)
            xx = []
            yy = []
            while query.next():
                record = query.record()
                count = record.value(0)
                val = str(record.value(1))
                if field == 'status':
                    val = Statuses[val]
                xx.append(val)
                yy.append(count)

            self.chart.setData(xx, yy)

    def fieldChaged(self, _text):
        fieldId = self.fieldSelector.currentData()
        self.statisticsParam.params()['fieldid'] = fieldId
        self.statisticsParam.save()

        self.modelChanged()

    def subfieldChaged(self, _text):
        subfieldId = self.fieldSelector.currentData()
        self.statisticsParam.params()['subfieldid'] = subfieldId
        self.statisticsParam.save()

        self.modelChanged()

    def chartChaged(self, _text):
        chart = self.chartSelector.currentData()
        self.statisticsParam.params()['chart'] = chart
        self.statisticsParam.save()

        self.subfieldSelector.setVisible(chart == 'stacked')
        self.fieldSelector.setVisible(chart != 'progress')
        self.periodSelector.setVisible(chart == 'progress')

        self.modelChanged()

    def periodChaged(self, _text):
        self.modelChanged()

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget
