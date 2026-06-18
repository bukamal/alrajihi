# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QShortcut
)

from core.services.barcode_input_service import barcode_input_service
from core.services.catalog_service import catalog_service
from core.services.inventory_operation_policy import inventory_operation_policy
from core.services.warehouse_service import warehouse_service
from features.inventory.inventory_printing_bridge import inventory_printing_bridge
from features.inventory.grids.inventory_transfer_grid import InventoryTransferGrid
from features.inventory.grids.inventory_transfer_lines_model import InventoryTransferLinesModel
from features.inventory.grids.inventory_transfer_schema import inventory_transfer_lines_schema
from i18n import qt_layout_direction, translate
from utils import show_toast
from workspace.documents import BaseDocumentTab


class InventoryTransferDocumentTab(BaseDocumentTab):
    """Professional, unit-aware warehouse transfer document."""

    def __init__(self, parent=None):
        super().__init__('warehouse_transfer', document_id=None, parent=parent)
        self.columns = inventory_transfer_lines_schema()
        self.model = InventoryTransferLinesModel(self.columns, self)
        self._build_ui()
        self._load_warehouses()
        self.model.add_empty_line()
        self._install_shortcuts()
        self._apply_operation_state()
        self._connect_dirty_signals()
        self.set_document_title(translate('inventory_transfer_document_new'))
        self.set_dirty(False)

    def workspace_title(self) -> str:
        return self.document_state.title or self.windowTitle() or translate('inventory_transfer_document_new')

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)
        header = QFrame(self); header.setObjectName('DocumentHeaderCard')
        header_layout = QVBoxLayout(header); header_layout.setContentsMargins(16, 14, 16, 14)
        title_row = QHBoxLayout()
        self.title_label = QLabel(translate('inventory_transfer_document_new')); self.title_label.setObjectName('DocumentTitle')
        title_row.addWidget(self.title_label); title_row.addStretch(1)
        self.print_btn = QPushButton(translate('print_preview'))
        self.save_btn = QPushButton(translate('execute_transfer')); self.save_btn.setObjectName('primary')
        title_row.addWidget(self.print_btn)
        title_row.addWidget(self.save_btn); header_layout.addLayout(title_row)
        meta = QGridLayout(); meta.setHorizontalSpacing(10); meta.setVerticalSpacing(8)
        self.from_combo = QComboBox(self); self.to_combo = QComboBox(self)
        self.lookup_edit = QLineEdit(self); self.lookup_edit.setPlaceholderText(translate('inventory_transfer_lookup_placeholder'))
        self.lookup_qty = QDoubleSpinBox(self); self.lookup_qty.setRange(0.0001, 999999999); self.lookup_qty.setDecimals(4); self.lookup_qty.setValue(1)
        self.add_line_btn = QPushButton(translate('add_line'))
        meta.addWidget(QLabel(translate('from_warehouse_clean')), 0, 0); meta.addWidget(self.from_combo, 0, 1)
        meta.addWidget(QLabel(translate('to_warehouse_clean')), 0, 2); meta.addWidget(self.to_combo, 0, 3)
        meta.addWidget(QLabel(translate('inventory_transfer_lookup')), 1, 0); meta.addWidget(self.lookup_edit, 1, 1, 1, 2)
        meta.addWidget(self.lookup_qty, 1, 3); meta.addWidget(self.add_line_btn, 1, 4)
        header_layout.addLayout(meta); root.addWidget(header)

        self.grid = InventoryTransferGrid(self.columns, self, identity='inventory.transfer.lines')
        self.grid.setModel(self.model)
        self.grid.configure_item_delegate(
            items_provider=lambda search, limit: catalog_service.items(search=search or None, limit=limit),
            price_key_provider=lambda: 'purchase_price',
            availability_provider=lambda item: self._available_for_item(item.get('id')),
        )
        self.grid.apply_named_preset('manager')
        grid_card = QFrame(self); grid_card.setObjectName('FormCard')
        grid_layout = QVBoxLayout(grid_card); grid_layout.setContentsMargins(12, 12, 12, 12)
        grid_header = QHBoxLayout(); grid_title = QLabel(translate('inventory_transfer_lines')); grid_title.setObjectName('PanelTitle')
        self.remove_line_btn = QPushButton(translate('delete_selected_line'))
        self.add_empty_btn = QPushButton(translate('add_line'))
        grid_header.addWidget(grid_title); grid_header.addStretch(1); grid_header.addWidget(self.add_empty_btn); grid_header.addWidget(self.remove_line_btn)
        grid_layout.addLayout(grid_header); grid_layout.addWidget(self.grid, 1)

        notes_card = QFrame(self); notes_card.setObjectName('FormCard')
        notes_layout = QVBoxLayout(notes_card); notes_layout.setContentsMargins(12, 12, 12, 12)
        notes_title = QLabel(translate('notes')); notes_title.setObjectName('PanelTitle')
        self.notes_edit = QTextEdit(self); self.notes_edit.setMaximumHeight(150)
        self.summary_label = QLabel(''); self.summary_label.setObjectName('mutedLabel')
        notes_layout.addWidget(notes_title); notes_layout.addWidget(self.notes_edit); notes_layout.addWidget(self.summary_label)
        splitter = QSplitter(Qt.Horizontal, self); splitter.addWidget(grid_card); splitter.addWidget(notes_card)
        splitter.setStretchFactor(0, 5); splitter.setStretchFactor(1, 1); root.addWidget(splitter, 1)
        bottom = QHBoxLayout(); bottom.addStretch(1)
        self.close_btn = QPushButton(translate('close'))
        self.bottom_save_btn = QPushButton(translate('execute_transfer')); self.bottom_save_btn.setObjectName('primary')
        bottom.addWidget(self.close_btn); bottom.addWidget(self.bottom_save_btn); root.addLayout(bottom)
        self.save_btn.clicked.connect(self.workspace_save); self.bottom_save_btn.clicked.connect(self.workspace_save)
        self.print_btn.clicked.connect(self.workspace_print); self.bottom_print_btn.clicked.connect(self.workspace_print)
        self.add_line_btn.clicked.connect(self._add_line_from_lookup); self.lookup_edit.returnPressed.connect(self._add_line_from_lookup)
        self.add_empty_btn.clicked.connect(self.model.add_empty_line); self.remove_line_btn.clicked.connect(self._remove_selected_line)
        self.close_btn.clicked.connect(self._close_parent_tab); self.from_combo.currentIndexChanged.connect(self._refresh_availability)
        self.to_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.model.dataChanged.connect(lambda *args: self._on_model_changed())
        self.model.rowsInserted.connect(lambda *args: self._on_model_changed()); self.model.rowsRemoved.connect(lambda *args: self._on_model_changed())
        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#FormCard { border: 1px solid palette(mid); border-radius: 14px; background: palette(base); }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLabel#PanelTitle { font-size: 14px; font-weight: 900; }
            QLineEdit, QComboBox, QDoubleSpinBox { min-height: 34px; padding: 5px 9px; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
        ''')

    def _connect_dirty_signals(self) -> None:
        self.notes_edit.textChanged.connect(lambda: self.set_dirty(True))
        self.from_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.to_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, activated=self.workspace_save)
        QShortcut(QKeySequence('Ctrl+F'), self, activated=self.lookup_edit.setFocus)
        QShortcut(QKeySequence('Insert'), self, activated=self.model.add_empty_line)
        QShortcut(QKeySequence.Delete, self, activated=self._remove_selected_line)

    def _apply_operation_state(self) -> None:
        allowed = warehouse_service.can_operation(inventory_operation_policy.OP_TRANSFER_CREATE) if hasattr(warehouse_service, 'can_operation') else inventory_operation_policy.can(inventory_operation_policy.OP_TRANSFER_CREATE)
        print_allowed = inventory_operation_policy.can(inventory_operation_policy.OP_PRINT)
        for widget in (self.save_btn, self.bottom_save_btn, self.add_line_btn, self.add_empty_btn, self.remove_line_btn, self.grid):
            widget.setEnabled(bool(allowed))
        for widget in (getattr(self, 'print_btn', None), getattr(self, 'bottom_print_btn', None)):
            if widget is not None:
                widget.setEnabled(bool(print_allowed))

    def _load_warehouses(self) -> None:
        self.from_combo.clear(); self.to_combo.clear()
        try:
            warehouses = warehouse_service.warehouses(include_archived=False)
        except Exception as exc:
            show_toast(str(exc), 'error', self); warehouses = []
        for wh in warehouses or []:
            label = f"{wh.get('name','')} ({wh.get('code') or '—'})"
            self.from_combo.addItem(label, wh.get('id')); self.to_combo.addItem(label, wh.get('id'))
        if self.to_combo.count() > 1:
            self.to_combo.setCurrentIndex(1)

    def _available_for_item(self, item_id) -> Any:
        if not item_id or not self.from_combo.currentData():
            return ''
        try:
            return warehouse_service.available_qty(int(item_id), int(self.from_combo.currentData()))
        except Exception:
            return ''

    def _refresh_availability(self) -> None:
        self.model.apply_availability(self._available_for_item); self._refresh_summary()

    def _add_line_from_lookup(self) -> None:
        text = (self.lookup_edit.text() or '').strip()
        if not text:
            return
        try:
            lookup = barcode_input_service.lookup_entry(text, mode='auto')
            item = getattr(lookup, 'item', None) if lookup is not None else None
        except Exception as exc:
            show_toast(str(exc), 'warning', self); item = None
        if not item:
            show_toast(translate('barcode_not_found'), 'warning', self); return
        row = self.model.add_item_from_lookup(item, warehouse_available=self._available_for_item(item.get('id')))
        self.model.setData(self.model.index(row, self._column_index('qty')), self.lookup_qty.value())
        self.lookup_edit.clear(); self.lookup_qty.setValue(1); self.set_dirty(True); self._refresh_summary()

    def _column_index(self, key: str) -> int:
        for idx, col in enumerate(self.columns):
            if col.key == key:
                return idx
        return 0

    def _remove_selected_line(self) -> None:
        idx = self.grid.currentIndex()
        if not idx or not idx.isValid():
            return
        self.model.remove_row(idx.row()); self.set_dirty(True); self._refresh_summary()

    def _on_model_changed(self) -> None:
        self.set_dirty(True); self._refresh_summary()

    def _refresh_summary(self) -> None:
        count = len(self.model.payload_lines())
        total_base = sum((self.model._decimal(line.get('base_qty')) for line in self.model.payload_lines()), self.model._decimal(0))
        self.summary_label.setText(translate('inventory_transfer_summary', count=count, base_qty=total_base))

    def _validation_errors(self) -> list[str]:
        errors: list[str] = []
        from_wh = self.from_combo.currentData(); to_wh = self.to_combo.currentData()
        if not from_wh: errors.append(translate('inventory_transfer_missing_from'))
        if not to_wh: errors.append(translate('inventory_transfer_missing_to'))
        if from_wh and to_wh and int(from_wh) == int(to_wh): errors.append(translate('inventory_transfer_same_warehouse'))
        errors.extend(self.model.validation_errors())
        if not self.model.payload_lines(): errors.append(translate('inventory_transfer_no_lines'))
        return errors

    def workspace_save(self) -> None:
        errors = self._validation_errors()
        if errors:
            QMessageBox.warning(self, translate('validation_error'), '\n'.join(errors)); return
        from_wh = self.from_combo.currentData(); to_wh = self.to_combo.currentData(); shared_notes = self.notes_edit.toPlainText().strip()
        created: list[int] = []
        try:
            for line in self.model.payload_lines():
                payload = dict(line); payload['from_warehouse_id'] = from_wh; payload['to_warehouse_id'] = to_wh
                payload['notes'] = '\n'.join([p for p in (shared_notes, payload.get('notes') or '') if p]).strip()
                created.append(warehouse_service.create_transfer(payload))
            show_toast(translate('transfer_done'), 'success', self); self.set_dirty(False); self.saved.emit(created); self._close_parent_tab()
        except Exception as exc:
            QMessageBox.warning(self, translate('warehouse_transfers'), str(exc))

    def _print_payload(self) -> dict:
        transfer = {
            'transfer_no': translate('inventory_transfer_document_new'),
            'from_warehouse_name': self.from_combo.currentText(),
            'to_warehouse_name': self.to_combo.currentText(),
            'notes': self.notes_edit.toPlainText().strip(),
            'status': translate('active'),
        }
        return inventory_printing_bridge.transfer_payload(transfer, self.model.payload_lines())

    def workspace_print(self) -> None:
        errors = self._validation_errors()
        if errors:
            QMessageBox.warning(self, translate('validation_error'), '\n'.join(errors)); return
        try:
            inventory_printing_bridge.transfer_preview(self._print_payload(), self)
        except Exception as exc:
            QMessageBox.warning(self, translate('printing'), str(exc))

    def _close_parent_tab(self) -> None:
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'close_current_tab'):
                parent.close_current_tab(); return
            parent = parent.parent()
        self.close()
