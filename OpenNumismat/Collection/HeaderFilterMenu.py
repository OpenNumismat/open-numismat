from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtSql import QSqlQuery

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.Tools.Gui import createIcon


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

        self.setToolTip(self.tr("Filter items"))

        self.setFixedHeight(self.parent().height() - 2)
        self.setFixedWidth(self.height())
        self.setMenu(menu)
        if self.fieldid in self.filters.keys():
            self.setIcon(createIcon('filters.ico'))

        menu.aboutToShow.connect(self.prepareMenu)

    def prepareMenu(self):
        self.listWidget = QtGui.QListWidget(self)

        item = QtGui.QListWidgetItem(self.tr("(Select all)"), self.listWidget,
                                     FilterMenuButton.SelectAllType)
        item.setData(Qt.UserRole, self.tr("(Select all)"))
        item.setCheckState(Qt.PartiallyChecked)
        self.listWidget.addItem(item)

        filters = self.filters.copy()
        appliedValues = []
        columnFilters = None
        revert = False
        if self.fieldid in filters.keys():
            columnFilters = filters.pop(self.fieldid)
            for filter_ in columnFilters.filters():
                if filter_.isRevert():
                    revert = True
                appliedValues.append(filter_.value)

        hasBlanks = False
        columnType = self.model.columnType(self.fieldid)
        if columnType == Type.Text or columnType in Type.ImageTypes:
            dataFilter = BlankFilter(self.columnName).toSql()
            blanksFilter = DataFilter(self.columnName).toSql()

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
                if columnType in Type.ImageTypes:
                    label = self.tr("(Images)")
                elif columnType == Type.Text:
                    label = self.tr("(Text)")
                else:
                    label = self.tr("(Data)")
                item = QtGui.QListWidgetItem(label, self.listWidget,
                                             FilterMenuButton.DataType)
                item.setData(Qt.UserRole, label)
                item.setCheckState(Qt.Checked)
                if columnFilters and columnFilters.hasData():
                    item.setCheckState(Qt.Unchecked)
                self.listWidget.addItem(item)

            if blanksCount > 0:
                hasBlanks = True
        elif self.model.columnType(self.fieldid) == Type.Status:
            filtersSql = self.filtersToSql(filters.values())
            if filtersSql:
                filtersSql = 'WHERE ' + filtersSql
            sql = "SELECT DISTINCT %s FROM coins %s" % (self.columnName, filtersSql)
            query = QSqlQuery(sql, self.db)

            while query.next():
                value = query.record().value(0)
                label = Statuses[value]
                item = QtGui.QListWidgetItem(label, self.listWidget)
                item.setData(Qt.UserRole, value)
                if label in appliedValues:
                    if revert:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                else:
                    if revert:
                        item.setCheckState(Qt.Unchecked)
                    else:
                        item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)
        else:
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
                item.setData(Qt.UserRole, label)
                if label in appliedValues:
                    if revert:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
                else:
                    if revert:
                        item.setCheckState(Qt.Unchecked)
                    else:
                        item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)

        if hasBlanks:
            item = QtGui.QListWidgetItem(self.tr("(Blanks)"), self.listWidget,
                                         FilterMenuButton.BlanksType)
            item.setData(Qt.UserRole, self.tr("(Blanks)"))
            item.setCheckState(Qt.Checked)
            if revert:
                if columnFilters and not columnFilters.hasBlank():
                    item.setCheckState(Qt.Unchecked)
            else:
                if columnFilters and columnFilters.hasBlank():
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
            button = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
            button.setDisabled(item.checkState() == Qt.Unchecked)
        else:
            checkedCount = 0
            for i in range(1, self.listWidget.count()):
                item = self.listWidget.item(i)
                if item.checkState() == Qt.Checked:
                    checkedCount = checkedCount + 1

            if checkedCount == 0:
                state = Qt.Unchecked
            elif checkedCount == self.listWidget.count() - 1:
                state = Qt.Checked
            else:
                state = Qt.PartiallyChecked
            self.listWidget.item(0).setCheckState(state)

            # Disable applying filter when nothing to show
            button = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
            button.setDisabled(checkedCount == 0)

        self.listWidget.itemChanged.connect(self.itemChanged)

    def apply(self):
        filters = ColumnFilters(self.columnName)
        unchecked = 0
        checked = 0
        for i in range(1, self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Unchecked:
                unchecked = unchecked + 1
            else:
                checked = checked + 1

        for i in range(1, self.listWidget.count()):
            item = self.listWidget.item(i)
            if unchecked > checked:
                if item.checkState() == Qt.Checked:
                    if item.type() == FilterMenuButton.BlanksType:
                        filter_ = BlankFilter(self.columnName)
                    elif item.type() == FilterMenuButton.DataType:
                        filter_ = DataFilter(self.columnName)
                    else:
                        value = item.data(Qt.UserRole)
                        filter_ = ValueFilter(self.columnName, value)

                    filter_.revert = True
                    filters.addFilter(filter_)
            else:
                if item.checkState() == Qt.Unchecked:
                    if item.type() == FilterMenuButton.BlanksType:
                        filter_ = BlankFilter(self.columnName)
                    elif item.type() == FilterMenuButton.DataType:
                        filter_ = DataFilter(self.columnName)
                    else:
                        value = item.data(Qt.UserRole)
                        filter_ = ValueFilter(self.columnName, value)

                    filters.addFilter(filter_)

        if filters.filters():
            self.setIcon(createIcon('filters.ico'))
            self.filters[self.fieldid] = filters
        else:
            self.setIcon(createIcon())
            if self.fieldid in self.filters.keys():
                self.filters.pop(self.fieldid)

        filtersSql = self.filtersToSql(self.filters.values())
        self.model.setFilter(filtersSql)

        self.menu().hide()

        self.listParam.save()

    def clear(self):
        self.setIcon(createIcon())

    @staticmethod
    def filtersToSql(filters):
        sqlFilters = []
        for columnFilters in filters:
            sqlFilters.append(columnFilters.toSql())

        return ' AND '.join(sqlFilters)


class BaseFilter:
    def __init__(self, name):
        self.name = name
        self.value = None
        self.revert = False

    def toSql(self):
        raise NotImplementedError

    def isBlank(self):
        return False

    def isData(self):
        return False

    def isRevert(self):
        return self.revert


class ValueFilter(BaseFilter):
    def __init__(self, name, value):
        super(ValueFilter, self).__init__(name)

        self.value = value

    def toSql(self):
        if self.revert:
            return "%s='%s'" % (self.name, self.value.replace("'", "''"))
        else:
            return "%s<>'%s'" % (self.name, self.value.replace("'", "''"))


class DataFilter(BaseFilter):
    def __init__(self, name):
        super(DataFilter, self).__init__(name)

    def toSql(self):
        if self.revert:
            # Filter out blank values
            return "%s<>'' AND %s IS NOT NULL" % (self.name, self.name)
        else:
            # Filter out not null and not empty values
            return "ifnull(%s,'')=''" % self.name

    def isData(self):
        return True


class BlankFilter(BaseFilter):
    def __init__(self, name):
        super(BlankFilter, self).__init__(name)

    def toSql(self):
        if self.revert:
            # Filter out not null and not empty values
            return "ifnull(%s,'')=''" % self.name
        else:
            # Filter out blank values
            return "%s<>'' AND %s IS NOT NULL" % (self.name, self.name)

    def isBlank(self):
        return True


class ColumnFilters:
    def __init__(self, name):
        self.name = name
        self._filters = []
        self._blank = False  # blank out filter present
        self._data = False  # data out filter present
        self._revert = False

    def addFilter(self, filter_):
        self._blank = self._blank or filter_.isBlank()
        self._data = self._data or filter_.isData()
        self._revert = self._revert or filter_.isRevert()
        self._filters.append(filter_)

    def filters(self):
        return self._filters

    def hasBlank(self):
        return self._blank

    def hasData(self):
        return self._data

    def hasRevert(self):
        return self._revert

    def toSql(self):
        sqlFilters = []
        for filter_ in self._filters:
            sqlFilters.append(filter_.toSql())

        if self.hasRevert():
            combinedFilters = ' OR '.join(sqlFilters)
        else:
            combinedFilters = ' AND '.join(sqlFilters)

        # Note: In SQLite SELECT * FROM coins WHERE title<>'value' also filter
        # out a NULL values. Work around this problem
        if not self.hasBlank() and not self.hasData():
            combinedFilters = combinedFilters + (' OR %s IS NULL' % self.name)
        return '(' + combinedFilters + ')'
