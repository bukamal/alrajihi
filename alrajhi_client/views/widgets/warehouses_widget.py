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
from core.services.inventory_operation_policy import inventory_operation_policy
from core.services.branch_service import branch_service
from currency import currency
from models.table_models import GenericTableModel
from ui.smart_table_view import SmartTableView
from features.inventory.inventory_printing_bridge import inventory_printing_bridge
from features.inventory.inventory_workspace_schema import (
    columns_for, headers_and_keys, visible_keys_for,
    inventory_workspace_preset_names, inventory_workspace_preset_title,
)
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
        # Phase117: no duplicated top header card or repeated explanatory hint.
        apply_modern_widget(self)
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

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
        self.wh_preset = self._toolbar_preset_combo('warehouses')
        self.wh_density = self._toolbar_density_combo('warehouses')
        add_btn = QPushButton(translate('new_warehouse'))
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_warehouse)
        self.add_warehouse_btn = add_btn
        edit_btn = QPushButton('✏️ ' + translate('edit'))
        edit_btn.clicked.connect(self.edit_warehouse)
        self.edit_warehouse_btn = edit_btn
        archive_btn = QPushButton(translate('archive'))
        archive_btn.clicked.connect(self.archive_warehouse)
        self.archive_warehouse_btn = archive_btn
        tools.addWidget(QLabel(translate('warehouses')))
        tools.addWidget(self.wh_search, 1)
        tools.addWidget(self.show_archived)
        tools.addWidget(QLabel(translate('view_preset_label')))
        tools.addWidget(self.wh_preset)
        tools.addWidget(QLabel(translate('row_density')))
        tools.addWidget(self.wh_density)
        tools.addWidget(add_btn)
        tools.addWidget(edit_btn)
        tools.addWidget(archive_btn)
        layout.addLayout(tools)
        self.wh_table = SmartTableView(identity="warehouses.list")
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
        self.balance_stock_filter = QComboBox()
        self.balance_stock_filter.addItem(translate('inventory_stock_all'), 'all')
        self.balance_stock_filter.addItem(translate('inventory_stock_positive'), 'positive')
        self.balance_stock_filter.addItem(translate('inventory_stock_zero'), 'zero')
        self.balance_stock_filter.addItem(translate('inventory_stock_negative'), 'negative')
        self.balance_stock_filter.currentIndexChanged.connect(self.refresh_balances)
        self.balance_preset = self._toolbar_preset_combo('balances')
        self.balance_density = self._toolbar_density_combo('balances')
        tools.addWidget(QLabel(translate('item_balances')))
        tools.addWidget(self.balance_search, 1)
        tools.addWidget(QLabel(translate('warehouse_label')))
        tools.addWidget(self.warehouse_filter)
        tools.addWidget(QLabel(translate('inventory_stock_status')))
        tools.addWidget(self.balance_stock_filter)
        tools.addWidget(QLabel(translate('view_preset_label')))
        tools.addWidget(self.balance_preset)
        print_btn = QPushButton(translate('print'))
        print_btn.clicked.connect(self.print_balances)
        self.print_balances_btn = print_btn
        tools.addWidget(QLabel(translate('row_density')))
        tools.addWidget(self.balance_density)
        tools.addWidget(print_btn)
        layout.addLayout(tools)
        self.balance_table = SmartTableView(identity="warehouses.balances")
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
        self.mov_search = QLineEdit()
        self.mov_search.setClearButtonEnabled(True)
        self.mov_search.setPlaceholderText(translate('inventory_search_movements'))
        self.mov_search.textChanged.connect(self.refresh_movements)
        self.mov_warehouse_filter = QComboBox()
        self.mov_warehouse_filter.currentIndexChanged.connect(self.refresh_movements)
        self.mov_type_filter = QComboBox()
        self.mov_type_filter.addItem(translate('inventory_movement_all_types'), 'all')
        for code in ('purchase', 'sale', 'transfer', 'manufacturing', 'adjustment'):
            self.mov_type_filter.addItem(translate(f'inventory_movement_type_{code}'), code)
        self.mov_type_filter.currentIndexChanged.connect(self.refresh_movements)
        self.mov_preset = self._toolbar_preset_combo('movements')
        self.mov_density = self._toolbar_density_combo('movements')
        refresh_btn = QPushButton(translate('refresh_report'))
        refresh_btn.clicked.connect(self.refresh_movements)
        tools.addWidget(QLabel(translate('recent_warehouse_movements')))
        tools.addWidget(self.mov_search, 1)
        tools.addWidget(QLabel(translate('warehouse_label')))
        tools.addWidget(self.mov_warehouse_filter)
        tools.addWidget(QLabel(translate('type')))
        tools.addWidget(self.mov_type_filter)
        tools.addWidget(QLabel(translate('view_preset_label')))
        tools.addWidget(self.mov_preset)
        tools.addWidget(QLabel(translate('row_density')))
        tools.addWidget(self.mov_density)
        tools.addWidget(refresh_btn)
        layout.addLayout(tools)
        self.mov_table = SmartTableView(identity="warehouses.movements")
        self.mov_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.mov_table)
        self.tabs.addTab(page, translate('movements_tab'))

    def _setup_transfers_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.transfer_search = QLineEdit()
        self.transfer_search.setClearButtonEnabled(True)
        self.transfer_search.setPlaceholderText(translate('inventory_search_transfers'))
        self.transfer_search.textChanged.connect(self.refresh_transfers)
        self.transfer_status_filter = QComboBox()
        self.transfer_status_filter.addItem(translate('all'), 'all')
        self.transfer_status_filter.addItem(translate('active'), 'active')
        self.transfer_status_filter.addItem(translate('cancel'), 'cancelled')
        self.transfer_status_filter.currentIndexChanged.connect(self.refresh_transfers)
        self.transfer_preset = self._toolbar_preset_combo('transfers')
        self.transfer_density = self._toolbar_density_combo('transfers')
        add_btn = QPushButton(translate('new_transfer'))
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_transfer)
        self.add_transfer_btn = add_btn
        cancel_btn = QPushButton(translate('cancel_transfer'))
        cancel_btn.clicked.connect(self.cancel_transfer)
        self.cancel_transfer_btn = cancel_btn
        print_btn = QPushButton(translate('print'))
        print_btn.clicked.connect(self.print_selected_transfer)
        self.print_transfer_btn = print_btn
        refresh_btn = QPushButton(translate('refresh_report'))
        refresh_btn.clicked.connect(self.refresh_transfers)
        tools.addWidget(QLabel(translate('warehouse_transfers')))
        tools.addWidget(self.transfer_search, 1)
        tools.addWidget(QLabel(translate('status')))
        tools.addWidget(self.transfer_status_filter)
        tools.addWidget(QLabel(translate('view_preset_label')))
        tools.addWidget(self.transfer_preset)
        tools.addWidget(QLabel(translate('row_density')))
        tools.addWidget(self.transfer_density)
        tools.addWidget(add_btn)
        tools.addWidget(cancel_btn)
        tools.addWidget(print_btn)
        tools.addWidget(refresh_btn)
        layout.addLayout(tools)
        self.transfer_table = SmartTableView(identity="warehouses.transfers")
        self.transfer_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.transfer_table)
        self.tabs.addTab(page, translate('transfers_tab'))

    def _apply_inventory_operation_state(self):
        pairs = (
            ('add_warehouse_btn', inventory_operation_policy.OP_WAREHOUSE_CREATE),
            ('edit_warehouse_btn', inventory_operation_policy.OP_WAREHOUSE_EDIT),
            ('archive_warehouse_btn', inventory_operation_policy.OP_WAREHOUSE_ARCHIVE),
            ('add_transfer_btn', inventory_operation_policy.OP_TRANSFER_CREATE),
            ('cancel_transfer_btn', inventory_operation_policy.OP_TRANSFER_CANCEL),
            ('print_balances_btn', inventory_operation_policy.OP_PRINT),
            ('print_movements_btn', inventory_operation_policy.OP_PRINT),
            ('print_transfer_btn', inventory_operation_policy.OP_PRINT),
        )
        for attr, op in pairs:
            btn = getattr(self, attr, None)
            if btn is not None:
                try:
                    btn.setEnabled(inventory_operation_policy.can(op))
                except Exception:
                    btn.setEnabled(True)

    def _require_inventory_operation(self, op_key: str) -> bool:
        try:
            inventory_operation_policy.require(op_key, context='warehouses_widget')
            return True
        except PermissionError as exc:
            show_toast(str(exc), 'warning', self)
            return False

    def _toolbar_preset_combo(self, target: str):
        combo = QComboBox()
        for name in inventory_workspace_preset_names():
            combo.addItem(inventory_workspace_preset_title(name), name)
        combo.setCurrentIndex(max(0, combo.findData('manager')))
        combo.currentIndexChanged.connect(lambda _=0, t=target: self._apply_workspace_preset(t))
        return combo

    def _toolbar_density_combo(self, target: str):
        combo = QComboBox()
        for key in ('compact', 'comfortable', 'touch'):
            label = translate(f'density_{key}')
            combo.addItem(label if label != f'density_{key}' else key.title(), key)
        combo.setCurrentIndex(max(0, combo.findData('comfortable')))
        combo.currentIndexChanged.connect(lambda _=0, t=target: self._apply_density(t))
        return combo

    def _table_for_target(self, target: str):
        return {
            'warehouses': getattr(self, 'wh_table', None),
            'balances': getattr(self, 'balance_table', None),
            'movements': getattr(self, 'mov_table', None),
            'transfers': getattr(self, 'transfer_table', None),
        }.get(target)

    def _preset_for_target(self, target: str):
        return {
            'warehouses': getattr(self, 'wh_preset', None),
            'balances': getattr(self, 'balance_preset', None),
            'movements': getattr(self, 'mov_preset', None),
            'transfers': getattr(self, 'transfer_preset', None),
        }.get(target)

    def _density_for_target(self, target: str):
        return {
            'warehouses': getattr(self, 'wh_density', None),
            'balances': getattr(self, 'balance_density', None),
            'movements': getattr(self, 'mov_density', None),
            'transfers': getattr(self, 'transfer_density', None),
        }.get(target)

    def _apply_workspace_preset(self, target: str):
        table = self._table_for_target(target)
        combo = self._preset_for_target(target)
        if table is None or combo is None:
            return
        columns = columns_for(target)
        visible = visible_keys_for(target, combo.currentData() or 'manager')
        for col, column in enumerate(columns):
            table.setColumnHidden(col, column.key not in visible)
        try:
            table.save_layout()
            table.fit_columns_to_view()
        except Exception:
            pass

    def _apply_density(self, target: str):
        table = self._table_for_target(target)
        combo = self._density_for_target(target)
        if table is None or combo is None:
            return
        try:
            table.set_density(combo.currentData() or 'comfortable')
        except Exception:
            pass

    def _source_row_for_table(self, table):
        if table is None:
            return None
        try:
            if hasattr(table, 'current_source_row'):
                return table.current_source_row()
            idx = table.currentIndex()
            if not idx or not idx.isValid():
                return None
            if hasattr(table, 'source_model') and table.source_model() is not None and table.model() is not table.source_model():
                idx = table.model().mapToSource(idx)
            return idx.row()
        except Exception:
            return None

    def set_global_filter(self, text: str):
        text = text or ''
        for attr in ('wh_search', 'balance_search', 'mov_search', 'transfer_search'):
            widget = getattr(self, attr, None)
            if widget is not None:
                widget.setText(text)


    def refresh(self):
        warehouse_service.bootstrap()
        self._reload_warehouse_filters()
        self.refresh_warehouses()
        self.refresh_balances()
        self.refresh_movements()
        self._apply_inventory_operation_state()
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
        headers, keys = headers_and_keys(columns_for('warehouses'))
        self.wh_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.wh_table.setModel(self.wh_model)
        self.wh_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.wh_table.horizontalHeader().setStretchLastSection(True)
        self._apply_workspace_preset('warehouses')

    def refresh_balances(self):
        search = self.balance_search.text().strip() if hasattr(self, 'balance_search') else None
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        stock_filter = self.balance_stock_filter.currentData() if hasattr(self, 'balance_stock_filter') else 'all'
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
            if stock_filter == 'positive' and qty <= 0:
                continue
            if stock_filter == 'zero' and qty != 0:
                continue
            if stock_filter == 'negative' and qty >= 0:
                continue
            value = qty * avg
            total_value += value
            stock_status = translate('inventory_stock_negative') if qty < 0 else (translate('inventory_stock_zero') if qty == 0 else translate('inventory_stock_positive'))
            rows.append({
                'id': b.get('id'),
                'warehouse_name': b.get('warehouse_name', ''),
                'item_name': b.get('item_name', ''),
                'barcode': b.get('barcode') or '—',
                'quantity': f'{qty:.2f}',
                'unit': b.get('unit') or '',
                'stock_status': stock_status,
                'average_cost': currency.format_amount(avg),
                'stock_value': currency.format_amount(value),
                'updated_at': b.get('updated_at') or '',
            })
        headers, keys = headers_and_keys(columns_for('balances'))
        self.balance_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.balance_table.setModel(self.balance_model)
        self.balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.balance_table.horizontalHeader().setStretchLastSection(True)
        self._apply_workspace_preset('balances')
        self.balance_status.setText(translate('records_count_value', count=len(rows), value=currency.format_amount(total_value)))

    def refresh_movements(self):
        wh_id = self.mov_warehouse_filter.currentData() if hasattr(self, 'mov_warehouse_filter') else None
        text = (self.mov_search.text() if hasattr(self, 'mov_search') else '').strip().casefold()
        type_filter = self.mov_type_filter.currentData() if hasattr(self, 'mov_type_filter') else 'all'
        rows = []
        try:
            movements = warehouse_service.movements(warehouse_id=wh_id, limit=200)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('recent_warehouse_movements')), 'warning', self)
                return
            raise
        for m in movements:
            movement_type = m.get('movement_type') or ''
            family = self._movement_family(movement_type)
            if type_filter != 'all' and family != type_filter:
                continue
            haystack = ' '.join(str(m.get(k) or '') for k in ('warehouse_name', 'item_name', 'movement_type', 'reference_type', 'notes')).casefold()
            if text and text not in haystack:
                continue
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
        headers, keys = headers_and_keys(columns_for('movements'))
        self.mov_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.mov_table.setModel(self.mov_model)
        self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.mov_table.horizontalHeader().setStretchLastSection(True)
        self._apply_workspace_preset('movements')

    def _movement_family(self, mtype):
        mtype = (mtype or '').strip()
        if mtype in ('purchase',):
            return 'purchase'
        if mtype in ('sale',):
            return 'sale'
        if mtype.startswith('transfer_'):
            return 'transfer'
        if mtype.startswith('production_'):
            return 'manufacturing'
        if mtype in ('adjustment', 'opening', 'migration_opening'):
            return 'adjustment'
        return mtype or 'other'

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
        text = (self.transfer_search.text() if hasattr(self, 'transfer_search') else '').strip().casefold()
        status_filter = self.transfer_status_filter.currentData() if hasattr(self, 'transfer_status_filter') else 'all'
        for t in transfers:
            status_code = t.get('status') or 'active'
            if status_filter != 'all' and status_code != status_filter:
                continue
            haystack = ' '.join(str(t.get(k) or '') for k in ('transfer_no', 'item_name', 'from_warehouse_name', 'to_warehouse_name', 'notes')).casefold()
            if text and text not in haystack:
                continue
            rows.append({
                'id': t.get('id'),
                'transfer_no': t.get('transfer_no') or '',
                'created_at': t.get('created_at') or '',
                'item_name': t.get('item_name') or '',
                'from_warehouse': t.get('from_warehouse_name') or '',
                'to_warehouse': t.get('to_warehouse_name') or '',
                'quantity': t.get('quantity') or '0',
                'unit_name': t.get('unit_name') or t.get('unit') or '',
                'base_qty': t.get('base_qty') or t.get('quantity') or '0',
                'unit_cost': currency.format_amount(t.get('unit_cost') or 0),
                'status': translate('cancel') if status_code == 'cancelled' else translate('active'),
                'notes': t.get('notes') or '',
            })
        headers, keys = headers_and_keys(columns_for('transfers'))
        self.transfer_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.transfer_table.setModel(self.transfer_model)
        self.transfer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.transfer_table.horizontalHeader().setStretchLastSection(True)
        self._apply_workspace_preset('transfers')

    def current_transfer_id(self):
        idx = self.transfer_table.currentIndex() if hasattr(self, 'transfer_table') else None
        if not idx or not idx.isValid() or not hasattr(self, 'transfer_model'):
            return None
        row = self._source_row_for_table(self.transfer_table)
        return self.transfer_model.get_id(row) if row is not None else None


    def _table_rows_for_print(self, model_attr: str) -> list:
        model = getattr(self, model_attr, None)
        if model is None:
            return []
        return [dict(model.get_row(row) or {}) for row in range(model.rowCount())]

    def _selected_transfer_row(self) -> dict:
        if not hasattr(self, 'transfer_model'):
            return {}
        row = self._source_row_for_table(self.transfer_table)
        return dict(self.transfer_model.get_row(row) or {}) if row is not None else {}

    def print_balances(self):
        if not self._require_inventory_operation(inventory_operation_policy.OP_PRINT):
            return
        try:
            payload = inventory_printing_bridge.balances_payload(self._table_rows_for_print('balance_model'), warehouse=self.warehouse_filter.currentText() if hasattr(self, 'warehouse_filter') else '')
            inventory_printing_bridge.balances_print(payload, self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def print_movements(self):
        if not self._require_inventory_operation(inventory_operation_policy.OP_PRINT):
            return
        try:
            payload = inventory_printing_bridge.movements_payload(self._table_rows_for_print('mov_model'), warehouse=self.mov_warehouse_filter.currentText() if hasattr(self, 'mov_warehouse_filter') else '', movement_type=self.mov_type_filter.currentText() if hasattr(self, 'mov_type_filter') else '')
            inventory_printing_bridge.movements_print(payload, self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def print_selected_transfer(self):
        if not self._require_inventory_operation(inventory_operation_policy.OP_PRINT):
            return
        transfer = self._selected_transfer_row()
        if not transfer:
            show_toast(translate('select_transfer_first'), 'warning', self)
            return
        try:
            payload = inventory_printing_bridge.transfer_payload(transfer, [transfer])
            inventory_printing_bridge.transfer_print(payload, self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

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
        if not self._require_inventory_operation(inventory_operation_policy.OP_TRANSFER_CREATE):
            return
        main_window = self.window()
        if hasattr(main_window, 'open_inventory_transfer_document'):
            try:
                return main_window.open_inventory_transfer_document()
            except Exception as exc:
                show_toast(str(exc), 'warning', self)
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
        if not self._require_inventory_operation(inventory_operation_policy.OP_TRANSFER_CANCEL):
            return
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
        row = self._source_row_for_table(self.wh_table)
        return self.wh_model.get_id(row) if row is not None else None

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
        layout.addRow(translate('warehouse_name_label'), name)
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
        if not self._require_inventory_operation(inventory_operation_policy.OP_WAREHOUSE_CREATE):
            return
        main_window = self.window()
        if hasattr(main_window, 'open_warehouse_document'):
            try:
                return main_window.open_warehouse_document()
            except Exception as exc:
                show_toast(str(exc), 'warning', self)
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
        if not self._require_inventory_operation(inventory_operation_policy.OP_WAREHOUSE_EDIT):
            return
        wh_id = self.current_warehouse_id()
        if not wh_id:
            show_toast(translate('select_warehouse_first'), 'warning', self)
            return
        main_window = self.window()
        if hasattr(main_window, 'open_warehouse_document'):
            try:
                return main_window.open_warehouse_document(wh_id)
            except Exception as exc:
                show_toast(str(exc), 'warning', self)
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
        if not self._require_inventory_operation(inventory_operation_policy.OP_WAREHOUSE_ARCHIVE):
            return
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

# Phase110 offline guard markers: أرصدة المستودعات | تحويلات المستودعات
