from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from PyQt4.QtSql import QSqlQuery

from Collection.CollectionFields import CollectionFields

class FilterMenuButton(QtGui.QPushButton):
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
        sql = "SELECT DISTINCT %s FROM coins" % self.columnName
        query = QSqlQuery(sql, self.db)
        while query.next():
            item = QtGui.QListWidgetItem(str(query.record().value(0)), self.listWidget)
            item.setCheckState(Qt.Checked)
            self.listWidget.addItem(item)
        
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

    def apply(self):
        filters = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            if item.checkState() == Qt.Unchecked:
                filters.append("%s<>'%s'" % (self.columnName, item.text()))

        sql = ' AND '.join(filters)
        self.model.setFilter(sql)
                
        self.menu().hide()
