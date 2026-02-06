# -*- coding: utf-8 -*-

from PySide6.QtCore import Qt, QDate, QLocale
from PySide6.QtSql import QSqlQuery
from PySide6.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QDialogButtonBox

from OpenNumismat.Tools.DialogDecorators import storeDlgSizeDecorator
from OpenNumismat.Tools.Converters import stringToMoney


@storeDlgSizeDecorator
class SummaryDialog(QDialog):

    def __init__(self, model, parent=None):
        super().__init__(parent,
                         Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint)

        self.locale = QLocale.system()

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

        lines_all = self.fillSummary(model)
        lines_selected = self.fillSummary(model, model.filter())

        lines = [self.tr("[Selected]")] + lines_selected + ["", self.tr("[All]")] + lines_all
        self.textBox.setText('\n'.join(lines))

    def makeSql(self, sql, filter_):
        if filter_:
            if 'WHERE' in sql:
                sql = "%s AND %s" % (sql, filter_)
            else:
                sql = "%s WHERE %s" % (sql, filter_)

        return sql

    def fillSummary(self, model, filter_=None):
        lines = []

        sql = "SELECT count(*) FROM coins"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            totalCount = query.record().value(0)
            lines.append(self.tr("Total count: %d") % totalCount)

        count_owned = 0
        quantity_owned = 0
        sql = "SELECT quantity FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'duplicate', 'replacement')"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        while query.next():
            quantity = query.record().value('quantity')
            if not isinstance(quantity, int):
                quantity = 1
            quantity_owned += quantity
            count_owned += 1
        if count_owned == quantity_owned:
            lines.append(self.tr("Count owned: %d") % count_owned)
        else:
            lines.append(self.tr("Count owned: %d/%d") % (quantity_owned, count_owned))

        material_lines = self.fillMaterial('gold', model, filter_)
        lines.extend(material_lines)
        material_lines = self.fillMaterial('silver', model, filter_)
        lines.extend(material_lines)
        material_lines = self.fillMaterial('platinum', model, filter_)
        lines.extend(material_lines)
        material_lines = self.fillMaterial('palladium', model, filter_)
        lines.extend(material_lines)

        sql = "SELECT count(*) FROM coins WHERE status='wish'"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count wish: %d") % count)

        count_sold = 0
        sql = "SELECT count(*) FROM coins WHERE status='sold'"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            count_sold = query.record().value(0)
            if count_sold > 0:
                lines.append(self.tr("Count sales: %d") % count_sold)

        sql = "SELECT count(*) FROM coins WHERE status='bidding'"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            if count > 0:
                lines.append(self.tr("Count biddings: %d") % count)

        sql = "SELECT count(*) FROM coins WHERE status='missing'"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            if count > 0:
                lines.append(self.tr("Count missing: %d") % count)

        paid = 0
        commission = ""
        sql = "SELECT SUM(totalpayprice) FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'sold', 'missing', 'duplicate', 'replacement') AND totalpayprice<>'' AND totalpayprice IS NOT NULL"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            paid = query.record().value(0)
            if paid:
                sql = "SELECT SUM(payprice) FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'sold', 'missing', 'duplicate', 'replacement') AND payprice<>'' AND payprice IS NOT NULL"
                sql = self.makeSql(sql, filter_)
                query = QSqlQuery(sql, model.database())
                if query.first():
                    paid_without_commission = query.record().value(0)
                    if paid_without_commission:
                        commission = self.tr("(commission %d%%)") % ((paid - paid_without_commission) / paid_without_commission * 100)
                paid_str = self.locale.toString(float(paid), 'f', precision=2)
                lines.append(' '.join((self.tr("Paid: %s") % paid_str, commission)))

                if count_owned:
                    val = paid / count_owned
                    val_str = self.locale.toString(float(val), 'f', precision=2)
                    lines.append(self.tr("Average paid per item: %s") % val_str)

        earned = 0
        commission = ""
        sql = "SELECT SUM(totalsaleprice) FROM coins WHERE status='sold' AND totalsaleprice<>'' AND totalsaleprice IS NOT NULL"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            earned = query.record().value(0)
            if earned:
                sql = "SELECT SUM(saleprice) FROM coins WHERE status='sold' AND saleprice<>'' AND saleprice IS NOT NULL"
                sql = self.makeSql(sql, filter_)
                query = QSqlQuery(sql, model.database())
                if query.first():
                    earn_without_commission = query.record().value(0)
                    if earn_without_commission:
                        commission = self.tr("(commission %d%%)") % ((earn_without_commission - earned) / earn_without_commission * 100)
                earned_str = self.locale.toString(float(earned), 'f', precision=2)
                lines.append(' '.join((self.tr("Earned: %s") % earned_str, commission)))

                if count_sold:
                    val = earned / count_sold
                    val_str = self.locale.toString(float(val), 'f', precision=2)
                    lines.append(self.tr("Average earn per item: %s") % val_str)

        if paid and earned:
            total = paid - earned
            total_str = self.locale.toString(float(total), 'f', precision=2)
            lines.append(self.tr("Total (paid - earned): %s") % total_str)

        sql = "SELECT paydate FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'sold', 'missing', 'duplicate', 'replacement') AND paydate<>'' AND paydate IS NOT NULL ORDER BY paydate LIMIT 1"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            date = QDate.fromString(query.record().value(0), Qt.ISODate)
            paydate = self.locale.toString(date, QLocale.ShortFormat)
            lines.append(self.tr("First purchase: %s") % paydate)

        sql = "SELECT UPPER(grade), price1, price2, price3, price4, quantity FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'duplicate', 'replacement') AND (ifnull(price1,'')<>'' OR ifnull(price2,'')<>'' OR ifnull(price3,'')<>'' OR ifnull(price4,'')<>'')"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        est_owned = 0
        count = 0
        coins_quantity = 0
        comment = ""
        while query.next():
            record = query.record()
            grade = record.value(0)
            price1 = record.value(1)
            price2 = record.value(2)
            price3 = record.value(3)
            price4 = record.value(4)
            quantity = int(record.value(5) or 1)

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
                    est_owned += price * quantity
                    count += 1
                    coins_quantity += quantity

            except TypeError:
                continue

        if count:
            if count == coins_quantity:
                comment = self.tr("(calculated for %d coins)") % count
            else:
                comment = self.tr("(calculated for %d/%d coins)") % (coins_quantity, count)

        lines.append(' '.join((self.tr("Estimation owned: %d") % est_owned, comment)))

        sql = "SELECT price1, price2, price3, price4 FROM coins WHERE status='wish' AND (ifnull(price1,'')<>'' OR ifnull(price2,'')<>'' OR ifnull(price3,'')<>'' OR ifnull(price4,'')<>'')"
        sql = self.makeSql(sql, filter_)
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

        sql = "SELECT count(*) FROM photos"
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        if query.first():
            count = query.record().value(0)
            lines.append(self.tr("Count images: %d") % count)

        return lines

    def fillMaterial(self, material, model, filter_):
        lines = []

        materials = {
            'gold': ("Gold", self.tr("Gold"), "Au", "Aurum"),
            'silver': ("Silver", self.tr("Silver"), "Ag", "Argentum"),
            'platinum': ("Platinum", self.tr("Platinum"), "Pt"),
            'palladium': ("Palladium", self.tr("Palladium"), "Pd"),
        }
        titles = {
            'gold': (self.tr("Gold coins"), self.tr("Gold weight")),
            'silver': (self.tr("Silver coins"), self.tr("Silver weight")),
            'platinum': (self.tr("Platinum coins"), self.tr("Platinum weight")),
            'palladium': (self.tr("Palladium coins"), self.tr("Palladium weight")),
        }

        material_count, material_quantity = self.materialCount(
                materials[material], model, filter_)
        if material_count:
            if material_count == material_quantity:
                lines.append(f"{titles[material][0]}: {material_count}")
            else:
                lines.append(f"{titles[material][0]}: {material_quantity}/{material_count}")

            weight, weight_count, weight_quantity = self.materialWeight(
                materials[material], model, filter_)
            if weight:
                if weight_count == weight_quantity:
                    comment = self.tr("calculated for %d coins") % weight_quantity
                else:
                    comment = self.tr("calculated for %d/%d coins") % (weight_quantity, weight_count)
                weight_str = self.locale.toString(float(weight), 'f', precision=2)

                lines.append(f"{titles[material][1]}: {weight_str} {self.tr('gram')} ({comment})")

        return lines

    def materialFilter(self, *materials):
        filters = []
        for material in materials:
            for material_variant in (material.lower(), material.upper(), material.capitalize()):
                filters.append("'%s'" % material_variant)

        return 'material IN (%s)' % ','.join(filters)

    def materialCount(self, materials, model, filter_):
        material_count = 0
        material_quantity = 0
        material_filter = self.materialFilter(*materials)
        sql = "SELECT quantity FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'duplicate', 'replacement') AND " \
                "%s" % material_filter
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        while query.next():
            record = query.record()
            quantity = int(record.value('quantity') or 1)
            material_count += 1
            material_quantity += quantity

        return material_count, material_quantity

    def materialWeight(self, materials, model, filter_):
        material_filter = self.materialFilter(*materials)
        sql = "SELECT fineness, weight, quantity FROM coins WHERE status IN ('owned', 'ordered', 'sale', 'duplicate', 'replacement') AND " \
                "%s AND " \
                "ifnull(fineness,'')<>'' AND ifnull(weight,'')<>''" % material_filter
        sql = self.makeSql(sql, filter_)
        query = QSqlQuery(sql, model.database())
        material_weight = 0
        material_count = 0
        material_quantity = 0
        while query.next():
            record = query.record()
            fineness = record.value('fineness')
            if isinstance(fineness, str):
                fineness = stringToMoney(fineness)
            if isinstance(fineness, float):
                if fineness > 1:
                    fineness = str(fineness).replace('.', '')
                else:
                    fineness = str(fineness).replace('0.', '')
            weight = record.value('weight')
            if isinstance(weight, str):
                weight = stringToMoney(weight)
            quantity = int(record.value('quantity') or 1)
            material_weight += weight * float("0.%s" % fineness) * quantity
            material_count += 1
            material_quantity += quantity

        return material_weight, material_count, material_quantity
