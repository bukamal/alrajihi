# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTabWidget, QHeaderView, QMessageBox, QMenu, QAction,
                             QShortcut, QFormLayout, QComboBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from i18n import translate, qt_layout_direction
from PyQt5.QtGui import QKeySequence
from views.centered_dialog import CenteredDialog
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from core.services.manufacturing_service import manufacturing_service
from core.services.product_service import product_service
from currency import currency
from utils import show_toast
from views.widgets.modern_ui import apply_modern_dialog
from auth import can_manage_production, can_reverse_production
from decimal import Decimal

def _num(value, default=0):
    try:
        if value is None or value == '':
            return float(default)
        return float(Decimal(str(value)))
    except Exception:
        return float(default)


def _item_label(row, fallback_prefix=None):
    name = (row.get('item_name') or row.get('product_name') or row.get('name') or '').strip()
    if name:
        return name
    item_id = row.get('item_id') or row.get('product_id') or row.get('id')
    return translate('material_id_fallback', id=item_id) if item_id else '-'


class ProductionDetailsDialog(CenteredDialog):
    def __init__(self, parent, order_id):
        super().__init__(parent)
        self.order_id = order_id
        self.service = manufacturing_service
        self.setWindowTitle(translate("production_details"))
        self.resize(850, 700)

        order = self.service.get_production_order(order_id)
        if not order:
            show_toast(translate("production_order_not_found"), "error", self)
            self.reject()
            return

        layout = QVBoxLayout(self.content_widget)
        status_map = {'planned': translate('status_planned'), 'in_progress': translate('status_in_progress'), 'completed': translate('status_completed'), 'cancelled': translate('status_cancelled')}
        info = QLabel(f"""
            <b>{translate('order_number_label')}</b> {order.get('order_number', '')}<br>
            <b>{translate('product_label')}</b> {order.get('product_name', '')}<br>
            <b>{translate('planned_quantity_label')}</b> {order.get('planned_qty', 0)}<br>
            <b>{translate('produced_quantity_label')}</b> {order.get('produced_qty', 0)}<br>
            <b>{translate('status_label')}</b> {status_map.get(order.get('status', 'planned'), translate('status_planned'))}<br>
            <b>{translate('raw_warehouse_long_label')}</b> {order.get('raw_warehouse_name') or '-'}<br>
            <b>{translate('output_warehouse_long_label')}</b> {order.get('output_warehouse_name') or '-'}<br>
            <b>{translate('start_date_label')}</b> {order.get('start_date', '-')}<br>
            <b>{translate('notes_label')}</b> {order.get('notes', '')}
        """)
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        if can_manage_production():
            if order.get('status') == 'planned':
                start_btn = QPushButton(translate("start_production"))
                start_btn.clicked.connect(self.start_production)
                btn_layout.addWidget(start_btn)
                cancel_order_btn = QPushButton(translate("cancel_order"))
                cancel_order_btn.clicked.connect(self.cancel_production)
                btn_layout.addWidget(cancel_order_btn)
            elif order.get('status') == 'in_progress':
                consume_btn = QPushButton(translate("consume_materials"))
                consume_btn.clicked.connect(self.add_consumption)
                complete_btn = QPushButton(translate("complete_production"))
                complete_btn.clicked.connect(self.complete_production)
                btn_layout.addWidget(consume_btn)
                btn_layout.addWidget(complete_btn)
        if can_reverse_production() and order.get('status') in ('in_progress', 'completed'):
            reverse_btn = QPushButton(translate("reverse_production"))
            reverse_btn.setObjectName("danger")
            reverse_btn.clicked.connect(self.reverse_production)
            btn_layout.addWidget(reverse_btn)

        print_btn = QPushButton(translate("print"))
        print_btn.clicked.connect(lambda: self.print_order('print'))
        btn_layout.addWidget(print_btn)

        close_btn = QPushButton(translate("close"))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        tabs = QTabWidget()
        # تبويب المواد المستهلكة
        self.cons_table = SmartTableView(identity='production_details.consumption')
        self.cons_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cons_table.customContextMenuRequested.connect(self.show_cons_menu)
        tabs.addTab(self.cons_table, translate("consumed_materials"))
        # تبويب المنتج النهائي
        self.out_table = SmartTableView(identity='production_details.output')
        self.out_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.out_table.customContextMenuRequested.connect(self.show_out_menu)
        tabs.addTab(self.out_table, translate("finished_product_group"))
        # تبويب الحجوزات (يظهر فقط للأوامر المخطط لها أو قيد التنفيذ)
        if order.get('status') in ('planned', 'in_progress'):
            self.res_table = SmartTableView(identity='production_details.residuals')
            tabs.addTab(self.res_table, translate("reservations_remaining"))
        layout.addWidget(tabs)

        apply_modern_dialog(self, translate('production_details'))
        self.refresh_consumptions()
        self.refresh_outputs()
        if order.get('status') in ('planned', 'in_progress'):
            self.refresh_reservations()

    def refresh_consumptions(self):
        cons = self.service.get_consumptions(self.order_id)
        data = []
        for c in cons:
            data.append({
                'id': c['id'],
                'item': _item_label(c),
                'quantity': f"{_num(c.get('consumed_qty')):.2f}",
                'cost': currency.format_amount(currency.convert(_num(c.get('unit_cost')), currency.storage_currency(), currency.get_display_currency())),
                'date': c.get('movement_date', '')
            })
        headers = ['item', 'quantity', 'cost', 'date']
        display_headers = [translate('item_header'), translate('quantity'), translate('unit_price'), translate('date')]
        model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.cons_table.setModel(model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
        self.cons_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cons_table.refresh_style()

    def refresh_outputs(self):
        outs = self.service.get_outputs(self.order_id)
        data = []
        for o in outs:
            data.append({
                'id': o['id'],
                'item': _item_label(o),
                'quantity': f"{_num(o.get('produced_qty')):.2f}",
                'cost': currency.format_amount(currency.convert(_num(o.get('unit_cost')), currency.storage_currency(), currency.get_display_currency())),
                'date': o.get('output_date', '')
            })
        headers = ['item', 'quantity', 'cost', 'date']
        display_headers = [translate('product'), translate('quantity'), translate('unit_price'), translate('date')]
        model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.out_table.setModel(model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
        self.out_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.out_table.refresh_style()

    def refresh_reservations(self):
        reservations = self.service.get_reservations(self.order_id)
        data = []
        for r in reservations:
            reserved = _num(r.get('reserved_qty'))
            consumed = _num(r.get('consumed_qty'))
            remaining = reserved - consumed
            data.append({
                'id': r['id'],
                'item': _item_label(r),
                'reserved': f"{reserved:.2f}",
                'consumed': f"{consumed:.2f}",
                'remaining': f"{remaining:.2f}"
            })
        headers = ['item', 'reserved', 'consumed', 'remaining']
        display_headers = [translate('item_header'), translate('reserved'), translate('consumed'), translate('remaining')]
        model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.res_table.setModel(model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.res_table.refresh_style()

    def _print_payload(self):
        return {
            'order': self.service.get_production_order(self.order_id) or {},
            'consumptions': self.service.get_consumptions(self.order_id) or [],
            'outputs': self.service.get_outputs(self.order_id) or [],
            'reservations': self.service.get_reservations(self.order_id) or [],
        }

    def print_order(self, mode='preview'):
        from printing.printing_service import printing_service
        data = self._print_payload()
        # Phase 236: legacy production dialog print button follows project print settings.
        printing_service.production_print(data, self)

    def start_production(self):
        success, msg = self.service.start_production(self.order_id)
        if success:
            show_toast(translate("production_started"), "success", self)
            self.accept()
        else:
            QMessageBox.critical(self, translate("error"), msg)

    def cancel_production(self):
        reply = QMessageBox.question(self, translate("confirm_delete"), translate("confirm_cancel_production"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.service.cancel_production(self.order_id)
            show_toast(translate("production_cancelled"), "success", self)
            self.accept()

    def add_consumption(self):
        order = self.service.get_production_order(self.order_id)
        if not order:
            return
        # جلب الحجوزات لعرض المواد التي لم تستهلك بالكامل
        reservations = self.service.get_reservations(self.order_id)
        remaining_items = {}
        for r in reservations:
            reserved = _num(r.get('reserved_qty'))
            consumed = _num(r.get('consumed_qty'))
            remaining = reserved - consumed
            if remaining > 0:
                remaining_items[r['item_id']] = {
                    'name': _item_label(r),
                    'remaining': remaining,
                    'unit_cost': 0
                }
        if not remaining_items:
            show_toast(translate("all_materials_consumed"), "info", self)
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(translate("consume_materials"))
        dlg.setLayoutDirection(qt_layout_direction())
        dlg.resize(500, 400)
        layout = QFormLayout(dlg)
        item_combo = QComboBox()
        for item_id, data in remaining_items.items():
            item_combo.addItem(data['name'] + translate("material_remaining_suffix", remaining=data['remaining']), item_id)
        layout.addRow(translate("material_label"), item_combo)
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.01, 999999)
        qty_spin.setValue(1)
        layout.addRow(translate("consumed_quantity_label"), qty_spin)
        def update_max():
            item_id = item_combo.currentData()
            if item_id in remaining_items:
                max_qty = _num(remaining_items[item_id].get('remaining'))
                qty_spin.setMaximum(max_qty)
                qty_spin.setValue(min(qty_spin.value(), max_qty))
        item_combo.currentIndexChanged.connect(update_max)
        update_max()
        cost_spin = QDoubleSpinBox()
        cost_spin.setRange(0, 999999)
        cost_spin.setDecimals(2)
        cost_spin.setPrefix(f"{currency.get_currency_symbol()} ")
        layout.addRow(translate("unit_price_label"), cost_spin)
        def update_cost():
            item_id = item_combo.currentData()
            if item_id:
                it = product_service.item_by_id(item_id)
                if it:
                    average_cost = _num(it.get('average_cost'), 0)
                    purchase_price = _num(it.get('purchase_price'), 0)
                    price = average_cost if average_cost > 0 else purchase_price
                    price_display = currency.convert(price, currency.storage_currency(), currency.get_display_currency())
                    cost_spin.setValue(_num(price_display, 0))
        item_combo.currentIndexChanged.connect(update_cost)
        update_cost()
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(translate("register"))
        cancel_btn = QPushButton(translate("cancel"))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        def do_consume():
            item_id = item_combo.currentData()
            qty = qty_spin.value()
            cost_display = cost_spin.value()
            cost_usd = currency.convert(cost_display, currency.get_display_currency(), currency.storage_currency())
            success, msg = self.service.consume_material(self.order_id, item_id, qty, cost_usd)
            if success:
                show_toast(translate("consumption_registered"), "success", dlg)
                dlg.accept()
                self.refresh_consumptions()
                self.refresh_reservations()
            else:
                QMessageBox.critical(dlg, translate("error"), msg)
        save_btn.clicked.connect(do_consume)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()

    def complete_production(self):
        order = self.service.get_production_order(self.order_id)
        if not order:
            return
        # حساب أقصى كمية يمكن إنتاجها من الاستهلاكات المسجلة
        reservations = self.service.get_reservations(self.order_id)
        max_producible = None
        for r in reservations:
            reserved = _num(r.get('reserved_qty'))
            consumed = _num(r.get('consumed_qty'))
            remaining = reserved - consumed
            # المطلوب استهلاكه بالكامل، لذا إذا بقي شيء لا يمكن إتمام الإنتاج
            if remaining > 0.001:
                QMessageBox.warning(self, translate("missing_consumption_title"), translate("missing_consumption_msg", item=_item_label(r), remaining=remaining))
                return
            # يمكننا أيضاً حساب الكمية القصوى بناءً على أقل نسبة (لكن بما أن الاستهلاك كامل، كل شيء جيد)
        # السماح بإنتاج الكمية المخططة فقط (أو أقل إذا كان هناك قيود أخرى)
        max_producible = _num(order.get('planned_qty')) - _num(order.get('produced_qty', 0))
        if max_producible <= 0:
            QMessageBox.warning(self, translate("warning"), translate("planned_quantity_completed"))
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(translate("complete_production"))
        dlg.setLayoutDirection(qt_layout_direction())
        dlg.resize(450, 250)
        layout = QFormLayout(dlg)
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.01, float(max_producible))
        qty_spin.setValue(float(max_producible))
        layout.addRow(translate("actual_produced_quantity"), qty_spin)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(translate("complete"))
        cancel_btn = QPushButton(translate("cancel"))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        def do_complete():
            success, msg = self.service.complete_production(self.order_id, qty_spin.value())
            if success:
                show_toast(translate("production_completed"), "success", dlg)
                dlg.accept()
                self.accept()
            else:
                QMessageBox.critical(dlg, translate("error"), msg)
        save_btn.clicked.connect(do_complete)
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()

    def reverse_production(self):
        reply = QMessageBox.question(self, translate("confirm_reverse_title"), translate("confirm_reverse_production"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, msg = self.service.reverse_production_order(self.order_id)
            if success:
                show_toast(msg, "success", self)
                self.accept()
            else:
                QMessageBox.critical(self, translate("error"), msg)

    def show_cons_menu(self, pos):
        index = self.cons_table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        cons_id = self.cons_table.model().get_id(row)
        if not cons_id:
            return
        menu = QMenu()
        delete_action = QAction(translate("delete_consumption"), self)
        delete_action.triggered.connect(lambda: self.delete_consumption(cons_id))
        menu.addAction(delete_action)
        menu.exec(self.cons_table.viewport().mapToGlobal(pos))

    def show_out_menu(self, pos):
        index = self.out_table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        out_id = self.out_table.model().get_id(row)
        if not out_id:
            return
        menu = QMenu()
        delete_action = QAction(translate("delete_output"), self)
        delete_action.triggered.connect(lambda: self.delete_output(out_id))
        menu.addAction(delete_action)
        menu.exec(self.out_table.viewport().mapToGlobal(pos))

    def delete_consumption(self, cons_id):
        reply = QMessageBox.question(self, translate("confirm_delete"), translate("confirm_delete_consumption"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, msg = self.service.delete_consumption(cons_id)
            if success:
                show_toast(translate("consumption_deleted"), "success", self)
                self.refresh_consumptions()
                self.refresh_reservations()
            else:
                QMessageBox.critical(self, translate("error"), msg)

    def delete_output(self, out_id):
        reply = QMessageBox.question(self, translate("confirm_delete"), translate("confirm_delete_output"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, msg = self.service.delete_output(out_id)
            if success:
                show_toast(translate("output_deleted"), "success", self)
                self.refresh_outputs()
            else:
                QMessageBox.critical(self, translate("error"), msg)


