# -*- coding: utf-8 -*-
from decimal import Decimal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTableView,
    QTabWidget, QDialog, QFormLayout, QCheckBox, QTextEdit, QMessageBox, QComboBox,
    QHeaderView, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from i18n import translate, qt_layout_direction

from core.services.warehouse_service import warehouse_service
from core.services.branch_service import branch_service
from currency import currency
from models.table_models import GenericTableModel
from views.custom_table_view import CustomTableView
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from views.widgets.modern_ui import apply_modern_widget


class WarehousesWidget(QWidget):
    """Warehouse-1 UI: warehouse master data and read-only item balances."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.setObjectName('WarehousesWidget')
        warehouse_service.bootstrap()
        self.setup_ui()
        apply_modern_widget(self, '🏬 ' + translate('warehouses'), translate('warehouse_hint'))
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QLabel(translate('warehouse_management'))
        header.setObjectName('pageTitle')
        layout.addWidget(header)

        hint = QLabel(translate('warehouse_hint'))
        hint.setObjectName('mutedLabel')
        layout.addWidget(hint)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._setup_warehouses_tab()
        self._setup_balances_tab()
        self._setup_movements_tab()
        self._setup_transfers_tab()

    def _setup_warehouses_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.wh_search = QLineEdit()
        self.wh_search.setPlaceholderText(translate('warehouses_search'))
        self.wh_search.textChanged.connect(self.refresh_warehouses)
        self.show_archived = QCheckBox(translate('show_archived'))
        self.show_archived.stateChanged.connect(self.refresh_warehouses)
        add_btn = QPushButton(translate('new_warehouse'))
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_warehouse)
        edit_btn = QPushButton('✏️ ' + translate('edit'))
        edit_btn.clicked.connect(self.edit_warehouse)
        archive_btn = QPushButton(translate('archive'))
        archive_btn.clicked.connect(self.archive_warehouse)
        tools.addWidget(QLabel(translate('warehouses')))
        tools.addWidget(self.wh_search, 1)
        tools.addWidget(self.show_archived)
        tools.addWidget(add_btn)
        tools.addWidget(edit_btn)
        tools.addWidget(archive_btn)
        layout.addLayout(tools)
        self.wh_table = CustomTableView()
        self.wh_table.setSelectionBehavior(QTableView.SelectRows)
        self.wh_table.doubleClicked.connect(lambda _idx: self.edit_warehouse())
        layout.addWidget(self.wh_table)
        self.tabs.addTab(page, translate('warehouses'))

    def _setup_balances_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.balance_search = QLineEdit()
        self.balance_search.setPlaceholderText(translate('balance_search'))
        self.balance_search.textChanged.connect(self.refresh_balances)
        self.warehouse_filter = QComboBox()
        self.warehouse_filter.currentIndexChanged.connect(self.refresh_balances)
        tools.addWidget(QLabel(translate('item_balances')))
        tools.addWidget(self.balance_search, 1)
        tools.addWidget(QLabel(translate('warehouse_label')))
        tools.addWidget(self.warehouse_filter)
        layout.addLayout(tools)
        self.balance_table = CustomTableView()
        self.balance_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.balance_table)
        self.balance_status = QLabel()
        self.balance_status.setObjectName('mutedLabel')
        layout.addWidget(self.balance_status)
        self.tabs.addTab(page, translate('balances_tab'))

    def _setup_movements_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.mov_warehouse_filter = QComboBox()
        self.mov_warehouse_filter.currentIndexChanged.connect(self.refresh_movements)
        refresh_btn = QPushButton(translate('refresh_report'))
        refresh_btn.clicked.connect(self.refresh_movements)
        tools.addWidget(QLabel(translate('recent_warehouse_movements')))
        tools.addStretch()
        tools.addWidget(QLabel(translate('warehouse_label')))
        tools.addWidget(self.mov_warehouse_filter)
        tools.addWidget(refresh_btn)
        layout.addLayout(tools)
        self.mov_table = CustomTableView()
        self.mov_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.mov_table)
        self.tabs.addTab(page, translate('movements_tab'))

    def _setup_transfers_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        add_btn = QPushButton(translate('new_transfer'))
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_transfer)
        cancel_btn = QPushButton(translate('cancel_transfer'))
        cancel_btn.clicked.connect(self.cancel_transfer)
        refresh_btn = QPushButton(translate('refresh_report'))
        refresh_btn.clicked.connect(self.refresh_transfers)
        tools.addWidget(QLabel(translate('warehouse_transfers')))
        tools.addStretch()
        tools.addWidget(add_btn)
        tools.addWidget(cancel_btn)
        tools.addWidget(refresh_btn)
        layout.addLayout(tools)
        self.transfer_table = CustomTableView()
        self.transfer_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.transfer_table)
        self.tabs.addTab(page, translate('transfers_tab'))

    def refresh(self):
        warehouse_service.bootstrap()
        self._reload_warehouse_filters()
        self.refresh_warehouses()
        self.refresh_balances()
        self.refresh_movements()
        if hasattr(self, 'transfer_table'):
            self.refresh_transfers()

    def _reload_warehouse_filters(self):
        warehouses = warehouse_service.warehouses(include_archived=False)
        for combo in (self.warehouse_filter, self.mov_warehouse_filter):
            current = combo.currentData() if combo.count() else None
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(translate('all_warehouses'), None)
            for wh in warehouses:
                combo.addItem(wh.get('name', ''), wh.get('id'))
            if current is not None:
                for i in range(combo.count()):
                    if combo.itemData(i) == current:
                        combo.setCurrentIndex(i)
                        break
            combo.blockSignals(False)

    def refresh_warehouses(self):
        rows = []
        text = (self.wh_search.text() if hasattr(self, 'wh_search') else '').strip().lower()
        include_archived = self.show_archived.isChecked() if hasattr(self, 'show_archived') else False
        for wh in warehouse_service.warehouses(include_archived=include_archived):
            if text and text not in str(wh.get('name', '')).lower() and text not in str(wh.get('code', '')).lower():
                continue
            archived = bool(wh.get('deleted_at')) or int(wh.get('is_active') or 0) == 0
            rows.append({
                'id': wh.get('id'),
                'name': wh.get('name', ''),
                'code': wh.get('code') or '—',
                'location': wh.get('location') or '—',
                'branch_name': wh.get('branch_name') or translate('main_branch'),
                'item_count': int(wh.get('item_count') or 0),
                'total_qty': f"{Decimal(str(wh.get('total_qty') or 0)):.2f}",
                'is_default': translate('yes') if int(wh.get('is_default') or 0) == 1 else translate('no'),
                'status': translate('archived') if archived else translate('active'),
                'notes': wh.get('notes') or '',
            })
        headers = [translate('warehouse'), translate('warehouse_code'), translate('branch'), translate('location'), translate('items_count'), translate('total_quantities'), translate('default'), translate('status'), translate('notes')]
        keys = ['name', 'code', 'branch_name', 'location', 'item_count', 'total_qty', 'is_default', 'status', 'notes']
        self.wh_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.wh_table.setModel(self.wh_model)
        self.wh_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.wh_table.horizontalHeader().setStretchLastSection(True)

    def refresh_balances(self):
        search = self.balance_search.text().strip() if hasattr(self, 'balance_search') else None
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        try:
            balances = warehouse_service.balances(search=search, warehouse_id=wh_id)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('item_balances')), 'warning', self)
                return
            raise
        rows = []
        total_value = Decimal('0')
        for b in balances:
            qty = Decimal(str(b.get('quantity') or 0))
            avg = Decimal(str(b.get('average_cost') or 0))
            value = qty * avg
            total_value += value
            rows.append({
                'id': b.get('id'),
                'warehouse_name': b.get('warehouse_name', ''),
                'item_name': b.get('item_name', ''),
                'barcode': b.get('barcode') or '—',
                'quantity': f'{qty:.2f}',
                'unit': b.get('unit') or '',
                'average_cost': currency.format_amount(avg),
                'stock_value': currency.format_amount(value),
                'updated_at': b.get('updated_at') or '',
            })
        headers = [translate('warehouse'), translate('item'), translate('barcode'), translate('quantity'), translate('unit'), translate('unit_cost'), translate('stock_value'), translate('last_update')]
        keys = ['warehouse_name', 'item_name', 'barcode', 'quantity', 'unit', 'average_cost', 'stock_value', 'updated_at']
        self.balance_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.balance_table.setModel(self.balance_model)
        self.balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.balance_table.horizontalHeader().setStretchLastSection(True)
        self.balance_status.setText(translate('records_count_value', count=len(rows), value=currency.format_amount(total_value)))

    def refresh_movements(self):
        wh_id = self.mov_warehouse_filter.currentData() if hasattr(self, 'mov_warehouse_filter') else None
        rows = []
        try:
            movements = warehouse_service.movements(warehouse_id=wh_id, limit=200)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('recent_warehouse_movements')), 'warning', self)
                return
            raise
        for m in movements:
            rows.append({
                'id': m.get('id'),
                'date': m.get('movement_date') or m.get('created_at') or '',
                'warehouse_name': m.get('warehouse_name', ''),
                'item_name': m.get('item_name', ''),
                'type': self._movement_label(m.get('movement_type')),
                'quantity': m.get('quantity') or '0',
                'unit_cost': currency.format_amount(m.get('unit_cost') or 0),
                'reference': m.get('reference_type') or '—',
                'notes': m.get('notes') or '',
            })
        headers = [translate('date'), translate('warehouse'), translate('item'), translate('type'), translate('quantity'), translate('unit_cost'), translate('reference'), translate('notes')]
        keys = ['date', 'warehouse_name', 'item_name', 'type', 'quantity', 'unit_cost', 'reference', 'notes']
        self.mov_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.mov_table.setModel(self.mov_model)
        self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.mov_table.horizontalHeader().setStretchLastSection(True)

    def _movement_label(self, mtype):
        return {
            'migration_opening': translate('opening'),
            'opening': translate('opening'),
            'purchase': translate('purchase_type'),
            'sale': translate('sale_type'),
            'adjustment': translate('ledger_reconciliation'),
            'production_out': translate('nav_manufacturing'),
            'production_consume': translate('nav_manufacturing'),
            'transfer_out': translate('outgoing'),
            'transfer_in': translate('incoming'),
            'transfer_cancel_out': translate('cancel_transfer'),
            'transfer_cancel_in': translate('cancel_transfer'),
        }.get(mtype or '', mtype or '')



    def refresh_transfers(self):
        rows = []
        try:
            transfers = warehouse_service.transfers(limit=300)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('warehouse_transfers')), 'warning', self)
                return
            raise
        for t in transfers:
            rows.append({
                'id': t.get('id'),
                'transfer_no': t.get('transfer_no') or '',
                'created_at': t.get('created_at') or '',
                'item_name': t.get('item_name') or '',
                'from_warehouse': t.get('from_warehouse_name') or '',
                'to_warehouse': t.get('to_warehouse_name') or '',
                'quantity': t.get('quantity') or '0',
                'unit_cost': currency.format_amount(t.get('unit_cost') or 0),
                'status': translate('cancel') if t.get('status') == 'cancelled' else translate('active'),
                'notes': t.get('notes') or '',
            })
        headers = [translate('reference'), translate('date'), translate('item'), translate('from_warehouse').rstrip(':'), translate('to_warehouse').rstrip(':'), translate('quantity'), translate('unit_cost'), translate('status'), translate('notes')]
        keys = ['transfer_no', 'created_at', 'item_name', 'from_warehouse', 'to_warehouse', 'quantity', 'unit_cost', 'status', 'notes']
        self.transfer_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.transfer_table.setModel(self.transfer_model)
        self.transfer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.transfer_table.horizontalHeader().setStretchLastSection(True)

    def current_transfer_id(self):
        idx = self.transfer_table.currentIndex() if hasattr(self, 'transfer_table') else None
        if not idx or not idx.isValid() or not hasattr(self, 'transfer_model'):
            return None
        return self.transfer_model.get_id(idx.row())

    def _transfer_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(translate('warehouse_transfer_dialog'))
        dialog.setLayoutDirection(qt_layout_direction())
        dialog.resize(520, 360)
        layout = QFormLayout(dialog)
        from_combo = QComboBox()
        to_combo = QComboBox()
        item_combo = QComboBox()
        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.0001, 999999999)
        qty_spin.setDecimals(3)
        qty_spin.setValue(1)
        notes = QTextEdit()
        notes.setMaximumHeight(90)
        warehouses = warehouse_service.warehouses(include_archived=False)
        for wh in warehouses:
            label = f"{wh.get('name','')} ({wh.get('code') or '—'})"
            from_combo.addItem(label, wh.get('id'))
            to_combo.addItem(label, wh.get('id'))
        balances = warehouse_service.balances()
        seen = set()
        for b in balances:
            item_id = b.get('item_id')
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            item_combo.addItem(f"{b.get('item_name','')} - {b.get('barcode') or ''}", item_id)
        layout.addRow(translate('from_warehouse'), from_combo)
        layout.addRow(translate('to_warehouse'), to_combo)
        layout.addRow(translate('item') + ':', item_combo)
        layout.addRow(translate('quantity') + ':', qty_spin)
        layout.addRow(translate('notes') + ':', notes)
        btns = QHBoxLayout()
        save = QPushButton(translate('execute_transfer'))
        save.setObjectName('primary')
        cancel = QPushButton(translate('cancel'))
        btns.addWidget(save)
        btns.addWidget(cancel)
        layout.addRow(btns)
        payload = {}
        def do_save():
            payload.update({
                'from_warehouse_id': from_combo.currentData(),
                'to_warehouse_id': to_combo.currentData(),
                'item_id': item_combo.currentData(),
                'quantity': qty_spin.value(),
                'notes': notes.toPlainText().strip(),
            })
            dialog.accept()
        save.clicked.connect(do_save)
        cancel.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted:
            return payload
        return None

    def add_transfer(self):
        payload = self._transfer_dialog()
        if not payload:
            return
        try:
            warehouse_service.create_transfer(payload)
            show_toast(translate('transfer_done'), 'success', self)
            self.refresh()
            self.tabs.setCurrentIndex(self.tabs.indexOf(self.transfer_table.parent()))
        except Exception as e:
            show_toast(str(e), 'error', self)

    def cancel_transfer(self):
        transfer_id = self.current_transfer_id()
        if not transfer_id:
            show_toast(translate('select_transfer_first'), 'warning', self)
            return
        reply = QMessageBox.question(self, translate('confirm_cancel_transfer_title'), translate('confirm_cancel_transfer_msg'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            warehouse_service.cancel_transfer(transfer_id)
            show_toast(translate('transfer_cancelled'), 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def current_warehouse_id(self):
        idx = self.wh_table.currentIndex()
        if not idx.isValid() or not hasattr(self, 'wh_model'):
            return None
        return self.wh_model.get_id(idx.row())

    def _warehouse_dialog(self, title, warehouse=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLayoutDirection(qt_layout_direction())
        dialog.resize(460, 320)
        layout = QFormLayout(dialog)
        name = QLineEdit()
        code = QLineEdit()
        branch_combo = QComboBox()
        for br in branch_service.branches(include_archived=False):
            branch_combo.addItem(br.get('name',''), br.get('id'))
        location = QLineEdit()
        notes = QTextEdit()
        notes.setMaximumHeight(90)
        active = QCheckBox(translate('active'))
        active.setChecked(True)
        if warehouse:
            name.setText(warehouse.get('name', ''))
            code.setText(warehouse.get('code') or '')
            location.setText(warehouse.get('location') or '')
            current_branch = warehouse.get('branch_id') or branch_service.default_branch_id()
            for i in range(branch_combo.count()):
                if branch_combo.itemData(i) == current_branch:
                    branch_combo.setCurrentIndex(i)
                    break
            notes.setPlainText(warehouse.get('notes') or '')
            active.setChecked(int(warehouse.get('is_active') or 0) == 1 and not warehouse.get('deleted_at'))
        layout.addRow(translate('item_name_label'), name)
        layout.addRow(translate('warehouse_code') + ':', code)
        layout.addRow(translate('branch') + ':', branch_combo)
        layout.addRow(translate('location') + ':', location)
        layout.addRow(translate('notes') + ':', notes)
        layout.addRow('', active)
        btns = QHBoxLayout()
        save = QPushButton(translate('save'))
        save.setObjectName('primary')
        cancel = QPushButton(translate('cancel'))
        btns.addWidget(save)
        btns.addWidget(cancel)
        layout.addRow(btns)
        payload = {}
        def do_save():
            if not name.text().strip():
                show_toast(translate('warehouse_name_required'), 'error', dialog)
                name.setFocus()
                return
            payload.update({
                'name': name.text().strip(),
                'code': code.text().strip(),
                'location': location.text().strip(),
                'branch_id': branch_combo.currentData(),
                'notes': notes.toPlainText().strip(),
                'is_active': 1 if active.isChecked() else 0,
            })
            dialog.accept()
        save.clicked.connect(do_save)
        cancel.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted:
            return payload
        return None

    def add_warehouse(self):
        payload = self._warehouse_dialog(translate('add_warehouse_title'))
        if not payload:
            return
        try:
            warehouse_service.add_warehouse(payload)
            show_toast(translate('warehouse_created'), 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def edit_warehouse(self):
        wh_id = self.current_warehouse_id()
        if not wh_id:
            show_toast(translate('select_warehouse_first'), 'warning', self)
            return
        wh = warehouse_service.warehouse_by_id(wh_id)
        if not wh:
            show_toast(translate('warehouse_not_found'), 'error', self)
            return
        payload = self._warehouse_dialog(translate('edit_warehouse_title'), wh)
        if not payload:
            return
        try:
            warehouse_service.update_warehouse(wh_id, payload)
            show_toast(translate('warehouse_updated'), 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def archive_warehouse(self):
        wh_id = self.current_warehouse_id()
        if not wh_id:
            show_toast(translate('select_warehouse_first'), 'warning', self)
            return
        reply = QMessageBox.question(self, translate('confirm_archive_title'), translate('confirm_archive_msg'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            warehouse_service.archive_warehouse(wh_id)
            show_toast(translate('warehouse_archived'), 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)
