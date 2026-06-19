# -*- coding: utf-8 -*-
from __future__ import annotations

from decimal import Decimal
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSplitter, QToolButton, QVBoxLayout,
    QWidget, QCompleter
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from core.offline_guard import is_offline_read_error, offline_read_message
from core.services.barcode_input_service import barcode_input_service
from core.services.catalog_service import catalog_service
from core.services.manufacturing_operation_policy import manufacturing_operation_policy
from core.services.manufacturing_service import manufacturing_service
from features.manufacturing.manufacturing_printing_bridge import manufacturing_printing_bridge
from features.dialog_documents import DialogDocumentTab
from features.manufacturing.components.bom_summary_panel import BomSummaryPanel
from features.manufacturing.grids.bom_components_grid import BomComponentsGrid
from features.manufacturing.grids.bom_components_model import BomComponentsModel
from features.manufacturing.grids.manufacturing_column_schema import bom_components_schema
from i18n import qt_layout_direction, translate
from utils import show_toast
from views.dialogs.bom_dialog import BOMDialog
from workspace.documents import BaseDocumentTab


class LegacyBomDocumentTab(DialogDocumentTab):
    """Legacy fallback wrapper around BOMDialog."""

    def __init__(self, parent=None, bom_id=None):
        title = translate('edit_bom_title') if bom_id else translate('add_bom_title')
        super().__init__(
            document_type='bom',
            dialog_cls=BOMDialog,
            parent=parent,
            document_id=bom_id,
            title=title,
            bom_id=bom_id,
        )

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('bom_recipe')


class BomDocumentTab(BaseDocumentTab):
    """Professional BOM document tab.

    Phase 188 replaces the modal-list BOM editor with a real workspace document:
    a unit-aware components grid, barcode/manual material lookup, cost summary,
    and service-backed save.  BOMDialog remains available as LegacyBomDocumentTab
    for emergency fallback, but this tab no longer embeds it.
    """

    def __init__(self, parent=None, bom_id=None):
        super().__init__('bom', document_id=bom_id, parent=parent)
        self.bom_id = bom_id
        self.is_edit = bom_id is not None
        self.service = manufacturing_service
        self.columns = bom_components_schema()
        self.model = BomComponentsModel(self.columns, self)
        self._product_items: list[dict[str, Any]] = []
        self._build_ui()
        self._load_products()
        self.model.add_empty_line()
        if self.is_edit:
            self._load_bom()
        else:
            self.set_document_title(translate('add_bom_title'))
        self._install_shortcuts()
        self._apply_operation_state()
        self._connect_dirty_signals()
        self._refresh_summary()
        self.set_dirty(False)

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('bom_recipe')

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)

        self.header_card = QFrame(self)
        self.header_card.setObjectName('DocumentHeaderCard')
        header_layout = QVBoxLayout(self.header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)
        top_row = QHBoxLayout()
        self.title_label = QLabel(translate('edit_bom_title') if self.is_edit else translate('add_bom_title'))
        self.title_label.setObjectName('DocumentTitle')
        top_row.addWidget(self.title_label)
        top_row.addStretch(1)
        # Phase 229: header is informational; print/save live in the bottom action bar.
        header_layout.addLayout(top_row)

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
        self.qty_spin.setDecimals(4)
        self.qty_spin.setValue(1)
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText(translate('manufacturing_component_search_placeholder'))
        self.add_component_btn = QPushButton(translate('add_component'))
        meta.addWidget(QLabel(translate('finished_product')), 0, 0)
        meta.addWidget(self.product_combo, 0, 1)
        meta.addWidget(QLabel(translate('quantity_per_unit')), 0, 2)
        meta.addWidget(self.qty_spin, 0, 3)
        meta.addWidget(QLabel(translate('manufacturing_component_lookup')), 1, 0)
        meta.addWidget(self.search_edit, 1, 1, 1, 2)
        meta.addWidget(self.add_component_btn, 1, 3)
        header_layout.addLayout(meta)
        root.addWidget(self.header_card)

        self.grid = BomComponentsGrid(self.columns, self, identity='manufacturing.bom.components')
        self.grid.setModel(self.model)
        self.grid.apply_named_preset('manager')
        self.remove_component_btn = QPushButton(translate('delete_selected_component'))
        self.add_empty_btn = QToolButton(self)
        self.add_empty_btn.setText(translate('add_line'))
        grid_card = QFrame(self)
        grid_card.setObjectName('FormCard')
        grid_layout = QVBoxLayout(grid_card)
        grid_layout.setContentsMargins(12, 12, 12, 12)
        grid_header = QHBoxLayout()
        grid_title = QLabel(translate('bom_components_group'))
        grid_title.setObjectName('PanelTitle')
        grid_header.addWidget(grid_title)
        grid_header.addStretch(1)
        grid_header.addWidget(self.add_empty_btn)
        grid_header.addWidget(self.remove_component_btn)
        grid_layout.addLayout(grid_header)
        grid_layout.addWidget(self.grid, 1)

        self.summary_panel = BomSummaryPanel(self)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(grid_card)
        splitter.addWidget(self.summary_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.bottom_print_btn = QPushButton(translate('print'))
        self.cancel_btn = QPushButton(translate('close'))
        self.bottom_save_btn = QPushButton(translate('save_ctrl_s'))
        self.bottom_save_btn.setObjectName('primary')
        bottom.addWidget(self.bottom_print_btn)
        bottom.addWidget(self.cancel_btn)
        bottom.addWidget(self.bottom_save_btn)
        root.addLayout(bottom)

        self.bottom_save_btn.clicked.connect(self.workspace_save)
        self.bottom_print_btn.clicked.connect(self.workspace_print)
        self.save_btn = self.bottom_save_btn
        self.print_btn = self.bottom_print_btn
        self.add_component_btn.clicked.connect(self._add_component_from_search)
        self.search_edit.returnPressed.connect(self._add_component_from_search)
        self.add_empty_btn.clicked.connect(lambda: self.model.add_empty_line())
        self.remove_component_btn.clicked.connect(self._remove_selected_component)
        self.cancel_btn.clicked.connect(self._close_parent_tab)
        self.qty_spin.valueChanged.connect(self._refresh_summary)
        self.model.dataChanged.connect(lambda *args: self._on_model_changed())
        self.model.rowsInserted.connect(lambda *args: self._on_model_changed())
        self.model.rowsRemoved.connect(lambda *args: self._on_model_changed())

        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#FormCard, QFrame#BomSummaryPanel {
                border: 1px solid palette(mid); border-radius: 14px; background: palette(base);
            }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#PanelTitle { font-size: 14px; font-weight: 900; }
            QLabel#SummaryValue { font-weight: 800; }
            QLineEdit, QComboBox, QDoubleSpinBox { min-height: 34px; padding: 5px 9px; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
            QTableView { gridline-color: palette(midlight); alternate-background-color: palette(alternate-base); }
        ''')

    def _connect_dirty_signals(self) -> None:
        self.product_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.qty_spin.valueChanged.connect(lambda *_: self.set_dirty(True))

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, activated=self.workspace_save)
        QShortcut(QKeySequence('Ctrl+F'), self, activated=self.search_edit.setFocus)
        QShortcut(QKeySequence('Insert'), self, activated=self.model.add_empty_line)
        QShortcut(QKeySequence.Delete, self, activated=self._remove_selected_component)

    def _apply_operation_state(self) -> None:
        can_save = self.service.can_operation(
            manufacturing_operation_policy.OP_BOM_EDIT if self.is_edit else manufacturing_operation_policy.OP_BOM_CREATE
        )
        self.bottom_save_btn.setEnabled(can_save)
        self.add_component_btn.setEnabled(can_save)
        self.add_empty_btn.setEnabled(can_save)
        self.remove_component_btn.setEnabled(can_save)
        self.grid.setEnabled(can_save)
        can_print = self.service.can_operation(manufacturing_operation_policy.OP_PRINT)
        self.bottom_print_btn.setEnabled(can_print)

    def _load_products(self) -> None:
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        self._product_items = []
        try:
            rows = catalog_service.items(limit=500) or []
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_products_offline')), 'warning', self)
                rows = []
            else:
                raise
        for item in rows:
            if item.get('item_type') in ('منتج نهائي', 'finished_product'):
                self._product_items.append(item)
                self.product_combo.addItem(str(item.get('name') or item.get('item_name') or ''), item.get('id'))
        self.product_combo.blockSignals(False)

    def _load_bom(self) -> None:
        try:
            bom = self.service.get_bom(int(self.bom_id))
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return
        if not bom:
            show_toast(translate('bom_not_found'), 'error', self)
            return
        idx = self.product_combo.findData(bom.get('product_id'))
        if idx >= 0:
            self.product_combo.setCurrentIndex(idx)
        self.qty_spin.setValue(float(bom.get('quantity') or 1))
        self.model.load_lines(bom.get('lines') or [])
        title = f"{translate('bom_recipe')}: {bom.get('product_name') or self.product_combo.currentText()}"
        self.title_label.setText(title)
        self.set_document_title(title)
        self.set_dirty(False)

    def _add_component_from_search(self) -> None:
        text = self.search_edit.text().strip()
        if not text:
            self.model.add_empty_line()
            return
        try:
            lookup = barcode_input_service.lookup_entry(text, mode='auto')
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return
        if not lookup.found:
            show_toast(translate(getattr(lookup, 'message_key', '') or 'transaction_item_not_found'), 'warning', self)
            return
        item = lookup.item or {}
        if item.get('id') == self.product_combo.currentData():
            show_toast(translate('bom_self_component_error'), 'error', self)
            return
        self.model.add_item(item, qty=1, price_key='purchase_price')
        self.search_edit.clear()
        self.set_dirty(True)
        self._refresh_summary()

    def _remove_selected_component(self) -> None:
        row = -1
        try:
            row = self.grid.currentIndex().row()
        except Exception:
            row = -1
        if row >= 0 and self.model.remove_row(row):
            self.set_dirty(True)
            self._refresh_summary()

    def _on_model_changed(self) -> None:
        self.set_dirty(True)
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        self.summary_panel.update_summary(self.model.cost_summary(), self.qty_spin.value())

    def _payload(self) -> dict[str, Any]:
        return {
            'id': self.bom_id or 0,
            'product_id': self.product_combo.currentData(),
            'quantity': str(Decimal(str(self.qty_spin.value()))),
            'lines': self.model.payload_lines(),
        }

    def _validate(self) -> list[str]:
        errors: list[str] = []
        product_id = self.product_combo.currentData()
        if not product_id:
            errors.append(translate('select_finished_product'))
        if Decimal(str(self.qty_spin.value())) <= 0:
            errors.append(translate('component_quantity_positive'))
        for err in self.model.validation_errors(product_id=product_id):
            # Model errors are intentionally English-coded; map common cases to
            # project translations at the boundary.
            if 'self component' in err:
                errors.append(translate('bom_self_component_error'))
            elif 'duplicate component' in err:
                errors.append(translate('manufacturing_duplicate_component'))
            elif 'quantity must be positive' in err:
                errors.append(translate('component_quantity_positive'))
            elif 'no components' in err:
                errors.append(translate('component_required'))
            else:
                errors.append(err)
        return errors

    def workspace_save(self) -> None:
        errors = self._validate()
        if errors:
            show_toast(errors[0], 'error', self)
            return
        try:
            saved_id = self.service.save_bom(self._payload())
            self.bom_id = saved_id
            self.is_edit = True
            self.document_state.document_id = saved_id
            title = f"{translate('bom_recipe')}: {self.product_combo.currentText()}"
            self.title_label.setText(title)
            self.set_document_title(title)
            self.set_dirty(False)
            show_toast(translate('bom_saved'), 'success', self)
            self.saved.emit(saved_id)
            self._apply_operation_state()
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def workspace_print(self) -> None:
        if self.is_dirty():
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
            if self.is_dirty():
                return
        try:
            bom_data = self.service.get_bom(self.bom_id) if self.bom_id else self._payload()
            manufacturing_printing_bridge.bom_print(self.bom_id, bom_data, self)
        except PermissionError as exc:
            show_toast(str(exc) or translate('permission_denied'), 'warning', self)
        except Exception as exc:
            show_toast(str(exc), 'error', self)

    def _close_parent_tab(self) -> None:
        # The workspace controls tab closing.  This button keeps the editor
        # non-modal without calling reject()/accept() like the legacy dialog.
        parent = self.parent()
        if parent and hasattr(parent, 'close_current_tab'):
            parent.close_current_tab()
        else:
            self.close()
