# -*- coding: utf-8 -*-
from PySide6.QtCharts import QChart
from PySide6.QtCore import (
    Qt,
    QCollator,
    QDateTime,
    QLocale,
    QMargins,
    QSize,
)
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

import OpenNumismat
from OpenNumismat.Collection.CollectionFields import StatisticsFields
from OpenNumismat.Tools.Gui import getSaveFileName
from OpenNumismat.Settings import Settings
from OpenNumismat.Statistics.BaseChart import BaseChartModel
from OpenNumismat.Statistics.GeoChart import GeoChart, GeoChartModel
from OpenNumismat.Statistics.BarChart import BarChart
from OpenNumismat.Statistics.BarHChart import BarHChart, BarHChartModel
from OpenNumismat.Statistics.PieChart import PieChart
from OpenNumismat.Statistics.StackedBarChart import StackedBarChart, StackedBarChartModel
from OpenNumismat.Statistics.AreaChart import AreaChart, AreaChartModel, AreaNiceChart
from OpenNumismat.Statistics.AreaStatusChart import AreaNiceStatusChart, AreaStatusChart, AreaStatusChartModel
from OpenNumismat.Statistics.ProgressChart import ProgressChart, ProgressChartModel
from OpenNumismat.Statistics.ProgressPreciousChart import ProgressPreciousChart, ProgressPreciousChartModel
from OpenNumismat.Statistics.ProgressPreciousPriceChart import ProgressPreciousPriceChart, ProgressPreciousPriceChartModel


class StatisticsView(QWidget):

    def __init__(self, statisticsParam, parent=None):
        super().__init__(parent)

        locale = Settings()['locale']
        self.collator = QCollator(QLocale(locale))
        self.collator.setNumericMode(True)

        self.statisticsParam = statisticsParam

        layout = QHBoxLayout()
        layout.setContentsMargins(QMargins())
        layout.setAlignment(Qt.AlignTop)

        ctrlLayout = QVBoxLayout()
        ctrlLayout.setAlignment(Qt.AlignTop)
        ctrlLayout.setContentsMargins(QMargins(10, 10, 0, 10))
        layout.addLayout(ctrlLayout)

        self.chart = QWidget(self)
        self.scroll = QScrollArea(self)

        self.chartSelector = QComboBox(self)
        self.chartSelector.addItem(self.tr("Bar"), 'bar')
        self.chartSelector.addItem(self.tr("Horizontal bar"), 'barh')
        self.chartSelector.addItem(self.tr("Pie"), 'pie')
        self.chartSelector.addItem(self.tr("Stacked bar"), 'stacked')
        self.chartSelector.addItem(self.tr("Progress"), 'progress')
        self.chartSelector.addItem(self.tr("Area"), 'area')
        self.chartSelector.addItem(self.tr("GeoChart"), 'geochart')
        ctrlLayout.addWidget(QLabel(self.tr("Chart:")))
        ctrlLayout.addWidget(self.chartSelector)

        self.fieldLabel = QLabel(self.tr("Field:"))
        ctrlLayout.addWidget(self.fieldLabel)
        self.fieldSelector = QComboBox(self)
        ctrlLayout.addWidget(self.fieldSelector)

        self.subfieldLabel = QLabel(self.tr("Additional field:"))
        ctrlLayout.addWidget(self.subfieldLabel)
        self.subfieldSelector = QComboBox(self)
        ctrlLayout.addWidget(self.subfieldSelector)

        self.periodLabel = QLabel(self.tr("Sum per:"))
        ctrlLayout.addWidget(self.periodLabel)
        self.periodSelector = QComboBox(self)
        self.periodSelector.addItem(self.tr("Year"), 'year')
        self.periodSelector.addItem(self.tr("Month"), 'month')
        self.periodSelector.addItem(self.tr("Week"), 'week')
        self.periodSelector.addItem(self.tr("Day"), 'day')
        ctrlLayout.addWidget(self.periodSelector)

        self.itemsLabel = QLabel(self.tr("Items:"))
        ctrlLayout.addWidget(self.itemsLabel)
        self.itemsSelector = QComboBox(self)
        ctrlLayout.addWidget(self.itemsSelector)

        self.areaLabel = QLabel(self.tr("Items:"))
        ctrlLayout.addWidget(self.areaLabel)
        self.areaSelector = QComboBox(self)
        self.areaSelector.addItem(self.tr("Status changing"), 'status')
        ctrlLayout.addWidget(self.areaSelector)

        self.regionLabel = QLabel(self.tr("Region:"))
        ctrlLayout.addWidget(self.regionLabel)
        self.regionSelector = QComboBox(self)
        self.regionSelector.addItem(self.tr("All"), "'world'")
        self.regionSelector.addItem(self.tr("Europe"), "'150'")
        self.regionSelector.addItem(self.tr("Africa"), "'002'")
        self.regionSelector.addItem(self.tr("Americas"), "'019'")
        self.regionSelector.addItem(self.tr("Asia"), "'142'")
        self.regionSelector.addItem(self.tr("Oceania"), "'009'")
        ctrlLayout.addWidget(self.regionSelector)

        saveButton = QPushButton()
        saveButton.setIcon(QIcon(':/save.png'))
        saveButton.setToolTip(self.tr("Save chart"))
        saveButton.setFixedWidth(25)
        saveButton.clicked.connect(self.save)

        settingsButton = QPushButton()
        settingsButton.setIcon(QIcon(':/cog.png'))
        settingsButton.setToolTip(self.tr("Settings"))
        settingsButton.setFixedWidth(25)
        settingsButton.clicked.connect(self.settings)

        self.zoomInButton = QPushButton()
        self.zoomInButton.setIcon(QIcon(':/zoom_in.png'))
        self.zoomInButton.setToolTip(self.tr("Zoom In (25%)"))
        self.zoomInButton.setFixedWidth(25)
        self.zoomInButton.clicked.connect(self.zoomIn)

        self.zoomOutButton = QPushButton()
        self.zoomOutButton.setIcon(QIcon(':/zoom_out.png'))
        self.zoomOutButton.setToolTip(self.tr("Zoom Out (25%)"))
        self.zoomOutButton.setFixedWidth(25)
        self.zoomOutButton.clicked.connect(self.zoomOut)

        button_layout = QHBoxLayout()
        button_layout.addWidget(saveButton)
        button_layout.addWidget(settingsButton)
        button_layout.addWidget(self.zoomInButton, alignment=Qt.AlignRight)
        button_layout.addWidget(self.zoomOutButton)

        ctrlLayout.addSpacing(1000)
        ctrlLayout.addLayout(button_layout)

        self.setLayout(layout)
        layout.addWidget(self.scroll)

    def setModel(self, model):
        self.model = model

        dbnomicsEnabled = Settings()['dbnomics_enabled']

        default_subfieldid = 0
        for field in self.model.fields.userFields:
            if field.name in StatisticsFields:
                if field.name == 'fineness':
                    title = self.model.fields.material.title + '+' + field.title
                    self.fieldSelector.addItem(title, field.id)
                elif field.name == 'unit':
                    title = self.model.fields.value.title + '+' + field.title
                    self.fieldSelector.addItem(title, field.id)
                else:
                    self.fieldSelector.addItem(field.title, field.id)
                    self.subfieldSelector.addItem(field.title, field.id)
                if field.name == 'status':
                    default_subfieldid = field.id

            if field.name in ('issuedate', 'year', 'createdat'):
                self.areaSelector.addItem(field.title, field.name)
            elif field.name == 'paydate':
                self.areaSelector.addItem(self.tr("Pay date"), field.name)
            elif field.name == 'saledate':
                self.areaSelector.addItem(self.tr("Sale date"), field.name)

            if field.name in ('issuedate', 'createdat', 'payprice', 'year', 'totalpayprice'):
                self.itemsSelector.addItem(field.title, field.name)
            elif field.name == 'paydate':
                self.itemsSelector.addItem(self.tr("Pay date"), field.name)
            elif field.name == 'weight':
                self.itemsSelector.addItem(self.tr("Precious weight"), field.name)
            elif dbnomicsEnabled and field.name == 'fineness':
                self.itemsSelector.addItem(self.tr("Precious price"), field.name)

        # TODO: Store field name instead field ID
        fieldid = self.statisticsParam['fieldid']
        index = self.fieldSelector.findData(fieldid)
        if index >= 0:
            self.fieldSelector.setCurrentIndex(index)

        subfieldid = self.statisticsParam['subfieldid']
        index = self.subfieldSelector.findData(subfieldid)
        if index >= 0:
            self.subfieldSelector.setCurrentIndex(index)
        elif default_subfieldid:
            index = self.subfieldSelector.findData(default_subfieldid)
            self.subfieldSelector.setCurrentIndex(index)

        chart = self.statisticsParam['chart']
        index = self.chartSelector.findData(chart)
        if index >= 0:
            self.chartSelector.setCurrentIndex(index)

        items = self.statisticsParam['items']
        index = self.itemsSelector.findData(items)
        if index >= 0:
            self.itemsSelector.setCurrentIndex(index)

        # TODO: Store selected area in separate field
        area = self.statisticsParam['items']
        index = self.areaSelector.findData(area)
        if index >= 0:
            self.areaSelector.setCurrentIndex(index)

        period = self.statisticsParam['period']
        index = self.periodSelector.findData(period)
        if index >= 0:
            self.periodSelector.setCurrentIndex(index)

        self.showConfig(chart)
        self.chartSelector.currentIndexChanged.connect(self.chartChaged)
        self.fieldSelector.currentIndexChanged.connect(self.fieldChaged)
        self.subfieldSelector.currentIndexChanged.connect(self.subfieldChaged)
        self.periodSelector.currentIndexChanged.connect(self.periodChaged)
        self.itemsSelector.currentIndexChanged.connect(self.itemsChaged)
        self.areaSelector.currentIndexChanged.connect(self.areaChaged)
        self.regionSelector.currentIndexChanged.connect(self.regionChanged)

    def modelChanged(self):
        chart = self.chartSelector.currentData()
        if chart == 'geochart':
            self.chart = self.geoChart()
        elif chart == 'barh':
            self.chart = self.barHChart()
        elif chart == 'pie':
            self.chart = self.pieChart()
        elif chart == 'stacked':
            self.chart = self.stackedChart()
        elif chart == 'progress':
            dbnomicsEnabled = Settings()['dbnomics_enabled']
            items = self.itemsSelector.currentData()
            if items == 'weight':
                self.chart = self.progressPreciousChart()
            elif dbnomicsEnabled and items == 'fineness':
                self.chart = self.progressPreciousPriceChart()
            else:
                self.chart = self.progressChart()
        elif chart == 'area':
            area = self.areaSelector.currentData()
            if area == 'status':
                self.chart = self.areaStatusChart()
            else:
                self.chart = self.areaChart()
        else:
            self.chart = self.barChart()

        self.scroll.setWidget(self.chart)
        self.chart.doubleClicked.connect(self.zoomInPos)

        self.resizeEvent(None)

    def fieldChaged(self, _text):
        fieldId = self.fieldSelector.currentData()
        self.statisticsParam['fieldid'] = fieldId

        self.modelChanged()

    def subfieldChaged(self, _text):
        subfieldId = self.fieldSelector.currentData()
        self.statisticsParam['subfieldid'] = subfieldId

        self.modelChanged()

    def chartChaged(self, _text):
        chart = self.chartSelector.currentData()
        self.statisticsParam['chart'] = chart

        self.showConfig(chart)

        self.modelChanged()

    def showConfig(self, chart):
        self.subfieldSelector.setVisible(chart == 'stacked')
        self.subfieldLabel.setVisible(chart == 'stacked')
        self.fieldSelector.setVisible(chart not in ('progress', 'geochart'))
        self.fieldLabel.setVisible(chart not in ('progress', 'geochart'))
        self.periodSelector.setVisible(chart == 'progress')
        self.periodLabel.setVisible(chart == 'progress')
        self.itemsSelector.setVisible(chart == 'progress')
        self.itemsLabel.setVisible(chart == 'progress')
        self.areaSelector.setVisible(chart == 'area')
        self.areaLabel.setVisible(chart == 'area')
        if chart == 'area':
            area = self.areaSelector.currentData()
            self.fieldSelector.setDisabled(area == 'status')
        else:
            self.fieldSelector.setDisabled(False)
        self.regionLabel.setVisible(chart == 'geochart')
        self.regionSelector.setVisible(chart == 'geochart')

    def periodChaged(self, _text):
        period = self.periodSelector.currentData()
        self.statisticsParam['period'] = period

        self.modelChanged()

    def itemsChaged(self, _text):
        items = self.itemsSelector.currentData()
        self.statisticsParam['items'] = items

        self.modelChanged()

    def areaChaged(self, _text):
        area = self.areaSelector.currentData()
        self.statisticsParam['items'] = area

        self.fieldSelector.setDisabled(area == 'status')

        self.modelChanged()

    def regionChanged(self, _text):
        # region = self.itemsSelector.currentData()
        # self.statisticsParam['region'] = region

        self.modelChanged()
    
    def barChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = BaseChartModel(db, filter_)

        field_id = self.fieldSelector.currentData()
        field = self.model.fields.field(field_id).name
        model.loadData(field)

        chart = BarChart(model, self)
        field_title = self.fieldSelector.currentText()
        chart.setLabelY(field_title)
        chart.updateChart()

        return chart
    
    def barHChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = BarHChartModel(db, filter_)

        field_id = self.fieldSelector.currentData()
        field = self.model.fields.field(field_id).name
        model.loadData(field)

        chart = BarHChart(model, self)
        field_title = self.fieldSelector.currentText()
        chart.setLabelY(field_title)
        chart.updateChart()

        return chart

    def pieChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = BaseChartModel(db, filter_)

        field_id = self.fieldSelector.currentData()
        field = self.model.fields.field(field_id).name
        model.loadData(field)

        chart = PieChart(model, self)
        field_title = self.fieldSelector.currentText()
        chart.setLabelY(field_title)
        chart.updateChart()

        return chart

    def stackedChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = StackedBarChartModel(db, filter_)

        field_id = self.fieldSelector.currentData()
        field = self.model.fields.field(field_id).name
        subfield_id = self.subfieldSelector.currentData()
        subfield = self.model.fields.field(subfield_id).name
        model.loadData(field, subfield)

        chart = StackedBarChart(model, self)
        subfield_title = self.subfieldSelector.currentText()
        chart.setLabelZ(subfield_title)
        chart.updateChart()

        return chart

    def progressChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = ProgressChartModel(db, filter_)

        items = self.itemsSelector.currentData()
        period = self.periodSelector.currentData()
        model.loadData(items, period)

        chart = ProgressChart(model, self)
        field_title = self.periodSelector.currentText()
        chart.setLabelY(field_title)

        if items == 'payprice':
            chart.setLabel(self.tr("Total price"))
        elif items == 'totalpayprice':
            chart.setLabel(self.tr("Total paid"))
        chart.updateChart()

        return chart

    def progressPreciousChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = ProgressPreciousChartModel(db, filter_)

        period = self.periodSelector.currentData()
        model.loadData(period)

        chart = ProgressPreciousChart(model, self)
        field_title = self.periodSelector.currentText()
        chart.setLabelY(field_title)
        chart.setLabel(self.tr("Weight"))
        chart.updateChart()

        return chart

    def progressPreciousPriceChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = ProgressPreciousPriceChartModel(db, filter_)

        period = self.periodSelector.currentData()
        model.loadData(period)

        currency_symbols = {
            'USD': "$",
            'EUR': "€",
            'GBP': "£",
            'RUB': "₽",
            'PLN': "zł",
        }

        dbnomicsCurrency = Settings()['dbnomics_currency']

        if dbnomicsCurrency in currency_symbols:
            symbol = currency_symbols[dbnomicsCurrency]
        else:
            symbol = dbnomicsCurrency

        chart = ProgressPreciousPriceChart(model, self)
        field_title = self.periodSelector.currentText()
        chart.setLabelY(field_title)
        title = self.tr("Price")
        chart.setLabel(f"{title}, {symbol}")
        chart.updateChart()

        return chart

    def areaChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = AreaChartModel(db, filter_)

        field_id = self.fieldSelector.currentData()
        field = self.model.fields.field(field_id).name
        area = self.areaSelector.currentData()
        model.loadData(field, area)

        nice_years = Settings()['nice_years_chart']
        if nice_years:
            chart = AreaNiceChart(model, self)
        else:
            chart = AreaChart(model, self)
        field_title = self.fieldSelector.currentText()
        chart.setLabelY(field_title)
        chart.updateChart()

        return chart

    def areaStatusChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = AreaStatusChartModel(db, filter_)

        model.loadData()

        nice_years = Settings()['nice_years_chart']
        if nice_years:
            chart = AreaNiceStatusChart(model, self)
        else:
            chart = AreaStatusChart(model, self)
        chart.updateChart()

        return chart

    def geoChart(self):
        db = self.model.database()
        filter_ = self.model.filter()
        model = GeoChartModel(db, filter_, self)

        region = self.regionSelector.currentData()
        model.loadData(region)

        chart = GeoChart(model, self)
        chart.updateChart()

        return chart

    def save(self):
        defaultFileName = "%s_%s" % (self.chartSelector.currentText(),
                                     QDateTime.currentDateTime().toString('yyyyMMdd'))

        fileName, selectedFilter = getSaveFileName(
            self, 'export_statistics', defaultFileName,
            OpenNumismat.HOME_PATH, self.chart.filters())
        if fileName:
            self.chart.save(fileName, selectedFilter)

    def settings(self):
        dialog = SettingsDialog(self)
        dialog.applyClicked.connect(self.applySettings)
        res = dialog.exec()
        if res == QDialog.Accepted:
            self.applySettings()
        dialog.deleteLater()

    def applySettings(self):
        self.modelChanged()

    def resizeEvent(self, _e):
        scroll_size = self.scroll.size() - QSize(2, 2)
        chart_size = self.chart.size()

        if scroll_size.height() >= chart_size.height() or \
                scroll_size.width() >= chart_size.width():
            self.chart.resize(scroll_size)
            self.zoomOutButton.setDisabled(True)
            self.zoomInButton.setEnabled(True)

    def zoomInPos(self, point):
        if not self.zoomInButton.isEnabled():
            return

        scroll_size = self.scroll.size() - QSize(2, 2)
        target_size = self.chart.size() * 1.5

        old_pos_h = (self.scroll.horizontalScrollBar().value() + point.x()) * 1.5
        old_pos_v = (self.scroll.verticalScrollBar().value() + point.y()) * 1.5

        if scroll_size.height() * 5 <= target_size.height() or \
                scroll_size.width() * 5 <= target_size.width():
            self.zoomInButton.setDisabled(True)
        self.zoomOutButton.setEnabled(True)

        self.chart.resize(target_size)

        self.scroll.horizontalScrollBar().setValue((old_pos_h - point.x()))
        self.scroll.verticalScrollBar().setValue((old_pos_v - point.y()))

    def zoomIn(self):
        old_size = self.chart.size()
        scroll_size = self.scroll.size() - QSize(2, 2)
        target_size = self.chart.size() * 1.25

        if scroll_size.height() * 5 <= target_size.height() or \
                scroll_size.width() * 5 <= target_size.width():
            self.zoomInButton.setDisabled(True)
        self.zoomOutButton.setEnabled(True)

        self.chart.resize(target_size)

        w = target_size.width() - old_size.width()
        pos = self.scroll.horizontalScrollBar().value()
        self.scroll.horizontalScrollBar().setValue(pos + w // 2)

        h = target_size.height() - old_size.height()
        pos = self.scroll.verticalScrollBar().value()
        self.scroll.verticalScrollBar().setValue(pos + h // 2)

    def zoomOut(self):
        old_size = self.chart.size()
        scroll_size = self.scroll.size() - QSize(2, 2)
        target_size = self.chart.size() / 1.25

        old_pos_h = self.scroll.horizontalScrollBar().value()
        old_pos_v = self.scroll.verticalScrollBar().value()

        if scroll_size.height() >= target_size.height() or \
                scroll_size.width() >= target_size.width():
            self.chart.resize(scroll_size)
            self.zoomOutButton.setDisabled(True)
        else:
            self.chart.resize(target_size)
        self.zoomInButton.setEnabled(True)

        w1 = target_size.width() - scroll_size.width()
        if w1:
            w2 = old_size.width() - scroll_size.width()
            scale = w2 / w1
            self.scroll.horizontalScrollBar().setValue(old_pos_h / scale)

        h1 = target_size.height() - scroll_size.height()
        if h1:
            h2 = old_size.height() - scroll_size.height()
            scale = h2 / h1
            self.scroll.verticalScrollBar().setValue(old_pos_v / scale)


class SettingsDialog(QDialog):
    applyClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        settings = Settings()

        self.setWindowTitle(self.tr("Chart settings"))

        formLayout = QFormLayout()
        formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)

        self.chartThemeSelector = QComboBox(self)
        self.chartThemeSelector.addItem(self.tr("Light"),
                                        QChart.ChartThemeLight.value)
        self.chartThemeSelector.addItem(self.tr("Blue Cerulean"),
                                        QChart.ChartThemeBlueCerulean.value)
        self.chartThemeSelector.addItem(self.tr("Dark"),
                                        QChart.ChartThemeDark.value)
        self.chartThemeSelector.addItem(self.tr("Brown Sand"),
                                        QChart.ChartThemeBrownSand.value)
        self.chartThemeSelector.addItem(self.tr("Blue Ncs"),
                                        QChart.ChartThemeBlueNcs.value)
        self.chartThemeSelector.addItem(self.tr("High Contrast"),
                                        QChart.ChartThemeHighContrast.value)
        self.chartThemeSelector.addItem(self.tr("Blue Icy"),
                                        QChart.ChartThemeBlueIcy.value)
        self.chartThemeSelector.addItem(self.tr("Qt"),
                                        QChart.ChartThemeQt.value)
        index = self.chartThemeSelector.findData(settings['chart_theme'])
        if index >= 0:
            self.chartThemeSelector.setCurrentIndex(index)
        self.chartThemeSelector.setSizePolicy(QSizePolicy.Fixed,
                                              QSizePolicy.Fixed)
        formLayout.addRow(self.tr("Chart theme"), self.chartThemeSelector)

        self.colorCheck = QCheckBox(self.tr("Multicolor"), self)
        self.colorCheck.setChecked(settings['multicolor_chart'])
        formLayout.addRow(self.colorCheck)

        self.useBlafPalette = QCheckBox(
                        self.tr("Use BLAF palette"), self)
        self.useBlafPalette.setChecked(settings['use_blaf_palette'])
        formLayout.addRow(self.useBlafPalette)

        self.legendCheck = QCheckBox(self.tr("Show legend (Pie)"), self)
        self.legendCheck.setChecked(settings['show_chart_legend'])
        formLayout.addRow(self.legendCheck)

        self.legendPosSelector = QComboBox(self)
        self.legendPosSelector.addItem(self.tr("Top"), Qt.AlignTop.value)
        self.legendPosSelector.addItem(self.tr("Right"), Qt.AlignRight.value)
        self.legendPosSelector.addItem(self.tr("Bottom"), Qt.AlignBottom.value)
        self.legendPosSelector.addItem(self.tr("Left"), Qt.AlignLeft.value)
        index = self.legendPosSelector.findData(settings['chart_legend_pos'])
        if index >= 0:
            self.legendPosSelector.setCurrentIndex(index)
        self.legendPosSelector.setSizePolicy(QSizePolicy.Fixed,
                                             QSizePolicy.Fixed)
        formLayout.addRow(self.tr("Legend position"), self.legendPosSelector)

        self.niceYearsCheck = QCheckBox(self.tr("Nice years (Area)"), self)
        self.niceYearsCheck.setChecked(settings['nice_years_chart'])
        formLayout.addRow(self.niceYearsCheck)

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.addButton(QDialogButtonBox.Cancel)
        applyButton = buttonBox.addButton(QDialogButtonBox.Apply)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.reject)
        applyButton.clicked.connect(self.apply)

        layout = QVBoxLayout()
        layout.addLayout(formLayout)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

    def save(self):
        self.save_settings()
        self.accept()

    def apply(self):
        self.save_settings()
        self.applyClicked.emit()

    def save_settings(self):
        settings = Settings()

        settings['use_blaf_palette'] = self.useBlafPalette.isChecked()
        settings['chart_theme'] = self.chartThemeSelector.currentData()
        settings['multicolor_chart'] = self.colorCheck.isChecked()
        settings['show_chart_legend'] = self.legendCheck.isChecked()
        settings['chart_legend_pos'] = self.legendPosSelector.currentData()
        settings['nice_years_chart'] = self.niceYearsCheck.isChecked()

        settings.save()
