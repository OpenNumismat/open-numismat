from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtSql import QSqlQuery

from .CollectionFields import FieldTypes as Type

class FilterMenuButton(QtGui.QPushButton):
    DefaultType = 0
    SelectAllType = 1
    BlanksType = 2
    DataType = 3
    
    def __init__(self, columnParam, listParam, model, parent):
        super(FilterMenuButton, self).__init__(parent)
        
        self.db = model.database()
        self.model = model
        self.columnName = self.model.fields.fields[columnParam.fieldid].name
        self.fieldid = columnParam.fieldid
        self.filters = listParam.filters
        self.listParam = listParam
        
        menu = QtGui.QMenu()

        self.setFixedHeight(self.parent().height()-2)
        self.setFixedWidth(self.height())
        self.setMenu(menu)
        if self.fieldid in self.filters.keys():
            self.setIcon(QtGui.QIcon('icons/filters.ico'))
        
        menu.aboutToShow.connect(self.prepareMenu)

    def prepareMenu(self):
        self.listWidget = QtGui.QListWidget(self)

        item = QtGui.QListWidgetItem(self.tr("(Select all)"), self.listWidget, FilterMenuButton.SelectAllType)
        item.setCheckState(Qt.PartiallyChecked)
        self.listWidget.addItem(item)

        filters = self.filters.copy()
        appliedValues = []
        appliedFilters = None
        if self.fieldid in filters.keys():
            appliedFilters = filters.pop(self.fieldid)
            for filter in appliedFilters:
                appliedValues.append(filter.value)

        hasBlanks = False
        if not self.model.columnType(self.fieldid) in [Type.Image, Type.Text]:
            filtersSql = self.filtersToSql(filters.values())
            if filtersSql:
                filtersSql = 'WHERE ' + filtersSql 
            sql = "SELECT DISTINCT %s FROM coins %s" % (self.columnName, filtersSql)
            query = QSqlQuery(sql, self.db)

            while query.next():
                if query.record().isNull(0):
                    label = None
                else:
                    label = str(query.record().value(0))
                if not label:
                    hasBlanks = True
                    continue
                item = QtGui.QListWidgetItem(label, self.listWidget)
                if label in appliedValues:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)
        else:
            dataFilter = Filter(self.columnName, blank=True).toSql()
            blanksFilter = Filter(self.columnName, data=True).toSql()

            filtersSql = self.filtersToSql(filters.values())
            sql = "SELECT count(*) FROM coins WHERE " + filtersSql
            if filtersSql:
                sql = sql + ' AND '

            # Get blank row count
            query = QSqlQuery(sql + blanksFilter, self.db)
            query.first()
            blanksCount = query.record().value(0)

            # Get not blank row count
            query = QSqlQuery(sql + dataFilter, self.db)
            query.first()
            dataCount = query.record().value(0)
            
            if dataCount > 0:
                if self.model.columnType(self.fieldid) == Type.Image:
                    label = self.tr("(Images)")
                elif self.model.columnType(self.fieldid) == Type.Text:
                    label = self.tr("(Text)")
                else:
                    label = self.tr("(Data)")
                item = QtGui.QListWidgetItem(label, self.listWidget, FilterMenuButton.DataType)
                item.setCheckState(Qt.Checked)
                if appliedFilters:
                    filter = appliedFilters[-1]   # data filter always is last element
                    if filter.data:
                        item.setCheckState(Qt.Unchecked)
                self.listWidget.addItem(item)

            if blanksCount > 0:
                hasBlanks = True
        
        if hasBlanks:
            item = QtGui.QListWidgetItem(self.tr("(Blanks)"), self.listWidget, FilterMenuButton.BlanksType)
            item.setCheckState(Qt.Checked)
            if appliedFilters:
                filter = appliedFilters[-1]   # blank filter always is last element
                if filter.blank:
                    item.setCheckState(Qt.Unchecked)
            self.listWidget.addItem(item)
        
        self.listWidget.itemChanged.connect(self.itemChanged)
        
        self.buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        self.buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.apply)
        self.buttonBox.rejected.connect(self.menu().hide)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.buttonBox)

        widget = QtGui.QWidget(self)
        widget.setLayout(layout)

        widgetAction = QtGui.QWidgetAction(self)
        widgetAction.setDefaultWidget(widget)
        self.menu().clear()
        self.menu().addAction(widgetAction)
    
        # Fill items
        self.itemChanged(item)
        
    def itemChanged(self, item):
        self.listWidget.itemChanged.disconnect(self.itemChanged)

        if item.type() == FilterMenuButton.SelectAllType:
            for i in range(1, self.listWidget.count()):
                self.listWidget.item(i).setCheckState(item.checkState())

            # Disable applying filter when nothing to show
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(item.checkState() == Qt.Unchecked)
        else:
            checkedCount = 0
            for i in range(1, self.listWidget.count()):
                item = self.listWidget.item(i)
                if item.checkState() == Qt.Checked:
                    checkedCount = checkedCount + 1

            if checkedCount == 0:
                state = Qt.Unchecked
            elif checkedCount == self.listWidget.count()-1:
                state = Qt.Checked
            else:
                state = Qt.PartiallyChecked
            self.listWidget.item(0).setCheckState(state)

            # Disable applying filter when nothing to show
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setDisabled(checkedCount == 0)

        self.listWidget.itemChanged.connect(self.itemChanged)

    def apply(self):
        filters = ColumnFilters(self.columnName)
        for i in range(1, self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Unchecked:
                if item.type() == FilterMenuButton.BlanksType:
                    filters.addFilter(blank=True)
                elif item.type() == FilterMenuButton.DataType:
                    filters.addFilter(data=True)
                else:
                    filters.addFilter(item.text())

        if filters.filters():
            self.setIcon(QtGui.QIcon('icons/filters.ico'))
            self.filters[self.fieldid] = filters.filters()
        else:
            self.setIcon(QtGui.QIcon())
            if self.fieldid in self.filters.keys():
                self.filters.pop(self.fieldid)

        filtersSql = self.filtersToSql(self.filters.values())
        self.model.setFilter(filtersSql)
        
        self.menu().hide()
        
        self.listParam.save()
    
    @staticmethod
    def filtersToSql(filters):
        sqlFilters = []
        for columnFilters in filters:
            for filter in columnFilters:
                sqlFilters.append(filter.toSql())
        
        return ' AND '.join(sqlFilters)

class Filter:
    def __init__(self, name, value=None, data=None, blank=None):
        self.name = name
        self.value = value
        self.data = data
        self.blank = blank

    def toSql(self):
        name = self.name
        if self.blank:
            # Filter out blank values
            return "%s<>'' AND %s IS NOT NULL" % (name, name)
        elif self.data:
            # Filter out not null and not empty values
            return "ifnull(%s,'')=''" % name
        else:
            return "%s<>'%s'" % (name, self.value)

class ColumnFilters:
    def __init__(self, name):
        self.name = name
        self._filters = []

    def addFilter(self, value=None, data=None, blank=None):
        self._filters.append(Filter(self.name, value, data, blank))
    
    def filters(self):
        return self._filters
