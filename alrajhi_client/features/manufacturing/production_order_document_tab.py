# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QComboBox,
    QCompleter,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
)

from core.offline_guard import is_offline_read_error, offline_read_message
from core.services.catalog_service import catalog_service
from core.services.manufacturing_operation_policy import manufacturing_operation_policy
from core.services.manufacturing_service import manufacturing_service
from features.manufacturing.manufacturing_printing_bridge import manufacturing_printing_bridge
from core.services.settings_service import settings_service
from core.services.warehouse_service import warehouse_service
from features.dialog_documents import DialogDocumentTab
from features.manufacturing.components.production_summary_panel import ProductionSummaryPanel
from features.manufacturing.grids.manufacturing_column_schema import production_required_materials_schema
from features.manufacturing.grids.production_required_materials_grid import ProductionRequiredMaterialsGrid
from features.manufacturing.grids.production_required_materials_model import ProductionRequiredMaterialsModel
from i18n import qt_layout_direction, translate
from utils import show_toast
from views.dialogs.production_details_dialog import ProductionDetailsDialog
from views.dialogs.production_order_dialog import ProductionOrderDialog
from workspace.documents.base_document_tab import BaseDocumentTab


class LegacyProductionOrderDocumentTab(DialogDocumentTab):
    """Emergency fallback for the old modal production-order dialog."""

    def __init__(self, parent=None):
        super().__init__(
            document_type='production_order',
            dialog_cls=ProductionOrderDialog,
            parent=parent,
            document_id=None,
            title=translate('new_production_order_title'),
        )

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('production_order')


class ProductionOrderDocumentTab(BaseDocumentTab):
    """Professional production-order document tab.

    Phase 189 replaces the embedded ProductionOrderDialog with a service-backed
    workspace document: product selection, raw/output warehouses, required
    materials grid, availability summary, settings-aware validation and
    manufacturing-operation policy enforcement.
    """

    def __init__(self, parent=None):
        super().__init__('production_order', document_id=None, parent=parent)
        self.service = manufacturing_service
        self.settings = settings_service.get_manufacturing_settings()
        self.columns = production_required_materials_schema()
        self.materials_model = ProductionRequiredMaterialsModel(self.columns, self)
        self._product_items: list[dict[str, Any]] = []
        self._product_bom_map: dict[int, dict | None] = {}
        self._build_ui()
        self._load_warehouses()
        self._load_products()
        self._install_shortcuts()
        self._connect_dirty_signals()
        self._apply_operation_state()
        self._refresh_required_materials()
        self.set_document_title(translate('new_production_order_title'))
        self.set_dirty(False)

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('production_order')

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        self.header_card = QFrame(self)
        self.header_card.setObjectName('DocumentHeaderCard')
        header = QVBoxLayout(self.header_card)
        header.setContentsMargins(16, 14, 16, 14)

        top = QHBoxLayout()
        self.title_label = QLabel(translate('new_production_order_title'))
        self.title_label.setObjectName('DocumentTitle')
        top.addWidget(self.title_label)
        top.addStretch(1)
        self.refresh_btn = QPushButton(translate('refresh'))
        self.save_btn = QPushButton(translate('create_ctrl_s'))
        self.save_btn.setObjectName('primary')
        top.addWidget(self.refresh_btn)
        top.addWidget(self.save_btn)
        header.addLayout(top)

        meta = QGridLayout()
        meta.setHorizontalSpacing(10)
        meta.setVerticalSpacing(8)
        self.product_combo = QComboBox(self)
        self.product_combo.setEditable(True)
        try:
            self.product_combo.completer().setCaseSensitivity(Qt.CaseInsensitive)
            self.product_combo.completer().setFilterMode(Qt.MatchContains)
            self.product_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        except Exception:
            pass

        self.qty_spin = QDoubleSpinBox(self)
        self.qty_spin.setRange(0.0001, 999999999)
        self.qty_spin.setDecimals(int(self.settings.get('quantity_decimals', 3) or 3))
        self.qty_spin.setValue(1)

        self.raw_warehouse_combo = QComboBox(self)
        self.output_warehouse_combo = QComboBox(self)
        self.notes_edit = QTextEdit(self)
        self.notes_edit.setMaximumHeight(78)

        meta.addWidget(QLabel(translate('finished_product')), 0, 0)
        meta.addWidget(self.product_combo, 0, 1)
        meta.addWidget(QLabel(translate('planned_quantity_label')), 0, 2)
        meta.addWidget(self.qty_spin, 0, 3)
        meta.addWidget(QLabel(translate('raw_warehouse_label')), 1, 0)
        meta.addWidget(self.raw_warehouse_combo, 1, 1)
        meta.addWidget(QLabel(translate('output_warehouse_label')), 1, 2)
        meta.addWidget(self.output_warehouse_combo, 1, 3)
        meta.addWidget(QLabel(translate('notes_label')), 2, 0)
        meta.addWidget(self.notes_edit, 2, 1, 1, 3)
        header.addLayout(meta)
        root.addWidget(self.header_card)

        grid_card = QFrame(self)
        grid_card.setObjectName('FormCard')
        grid_layout = QVBoxLayout(grid_card)
        grid_layout.setContentsMargins(12, 12, 12, 12)
        grid_header = QHBoxLayout()
        grid_title = QLabel(translate('required_materials_group'))
        grid_title.setObjectName('PanelTitle')
        self.material_state_label = QLabel('')
        self.material_state_label.setObjectName('MutedLabel')
        grid_header.addWidget(grid_title)
        grid_header.addStretch(1)
        grid_header.addWidget(self.material_state_label)
        grid_layout.addLayout(grid_header)

        self.materials_grid = ProductionRequiredMaterialsGrid(self.columns, self)
        self.materials_grid.setModel(self.materials_model)
        self.materials_grid.apply_named_preset('warehouse')
        grid_layout.addWidget(self.materials_grid, 1)

        self.summary_panel = ProductionSummaryPanel(self)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(grid_card)
        splitter.addWidget(self.summary_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.cancel_btn = QPushButton(translate('close'))
        self.bottom_save_btn = QPushButton(translate('create_ctrl_s'))
        self.bottom_save_btn.setObjectName('primary')
        bottom.addWidget(self.cancel_btn)
        bottom.addWidget(self.bottom_save_btn)
        root.addLayout(bottom)

        self.save_btn.clicked.connect(self.workspace_save)
        self.bottom_save_btn.clicked.connect(self.workspace_save)
        self.refresh_btn.clicked.connect(self._refresh_required_materials)
        self.cancel_btn.clicked.connect(self._close_parent_tab)
        self.product_combo.currentIndexChanged.connect(self._refresh_required_materials)
        self.qty_spin.valueChanged.connect(self._refresh_required_materials)
        self.raw_warehouse_combo.currentIndexChanged.connect(self._refresh_required_materials)

        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#FormCard, QFrame#ProductionSummaryPanel {
                border: 1px solid palette(mid); border-radius: 14px; background: palette(base);
            }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#PanelTitle { font-size: 14px; font-weight: 900; }
            QLabel#SummaryValue { font-weight: 800; }
            QLabel#MutedLabel { color: palette(mid); }
            QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit { min-height: 34px; padding: 5px 9px; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
            QTableView { gridline-color: palette(midlight); alternate-background-color: palette(alternate-base); }
        ''')

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, activated=self.workspace_save)
        QShortcut(QKeySequence.Refresh, self, activated=self._refresh_required_materials)

    def _connect_dirty_signals(self) -> None:
        self.product_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.raw_warehouse_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.output_warehouse_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.qty_spin.valueChanged.connect(lambda *_: self.set_dirty(True))
        self.notes_edit.textChanged.connect(lambda: self.set_dirty(True))

    def _apply_operation_state(self) -> None:
        can_create = self.service.can_operation(manufacturing_operation_policy.OP_ORDER_CREATE)
        self.save_btn.setEnabled(can_create)
        self.bottom_save_btn.setEnabled(can_create)
        self.product_combo.setEnabled(can_create)
        self.qty_spin.setEnabled(can_create)
        self.raw_warehouse_combo.setEnabled(can_create)
        self.output_warehouse_combo.setEnabled(can_create)
        self.notes_edit.setReadOnly(not can_create)

    def _load_warehouses(self) -> None:
        try:
            warehouses = warehouse_service.warehouses()
            fallback_default = warehouse_service.default_warehouse_id()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_warehouses_offline')), 'warning', self)
                warehouses = []
                fallback_default = None
            else:
                raise
        for combo in (self.raw_warehouse_combo, self.output_warehouse_combo):
            combo.blockSignals(True)
            combo.clear()
            for wh in warehouses:
                combo.addItem(str(wh.get('name') or ''), wh.get('id'))
            combo.blockSignals(False)
        raw_default = self._int_or_none(self.settings.get('default_raw_warehouse_id')) or fallback_default
        output_default = self._int_or_none(self.settings.get('default_output_warehouse_id')) or fallback_default
        self._select_combo_data(self.raw_warehouse_combo, raw_default)
        self._select_combo_data(self.output_warehouse_combo, output_default)

    def _load_products(self) -> None:
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        self._product_items = []
        self._product_bom_map = {}
        try:
            rows = catalog_service.items(limit=1000) or []
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_products_offline')), 'warning', self)
                rows = []
            else:
                raise
        for item in rows:
            if item.get('item_type') not in ('منتج نهائي', 'finished_product'):
                continue
            item_id = item.get('id')
            bom = None
            try:
                bom = self.service.get_bom_for_product(int(item_id)) if item_id else None
            except Exception:
                bom = None
            self._product_items.append(item)
            if item_id is not None:
                self._product_bom_map[int(item_id)] = bom
            label = str(item.get('name') or item.get('item_name') or '')
            if not bom:
                label = f"{label} - {translate('no_bom_for_product')}"
            self.product_combo.addItem(label, item_id)
        self.product_combo.blockSignals(False)

    def _current_product_id(self):
        data = self.product_combo.currentData()
        if data not in (None, ''):
            return data
        typed = self.product_combo.currentText().strip().casefold()
        for item in self._product_items:
            name = str(item.get('name') or item.get('item_name') or '').strip().casefold()
            if typed and typed == name:
                idx = self.product_combo.findData(item.get('id'))
                if idx >= 0:
                    self.product_combo.setCurrentIndex(idx)
                return item.get('id')
        return None

    def _refresh_required_materials(self) -> None:
        product_id = self._current_product_id()
        if not product_id:
            self.materials_model.load_materials([])
            self.summary_panel.update_summary(self.materials_model.summary())
            self.material_state_label.setText(translate('select_finished_product'))
            return
        bom = self._product_bom_map.get(int(product_id))
        if not bom:
            self.materials_model.load_materials([])
            self.summary_panel.update_summary(self.materials_model.summary())
            self.material_state_label.setText(translate('no_bom_for_product'))
            return
        qty = Decimal(str(self.qty_spin.value()))
        raw_warehouse_id = self.raw_warehouse_combo.currentData()
        try:
            materials = self.service.get_required_materials_recursive(int(product_id), qty, raw_warehouse_id)
        except Exception as exc:
            self.materials_model.load_materials([])
            self.summary_panel.update_summary(self.materials_model.summary())
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_items_offline')), 'warning', self)
            else:
                show_toast(str(exc), 'error', self)
            return
        self.materials_model.load_materials(materials)
        self.summary_panel.update_summary(self.materials_model.summary())
        insufficient = self.materials_model.insufficient_lines()
        if insufficient:
            self.material_state_label.setText(translate('manufacturing_materials_insufficient_short'))
        elif materials:
            self.material_state_label.setText(translate('manufacturing_materials_sufficient_short'))
        else:
            self.material_state_label.setText(translate('no_required_materials'))

    def _payload(self) -> dict[str, Any]:
        return {
            'product_id': self._current_product_id(),
            'planned_qty': str(Decimal(str(self.qty_spin.value()))),
            'notes': self.notes_edit.toPlainText().strip(),
            'raw_warehouse_id': self.raw_warehouse_combo.currentData(),
            'output_warehouse_id': self.output_warehouse_combo.currentData(),
        }

    def _validate(self) -> list[str]:
        errors: list[str] = []
        product_id = self._current_product_id()
        if not product_id:
            errors.append(translate('select_finished_product'))
        elif not self._product_bom_map.get(int(product_id)):
            errors.append(translate('no_bom_for_product_msg'))
        if Decimal(str(self.qty_spin.value())) <= 0:
            errors.append(translate('quantity_positive_error'))
        if not self.raw_warehouse_combo.currentData() or not self.output_warehouse_combo.currentData():
            errors.append(translate('manufacturing_select_raw_output_warehouses'))
        insufficient = self.materials_model.insufficient_lines()
        if insufficient and not bool(self.settings.get('allow_negative_raw_consumption')):
            first = insufficient[0]
            errors.append(translate(
                'manufacturing_material_shortage_line',
                item=first.get('item') or '-',
                required=first.get('required_qty') or 0,
                available=first.get('available_qty') or 0,
            ))
        return errors

    def workspace_save(self) -> None:
        self._refresh_required_materials()
        errors = self._validate()
        if errors:
            show_toast(errors[0], 'error', self)
            return
        try:
            payload = self._payload()
            order_id = self.service.create_production_order(payload)
            self.document_state.document_id = order_id
            self.set_document_title(f"{translate('production_order')}: {order_id}")
            self.set_dirty(False)
            show_toast(translate('production_order_created', number=order_id), 'success', self)
            self.saved.emit(order_id)
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def workspace_print(self) -> None:
        order_id = self.document_state.document_id
        if not order_id:
            reply = QMessageBox.question(
                self,
                translate('printing'),
                translate('workspace.save_before_output'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return
            self.workspace_save()
            order_id = self.document_state.document_id
        if not order_id:
            return
        try:
            manufacturing_printing_bridge.production_order_preview(int(order_id), self)
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    @staticmethod
    def _int_or_none(value):
        try:
            return int(value) if value not in (None, '') else None
        except Exception:
            return None

    @staticmethod
    def _select_combo_data(combo: QComboBox, value) -> None:
        if value in (None, ''):
            return
        for i in range(combo.count()):
            if str(combo.itemData(i)) == str(value):
                combo.setCurrentIndex(i)
                return

    def _close_parent_tab(self) -> None:
        parent = self.parent()
        if parent and hasattr(parent, 'close_current_tab'):
            parent.close_current_tab()
        else:
            self.close()


class ProductionOrderDetailsTab(DialogDocumentTab):
    """Read/action document tab for a production order lifecycle.

    Details remain service-backed and include unified print/export through the
    embedded dialog's print_order implementation where available.
    """

    def __init__(self, parent=None, order_id: Optional[int] = None):
        super().__init__(
            document_type='production_order_details',
            dialog_cls=ProductionDetailsDialog,
            parent=parent,
            document_id=order_id,
            title=translate('production_details'),
            order_id=order_id,
        )

    def workspace_save(self) -> None:
        self.set_dirty(False)

    def workspace_print(self) -> None:
        method = getattr(self.dialog, 'print_order', None)
        if callable(method):
            method('preview')
            return
        super().workspace_print()

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('production_details')
