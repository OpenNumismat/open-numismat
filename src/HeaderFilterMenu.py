from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtSql import QSqlQuery

from Collection.CollectionFields import CollectionFields

class FilterMenuButton(QtGui.QPushButton):
    def __init__(self, column, db, parent):
        super(FilterMenuButton, self).__init__(parent)
        
        self.db = db
        self.column = column
        
        menu = QtGui.QMenu()

        self.setFixedHeight(self.parent().height()-2)
        self.setFixedWidth(self.height())
        self.setMenu(menu)
        
        menu.aboutToShow.connect(self.prepareMenu)

    def prepareMenu(self):
        listWidget = QtGui.QListWidget(self)
        collectionFields = CollectionFields().fields
        sql = "SELECT DISTINCT %s FROM coins" % collectionFields[self.column].name
        query = QSqlQuery(sql, self.db)
        while query.next():
            item = QtGui.QListWidgetItem(str(query.record().value(0)), listWidget)
            item.setCheckState(Qt.Checked)
            listWidget.addItem(item)
        
        buttonBox = QtGui.QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QtGui.QDialogButtonBox.Ok)
        buttonBox.addButton(QtGui.QDialogButtonBox.Cancel)
#            buttonBox.accepted.connect(self.save)
#            buttonBox.rejected.connect(self.reject)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(listWidget)
        layout.addWidget(buttonBox)

        widget = QtGui.QWidget(self)
        widget.setLayout(layout)

        widgetAction = QtGui.QWidgetAction(self)
        widgetAction.setDefaultWidget(widget)
        self.menu().clear()
        self.menu().addAction(widgetAction)
