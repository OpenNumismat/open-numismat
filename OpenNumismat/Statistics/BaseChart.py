from functools import cmp_to_key

from PySide6.QtCharts import QChart, QChartView
from PySide6.QtCore import QCollator, QLocale, QObject, QPoint
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QColor, QCursor, QPainter
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QApplication, QToolTip

from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Tools.misc import saveImageFilters
from OpenNumismat.Settings import Settings


class BaseChartView(QChartView):
    doubleClicked = pyqtSignal(QPoint)
    
    BLAF_PALETTE = (
            '#336699', '#99CCFF', '#999933', '#666699', '#CC9933', '#006666',
            '#3399FF', '#993300', '#CCCC99', '#666666', '#FFCC66', '#6699CC',
            '#663366', '#9999CC', '#CCCCCC', '#669999', '#CCCC66', '#CC6600',
            '#9999FF', '#0066CC', '#99CCCC', '#999999', '#FFCC00', '#009999',
            '#99CC33', '#FF9900', '#999966', '#66CCCC', '#339966', '#CCCC33')

    def __init__(self, model, parent=None):
        self.model = model

        chart = QChart()
        theme = QChart.ChartTheme(Settings()['chart_theme'])
        chart.setTheme(theme)
        chart.legend().hide()
        chart.layout().setContentsMargins(0, 0, 0, 0)
        chart.setBackgroundRoundness(0)
        
        self.label = QApplication.translate('BaseCanvas', "Quantity")
        self.label_y = ''
        self.colors = Settings()['multicolor_chart']
        self.use_blaf_palette = Settings()['use_blaf_palette']
        
        super().__init__(chart, parent)

        self.setRenderHint(QPainter.Antialiasing)

    def updateChart(self):
        pass

    def setLabel(self, text):
        self.label = text

    def setLabelY(self, text):
        self.label_y = text

    def xLabels(self):
        if Settings()['tree_counter']:
            labels = []
            for x, y in zip(self.model.x_data, self.model.y_data):
                labels.append(f"{x} [{y}]")
            return labels
        else:
            return self.model.x_data

    def hover(self, status, index, _barset):
        if status:
            QToolTip.showText(QCursor.pos(), self.tooltip(index))
        else:
            QToolTip.showText(QPoint(), "")

    def tooltip(self, pos):
        x = self.model.x_data[pos]
        y = self.model.y_data[pos]
        return "%s: %s\n%s: %d" % (self.label_y, x, self.label, y)

    def filters(self):
        return saveImageFilters()

    def save(self, fileName, _selectedFilter):
        self.grab().save(fileName)

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(event.position().toPoint())

    def blafColor(self, index):
        blaf_index = index % len(self.BLAF_PALETTE)
        return QColor(self.BLAF_PALETTE[blaf_index])


class BaseChartModel(QObject):

    def __init__(self, db, filter_, parent=None):
        super().__init__(parent)
        self.db = db
        self.filter = filter_
        self.raw_data = []
        self.x_data = []
        self.y_data = []

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

    def sortStrings(self, leftData, rightData):
        if type(leftData) is tuple:
            leftData = leftData[0]
        if type(rightData) is tuple:
            rightData = rightData[0]

        return self.collator.compare(leftData, rightData)

    def sortStatuses(self, leftData, rightData):
        if type(leftData) is tuple:
            leftData = leftData[0]
        if type(rightData) is tuple:
            rightData = rightData[0]

        leftData = Statuses.reverse(leftData)
        rightData = Statuses.reverse(rightData)

        return Statuses.compare(leftData, rightData)

    def sortYears(self, leftData, rightData):
        if type(leftData) is tuple:
            leftData = leftData[0]
        if type(rightData) is tuple:
            rightData = rightData[0]

        try:
            leftData = int(leftData)
            rightData = int(rightData)
        except ValueError:
            leftData = str(leftData)
            rightData = str(rightData)

        if leftData < rightData:
            return -1
        elif leftData > rightData:
            return 1
        else:
            return 0

    def loadData(self, field):
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

        sql = "SELECT sum(iif(quantity!='',quantity,1)), %s FROM coins %s GROUP BY %s" % (
            sql_field, sql_filter, sql_field)
        query = QSqlQuery(self.db)
        query.exec(sql)
        zz = {}
        while query.next():
            record = query.record()
            count = record.value(0)
            val = str(record.value(1))
            if field == 'unit':
                val = numberWithFraction(val)[0] + ' ' + str(record.value(2))
            elif field == 'fineness':
                val += ' ' + str(record.value(2))
            zz[val] = count

        if field == 'status':
            sorted_zz = dict(sorted(zz.items(), key=lambda x: Statuses.order(x[0])))
            zz = {}
            for key, val in sorted_zz.items():
                zz[Statuses[key]] = val
        elif field == 'year':
            pass
        else:
            zz = dict(sorted(zz.items(), key=cmp_to_key(self.sortStrings)))

        self.x_data = list(zz)
        self.y_data = list(zz.values())
