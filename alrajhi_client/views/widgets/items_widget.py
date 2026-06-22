# -*- coding: utf-8 -*-
from decimal import Decimal

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QComboBox, QLabel, QHeaderView, QCheckBox
from i18n import translate, qt_layout_direction
from core.services.product_service import product_service
from core.services.settings_service import settings_service
from core.services.permission_service import permission_service
from core.item_types import STOCK, FINISHED_PRODUCT, SERVICE, normalize_item_type
from currency import currency
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from views.dialogs.batch_print_dialog import BatchPrintDialog
from utils import show_toast
from views.widgets.base_widget import BaseWidget
from features.items.material_shell_contract import material_shell_contract
from workspace.documents.document_permission_binder import DocumentPermissionBinder
from workspace.lists.list_workspace_contract import bind_list_workspace
from features.items.material_list_schema import (
    MATERIAL_PRESETS,
    material_column_keys,
    material_display_headers,
    material_preset_label,
    material_visible_keys_for_preset,
)


class ItemsWidget(BaseWidget):
    """Professional materials workspace.

    Phase 173 keeps the legacy BaseWidget action shell but upgrades the actual
    materials grid to the same ERP table discipline as transaction documents:
    schema-driven columns, role-aware cost visibility, stock filters, static
    business presets, SmartTable column chooser, per-user/per-branch/profile
    layout persistence, and barcode-label actions through the existing printing
    service path.
    """

    entity_name = translate("item")
    search_placeholder = translate("items_search_placeholder")
    headers = material_column_keys()
    has_delete = True
    has_add = True
    has_export = True
    has_print = True
    has_pagination = True
    page_size = 50
    extra_buttons = []
    edit_permission_action = permission_service.ACTION_EDIT_ITEMS

    def _display_headers(self):
        return material_display_headers()

    def _extra_buttons(self):
        return [
            (translate("print_barcode"), "print_barcode", "print_barcode_btn"),
            (translate("batch_print"), "batch_print", "batch_print_btn"),
        ]

    def __init__(self, parent=None):
        self.entity_name = translate('item')
        self.search_placeholder = translate('items_search_placeholder')
        self.display_headers = self._display_headers()
        self.extra_buttons = self._extra_buttons()
        self.category_filter = QComboBox()
        self.type_filter = QComboBox()
        self.stock_filter = QComboBox()
        self.preset_filter = QComboBox()
        self.density_filter = QComboBox()
        self.show_apparel_base_filter = QCheckBox(translate('show_apparel_base_materials'))
        self.show_apparel_base_filter.setToolTip(translate('show_apparel_base_materials_hint'))
        self._all_categories = []
        self._apparel_variant_count_cache = {}
        self.material_shell_contract = material_shell_contract()
        self.document_descriptor = self.material_shell_contract.descriptor
        self.document_permission_binder = DocumentPermissionBinder(self.document_descriptor)
        bind_list_workspace(self, 'materials')
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.table.set_table_identity('materials.workspace.items_grid')
        self.table.setProperty('print_title', translate('items_inventory'))
        self.load_categories()
        self.load_filters()
        self.category_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.type_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.stock_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.preset_filter.currentIndexChanged.connect(self._on_preset_changed)
        self.density_filter.currentIndexChanged.connect(self._on_density_changed)
        self.show_apparel_base_filter.stateChanged.connect(self._on_filter_changed)
        self._restore_material_grid_view()
        self.refresh()

    def _pref_key(self, name):
        try:
            from auth.session import UserSession
            user_id = str(UserSession.get_current_user_id() or 'anonymous')
            branch_id = str(UserSession.get_current_branch_id() or 'global')
        except Exception:
            user_id, branch_id = 'anonymous', 'global'
        try:
            profile = settings_service.get_active_profile() or {}
            profile_id = str(profile.get('id') or 1)
        except Exception:
            profile_id = '1'
        return f'materials/workspace/users/{user_id}/branches/{branch_id}/profiles/{profile_id}/{name}'

    def _active_preset(self):
        value = self.preset_filter.currentData()
        return value or 'manager'

    def _active_density(self):
        value = self.density_filter.currentData()
        return value or 'comfortable'

    def _cost_columns_allowed(self):
        try:
            hide_for_non_admin = bool(settings_service.get_bool('security/hide_cost_for_non_admin', False)) or permission_service.should_hide_profit()
            return not hide_for_non_admin
        except Exception:
            return True


    def can_material_action(self, action: str, document_id=None) -> bool:
        try:
            return self.document_permission_binder.can(action, document_id=document_id)
        except Exception:
            return True

    def material_shell_matrix(self):
        return self.material_shell_contract.as_matrix()

    def _setup_extra_buttons(self):
        for btn_text, callback_name, btn_name in self.extra_buttons:
            btn = QPushButton(btn_text)
            callback = getattr(self, callback_name, None)
            if callback:
                btn.clicked.connect(callback)
            btn.setEnabled(False)
            if callback_name in ('print_barcode', 'batch_print') and not self.can_material_action('print'):
                btn.setEnabled(False)
            setattr(self, btn_name, btn)
            self.btn_layout.addWidget(btn)

    def load_categories(self):
        self.category_filter.clear()
        self.category_filter.addItem(translate("all_categories"), None)
        try:
            self._all_categories = product_service.categories()
        except Exception:
            self._all_categories = []
        for c in self._all_categories:
            self.category_filter.addItem(c.get('name', ''), c.get('id'))

    def load_filters(self):
        """Add material-specific filters above the grid while keeping toolbar search unified."""
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(QLabel(translate("category_label")))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel(translate("item_type_label")))
        if self.type_filter.count() == 0:
            self.type_filter.addItem(translate("all_types"), None)
            self.type_filter.addItem(translate("stock_item_type"), STOCK)
            self.type_filter.addItem(translate("finished_product_type"), FINISHED_PRODUCT)
            self.type_filter.addItem(translate("service_item_type"), SERVICE)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addWidget(QLabel(translate('material_stock_filter')))
        if self.stock_filter.count() == 0:
            self.stock_filter.addItem(translate('all_stock_statuses'), None)
            self.stock_filter.addItem(translate('stock_ok'), 'ok')
            self.stock_filter.addItem(translate('stock_low'), 'low')
            self.stock_filter.addItem(translate('stock_empty'), 'out')
        filter_layout.addWidget(self.stock_filter)

        filter_layout.addWidget(QLabel(translate('material_view_preset')))
        if self.preset_filter.count() == 0:
            for preset_name in ('compact', 'cashier', 'warehouse', 'accountant', 'manager'):
                self.preset_filter.addItem(material_preset_label(preset_name), preset_name)
        filter_layout.addWidget(self.preset_filter)

        filter_layout.addWidget(QLabel(translate('row_density')))
        if self.density_filter.count() == 0:
            for density_name in ('compact', 'comfortable', 'touch'):
                self.density_filter.addItem(translate(f'density_{density_name}'), density_name)
        filter_layout.addWidget(self.density_filter)
        filter_layout.addWidget(self.show_apparel_base_filter)
        filter_layout.addStretch()
        self.layout().insertLayout(1, filter_layout)

    def _restore_material_grid_view(self):
        preset = settings_service.get(self._pref_key('active_preset'), settings_service.get('materials/list/default_preset', 'manager')) or 'manager'
        density = settings_service.get(self._pref_key('density'), settings_service.get('materials/list/density', 'comfortable')) or 'comfortable'
        for i in range(self.preset_filter.count()):
            if self.preset_filter.itemData(i) == preset:
                self.preset_filter.setCurrentIndex(i)
                break
        for i in range(self.density_filter.count()):
            if self.density_filter.itemData(i) == density:
                self.density_filter.setCurrentIndex(i)
                break
        self._apply_density(density)

    def _on_filter_changed(self):
        self.current_page = 0
        self.refresh()

    def _on_preset_changed(self):
        preset = self._active_preset()
        settings_service.set(self._pref_key('active_preset'), preset)
        self._apply_material_preset(preset)

    def _on_density_changed(self):
        density = self._active_density()
        settings_service.set(self._pref_key('density'), density)
        self._apply_density(density)

    def _apply_density(self, density):
        if hasattr(self.table, 'set_density'):
            self.table.set_density(density or 'comfortable')


    def _show_apparel_base_materials(self):
        return bool(self.show_apparel_base_filter.isChecked()) if hasattr(self, 'show_apparel_base_filter') else False

    def _item_has_apparel_variants(self, item):
        try:
            item_id = int((item or {}).get('id') or 0)
        except Exception:
            item_id = 0
        if not item_id:
            return False
        if item_id not in self._apparel_variant_count_cache:
            try:
                self._apparel_variant_count_cache[item_id] = bool(product_service.item_variants(item_id))
            except Exception:
                self._apparel_variant_count_cache[item_id] = False
        return bool(self._apparel_variant_count_cache[item_id])

    def _filter_apparel_base_materials(self, items):
        if self._show_apparel_base_materials():
            return list(items or [])
        return [item for item in (items or []) if not self._item_has_apparel_variants(item)]

    def _filter_limit(self):
        try:
            return max(500, int(settings_service.get('materials/list/filter_limit', '5000') or 5000))
        except Exception:
            return 5000

    def fetch_data(self, search=None, limit=None, offset=None):
        return product_service.items_pair(search=search, limit=limit, offset=offset)

    def get_total_count(self, search=None):
        _, total = product_service.items_pair(search=search, limit=1, offset=0)
        return total

    def delete_item(self, item_id):
        if not self.can_material_action('delete', document_id=item_id):
            show_toast(permission_service.denied_message(permission_service.ACTION_DELETE), 'warning', self)
            return
        product_service.delete_item(item_id)

    def _main_window(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'open_item_document'):
                return parent
            parent = parent.parent()
        return None

    def open_dialog(self, is_edit=False, item_id=None):
        main = self._main_window()
        if main is not None:
            main.open_item_document(item_id=item_id if is_edit else None)
            return
        show_toast(translate('material_workspace_unavailable'), 'error', self)

    def get_item_name_from_row(self, row):
        if self.model and row < self.model.rowCount():
            row_data = self.model.get_row(row)
            return row_data.get('name', translate('item'))
        return translate("item")

    def _stock_status(self, available_qty, reorder_level):
        if available_qty <= 0:
            return translate('stock_empty'), 'out'
        if reorder_level > 0 and available_qty <= reorder_level:
            return translate('stock_low'), 'low'
        return translate('stock_ok'), 'ok'

    def _passes_filters(self, item):
        category_id = self.category_filter.currentData()
        item_type = self.type_filter.currentData()
        stock_filter = self.stock_filter.currentData()
        if category_id and item.get('category_id') != category_id:
            return False
        if item_type and normalize_item_type(item.get('item_type')) != normalize_item_type(item_type):
            return False
        if stock_filter:
            available_qty = Decimal(str(item.get('available', item.get('quantity', 0)) or 0))
            reorder_level = Decimal(str(item.get('reorder_level', 0) or 0))
            _, severity = self._stock_status(available_qty, reorder_level)
            if severity != stock_filter:
                return False
        return True

    def _format_qty(self, value):
        try:
            return settings_service.format_quantity(value)
        except Exception:
            return f"{Decimal(str(value or 0)):.2f}"

    def prepare_table_data(self, items):
        data = []
        display_curr = currency.get_display_currency()
        item_ids = [it.get('id') for it in items if it.get('id') is not None]
        sold_map = product_service.sold_quantities(item_ids)
        show_cost = self._cost_columns_allowed()
        for it in items:
            item_id = it.get('id')
            current_qty = Decimal(str(it.get('quantity', it.get('available', 0)) or 0))
            available_qty = Decimal(str(it.get('available', current_qty) or 0))
            sold_qty = Decimal(str(sold_map.get(int(item_id), 0))) if item_id is not None else Decimal('0')
            unit_cost_usd = Decimal(str(it.get('average_cost', it.get('purchase_price', 0)) or 0))
            total_value_usd = available_qty * unit_cost_usd
            unit_cost_display = currency.convert(unit_cost_usd, currency.storage_currency(), display_curr)
            total_value_display = currency.convert(total_value_usd, currency.storage_currency(), display_curr)
            reorder_level = Decimal(str(it.get('reorder_level', 0) or 0))
            status_label, severity = self._stock_status(available_qty, reorder_level)
            data.append({
                'id': it.get('id'),
                'name': it.get('name', ''),
                'barcode': it.get('barcode') or '',
                'category': it.get('category_name') or '',
                'item_type': it.get('item_type') or '',
                'quantity': self._format_qty(current_qty),
                'unit': it.get('unit') or translate('unit_piece'),
                'sold_quantity': self._format_qty(sold_qty),
                'available_quantity': self._format_qty(available_qty),
                'stock_status': status_label,
                'reorder_level': self._format_qty(reorder_level),
                'available_total': currency.format_amount(total_value_display) if show_cost else '•••',
                'unit_cost': currency.format_amount(unit_cost_display) if show_cost else '•••',
                '_row_status': severity,
            })
        return data

    def get_data_keys(self):
        return material_column_keys()

    def _apply_material_preset(self, preset=None):
        if not self.table or not self.model:
            return
        preset = preset or self._active_preset()
        keys = set(material_visible_keys_for_preset(preset))
        if not self._cost_columns_allowed():
            keys.discard('available_total')
            keys.discard('unit_cost')
        data_keys = self.get_data_keys()
        for col, key in enumerate(data_keys):
            self.table.setColumnHidden(col, key not in keys)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if hasattr(self.table, 'fit_columns_to_view'):
            self.table.fit_columns_to_view()
        if hasattr(self.table, 'save_layout'):
            self.table.save_layout()

    def print_barcode(self):
        if not permission_service.can(permission_service.ACTION_PRINT_BARCODES) or not self.can_material_action('print'):
            show_toast(permission_service.denied_message(permission_service.ACTION_PRINT_BARCODES), 'warning', self)
            return
        selected_rows = self.table.selected_source_rows() if hasattr(self.table, 'selected_source_rows') else [r.row() for r in self.table.selectionModel().selectedRows()]
        if not selected_rows:
            show_toast(translate("select_item_first"), "warning", self)
            return
        row = selected_rows[0]
        item_id = self.model.get_id(row)
        if not item_id:
            return
        item = product_service.item_by_id(item_id)
        if not item or not item.get('barcode'):
            show_toast(translate("item_has_no_barcode"), "error", self)
            return
        dialog = BatchPrintDialog(self, selected_items=[item])
        dialog.exec()

    def batch_print(self):
        if not permission_service.can(permission_service.ACTION_PRINT_BARCODES) or not self.can_material_action('print'):
            show_toast(permission_service.denied_message(permission_service.ACTION_PRINT_BARCODES), 'warning', self)
            return
        dialog = BatchPrintDialog(self)
        dialog.exec()

    def _update_action_buttons_state(self):
        super()._update_action_buttons_state()
        has_selection = len(self.table.selectionModel().selectedRows()) > 0 if self.table.selectionModel() else False
        can_print = self.can_material_action('print')
        if hasattr(self, 'print_barcode_btn'):
            self.print_barcode_btn.setEnabled(has_selection and can_print)
        if hasattr(self, 'batch_print_btn'):
            self.batch_print_btn.setEnabled(bool(can_print))

    def refresh(self):
        search = self.search_edit.text().strip().lower() or None
        self._apparel_variant_count_cache = {}
        has_material_filters = any([
            self.category_filter.currentData(),
            self.type_filter.currentData(),
            self.stock_filter.currentData(),
            not self._show_apparel_base_materials(),
        ])
        if has_material_filters:
            raw_items, raw_total = product_service.items_pair(search=search, limit=self._filter_limit(), offset=0)
            filtered = [it for it in self._filter_apparel_base_materials(raw_items or []) if self._passes_filters(it)]
            self.total_count = len(filtered)
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)
            start = self.current_page * self.page_size
            items = filtered[start:start + self.page_size]
        else:
            offset = self.current_page * self.page_size
            items, self.total_count = self.fetch_data(search=search, limit=self.page_size, offset=offset)
            items = self._filter_apparel_base_materials(items)
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)

        data = self.prepare_table_data(items or [])
        self.display_headers = self._display_headers()
        self.model = GenericTableModel(data, self.display_headers, key_fields=['id'], data_keys=self.get_data_keys())
        self.table.setModel(self.model)
        self._apply_material_preset(self._active_preset())
        self._apply_density(self._active_density())
        if self.has_pagination:
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            self.page_label.setText(translate("page_of", page=self.current_page + 1, pages=total_pages))
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page + 1 < total_pages)
        visible_count = len(data)
        start_row = 0 if self.total_count == 0 else self.current_page * self.page_size + 1
        end_row = min(self.total_count, self.current_page * self.page_size + visible_count)
        counter_text = translate("showing_records", start=start_row, end=end_row, total=self.total_count)
        self.status_label.setText(counter_text)
        if hasattr(self, 'toolbar'):
            self.toolbar.set_counter(counter_text)
        sm = self.table.selectionModel()
        if sm is not None:
            try:
                sm.selectionChanged.disconnect(self._on_selection_changed)
            except Exception:
                pass
            sm.selectionChanged.connect(self._on_selection_changed)
        self._update_action_buttons_state()
