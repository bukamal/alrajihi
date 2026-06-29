# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QShortcut,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QVBoxLayout,
)

from core.services.barcode_label_service import barcode_label_service
from core.services.barcode_service import barcode_service, BarcodeError
from core.services.barcode_input_service import barcode_input_service
from core.services.permission_service import permission_service
from core.services.product_service import product_service
from core.services.settings_service import settings_service
from core.item_types import STOCK, FINISHED_PRODUCT, SERVICE, normalize_item_type, is_stock
from i18n import qt_layout_direction, translate
from currency import currency
from core.money_display_policy import format_money
from printing.printing_service import printing_service
from ui.editable_smart_grid import EditableSmartGrid
from ui.form_validation import FormValidator, make_error_label
from ui.visual_state import set_visual_state
from utils import show_toast
from workspace.documents import BaseDocumentTab
from workspace.documents.document_permission_binder import DocumentPermissionBinder
from features.items.material_shell_contract import (
    MATERIAL_DOCUMENT_TYPE,
    material_descriptor,
    material_shell_matrix,
)


def tr(key: str, **kwargs) -> str:
    return translate(key, **kwargs)


class MaterialDocumentTab(BaseDocumentTab):
    # Phase 254 contract migration; legacy audit needle: DOCUMENT_DESCRIPTOR = descriptor_for("material")
    DOCUMENT_DESCRIPTOR = material_descriptor()
    """Unified tab-based material editor.

    This replaces the old modal ItemDialog for day-to-day material editing while
    preserving the project's existing services: product_service, barcode_service,
    barcode_input_service, barcode_label_service, settings_service and the
    local/remote gateway contract.
    """

    UNIT_COL_NAME = 0
    UNIT_COL_FACTOR = 1
    UNIT_COL_BARCODE = 2
    UNIT_COL_NOTES = 3

    def __init__(self, parent=None, item_id=None) -> None:
        super().__init__(MATERIAL_DOCUMENT_TYPE, document_id=item_id, parent=parent)
        self.document_descriptor = self.DOCUMENT_DESCRIPTOR
        self.document_permission_binder = DocumentPermissionBinder(self.document_descriptor)
        self.item_id = item_id
        self.is_edit = item_id is not None
        self.display_curr = currency.get_display_currency()
        self.symbol = currency.get_currency_symbol(self.display_curr)
        self.material_shell_contract = material_shell_matrix()
        self.setProperty('document_shell_type', MATERIAL_DOCUMENT_TYPE)
        self.setProperty('document_api_resource', self.document_descriptor.api_resource)
        self.setProperty('document_network_mode', self.document_descriptor.network_mode)
        self.categories: List[Dict[str, Any]] = []
        self.material_settings = self._load_material_settings()
        self.security_policy = self._load_material_security_policy()
        self.activity_summary: Dict[str, Any] = {'blocking_total': 0, 'has_movements': False}
        self._build_ui()
        self.reload_categories()
        if self.is_edit:
            self.load_item()
        else:
            self._prepare_new_material()
        self._connect_dirty_tracking()
        self._install_shortcuts()
        self._apply_security_policy()
        self.set_dirty(False)

    def _load_material_settings(self) -> Dict[str, Any]:
        try:
            return settings_service.get_material_settings()
        except Exception:
            printing = settings_service.get_printing_settings() if hasattr(settings_service, 'get_printing_settings') else {}
            return {
                'default_barcode_symbology': 'EAN13',
                'auto_generate_barcode_for_new_material': True,
                'require_barcode_for_stock_items': False,
                'allow_manual_barcode_edit': True,
                'ean13_internal_prefix': '290',
                'code128_prefix': 'ITM',
                'default_unit': tr('unit_piece'),
                'default_item_type': STOCK,
                'quantity_decimals': 2,
                'price_decimals': 2,
                'barcode_label_options': {
                    'label_size': printing.get('barcode_label_size', '50x30'),
                    'symbology': printing.get('barcode_symbology', 'AUTO'),
                    'columns': printing.get('barcode_columns', 2),
                    'show_company': printing.get('barcode_show_company', True),
                    'show_logo': printing.get('barcode_show_logo', True),
                    'show_qr': printing.get('barcode_show_qr', True),
                    'show_name': printing.get('barcode_show_name', True),
                    'show_price': printing.get('barcode_show_price', True),
                    'show_barcode_text': printing.get('barcode_show_text', True),
                },
            }


    def _load_material_security_policy(self) -> Dict[str, Any]:
        """Return the effective material security policy for this user/session."""
        can_edit = permission_service.can(permission_service.ACTION_EDIT_ITEMS)
        can_print = permission_service.can(permission_service.ACTION_PRINT_BARCODES)
        can_view_costs = permission_service.can(permission_service.ACTION_VIEW_ITEM_COSTS)
        can_edit_opening = permission_service.can(permission_service.ACTION_EDIT_OPENING_STOCK)
        if bool(self.material_settings.get('hide_cost_for_non_admin', False)):
            can_view_costs = can_view_costs and not permission_service.should_hide_profit()
        return {
            'can_edit': bool(can_edit),
            'can_print_barcodes': bool(can_print),
            'can_view_costs': bool(can_view_costs),
            'can_edit_opening_stock': bool(can_edit_opening),
        }

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        self.setProperty('visualWorkspaceType', 'materials')
        self.setProperty('materialsVisualPhase', '445')
        self.setProperty('visualRole', 'material_editor')
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        # Phase326: the workspace/tab title already identifies this document.
        # Do not render the top identity card ("new material") above the form;
        # keep the editor focused on the business fields.
        self.header_frame = self._build_header()
        self.header_frame.setVisible(False)

        body = QSplitter(Qt.Horizontal, self)
        body.setObjectName('ItemEditorResponsiveSplitter')
        body.setProperty('visualRole', 'workspace_splitter')
        body.setProperty('materialsVisualPhase', '445')
        body.setChildrenCollapsible(False)
        body.setProperty('shell_component', 'material.master_detail_splitter')
        root.addWidget(body, 1)

        left = QFrame(self)
        left.setObjectName('MaterialEditorPrimaryColumn')
        left.setProperty('visualRole', 'material_editor_column')
        left.setProperty('materialsVisualPhase', '445')
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._build_basic_panel())
        left_layout.addWidget(self._build_pricing_inventory_panel())
        left_layout.addStretch(1)
        body.addWidget(left)
        body.setStretchFactor(0, 3)

        right = QFrame(self)
        right.setObjectName('MaterialEditorDetailColumn')
        right.setProperty('visualRole', 'material_editor_column')
        right.setProperty('materialsVisualPhase', '445')
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        right_layout.addWidget(self._build_barcode_panel())
        right_layout.addWidget(self._build_units_panel(), 1)
        body.addWidget(right)
        body.setStretchFactor(1, 4)

        root.addWidget(self._build_bottom_actions())
        self._apply_styles()

    def _build_header(self) -> QFrame:
        header = QFrame(self)
        header.setObjectName('DocumentHeaderCard')
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_label = QLabel(tr('material_title_edit') if self.is_edit else tr('material_title_new'))
        self.title_label.setObjectName('DocumentTitle')
        subtitle = QLabel(tr('material_subtitle'))
        subtitle.setObjectName('DocumentSubtitle')
        title_box.addWidget(self.title_label)
        title_box.addWidget(subtitle)
        self.shell_badge_label = QLabel(tr('material_shell_badge'))
        self.shell_badge_label.setObjectName('DocumentShellBadge')
        title_box.addWidget(self.shell_badge_label)
        layout.addLayout(title_box, 1)

        # Phase 229: document headers are informational; commands live in BottomActionBar.
        return header

    def _build_basic_panel(self) -> QGroupBox:
        box = QGroupBox(tr('material_basic_data'), self)
        box.setObjectName('MaterialBasicCard')
        box.setProperty('visualRole', 'material_form_card')
        box.setProperty('materialsVisualPhase', '445')
        form = QFormLayout(box)
        form.setLabelAlignment(Qt.AlignRight)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr('material_name_placeholder'))
        self.name_error = make_error_label()
        form.addRow(tr('item_name_label'), self.name_edit)
        form.addRow('', self.name_error)

        self.category_combo = QComboBox()
        form.addRow(tr('category_label'), self.category_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItem(tr('stock_item_type'), STOCK)
        self.type_combo.addItem(tr('finished_product_type'), FINISHED_PRODUCT)
        self.type_combo.addItem(tr('service_item_type'), SERVICE)
        form.addRow(tr('item_type_field'), self.type_combo)

        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText(tr('base_unit_placeholder'))
        self.unit_error = make_error_label()
        form.addRow(tr('base_unit_label'), self.unit_edit)
        form.addRow('', self.unit_error)
        return box

    def _build_pricing_inventory_panel(self) -> QGroupBox:
        box = QGroupBox(tr('material_pricing_inventory'), self)
        box.setObjectName('MaterialPricingCard')
        box.setProperty('visualRole', 'material_form_card')
        box.setProperty('materialsVisualPhase', '445')
        form = QFormLayout(box)
        form.setLabelAlignment(Qt.AlignRight)

        price_decimals = int(self.material_settings.get('price_decimals', 2) or 2)
        qty_decimals = int(self.material_settings.get('quantity_decimals', 2) or 2)

        self.purchase_spin = QDoubleSpinBox()
        self.purchase_spin.setRange(0, 999999999)
        self.purchase_spin.setDecimals(price_decimals)
        self.purchase_spin.setPrefix(f'{self.symbol} ')
        self.selling_spin = QDoubleSpinBox()
        self.selling_spin.setRange(0, 999999999)
        self.selling_spin.setDecimals(price_decimals)
        self.selling_spin.setPrefix(f'{self.symbol} ')
        self.purchase_label = QLabel(tr('purchase_price'))
        self.selling_label = QLabel(tr('selling_price'))
        form.addRow(self.purchase_label, self.purchase_spin)
        form.addRow(self.selling_label, self.selling_spin)

        self.margin_label = QLabel(tr('profit_margin', value='—'))
        self.margin_label.setObjectName('InfoLabel')
        form.addRow('', self.margin_label)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0, 999999999)
        self.qty_spin.setDecimals(qty_decimals)
        self.qty_error = make_error_label()
        self.reorder_spin = QDoubleSpinBox()
        self.reorder_spin.setRange(0, 999999999)
        self.reorder_spin.setDecimals(qty_decimals)
        self.reorder_error = make_error_label()
        form.addRow(tr('opening_quantity'), self.qty_spin)
        form.addRow('', self.qty_error)
        form.addRow(tr('reorder_level'), self.reorder_spin)
        form.addRow('', self.reorder_error)

        self.stock_warning_label = QLabel(tr('stock_no_warning'))
        self.stock_warning_label.setObjectName('InfoLabel')
        form.addRow('', self.stock_warning_label)
        return box

    def _build_barcode_panel(self) -> QGroupBox:
        box = QGroupBox(tr('material_barcode_panel'), self)
        box.setObjectName('MaterialBarcodeCard')
        box.setProperty('visualRole', 'material_form_card')
        box.setProperty('materialsVisualPhase', '445')
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.barcode_edit = QLineEdit()
        self.barcode_edit.setPlaceholderText(tr('barcode_placeholder'))
        self.barcode_edit.setReadOnly(not bool(self.material_settings.get('allow_manual_barcode_edit', True)))
        self.barcode_type_combo = QComboBox()
        self.barcode_type_combo.addItem('EAN13', 'EAN13')
        self.barcode_type_combo.addItem('CODE128', 'CODE128')
        default_sym = str(self.material_settings.get('default_barcode_symbology') or 'EAN13').upper()
        idx = self.barcode_type_combo.findData(default_sym if default_sym in ('EAN13', 'CODE128') else 'EAN13')
        if idx >= 0:
            self.barcode_type_combo.setCurrentIndex(idx)
        row.addWidget(self.barcode_edit, 1)
        row.addWidget(self.barcode_type_combo)
        layout.addLayout(row)

        btns = QHBoxLayout()
        self.generate_btn = QPushButton(tr('material_generate_barcode'))
        self.scan_camera_btn = QPushButton(tr('material_scan_camera'))
        self.print_label_btn = QPushButton(tr('material_print_label'))
        self.generate_btn.clicked.connect(self.generate_barcode)
        self.scan_camera_btn.clicked.connect(self.scan_barcode_with_camera)
        self.print_label_btn.clicked.connect(self.workspace_print)
        btns.addWidget(self.generate_btn)
        btns.addWidget(self.scan_camera_btn)
        btns.addWidget(self.print_label_btn)
        layout.addLayout(btns)

        self.barcode_status_label = QLabel(tr('barcode_optional_hint'))
        self.barcode_status_label.setObjectName('BarcodeStatus')
        self.barcode_error = make_error_label()
        layout.addWidget(self.barcode_status_label)
        layout.addWidget(self.barcode_error)
        return box

    def _build_units_panel(self) -> QGroupBox:
        box = QGroupBox(tr('material_units_panel'), self)
        box.setObjectName('MaterialUnitsCard')
        box.setProperty('visualRole', 'material_form_card')
        box.setProperty('materialsVisualPhase', '445')
        layout = QVBoxLayout(box)
        layout.setSpacing(8)

        self.units_table = EditableSmartGrid(0, 4, self, identity='materials.units')
        self.units_table.setProperty('visualRole', 'materials_table')
        self.units_table.setProperty('materialsVisualPhase', '445')
        self.units_table.setHorizontalHeaderLabels([
            tr('material_unit'),
            tr('conversion_factor'),
            tr('material_unit_barcode'),
            tr('notes'),
        ])
        header = self.units_table.horizontalHeader()
        header.setSectionResizeMode(self.UNIT_COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(self.UNIT_COL_FACTOR, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.UNIT_COL_BARCODE, QHeaderView.Stretch)
        header.setSectionResizeMode(self.UNIT_COL_NOTES, QHeaderView.Stretch)
        layout.addWidget(self.units_table, 1)

        btns = QHBoxLayout()
        self.add_unit_btn = QPushButton(tr('add_unit'))
        self.remove_unit_btn = QPushButton(tr('remove_selected'))
        self.generate_unit_barcode_btn = QPushButton(tr('material_generate_unit_barcode'))
        self.add_unit_btn.clicked.connect(self.add_unit_row)
        self.remove_unit_btn.clicked.connect(self.remove_selected_unit_row)
        self.generate_unit_barcode_btn.clicked.connect(self.generate_barcode_for_selected_unit)
        btns.addWidget(self.add_unit_btn)
        btns.addWidget(self.remove_unit_btn)
        btns.addWidget(self.generate_unit_barcode_btn)
        btns.addStretch(1)
        layout.addLayout(btns)
        return box

    def _build_bottom_actions(self) -> QFrame:
        bar = QFrame(self)
        bar.setObjectName('MaterialEditorActionBar')
        bar.setProperty('visualRole', 'material_action_bar')
        bar.setProperty('materialsVisualPhase', '445')
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        self.new_btn = QPushButton(tr('new'))
        self.generate_barcode_btn = QPushButton(tr('material_generate_barcode'))
        self.save_btn = QPushButton(tr('save'))
        self.save_btn.setObjectName('primary')
        self.save_label_btn = QPushButton(tr('material_save_and_print_label'))
        self.save_label_btn.setVisible(False)
        self.close_btn = QPushButton(tr('close'))
        self.new_btn.clicked.connect(self.clear_for_new)
        self.generate_barcode_btn.clicked.connect(self.generate_barcode)
        self.save_btn.clicked.connect(self.workspace_save)
        self.save_label_btn.clicked.connect(self.save_and_print_label)
        self.close_btn.clicked.connect(self.request_close)
        layout.addWidget(self.new_btn)
        layout.addWidget(self.generate_barcode_btn)
        layout.addStretch(1)
        layout.addWidget(self.save_label_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.close_btn)
        return bar

    def _apply_styles(self) -> None:
        """Phase445: use centralized material visual identity instead of local QSS."""
        for widget in (self, self.header_frame):
            try:
                widget.setProperty('materialsVisualPhase', '445')
            except Exception:
                pass
        try:
            self.setStyleSheet('')
            self.style().unpolish(self)
            self.style().polish(self)
        except Exception:
            pass

    def _connect_dirty_tracking(self) -> None:
        for widget in (self.name_edit, self.barcode_edit, self.unit_edit):
            widget.textChanged.connect(lambda _text: self.set_dirty(True))
        self.barcode_edit.textChanged.connect(lambda _text: self.update_barcode_status())
        for widget in (self.category_combo, self.type_combo, self.barcode_type_combo):
            widget.currentIndexChanged.connect(lambda _index: self.set_dirty(True))
        for widget in (self.purchase_spin, self.selling_spin, self.qty_spin, self.reorder_spin):
            widget.valueChanged.connect(lambda _value: self.set_dirty(True))
        self.purchase_spin.valueChanged.connect(lambda _value: self.update_margin_preview())
        self.selling_spin.valueChanged.connect(lambda _value: self.update_margin_preview())
        self.qty_spin.valueChanged.connect(lambda _value: self.update_stock_preview())
        self.reorder_spin.valueChanged.connect(lambda _value: self.update_stock_preview())
        self.units_table.itemChanged.connect(lambda _item: self.set_dirty(True))

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, activated=self.workspace_save)
        QShortcut(QKeySequence('Ctrl+P'), self, activated=self.workspace_print)
        QShortcut(QKeySequence('Ctrl+B'), self, activated=self.generate_barcode)
        QShortcut(QKeySequence('Ctrl+Shift+B'), self, activated=self.scan_barcode_with_camera)


    def _editable_widgets(self):
        return [
            self.name_edit, self.category_combo, self.type_combo, self.unit_edit,
            self.purchase_spin, self.selling_spin, self.qty_spin, self.reorder_spin,
            self.barcode_edit, self.barcode_type_combo, self.units_table,
            self.add_unit_btn, self.remove_unit_btn, self.generate_unit_barcode_btn,
            self.generate_btn, self.scan_camera_btn, self.generate_barcode_btn,
        ]

    def _apply_security_policy(self) -> None:
        """Apply user/role/security settings without bypassing services."""
        can_edit = bool(self.security_policy.get('can_edit', True)) and self.can_document_action('save')
        can_print = bool(self.security_policy.get('can_print_barcodes', True)) and self.can_document_action('print')
        can_view_costs = bool(self.security_policy.get('can_view_costs', True))
        can_edit_opening = bool(self.security_policy.get('can_edit_opening_stock', True))

        if not can_edit:
            for widget in self._editable_widgets():
                try:
                    widget.setEnabled(False)
                except Exception:
                    pass
            self.save_btn.setEnabled(False)
            self.save_label_btn.setEnabled(False)
            self.stock_warning_label.setText(tr('material_readonly_permission'))
            set_visual_state(self.stock_warning_label, 'danger', weight='strong', size='caption', role='semantic_status')
        else:
            self.save_btn.setEnabled(True)
            self.save_label_btn.setEnabled(can_print)

        if not can_print:
            self.print_label_btn.setEnabled(False)
            self.save_label_btn.setEnabled(False)

        if not can_view_costs:
            for widget_name in ('purchase_label', 'purchase_spin', 'margin_label'):
                widget = getattr(self, widget_name, None)
                if widget is not None:
                    widget.setVisible(False)

        locked_by_activity = bool(self.is_edit and self.activity_summary.get('has_movements') and self.material_settings.get('prevent_opening_quantity_edit_after_activity', True))
        if locked_by_activity or not can_edit_opening:
            self.qty_spin.setEnabled(False)
            if locked_by_activity:
                self.stock_warning_label.setText(tr('material_opening_qty_locked'))
            elif not can_edit_opening:
                self.stock_warning_label.setText(tr('material_opening_qty_permission_locked'))
            set_visual_state(self.stock_warning_label, 'warning', weight='strong', size='caption', role='semantic_status')

        # material_shell_permission_binding: keep document contract actions in sync with legacy policy.
        try:
            self.apply_document_permissions()
        except Exception:
            pass

    def _load_activity_summary(self) -> None:
        if not self.item_id:
            self.activity_summary = {'blocking_total': 0, 'has_movements': False}
            return
        try:
            self.activity_summary = product_service.item_activity_summary(int(self.item_id)) or {'blocking_total': 0, 'has_movements': False}
        except Exception:
            self.activity_summary = {'blocking_total': 0, 'has_movements': False}

    def _prepare_new_material(self) -> None:
        if bool(self.material_settings.get('auto_generate_barcode_for_new_material', True)):
            self.generate_barcode(silent=True)
        self.unit_edit.setText(str(self.material_settings.get('default_unit') or tr('unit_piece')))
        self.add_unit_row(tr('unit_box') if tr('unit_box') != 'unit_box' else 'علبة', 1)
        default_type = normalize_item_type(self.material_settings.get('default_item_type') or STOCK)
        idx = self.type_combo.findData(default_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.set_document_title(tr('material_title_new'))
        self.update_barcode_status()
        self.update_margin_preview()
        self.update_stock_preview()

    def reload_categories(self) -> None:
        current = self.category_combo.currentData() if hasattr(self, 'category_combo') else None
        self.categories = product_service.categories()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem(tr('no_category'), None)
        for cat in self.categories:
            self.category_combo.addItem(cat.get('full_name') or cat.get('name', ''), cat.get('id'))
        if current is not None:
            idx = self.category_combo.findData(current)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)

    def add_unit_row(self, unit_name: str = '', conversion_factor: float = 1.0, barcode: str = '', notes: str = '') -> None:
        row = self.units_table.rowCount()
        self.units_table.insertRow(row)
        self.units_table.setItem(row, self.UNIT_COL_NAME, QTableWidgetItem(str(unit_name or '')))
        self.units_table.setItem(row, self.UNIT_COL_FACTOR, QTableWidgetItem(str(conversion_factor or 1)))
        self.units_table.setItem(row, self.UNIT_COL_BARCODE, QTableWidgetItem(str(barcode or '')))
        self.units_table.setItem(row, self.UNIT_COL_NOTES, QTableWidgetItem(str(notes or '')))

    def remove_selected_unit_row(self) -> None:
        row = self.units_table.currentRow()
        if row >= 0:
            self.units_table.removeRow(row)
            self.set_dirty(True)

    def _load_item_units(self) -> None:
        self.units_table.blockSignals(True)
        self.units_table.setRowCount(0)
        if not self.item_id:
            self.units_table.blockSignals(False)
            return
        try:
            units = product_service.item_units(int(self.item_id))
        except Exception:
            units = []
        for unit in units or []:
            self.add_unit_row(
                unit.get('unit_name') or unit.get('name') or '',
                unit.get('conversion_factor') or 1,
                unit.get('barcode') or unit.get('unit_barcode') or '',
                unit.get('notes') or '',
            )
        self.units_table.blockSignals(False)

    def _collect_item_units(self) -> List[Dict[str, Any]]:
        units: List[Dict[str, Any]] = []
        seen = set()
        for row in range(self.units_table.rowCount()):
            name_item = self.units_table.item(row, self.UNIT_COL_NAME)
            factor_item = self.units_table.item(row, self.UNIT_COL_FACTOR)
            barcode_item = self.units_table.item(row, self.UNIT_COL_BARCODE)
            notes_item = self.units_table.item(row, self.UNIT_COL_NOTES)
            name = (name_item.text() if name_item else '').strip()
            if not name or name in seen:
                continue
            try:
                factor = float((factor_item.text() if factor_item else '1') or 1)
            except Exception:
                factor = 1.0
            if factor <= 0:
                factor = 1.0
            unit_barcode = barcode_input_service.normalize(barcode_item.text() if barcode_item else '')
            seen.add(name)
            units.append({
                'unit_name': name,
                'conversion_factor': factor,
                'barcode': unit_barcode or None,
                'unit_barcode': unit_barcode or None,
                'notes': (notes_item.text() if notes_item else '').strip(),
            })
        return units

    def _save_item_units(self, item_id: int, units: List[Dict[str, Any]] | None = None) -> None:
        units = units if units is not None else self._collect_item_units()
        product_service.replace_units(int(item_id), units)

    def load_item(self) -> None:
        item = product_service.item_by_id(int(self.item_id))
        if not item:
            show_toast(tr('item_not_found'), 'error', self)
            return
        self.name_edit.setText(item.get('name', ''))
        self.barcode_edit.setText(item.get('barcode') or '')
        category_id = item.get('category_id')
        if category_id is not None:
            idx = self.category_combo.findData(category_id)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
        item_type = normalize_item_type(item.get('item_type') or STOCK)
        idx = self.type_combo.findData(item_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self.unit_edit.setText(item.get('unit') or tr('unit_piece'))
        self.purchase_spin.setValue(float(currency.convert(item.get('purchase_price') or 0, currency.storage_currency(), self.display_curr)))
        self.selling_spin.setValue(float(currency.convert(item.get('selling_price') or 0, currency.storage_currency(), self.display_curr)))
        self.qty_spin.setValue(float(item.get('opening_quantity', item.get('quantity') or 0) or 0))
        self.reorder_spin.setValue(float(item.get('reorder_level') or 0))
        self._load_item_units()
        self._load_activity_summary()
        self.set_document_title(f"{tr('item')}: {item.get('name', self.item_id)}")
        self.update_barcode_status()
        self.update_margin_preview()
        self.update_stock_preview()
        self._apply_security_policy()
        self.set_dirty(False)

    def clear_for_new(self) -> None:
        if self.is_edit:
            show_toast(tr('new_item_only'), 'info', self)
            return
        self.name_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.unit_edit.setText(str(self.material_settings.get('default_unit') or tr('unit_piece')))
        self.purchase_spin.setValue(0)
        self.selling_spin.setValue(0)
        self.qty_spin.setValue(0)
        self.reorder_spin.setValue(0)
        self.units_table.setRowCount(0)
        self.add_unit_row(tr('unit_box') if tr('unit_box') != 'unit_box' else 'علبة', 1)
        self.generate_barcode(silent=True)
        self.name_edit.setFocus()
        self._load_activity_summary()
        self._apply_security_policy()
        self.set_dirty(False)

    def generate_barcode(self, silent: bool = False) -> None:
        if not self.security_policy.get('can_edit', True) or not self.can_document_action('save'):
            if not silent:
                show_toast(self.permission_denied_message('save'), 'error', self)
            return
        sym = self.barcode_type_combo.currentData() or self.barcode_type_combo.currentText() or 'EAN13'
        prefix = self.material_settings.get('ean13_internal_prefix') if str(sym).upper() == 'EAN13' else self.material_settings.get('code128_prefix')
        try:
            self.barcode_edit.setText(product_service.generate_barcode(str(sym), prefix=prefix))
            self.update_barcode_status()
            if not silent:
                show_toast(tr('material_barcode_generated'), 'success', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def generate_barcode_for_selected_unit(self) -> None:
        if not self.security_policy.get('can_edit', True) or not self.can_document_action('save'):
            show_toast(self.permission_denied_message('save'), 'error', self)
            return
        row = self.units_table.currentRow()
        if row < 0:
            show_toast(tr('material_select_unit_first'), 'info', self)
            return
        sym = self.barcode_type_combo.currentData() or 'CODE128'
        prefix = self.material_settings.get('ean13_internal_prefix') if str(sym).upper() == 'EAN13' else self.material_settings.get('code128_prefix')
        try:
            code = product_service.generate_barcode(str(sym), prefix=prefix)
            self.units_table.setItem(row, self.UNIT_COL_BARCODE, QTableWidgetItem(code))
            self.set_dirty(True)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def scan_barcode_with_camera(self) -> None:
        try:
            from views.dialogs.barcode_camera_dialog import BarcodeCameraDialog
            dialog = BarcodeCameraDialog(self)
            dialog.barcode_scanned.connect(self.on_camera_barcode_scanned)
            dialog.exec()
        except Exception as exc:
            show_toast(tr('camera_scan_failed', error=str(exc)), 'error', self)

    def on_camera_barcode_scanned(self, value, symbology=None) -> None:
        normalized = barcode_input_service.normalize(value)
        self.barcode_edit.setText(normalized)
        if symbology:
            idx = self.barcode_type_combo.findData(str(symbology).upper())
            if idx >= 0:
                self.barcode_type_combo.setCurrentIndex(idx)
        self.update_barcode_status()

    def update_barcode_status(self) -> None:
        value = barcode_input_service.normalize(self.barcode_edit.text())
        if not value:
            self.barcode_status_label.setText(tr('barcode_optional_hint'))
            set_visual_state(self.barcode_status_label, 'muted', size='caption', role='semantic_status')
            FormValidator.clear(self.barcode_error, self.barcode_edit)
            return
        try:
            info = barcode_service.validate(value, allow_empty=False)
            self.barcode_status_label.setText(tr('barcode_valid', symbology=info.symbology))
            set_visual_state(self.barcode_status_label, 'success', weight='strong', size='caption', role='semantic_status')
            FormValidator.clear(self.barcode_error, self.barcode_edit)
        except BarcodeError as exc:
            self.barcode_status_label.setText(tr('material_barcode_invalid', error=str(exc)))
            set_visual_state(self.barcode_status_label, 'danger', weight='strong', size='caption', role='semantic_status')

    def update_margin_preview(self) -> None:
        purchase = float(self.purchase_spin.value()) if hasattr(self, 'purchase_spin') else 0.0
        selling = float(self.selling_spin.value()) if hasattr(self, 'selling_spin') else 0.0
        profit = selling - purchase
        margin = (profit / selling * 100) if selling > 0 else 0.0
        self.margin_label.setText(tr('profit_margin', value=f'{format_money(profit, self.display_curr)} ({margin:.1f}%)'))
        set_visual_state(self.margin_label, 'danger' if profit < 0 else 'success' if profit > 0 else 'muted', weight='strong' if profit != 0 else 'normal', size='caption', role='semantic_status')

    def update_stock_preview(self) -> None:
        qty = float(self.qty_spin.value()) if hasattr(self, 'qty_spin') else 0.0
        reorder = float(self.reorder_spin.value()) if hasattr(self, 'reorder_spin') else 0.0
        if reorder > 0 and qty <= reorder:
            self.stock_warning_label.setText(tr('stock_reorder_warning'))
            set_visual_state(self.stock_warning_label, 'danger', weight='strong', size='caption', role='semantic_status')
        else:
            self.stock_warning_label.setText(tr('stock_no_warning'))
            set_visual_state(self.stock_warning_label, 'success', weight='strong', size='caption', role='semantic_status')


    def _validate_unit_rows(self, validator: FormValidator) -> None:
        seen_names = set()
        seen_barcodes = set()
        base_barcode = barcode_input_service.normalize(self.barcode_edit.text())
        if base_barcode:
            seen_barcodes.add(base_barcode)
        for row in range(self.units_table.rowCount()):
            name_item = self.units_table.item(row, self.UNIT_COL_NAME)
            factor_item = self.units_table.item(row, self.UNIT_COL_FACTOR)
            barcode_item = self.units_table.item(row, self.UNIT_COL_BARCODE)
            name = (name_item.text() if name_item else '').strip()
            if not name:
                continue
            key = name.casefold()
            if bool(self.material_settings.get('require_unique_unit_names', True)) and key in seen_names:
                validator.custom(False, self.units_table, None, tr('material_duplicate_unit_name', unit=name))
            seen_names.add(key)
            try:
                factor = float((factor_item.text() if factor_item else '1') or 1)
            except Exception:
                factor = 0
            if factor <= 0:
                validator.custom(False, self.units_table, None, tr('material_invalid_unit_factor', unit=name))
            unit_barcode = barcode_input_service.normalize(barcode_item.text() if barcode_item else '')
            if not unit_barcode:
                continue
            if bool(self.material_settings.get('require_unit_barcode_validation', True)):
                try:
                    barcode_service.validate(unit_barcode, allow_empty=False)
                except BarcodeError as exc:
                    validator.custom(False, self.units_table, None, tr('material_invalid_unit_barcode', unit=name, error=str(exc)))
            if not bool(self.material_settings.get('allow_unit_barcode_duplicates', False)):
                if unit_barcode in seen_barcodes:
                    validator.custom(False, self.units_table, None, tr('material_duplicate_barcode', barcode=unit_barcode))
                seen_barcodes.add(unit_barcode)

    def _validate(self) -> bool:
        validator = FormValidator()
        if not self.security_policy.get('can_edit', True) or not self.can_document_action('save'):
            show_toast(self.permission_denied_message('save'), 'error', self)
            return False
        validator.required(self.name_edit, self.name_error, tr('item'))
        validator.required(self.unit_edit, self.unit_error, tr('base_unit_label').rstrip(':'))
        validator.positive(self.qty_spin, self.qty_error, tr('opening_quantity').rstrip(':'), allow_zero=True)
        validator.positive(self.reorder_spin, self.reorder_error, tr('reorder_level').rstrip(':'), allow_zero=True)
        barcode = barcode_input_service.normalize(self.barcode_edit.text())
        stock_type = is_stock(self.type_combo.currentData())
        if stock_type and bool(self.material_settings.get('require_barcode_for_stock_items', False)) and not barcode:
            validator.custom(False, self.barcode_edit, self.barcode_error, tr('material_barcode_required'))
        elif barcode:
            try:
                barcode_service.validate(barcode, allow_empty=False)
                FormValidator.clear(self.barcode_error, self.barcode_edit)
            except BarcodeError as exc:
                validator.custom(False, self.barcode_edit, self.barcode_error, str(exc))
        else:
            FormValidator.clear(self.barcode_error, self.barcode_edit)
        self._validate_unit_rows(validator)
        if not validator.is_valid:
            validator.focus_first_invalid()
            show_toast(tr('fix_marked_fields'), 'error', self)
        return validator.is_valid

    def _item_payload(self, units: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            'name': self.name_edit.text().strip(),
            'barcode': barcode_input_service.normalize(self.barcode_edit.text()) or None,
            'category_id': self.category_combo.currentData(),
            'item_type': self.type_combo.currentData() or self.type_combo.currentText(),
            'unit': self.unit_edit.text().strip() or tr('unit_piece'),
            'purchase_price': currency.convert(self.purchase_spin.value(), self.display_curr, currency.storage_currency()),
            'selling_price': currency.convert(self.selling_spin.value(), self.display_curr, currency.storage_currency()),
            'quantity': self.qty_spin.value(),
            'opening_quantity': self.qty_spin.value(),
            'average_cost': currency.convert(self.purchase_spin.value(), self.display_curr, currency.storage_currency()),
            'reorder_level': self.reorder_spin.value(),
            'units': units,
        }

    def workspace_save(self) -> None:
        if not self.can_document_action('save'):
            show_toast(self.permission_denied_message('save'), 'error', self)
            return
        if not self._validate():
            return
        units = self._collect_item_units()
        data = self._item_payload(units)
        try:
            if self.is_edit:
                product_service.update_item(int(self.item_id), data)
                saved_id = int(self.item_id)
                show_toast(tr('item_updated'), 'success', self)
            else:
                saved_id = product_service.add_item(data)
                self.item_id = saved_id
                self.document_state.document_id = saved_id
                self.is_edit = True
                show_toast(tr('item_added'), 'success', self)
            try:
                self._save_item_units(int(saved_id), units)
            except Exception:
                # Remote mode persists units atomically through item create/update.
                if not data.get('units'):
                    raise
            self.set_document_title(f"{tr('item')}: {data['name']}")
            self.title_label.setText(tr('material_title_edit'))
            self._load_activity_summary()
            self._apply_security_policy()
            self.set_dirty(False)
            self.saved.emit(saved_id)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _label_item_payload(self) -> Dict[str, Any]:
        return {
            'id': self.item_id,
            'name': self.name_edit.text().strip(),
            'barcode': barcode_input_service.normalize(self.barcode_edit.text()) or '',
            'selling_price': currency.convert(self.selling_spin.value(), self.display_curr, currency.storage_currency()),
            'price': self.selling_spin.value(),
            'unit': self.unit_edit.text().strip(),
        }

    def _label_options(self) -> Dict[str, Any]:
        # Phase 236: the unified material print button gets its label layout
        # from project printing settings, not per-screen overrides.
        return {}

    def preview_barcode_label(self) -> None:
        self.workspace_print()

    def workspace_print(self) -> None:
        if not self.security_policy.get('can_print_barcodes', True) or not self.can_document_action('print'):
            show_toast(self.permission_denied_message('print'), 'error', self)
            return
        item = self._label_item_payload()
        if not item.get('barcode'):
            show_toast(tr('material_barcode_required_for_label'), 'error', self)
            return
        try:
            copies = int(settings_service.get_printing_settings().get('barcode_copies', 1) or 1)
            printing_service.barcode_labels_print_settings([{**item, 'copies': max(1, copies)}], self, self._label_options())
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def save_and_print_label(self) -> None:
        self.workspace_save()
        if self.item_id and not self.is_dirty():
            self.workspace_print()


    def workspace_title(self) -> str:
        if self.is_edit and self.name_edit.text().strip():
            return f"{tr('item')}: {self.name_edit.text().strip()}"
        return tr('material_title_new')

    def shell_contract_matrix(self) -> Dict[str, Any]:
        """Return the inspectable material shell matrix for diagnostics/tests."""
        return dict(self.material_shell_contract)

    def request_close(self) -> None:
        # Phase351: material close follows the same function-aware workspace
        # lifecycle as invoices, returns, finance, inventory and manufacturing.
        self.request_workspace_close()


# Backward-compatible import used by MainWindow and ItemsWidget.
ItemEditorTab = MaterialDocumentTab
