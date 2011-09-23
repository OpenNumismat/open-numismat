from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtSql import QSqlQuery

from Collection.CollectionFields import FieldTypes as Type

class FilterMenuButton(QtGui.QPushButton):
    DefaultType = 0
    SelectAllType = 1
    BlanksType = 2
    DataType = 3
    
    def __init__(self, columnName, model, parent):
        super(FilterMenuButton, self).__init__(parent)
        
        self.db = model.database()
        self.model = model
        self.columnName = columnName
        
        menu = QtGui.QMenu()

        self.setFixedHeight(self.parent().height()-2)
        self.setFixedWidth(self.height())
        self.setMenu(menu)
        
        menu.aboutToShow.connect(self.prepareMenu)

    def prepareMenu(self):
        self.listWidget = QtGui.QListWidget(self)

        item = QtGui.QListWidgetItem(self.tr("(Select all)"), self.listWidget, FilterMenuButton.SelectAllType)
        item.setCheckState(Qt.PartiallyChecked)
        self.listWidget.addItem(item)

        hasBlanks = False
        if not self.model.columnType(self.columnName) in [Type.Image, Type.Text]:
            filters = self.model.filters
            if self.columnName in filters.keys():
                filters.pop(self.columnName)
            filtersSql = ' AND '.join(filters.values())
            if filtersSql:
                filtersSql = 'WHERE ' + filtersSql 
            sql = "SELECT DISTINCT %s FROM coins %s" % (self.columnName, filtersSql)
            query = QSqlQuery(sql, self.db)

            while query.next():
                label = str(query.record().value(0))
                if not label:
                    hasBlanks = True
                    continue
                item = QtGui.QListWidgetItem(label, self.listWidget)
                item.setCheckState(Qt.Checked)
                self.listWidget.addItem(item)
        else:
            # TODO: Check that values present or not 
            item = QtGui.QListWidgetItem(self.tr("(Data)"), self.listWidget, FilterMenuButton.DataType)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)

            hasBlanks = True
        
        if hasBlanks:
            item = QtGui.QListWidgetItem(self.tr("(Blanks)"), self.listWidget, FilterMenuButton.BlanksType)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)
        
        self.listWidget.itemChanged.connect(self.itemChanged)
        
        self.itemChanged(item)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.apply)
        buttonBox.rejected.connect(self.menu().hide)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.listWidget)
        layout.addWidget(buttonBox)

        widget = QtGui.QWidget(self)
        widget.setLayout(layout)

        widgetAction = QtGui.QWidgetAction(self)
        widgetAction.setDefaultWidget(widget)
        self.menu().clear()
        self.menu().addAction(widgetAction)
    
    def itemChanged(self, item):
        self.listWidget.itemChanged.disconnect(self.itemChanged)

        if item.type() == FilterMenuButton.SelectAllType:
            for i in range(1, self.listWidget.count()):
                self.listWidget.item(i).setCheckState(item.checkState())
        else:
            checkedCount = 0
            for i in range(1, self.listWidget.count()):
                item = self.listWidget.item(i)
                if item.checkState() == Qt.Checked:
                    checkedCount = checkedCount + 1

            if checkedCount == 0:
                # TODO: Disable applying filter when nothing to show 
                state = Qt.Unchecked
            elif checkedCount == self.listWidget.count()-1:
                state = Qt.Checked
            else:
                state = Qt.PartiallyChecked
            self.listWidget.item(0).setCheckState(state)

        self.listWidget.itemChanged.connect(self.itemChanged)

    def apply(self):
        filters = []
        for i in range(1, self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Unchecked:
                if item.type() == FilterMenuButton.BlanksType:
                    # Filter out empty and null values
                    filters.append("%s<>'' AND %s IS NOT NULL" % (self.columnName, self.columnName))
                elif item.type() == FilterMenuButton.DataType:
                    # Filter out not null and not empty values
                    filters.append("ifnull(%s,'')=''" % self.columnName)
                else:
                    filters.append("%s<>'%s'" % (self.columnName, item.text()))

        if filters:
            filterSql = ' AND '.join(filters)
            self.model.filters[self.columnName] = filterSql
        else:
            if self.columnName in self.model.filters.keys():
                self.model.filters.pop(self.columnName)

        filtersSql = ' AND '.join(self.model.filters.values())
        self.model.setFilter(filtersSql)
        
        self.menu().hide()
