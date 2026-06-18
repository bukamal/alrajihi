# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QHeaderView, QMessageBox, QMenu, QAction, QLabel, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt

from i18n import translate, qt_layout_direction
from core.services.manufacturing_service import manufacturing_service
from core.services.manufacturing_operation_policy import manufacturing_operation_policy
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from views.widgets.modern_ui import apply_modern_widget
from features.manufacturing.manufacturing_workspace_schema import (
    bom_columns, production_order_columns, headers_and_keys, visible_keys_for,
    workspace_preset_names, workspace_preset_title,
)


class ManufacturingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = manufacturing_service
        self.setLayoutDirection(qt_layout_direction())
        self.bom_page = 0
        self.orders_page = 0
        self.page_size = 30
        self._bom_rows = []
        self._orders_rows = []

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        self.bom_tab = QWidget()
        self.orders_tab = QWidget()
        self.setup_bom_tab()
        self.setup_orders_tab()
        self.tabs.addTab(self.bom_tab, translate("bom_lists"))
        self.tabs.addTab(self.orders_tab, translate("production_orders"))
        layout.addWidget(self.tabs)
        apply_modern_widget(self, '🏭 ' + translate('manufacturing_title'), translate('manufacturing_subtitle'))
        self._apply_manufacturing_operation_state()

        self.refresh_bom()
        self.refresh_orders()

    def _apply_manufacturing_operation_state(self):
        try:
            if hasattr(self, 'add_bom_btn'):
                self.add_bom_btn.setEnabled(manufacturing_operation_policy.can(manufacturing_operation_policy.OP_BOM_CREATE))
            if hasattr(self, 'add_order_btn'):
                self.add_order_btn.setEnabled(manufacturing_operation_policy.can(manufacturing_operation_policy.OP_ORDER_CREATE))
        except Exception:
            pass

    def _handle_permission_denied(self, exc: Exception):
        show_toast(str(exc) or translate('permission_denied'), 'warning', self)

    def _toolbar_button(self, text_key: str, slot):
        btn = QPushButton(translate(text_key))
        btn.clicked.connect(slot)
        return btn

    def _preset_combo(self, target: str):
        combo = QComboBox()
        for name in workspace_preset_names():
            combo.addItem(workspace_preset_title(name), name)
        combo.setCurrentIndex(max(0, combo.findData('manager')))
        combo.currentIndexChanged.connect(lambda _=0, t=target: self._apply_workspace_preset(t))
        return combo

    def _density_combo(self, target: str):
        combo = QComboBox()
        for key in ('compact', 'comfortable', 'touch'):
            combo.addItem(translate(f'density_{key}') if translate(f'density_{key}') != f'density_{key}' else key.title(), key)
        combo.setCurrentIndex(max(0, combo.findData('comfortable')))
        combo.currentIndexChanged.connect(lambda _=0, t=target: self._apply_density(t))
        return combo

    def setup_bom_tab(self):
        layout = QVBoxLayout(self.bom_tab)

        controls = QHBoxLayout()
        self.bom_search = QLineEdit()
        self.bom_search.setClearButtonEnabled(True)
        self.bom_search.setPlaceholderText(translate('manufacturing_search_bom'))
        self.bom_search.textChanged.connect(lambda text: self.bom_table.set_local_filter(text))
        controls.addWidget(self.bom_search, 2)

        controls.addWidget(QLabel(translate('view_preset_label')))
        self.bom_preset = self._preset_combo('bom')
        controls.addWidget(self.bom_preset)
        controls.addWidget(QLabel(translate('row_density')))
        self.bom_density = self._density_combo('bom')
        controls.addWidget(self.bom_density)

        self.add_bom_btn = self._toolbar_button('add_bom', self.add_bom)
        controls.addWidget(self.add_bom_btn)
        controls.addWidget(self._toolbar_button('refresh', self.refresh_bom))
        layout.addLayout(controls)

        self.bom_table = SmartTableView(identity="manufacturing.workspace.bom")
        self.bom_table.setSelectionBehavior(SmartTableView.SelectRows)
        self.bom_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bom_table.customContextMenuRequested.connect(self.show_bom_context_menu)
        self.bom_table.doubleClicked.connect(self.edit_bom)
        layout.addWidget(self.bom_table)

        pagination = QHBoxLayout()
        self.bom_prev = QPushButton(translate("previous"))
        self.bom_prev.clicked.connect(lambda: self.prev_page('bom'))
        self.bom_next = QPushButton(translate("next"))
        self.bom_next.clicked.connect(lambda: self.next_page('bom'))
        self.bom_page_label = QLabel()
        pagination.addWidget(self.bom_prev)
        pagination.addWidget(self.bom_page_label)
        pagination.addWidget(self.bom_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def setup_orders_tab(self):
        layout = QVBoxLayout(self.orders_tab)

        controls = QHBoxLayout()
        self.orders_search = QLineEdit()
        self.orders_search.setClearButtonEnabled(True)
        self.orders_search.setPlaceholderText(translate('manufacturing_search_orders'))
        self.orders_search.textChanged.connect(lambda text: self.orders_table.set_local_filter(text))
        controls.addWidget(self.orders_search, 2)

        self.orders_status_filter = QComboBox()
        self.orders_status_filter.addItem(translate('manufacturing_all_statuses'), 'all')
        for code in ('planned', 'in_progress', 'completed', 'cancelled'):
            self.orders_status_filter.addItem(self._status_text(code), code)
        self.orders_status_filter.currentIndexChanged.connect(lambda _=0: self._apply_order_filters())
        controls.addWidget(self.orders_status_filter)

        self.orders_warehouse_filter = QComboBox()
        self.orders_warehouse_filter.addItem(translate('all_warehouses'), 'all')
        self.orders_warehouse_filter.currentIndexChanged.connect(lambda _=0: self._apply_order_filters())
        controls.addWidget(self.orders_warehouse_filter)

        controls.addWidget(QLabel(translate('view_preset_label')))
        self.orders_preset = self._preset_combo('orders')
        controls.addWidget(self.orders_preset)
        controls.addWidget(QLabel(translate('row_density')))
        self.orders_density = self._density_combo('orders')
        controls.addWidget(self.orders_density)

        self.add_order_btn = self._toolbar_button('new_production_order', self.add_order)
        controls.addWidget(self.add_order_btn)
        controls.addWidget(self._toolbar_button('refresh', self.refresh_orders))
        layout.addLayout(controls)

        self.orders_table = SmartTableView(identity="manufacturing.workspace.orders")
        self.orders_table.setSelectionBehavior(SmartTableView.SelectRows)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.show_order_context_menu)
        self.orders_table.doubleClicked.connect(self.view_order)
        layout.addWidget(self.orders_table)

        pagination = QHBoxLayout()
        self.orders_prev = QPushButton(translate("previous"))
        self.orders_prev.clicked.connect(lambda: self.prev_page('orders'))
        self.orders_next = QPushButton(translate("next"))
        self.orders_next.clicked.connect(lambda: self.next_page('orders'))
        self.orders_page_label = QLabel()
        pagination.addWidget(self.orders_prev)
        pagination.addWidget(self.orders_page_label)
        pagination.addWidget(self.orders_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def _status_text(self, status: str) -> str:
        return {
            'planned': translate('status_planned'),
            'in_progress': translate('status_in_progress'),
            'completed': translate('status_completed'),
            'cancelled': translate('status_cancelled'),
        }.get(status or 'planned', translate('status_planned'))

    def _source_row_for_index(self, table: SmartTableView, index):
        if not index or not index.isValid():
            return None
        try:
            if hasattr(table, 'source_model') and table.source_model() is not None and table.model() is not table.source_model():
                index = table.model().mapToSource(index)
        except Exception:
            pass
        return index.row()

    def set_global_filter(self, text: str):
        text = text or ''
        if hasattr(self, 'bom_search'):
            self.bom_search.setText(text)
        if hasattr(self, 'orders_search'):
            self.orders_search.setText(text)

    def _apply_workspace_preset(self, target: str):
        table = self.bom_table if target == 'bom' else self.orders_table
        combo = self.bom_preset if target == 'bom' else self.orders_preset
        columns = bom_columns() if target == 'bom' else production_order_columns()
        preset = combo.currentData() or 'manager'
        visible = visible_keys_for('bom' if target == 'bom' else 'orders', preset)
        for col, column in enumerate(columns):
            table.setColumnHidden(col, column.key not in visible)
        table.save_layout()
        table.fit_columns_to_view()

    def _apply_density(self, target: str):
        table = self.bom_table if target == 'bom' else self.orders_table
        combo = self.bom_density if target == 'bom' else self.orders_density
        table.set_density(combo.currentData() or 'comfortable')

    def _update_order_warehouse_filter_options(self):
        if not hasattr(self, 'orders_warehouse_filter'):
            return
        current = self.orders_warehouse_filter.currentData() or 'all'
        values = []
        seen = set()
        for row in self._orders_rows:
            for key in ('raw_warehouse', 'output_warehouse'):
                value = str(row.get(key) or '').strip()
                if value and value != '-' and value not in seen:
                    seen.add(value)
                    values.append(value)
        self.orders_warehouse_filter.blockSignals(True)
        self.orders_warehouse_filter.clear()
        self.orders_warehouse_filter.addItem(translate('all_warehouses'), 'all')
        for value in sorted(values, key=lambda s: s.lower()):
            self.orders_warehouse_filter.addItem(value, value)
        idx = self.orders_warehouse_filter.findData(current)
        self.orders_warehouse_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.orders_warehouse_filter.blockSignals(False)

    def _set_bom_model(self, rows):
        headers, keys = headers_and_keys(bom_columns())
        self.bom_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.bom_table.setModel(self.bom_model)
        self.bom_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.bom_table.refresh_style()
        self._apply_workspace_preset('bom')
        if self.bom_search.text().strip():
            self.bom_table.set_local_filter(self.bom_search.text())

    def _set_orders_model(self, rows):
        headers, keys = headers_and_keys(production_order_columns())
        self.orders_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.orders_table.setModel(self.orders_model)
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.orders_table.refresh_style()
        self._apply_workspace_preset('orders')
        if self.orders_search.text().strip():
            self.orders_table.set_local_filter(self.orders_search.text())

    def refresh_bom(self, reset_page=True):
        if reset_page:
            self.bom_page = 0
        offset = self.bom_page * self.page_size
        try:
            boms, total = self.service.boms_pair(limit=self.page_size, offset=offset)
        except PermissionError as exc:
            self._handle_permission_denied(exc)
            return
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_bom_offline')), 'warning', self)
                return
            raise
        self._bom_rows = []
        for b in boms:
            lines = b.get('lines') or b.get('components') or []
            try:
                components_count = len(lines)
            except Exception:
                components_count = b.get('components_count', '')
            self._bom_rows.append({
                'id': b['id'],
                'product': b.get('product_name', ''),
                'quantity': str(b.get('quantity', 1)),
                'components_count': str(components_count or b.get('components_count', '')),
                'created_at': b.get('created_at', '')[:10] if b.get('created_at') else ''
            })
        self._set_bom_model(self._bom_rows)

        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.bom_page_label.setText(translate('page_of', page=self.bom_page + 1, pages=total_pages))
        self.bom_prev.setEnabled(self.bom_page > 0)
        self.bom_next.setEnabled(self.bom_page + 1 < total_pages)

    def refresh_orders(self, reset_page=True):
        if reset_page:
            self.orders_page = 0
        offset = self.orders_page * self.page_size
        try:
            orders, total = self.service.production_orders_pair(limit=self.page_size, offset=offset)
        except PermissionError as exc:
            self._handle_permission_denied(exc)
            return
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_orders_offline')), 'warning', self)
                return
            raise
        self._orders_rows = []
        for o in orders:
            raw_status = o.get('status', 'planned') or 'planned'
            self._orders_rows.append({
                'id': o['id'],
                'order_number': o.get('order_number', ''),
                'product': o.get('product_name', ''),
                'planned_qty': str(o.get('planned_qty', 0)),
                'produced_qty': str(o.get('produced_qty', 0)),
                'status': self._status_text(raw_status),
                'raw_status': raw_status,
                'raw_warehouse': o.get('raw_warehouse_name') or '-',
                'output_warehouse': o.get('output_warehouse_name') or '-',
                'start_date': o.get('start_date', '-')[:10] if o.get('start_date') else '-'
            })
        self._update_order_warehouse_filter_options()
        self._apply_order_filters()

        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.orders_page_label.setText(translate('page_of', page=self.orders_page + 1, pages=total_pages))
        self.orders_prev.setEnabled(self.orders_page > 0)
        self.orders_next.setEnabled(self.orders_page + 1 < total_pages)

    def _apply_order_filters(self):
        status_filter = self.orders_status_filter.currentData() if hasattr(self, 'orders_status_filter') else 'all'
        warehouse_filter = self.orders_warehouse_filter.currentData() if hasattr(self, 'orders_warehouse_filter') else 'all'
        rows = []
        for row in self._orders_rows:
            if status_filter and status_filter != 'all' and row.get('raw_status') != status_filter:
                continue
            if warehouse_filter and warehouse_filter != 'all':
                if warehouse_filter not in (row.get('raw_warehouse'), row.get('output_warehouse')):
                    continue
            rows.append(row)
        self._set_orders_model(rows)

    def show_bom_context_menu(self, pos):
        index = self.bom_table.indexAt(pos)
        row = self._source_row_for_index(self.bom_table, index)
        if row is None:
            return
        bom_id = self.bom_model.get_id(row)
        if not bom_id:
            return
        menu = QMenu()
        edit_action = QAction(translate("edit"), self)
        edit_action.triggered.connect(lambda: self.edit_bom_by_id(bom_id))
        delete_action = QAction(translate("delete"), self)
        delete_action.setEnabled(manufacturing_operation_policy.can(manufacturing_operation_policy.OP_BOM_DELETE))
        delete_action.triggered.connect(lambda: self.delete_bom_by_id(bom_id))
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(self.bom_table.viewport().mapToGlobal(pos))

    def show_order_context_menu(self, pos):
        index = self.orders_table.indexAt(pos)
        row = self._source_row_for_index(self.orders_table, index)
        if row is None:
            return
        order_id = self.orders_model.get_id(row)
        if not order_id:
            return
        raw_status = self.orders_model.get_row(row).get('raw_status', '')
        menu = QMenu()
        view_action = QAction(translate("view_details"), self)
        view_action.triggered.connect(lambda: self.view_order_by_id(order_id))
        menu.addAction(view_action)
        if raw_status in ('planned', 'cancelled'):
            delete_action = QAction(translate("delete_order"), self)
            delete_action.setEnabled(manufacturing_operation_policy.can(manufacturing_operation_policy.OP_ORDER_DELETE))
            delete_action.triggered.connect(lambda: self.delete_order_by_id(order_id))
            menu.addAction(delete_action)
        menu.exec(self.orders_table.viewport().mapToGlobal(pos))

    def _main_window_with_documents(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'open_bom_document') or hasattr(parent, 'open_production_order_document'):
                return parent
            parent = parent.parent() if hasattr(parent, 'parent') else None
        return None

    def add_bom(self):
        main = self._main_window_with_documents()
        if main and hasattr(main, 'open_bom_document'):
            tab = main.open_bom_document()
            if tab and hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh_bom())
            return
        self._open_legacy_bom_dialog()

    def _open_legacy_bom_dialog(self, bom_id=None):
        try:
            from views.dialogs.bom_dialog import BOMDialog
            dialog = BOMDialog(self, bom_id=bom_id) if bom_id is not None else BOMDialog(self)
            if dialog.exec():
                self.refresh_bom()
        except Exception as exc:
            QMessageBox.warning(self, translate('warning'), str(exc))

    def edit_bom(self, index):
        row = self._source_row_for_index(self.bom_table, index)
        if row is None:
            return
        bom_id = self.bom_model.get_id(row)
        self.edit_bom_by_id(bom_id)

    def edit_bom_by_id(self, bom_id):
        can_edit, msg = self.service.can_edit_bom(bom_id)
        if not can_edit:
            QMessageBox.warning(self, translate("warning"), msg)
            return
        main = self._main_window_with_documents()
        if main and hasattr(main, 'open_bom_document'):
            tab = main.open_bom_document(bom_id=bom_id)
            if tab and hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh_bom())
            return
        self._open_legacy_bom_dialog(bom_id=bom_id)

    def delete_bom_by_id(self, bom_id):
        reply = QMessageBox.question(self, translate("confirm_delete"), translate("confirm_delete_bom"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success, msg = self.service.delete_bom(bom_id)
            except PermissionError as exc:
                self._handle_permission_denied(exc)
                return
            if success:
                show_toast(translate("bom_deleted"), "success", self)
                self.refresh_bom()
            else:
                QMessageBox.critical(self, translate("error"), msg)

    def add_order(self):
        main = self._main_window_with_documents()
        if main and hasattr(main, 'open_production_order_document'):
            tab = main.open_production_order_document()
            if tab and hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh_orders())
            return
        self._open_legacy_order_dialog()

    def _open_legacy_order_dialog(self):
        try:
            from views.dialogs.production_order_dialog import ProductionOrderDialog
            dialog = ProductionOrderDialog(self)
            if dialog.exec():
                self.refresh_orders()
        except Exception as exc:
            QMessageBox.warning(self, translate('warning'), str(exc))

    def view_order(self, index):
        row = self._source_row_for_index(self.orders_table, index)
        if row is None:
            return
        order_id = self.orders_model.get_id(row)
        self.view_order_by_id(order_id)

    def view_order_by_id(self, order_id):
        main = self._main_window_with_documents()
        if main and hasattr(main, 'open_production_order_details'):
            tab = main.open_production_order_details(order_id=order_id)
            if tab and hasattr(tab, 'saved'):
                tab.saved.connect(lambda *_: self.refresh_orders())
            return
        try:
            from views.dialogs.production_details_dialog import ProductionDetailsDialog
            dialog = ProductionDetailsDialog(self, order_id)
            dialog.exec()
            self.refresh_orders()
        except Exception as exc:
            QMessageBox.warning(self, translate('warning'), str(exc))

    def delete_order_by_id(self, order_id):
        reply = QMessageBox.question(self, translate("confirm_delete"), translate("confirm_delete_order"), QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success, msg = self.service.delete_production_order(order_id)
            except PermissionError as exc:
                self._handle_permission_denied(exc)
                return
            if success:
                show_toast(translate("production_order_deleted"), "success", self)
                self.refresh_orders()
            else:
                QMessageBox.critical(self, translate("error"), msg)

    def prev_page(self, target):
        if target == 'bom' and self.bom_page > 0:
            self.bom_page -= 1
            self.refresh_bom(reset_page=False)
        elif target == 'orders' and self.orders_page > 0:
            self.orders_page -= 1
            self.refresh_orders(reset_page=False)

    def next_page(self, target):
        if target == 'bom':
            self.bom_page += 1
            self.refresh_bom(reset_page=False)
        elif target == 'orders':
            self.orders_page += 1
            self.refresh_orders(reset_page=False)


# Phase110 offline guard markers: أوامر التصنيع
