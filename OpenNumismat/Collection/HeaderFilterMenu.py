from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.Collection.CollectionFields import Statuses, BuyPriceFields, SellPriceFields, CatalogFields
from OpenNumismat.Tools.Gui import statusIcon
from OpenNumismat.Tools.Converters import numberWithFraction, compareYears


class CustomSortListWidgetItem(QListWidgetItem):

    def __lt__(self, other):
        left = self.data(Qt.UserRole + 1)
        right = other.data(Qt.UserRole + 1)

        if isinstance(left, str):
            right = str(right)
        elif isinstance(right, str):
            left = str(left)

        return left < right


class YearSortListWidgetItem(QListWidgetItem):

    def __lt__(self, other):
        left = self.data(Qt.UserRole + 1)
        right = other.data(Qt.UserRole + 1)
        return compareYears(left, right) < 0


class StatusSortListWidgetItem(QListWidgetItem):

    def __lt__(self, other):
        left = self.data(Qt.UserRole)
        right = other.data(Qt.UserRole)
        return Statuses.compare(left, right) < 0


class FilterMenuButton(QPushButton):
    DefaultType = QListWidgetItem.UserType
    SelectAllType = QListWidgetItem.UserType + 1
    BlanksType = QListWidgetItem.UserType + 2
    DataType = QListWidgetItem.UserType + 3

    def __init__(self, columnParam, listParam, model, parent):
        super().__init__(parent)

        self.db = model.database()
        self.model = model
        self.reference = model.reference
        self.field = self.model.fields.field(columnParam.fieldid)
        self.filters = listParam.filters
        self.listParam = listParam
        self.settings = model.settings

        menu = QMenu(self)
        menu.aboutToShow.connect(self.prepareMenu)
        self.setMenu(menu)

        self.setToolTip(self.tr("Filter items"))

        off = 2
        self.setFixedHeight(self.parent().height() - off)
        self.setFixedWidth(self.height())
        self.setObjectName("FilterMenuButton")
        padding = self.style().pixelMetric(QStyle.PM_MenuButtonIndicator) + off
        self.setStyleSheet(f"QPushButton#FilterMenuButton {{padding-left:{padding}px;}}")
        if self.field.id in self.filters.keys():
            self.setIcon(QIcon(':/filters.ico'))

    def prepareMenu(self):
        self.listWidget = QListWidget(self)

        filters = self.filters.copy()
        appliedValues = []
        columnFilters = None
        revert = False
        if self.field.id in filters.keys():
            columnFilters = filters.pop(self.field.id)
            for filter_ in columnFilters.filters():
                if filter_.isRevert():
                    revert = True
                appliedValues.append(filter_.value)

        from_sql = ("FROM coins"
                    f" {self.model.JOIN_BUY_PRICES}"
                    f" {self.model.JOIN_SELL_PRICES}"
                    f" {self.model.JOIN_CATALOGS}")

        filters_sql = self.filtersToSql(filters.values())
        where_clause = f"WHERE {filters_sql}" if filters_sql else ""

        hasBlanks = False
        if self.field.name == 'year':
            sql = f"SELECT DISTINCT coins.{self.field.name} AS {self.field.name} {from_sql} {where_clause}"
            query = QSqlQuery(sql, self.db)

            while query.next():
                if query.record().isNull(0):
                    data = None
                else:
                    orig_data = query.record().value(0)
                    data = str(orig_data)
                    label = data
                    try:
                        year = str(data)
                        if year and year[0] == '-':
                            label = "%s BC" % year[1:]
                    except ValueError:
                        pass

                if not data:
                    hasBlanks = True
                    continue

                item = YearSortListWidgetItem()
                item.setData(Qt.DisplayRole, label)
                item.setData(Qt.UserRole, data)
                item.setData(Qt.UserRole + 1, orig_data)
                if (data in appliedValues) ^ revert:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)

            self.listWidget.sortItems()
        elif self.field.type == Type.Text or self.field.type in Type.ImageTypes:
            dataFilter = BlankFilter(self.field.name).toSql()
            blanksFilter = DataFilter(self.field.name).toSql()

            sql = f"SELECT DISTINCT coins.{self.field.name} AS {self.field.name} {from_sql} WHERE {filters_sql}"
            if filters_sql:
                sql += ' AND '

            # Get blank row count
            blank_sql = sql + blanksFilter + " LIMIT 1"
            query = QSqlQuery(blank_sql, self.db)
            if query.first():
                hasBlanks = True

            # Get not blank row count
            not_blank_sql = sql + dataFilter + " LIMIT 1"
            query = QSqlQuery(not_blank_sql, self.db)
            if query.first():
                if self.field.type in Type.ImageTypes:
                    label = self.tr("(Images)")
                elif self.field.type == Type.Text:
                    label = self.tr("(Text)")
                else:
                    label = self.tr("(Data)")
                item = QListWidgetItem(label,
                                       type=FilterMenuButton.DataType)
                item.setData(Qt.UserRole, label)
                item.setCheckState(Qt.Checked)
                if columnFilters and columnFilters.hasData():
                    item.setCheckState(Qt.Unchecked)
                self.listWidget.addItem(item)
        elif self.field.type == Type.Status:
            sql = f"SELECT DISTINCT coins.{self.field.name} AS {self.field.name} {from_sql} {where_clause}"
            query = QSqlQuery(sql, self.db)

            while query.next():
                value = query.record().value(0)
                label = Statuses[value]

                item = StatusSortListWidgetItem(label)
                item.setData(Qt.UserRole, value)

                icon = statusIcon(value)
                item.setIcon(icon)

                if (value in appliedValues) ^ revert:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)

            self.listWidget.sortItems()
        elif self.field.type == Type.Denomination:
            sql = f"SELECT DISTINCT coins.{self.field.name} AS {self.field.name} {from_sql} {where_clause}"
            query = QSqlQuery(sql, self.db)

            while query.next():
                if query.record().isNull(0):
                    data = None
                else:
                    orig_data = query.record().value(0)
                    data = str(orig_data)
                    label, _ = numberWithFraction(data, self.settings['convert_fraction'])

                if not data:
                    hasBlanks = True
                    continue

                item = CustomSortListWidgetItem()
                item.setData(Qt.DisplayRole, label)
                item.setData(Qt.UserRole, data)
                item.setData(Qt.UserRole + 1, orig_data)
                if (data in appliedValues) ^ revert:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)

            self.listWidget.sortItems()
        else:
            if self.field.name in BuyPriceFields:
                table_name = 'buy_prices'
                field_name = BuyPriceFields[self.field.name]
            elif self.field.name in SellPriceFields:
                table_name = 'sell_prices'
                field_name = SellPriceFields[self.field.name]
            elif self.field.name in CatalogFields:
                table_name = 'catalogs'
                field_name = CatalogFields[self.field.name]
            else:
                table_name = 'coins'
                field_name = self.field.name

            sql = f"SELECT DISTINCT {table_name}.{field_name} AS {self.field.name} {from_sql} {where_clause}"
            query = QSqlQuery(sql, self.db)

            while query.next():
                icon = None
                if query.record().isNull(0):
                    data = None
                else:
                    orig_data = query.record().value(0)
                    data = str(orig_data)
                    icon = self.reference.getIcon(self.field.name, data)

                if not data:
                    hasBlanks = True
                    continue

                item = QListWidgetItem()
                item.setData(Qt.DisplayRole, orig_data)
                item.setData(Qt.UserRole, data)
                if icon:
                    item.setIcon(icon)
                if (data in appliedValues) ^ revert:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)

            self.listWidget.sortItems()

        item = QListWidgetItem(self.tr("(Select all)"),
                               type=FilterMenuButton.SelectAllType)
        item.setData(Qt.UserRole, self.tr("(Select all)"))
        item.setCheckState(Qt.Checked)
        self.listWidget.insertItem(0, item)

        if hasBlanks:
            item = QListWidgetItem(self.tr("(Blanks)"),
                                   type=FilterMenuButton.BlanksType)
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

        self.searchBox = QLineEdit(self)
        self.searchBox.setPlaceholderText(self.tr("Filter"))
        self.searchBox.textChanged.connect(self.applySearch)

        self.buttonBox = QDialogButtonBox(Qt.Horizontal)
        self.buttonBox.addButton(QDialogButtonBox.Ok)
        self.buttonBox.addButton(QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.apply)
        self.buttonBox.rejected.connect(self.menu().hide)

        layout = QVBoxLayout()
        layout.addWidget(self.searchBox)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.buttonBox)

        widget = QWidget(self)
        widget.setLayout(layout)

        widgetAction = QWidgetAction(self)
        widgetAction.setDefaultWidget(widget)
        self.menu().clear()
        self.menu().addAction(widgetAction)

        # Fill items
        if self.listWidget.count() > 1:
            self.itemChanged(self.listWidget.item(1))

    def itemChanged(self, item):
        self.listWidget.itemChanged.disconnect(self.itemChanged)

        if item.type() == FilterMenuButton.SelectAllType:
            for i in range(1, self.listWidget.count()):
                self.listWidget.item(i).setCheckState(item.checkState())

            # Disable applying filter when nothing to show
            button = self.buttonBox.button(QDialogButtonBox.Ok)
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
            button = self.buttonBox.button(QDialogButtonBox.Ok)
            button.setDisabled(checkedCount == 0)

        self.listWidget.itemChanged.connect(self.itemChanged)

    def apply(self):
        filters = ColumnFilters(self.field.name)
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
                        filter_ = BlankFilter(self.field.name)
                    elif item.type() == FilterMenuButton.DataType:
                        filter_ = DataFilter(self.field.name)
                    else:
                        value = item.data(Qt.UserRole)
                        filter_ = ValueFilter(self.field.name, value)

                    filter_.revert = True
                    filters.addFilter(filter_)
            else:
                if item.checkState() == Qt.Unchecked:
                    if item.type() == FilterMenuButton.BlanksType:
                        filter_ = BlankFilter(self.field.name)
                    elif item.type() == FilterMenuButton.DataType:
                        filter_ = DataFilter(self.field.name)
                    else:
                        value = item.data(Qt.UserRole)
                        filter_ = ValueFilter(self.field.name, value)

                    filters.addFilter(filter_)

        self.applyFilters(filters)

        self.menu().hide()

    def applyFilters(self, filters):
        if filters.filters():
            self.setIcon(QIcon(':/filters.ico'))
            self.filters[self.field.id] = filters
        else:
            self.setIcon(QIcon())
            if self.field.id in self.filters.keys():
                self.filters.pop(self.field.id)

        filtersSql = self.filtersToSql(self.filters.values())
        self.model.setFilter(filtersSql)

        self.listParam.save_filters()

    def clear(self):
        self.setIcon(QIcon())

    def applySearch(self, text):
        text = text.lower()
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.text().lower().find(text) >= 0:
                item.setHidden(False)
            else:
                item.setHidden(True)

    @staticmethod
    def filtersToSql(filters):
        sqlFilters = []
        for columnFilters in filters:
            sqlFilters.append(columnFilters.toSql())

        return ' AND '.join(sqlFilters)


class BaseFilter:
    def __init__(self, name):
        if name in BuyPriceFields:
            name = f"buy_prices.{BuyPriceFields[name]}"
        elif name in SellPriceFields:
            name = f"sell_prices.{SellPriceFields[name]}"
        elif name in CatalogFields:
            name = f"catalogs.{CatalogFields[name]}"
        else:
            name = f"coins.{name}"
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
        super().__init__(name)

        self.value = value

    # TODO: Deprecated method
    def toSql(self):
        if self.revert:
            return "%s='%s'" % (self.name, self.value.replace("'", "''"))
        else:
            return "%s<>'%s'" % (self.name, self.value.replace("'", "''"))


class DataFilter(BaseFilter):
    def toSql(self):
        if self.revert:
            # Filter out blank values
            return "ifnull(%s,'')<>''" % self.name
        else:
            # Filter out not null and not empty values
            return "ifnull(%s,'')=''" % self.name

    def isData(self):
        return True


class BlankFilter(BaseFilter):
    def toSql(self):
        if self.revert:
            # Filter out not null and not empty values
            return "ifnull(%s,'')=''" % self.name
        else:
            # Filter out blank values
            return "ifnull(%s,'')<>''" % self.name

    def isBlank(self):
        return True


class ColumnFilters:
    def __init__(self, name):
        if name in BuyPriceFields:
            name = f"buy_prices.{BuyPriceFields[name]}"
        elif name in SellPriceFields:
            name = f"sell_prices.{SellPriceFields[name]}"
        elif name in CatalogFields:
            name = f"catalogs.{CatalogFields[name]}"
        else:
            name = f"coins.{name}"
        self.name = name
        self._filters = []
        self._blank = None  # blank out filter
        self._data = None  # data out filter
        self._revert = False

    def addFilter(self, filter_):
        if filter_.isBlank():
            self._blank = filter_
        if filter_.isData():
            self._data = filter_
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
        values = []
        for filter_ in self._valueFilters():
            sql = "'%s'" % filter_.value.replace("'", "''")
            values.append(sql)

        combinedFilters = ''
        if values:
            sqlValueFilters = ','.join(values)
            if self.hasRevert():
                combinedFilters = "%s IN (%s)" % (self.name, sqlValueFilters)
            else:
                combinedFilters = "%s NOT IN (%s)" % (self.name, sqlValueFilters)

        if self.hasBlank():
            if combinedFilters:
                if self.hasRevert():
                    combinedFilters = combinedFilters + ' OR ' + self._blank.toSql()
                else:
                    combinedFilters = combinedFilters + ' AND ' + self._blank.toSql()
            else:
                combinedFilters = self._blank.toSql()
        elif self.hasData():
            # Data filter can't contain any additional value filters
            combinedFilters = self._data.toSql()

        # Note: In SQLite SELECT * FROM coins WHERE title NOT IN ('value') also
        # filter out a NULL values. Work around this problem
        if not self.hasBlank() and not self.hasRevert():
            combinedFilters = combinedFilters + (' OR %s IS NULL' % self.name)
        return '(' + combinedFilters + ')'

    def _valueFilters(self):
        for filter_ in self._filters:
            if isinstance(filter_, ValueFilter):
                yield filter_
