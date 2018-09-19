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

        layout = QVBoxLayout()
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
            lines.append(self.tr("Total count: %d") % totalCount)

        sql = "SELECT count(*) FROM coins WHERE status IN ('owned', 'ordered', 'sale')"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count owned: %d") % count)

        sql = "SELECT count(*) FROM coins WHERE status='wish'"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count wish: %d") % count)

        sql = "SELECT count(*) FROM coins WHERE status='sold'"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            if count > 0:
                lines.append(self.tr("Count sales: %d") % count)

        sql = "SELECT count(*) FROM coins WHERE status='bidding'"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            if count > 0:
                lines.append(self.tr("Count biddings: %d") % count)

        sql = "SELECT count(*) FROM coins WHERE status='missing'"
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            if count > 0:
                lines.append(self.tr("Count missing: %d") % count)

        paid = 0
        sql = "SELECT SUM(totalpayprice) FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'sold', 'missing') AND totalpayprice<>'' AND totalpayprice IS NOT NULL"
        query = QSqlQuery(sql, model.database())
        if query.first():
            paid = query.record().value(0)
            if paid:
                lines.append(self.tr("Paid: %.2f") % paid)

        earned = 0
        sql = "SELECT SUM(totalsaleprice) FROM coins WHERE status='sold' AND totalsaleprice<>'' AND totalsaleprice IS NOT NULL"
        query = QSqlQuery(sql, model.database())
        if query.first():
            earned = query.record().value(0)
            if earned:
                lines.append(self.tr("Earned: %.2f") % earned)

        if paid and earned:
            total = (paid - earned)
            lines.append(self.tr("Total (paid - earned): %.2f") % total)

        sql = "SELECT paydate FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'sold', 'missing') AND paydate<>'' AND paydate IS NOT NULL ORDER BY paydate LIMIT 1"
        query = QSqlQuery(sql, model.database())
        if query.first():
            date = QDate.fromString(query.record().value(0), Qt.ISODate)
            paydate = date.toString(Qt.SystemLocaleShortDate)
            lines.append(self.tr("First purchase: %s") % paydate)

        sql = "SELECT UPPER(grade), price1, price2, price3, price4 FROM coins WHERE status IN ('owned', 'ordered', 'sale') AND (ifnull(price1,'')<>'' OR ifnull(price2,'')<>'' OR ifnull(price3,'')<>'' OR ifnull(price4,'')<>'')"
        query = QSqlQuery(sql, model.database())
        est_owned = 0
        count = 0
        comment = ""
        while query.next():
            record = query.record()
            grade = record.value(0)
            price1 = record.value(1)
            price2 = record.value(2)
            price3 = record.value(3)
            price4 = record.value(4)

            try:
                if grade[:2] in ('UN', 'MS'):
                    price = price4 if price4 else price3 * 1.6 if price3 else price2 * 2.2 if price2 else price1 * 5.5 if price1 else 0
                elif grade[:2] in ('XF', 'EF'):
                    price = price3 if price3 else price4 * 0.6 if price4 else price2 * 1.4 if price2 else price1 * 3.5 if price1 else 0
                elif grade[:2] in ('AU',):
                    priceU = price4 if price4 else price3 * 1.6 if price3 else price2 * 2.2 if price2 else price1 * 5.5 if price1 else 0
                    priceX = price3 if price3 else price4 * 0.6 if price4 else price2 * 1.4 if price2 else price1 * 3.5 if price1 else 0
                    price = priceX + (priceU - priceX) * 0.6
                elif grade[:2] in ('VF',):
                    price = price2 if price2 else price3 * 0.7 if price3 else price4 * 0.45 if price4 else price1 * 2.5 if price1 else 0
                elif grade[:2] in ('F', 'FI'):
                    price = price1 if price1 else price2 * 0.4 if price2 else price3 * 0.3 if price3 else price4 * 0.18 if price4 else 0
                elif grade[:2] in ('VG',):
                    price = price1 * 0.5 if price1 else price2 * 0.2 if price2 else price3 * 0.14 if price3 else price4 * 0.09 if price4 else 0
                else:
                    price = price4 if price4 else price3 if price3 else price2 if price2 else price1 if price1 else 0

                if price:
                    est_owned += price
                    count += 1

            except TypeError:
                continue

        if count:
            comment = self.tr("(calculated for %d coins)") % count

        lines.append(' '.join((self.tr("Estimation owned: %d") % est_owned, comment)))

        sql = "SELECT price1, price2, price3, price4 FROM coins WHERE status='wish' AND (ifnull(price1,'')<>'' OR ifnull(price2,'')<>'' OR ifnull(price3,'')<>'' OR ifnull(price4,'')<>'')"
        query = QSqlQuery(sql, model.database())
        est_wish = 0
        count = 0
        comment = ""
        while query.next():
            record = query.record()
            price1 = record.value(0)
            price2 = record.value(1)
            price3 = record.value(2)
            price4 = record.value(3)

            price = price4 if price4 else price3 if price3 else price2 if price2 else price1 if price1 else 0

            try:
                if price:
                    est_wish += price
                    count += 1
            except TypeError:
                continue

        if count:
            comment = self.tr("(calculated for %d coins)") % count

        lines.append(' '.join((self.tr("Estimation wish: %d") % est_wish, comment)))

        self.textBox.setText('\n'.join(lines))
