# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QDate
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QDialogButtonBox

from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator


@storeDlgSizeDecorator
class SummaryDialog(QDialog):

    def __init__(self, model, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.setWindowTitle(self.tr("Summary"))

        buttonBox = QDialogButtonBox(Qt.Horizontal)
        buttonBox.addButton(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)

        self.textBox = QTextEdit(self)
        self.textBox.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.textBox)
        layout.addWidget(buttonBox)

        self.setLayout(layout)

        self.__fillSummary(model)

    def __fillSummary(self, model):
        lines = []

        sql = "SELECT count(*) FROM coins"
        query = QSqlQuery(sql, model.database())
        if query.first():
            totalCount = query.record().value(0)
            lines.append(self.tr("Total count: %d" % totalCount))

        sql = "SELECT count(*) FROM coins WHERE status IN ('owned', 'ordered', 'sale')"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count owned: %d" % count))

        sql = "SELECT count(*) FROM coins WHERE status='wish'"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count wish: %d" % count))

        sql = "SELECT count(*) FROM coins WHERE status='sold')"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count sales: %d" % count))

        paid = 0
        sql = "SELECT SUM(totalpayprice) FROM COINS WHERE status IN ('owned', 'ordered', 'sale', 'sold') AND totalpayprice<>'' AND totalpayprice IS NOT NULL"
        query = QSqlQuery(sql, model.database())
        if query.first():
            paid = query.record().value(0)
            if paid:
                lines.append(self.tr("Paid: %.2f" % paid))

        earned = 0
        sql = "SELECT SUM(totalsaleprice) FROM COINS WHERE status='sold' AND totalsaleprice<>'' AND totalsaleprice IS NOT NULL"
        query = QSqlQuery(sql, model.database())
        if query.first():
            earned = query.record().value(0)
            if earned:
                lines.append(self.tr("Earned: %.2f" % earned))

        if paid and earned:
            total = (paid - earned)
            lines.append(self.tr("Total (paid - earned): %.2f" % total))

        sql = "SELECT paydate FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'sold') AND paydate<>'' AND paydate IS NOT NULL ORDER BY paydate LIMIT 1"
        query = QSqlQuery(sql, model.database())
        if query.first():
            date = QDate.fromString(query.record().value(0), Qt.ISODate)
            paydate = date.toString(Qt.SystemLocaleShortDate)
            lines.append(self.tr("First purchase: %s" % paydate))

        self.textBox.setText('\n'.join(lines))
