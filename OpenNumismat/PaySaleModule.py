# -*- coding: utf-8 -*-
import datetime

# import dateutil.parser
from PySide6.QtCore import Qt
from PySide6.QtSql import QSqlQueryModel, QSqlQuery
# from PySide6.QtWidgets import *
from OpenNumismat.EditCoinDialog.FormItems import *


class PaySaleForm(QDialog):
    def __init__(self, uid, places, rec=None):
        super().__init__()

        self.uid = uid
        self.rec = rec
        self.fld_date = None
        self.fld_act = None
        self.fld_cost = None
        self.fld_quant = None
        self.fld_place = None
        self.fld_actor = None

        self.setWindowTitle("Операция покупки/продажи")
        qbtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(qbtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QGridLayout()

        lbl = QLabel("Дата")
        self.layout.addWidget(lbl, 0, 0)
        self.fld_date = DateEdit()
        self.layout.addWidget(self.fld_date, 0, 1)

        lbl = QLabel("Действие")
        self.layout.addWidget(lbl, 1, 0)
        self.fld_act = QComboBox()
        self.fld_act.addItems(["Купил", "Продал"])
        self.layout.addWidget(self.fld_act, 1, 1)

        lbl = QLabel("Цена")
        self.layout.addWidget(lbl, 2, 0)
        self.fld_cost = MoneyEdit()
        self.layout.addWidget(self.fld_cost, 2, 1)

        lbl = QLabel("Количество")
        self.layout.addWidget(lbl, 3, 0)
        self.fld_quant = BigIntEdit()
        self.layout.addWidget(self.fld_quant, 3, 1)

        lbl = QLabel("Место")
        self.layout.addWidget(lbl, 4, 0)
        self.fld_place = LineEditRef(reference=places)
        self.layout.addWidget(self.fld_place, 4, 1)

        lbl = QLabel("Продавец")
        self.layout.addWidget(lbl, 5, 0)
        self.fld_actor = TextEdit()
        self.layout.addWidget(self.fld_actor, 5, 1)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        if self.rec:
            # self.fld_date.setDate(dateutil.parser.parse(str(rec[2])))
            self.fld_date.setDate(datetime.datetime.strptime(str(rec[2]), "%d.%m.%Y"))
            _act = self.fld_act.findText(str(rec[3]))
            if _act != -1:
                self.fld_act.setCurrentIndex(_act)
            self.fld_cost.setText(str(rec[4]))
            self.fld_quant.setText(str(rec[5]))
            _place = self.fld_place.comboBox.findText(str(rec[6]))
            if _place != -1:
                self.fld_place.comboBox.setCurrentIndex(_place)
            self.fld_actor.setText(str(rec[7]))
        else:
            self.fld_date.setDate(datetime.date.today())

    def accept(self):
        # print(self.fld_date.text(), self.fld_act.itemText(self.fld_act.currentIndex()), self.fld_cost.text(),
        #       self.fld_quant.text(), self.fld_place.itemText(self.fld_place.currentIndex()),
        #       self.fld_actor.itemText(self.fld_actor.currentIndex()))
        # update
        if self.rec:
            query = QSqlQuery()
            query.prepare("""update coins_paysales set 
                             oper_date=?,
                             oper_name=?,
                             cost=?,
                             quantity=?,
                             place=?,
                             oper_actor=?
                             where id = ?""")
            query.addBindValue(self.fld_date.text())
            query.addBindValue(self.fld_act.itemText(self.fld_act.currentIndex()))

            query.addBindValue(self.fld_cost.text())
            query.addBindValue(self.fld_quant.text())
            query.addBindValue(self.fld_place.text())

            query.addBindValue(self.fld_actor.text())
            query.addBindValue(self.rec[0])
            query.exec_()
        # insert
        else:
            query = QSqlQuery()
            query.prepare("""insert into coins_paysales(coin_id,oper_date,oper_name,cost,quantity,place,oper_actor)
                             values(?, ?, ?, ?, ?, ?, ?)""")
            query.addBindValue(self.uid)
            query.addBindValue(self.fld_date.text())
            query.addBindValue(self.fld_act.itemText(self.fld_act.currentIndex()))

            query.addBindValue(self.fld_cost.text())
            query.addBindValue(self.fld_quant.text())
            query.addBindValue(self.fld_place.text())

            query.addBindValue(self.fld_actor.text())
            query.exec_()

        super().accept()

    def reject(self):
        #
        super().reject()


class PaySaleLayout(QGroupBox):
    def __init__(self, title, uid, places, _ftype, _tq, _ts):
        super().__init__(title)

        self.uid = uid
        self.tq = _tq
        self.ts = _ts
        self.places = places
        self.sel_query = ("select * from coins_paysales where coin_id = %s order by cast(substr(oper_date, 7,4)||substr(oper_date, 4,2)||substr(oper_date, 1,2) as int) desc" % uid)
        self.tbl_view = None
        self.model = None

        self.setModel(self.sel_query)
        self.setTblViewLayout()
        lay = QVBoxLayout()
        if _ftype == "DetailsTabWidget":
            pass
        else:
            lay.addLayout(self.setBtnLineLayout())
        lay.addWidget(self.tbl_view)
        self.setLayout(lay)

    def setBtnLineLayout(self):
        add_btn = QPushButton(self.tr("Добавить"))
        add_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        add_btn.clicked.connect(self.addPaySaleForm)

        upd_btn = QPushButton(self.tr("Изменить"))
        upd_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        upd_btn.clicked.connect(self.updPaySaleForm)

        del_btn = QPushButton(self.tr("Удалить"))
        del_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        del_btn.clicked.connect(self.delPaySale)

        sp_item = QSpacerItem(1, 1, QSizePolicy.Expanding, QSizePolicy.Fixed)

        btn_line = QHBoxLayout()
        btn_line.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_line.addWidget(upd_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_line.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        btn_line.addSpacerItem(sp_item)

        return btn_line

    def setTblViewLayout(self):
        self.tbl_view = QTableView()
        self.tbl_view.setModel(self.model)
        self.tbl_view.hideColumn(0)
        self.tbl_view.hideColumn(1)
        self.tbl_view.verticalHeader().setVisible(False)
        self.tbl_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.tbl_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tbl_view.horizontalHeader().setStretchLastSection(True)
        self.tbl_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_view.setSelectionMode(QAbstractItemView.SingleSelection)

    def setModel(self, query):
        self.model = QSqlQueryModel()
        self.model.setQuery(query)
        self.model.setHeaderData(2, Qt.Orientation.Horizontal, "Дата")
        self.model.setHeaderData(3, Qt.Orientation.Horizontal, "Действие")
        self.model.setHeaderData(4, Qt.Orientation.Horizontal, "Цена")
        self.model.setHeaderData(5, Qt.Orientation.Horizontal, "Количество")
        self.model.setHeaderData(6, Qt.Orientation.Horizontal, "Место")
        self.model.setHeaderData(7, Qt.Orientation.Horizontal, "Продавец")

    def delPaySale(self):
        rowList = self.tbl_view.selectionModel().selectedRows()
        _idx = None
        if rowList.__len__() > 0:
            _idx = rowList[0].row()
        _t = None
        if _idx is not None:
            _id = self.model.index(_idx, 0).data()
            query = QSqlQuery()
            query.prepare("""delete from coins_paysales where id = ?""")
            query.addBindValue(_id)
            query.exec_()
            self.refreshTable()
        else:
            self.showWarn()

    def addPaySaleForm(self):
        self.showPaySaleForm()

    def updPaySaleForm(self):
        rowList = self.tbl_view.selectionModel().selectedRows()
        _idx = None
        if rowList.__len__() > 0:
            _idx = rowList[0].row()
        _t = None
        if _idx is not None:
            _t = (
                self.model.index(_idx, 0).data(),
                self.model.index(_idx, 1).data(),
                self.model.index(_idx, 2).data(),
                self.model.index(_idx, 3).data(),
                self.model.index(_idx, 4).data(),
                self.model.index(_idx, 5).data(),
                self.model.index(_idx, 6).data(),
                self.model.index(_idx, 7).data()
            )
            self.showPaySaleForm(_t)
        else:
            self.showWarn()

    def showWarn(self):
        warn = QMessageBox()
        warn.setWindowTitle("Предупреждение")
        warn.setText("Строка не выбрана!")
        warn.exec()

    def refreshTable(self):
        self.tbl_view.model().setQuery(self.sel_query)
        self.calcTotal()

    def calcTotal(self):
        query = QSqlQuery()
        query.prepare("""select coin_id,
                        round(sum(cost*quantity*(case oper_name when 'Продал' then 1 else -1 end)),2) as ts,
                        sum(quantity*(case oper_name when 'Продал' then -1 else 1 end)) as tq
                        from coins_paysales
                        where coin_id = ?
                        group by coin_id""")
        query.addBindValue(self.uid)
        query.exec_()
        ts = tq = 0
        while query.next():
            record = query.record()
            ts = record.value('ts')
            tq = record.value('tq')

        query = QSqlQuery()
        query.prepare("""update coins set quantity=?, totalsum=? where id=?""")
        query.addBindValue(tq)
        query.addBindValue(ts)
        query.addBindValue(self.uid)
        query.exec_()

        self.tq.widget().setText(str(tq))
        self.ts.widget().setText(str(ts))

    def showPaySaleForm(self, rec=None):
        ps_form = PaySaleForm(self.uid, self.places, rec)
        if ps_form.exec():
            self.refreshTable()
            # __t = ps_form
            # print("ok", rec)
            pass
        else:
            # print("cancel")
            pass
