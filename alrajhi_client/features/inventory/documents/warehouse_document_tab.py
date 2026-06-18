# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QCheckBox, QPushButton, QMessageBox, QShortcut,
    QFrame,
)

from i18n import qt_layout_direction, translate
from workspace.documents.base_document_tab import BaseDocumentTab
from core.services.branch_service import branch_service
from core.services.warehouse_service import warehouse_service
from core.services.inventory_operation_policy import inventory_operation_policy
from utils import show_toast


class WarehouseDocumentTab(BaseDocumentTab):
    """Create/edit warehouse master data inside the tabbed workspace.

    This replaces the old inline QDialog used by WarehousesWidget while keeping
    persistence behind WarehouseService and inventory_operation_policy.
    """

    def __init__(self, parent=None, warehouse_id: Optional[int] = None):
        super().__init__('warehouse', document_id=warehouse_id, parent=parent)
        self.setLayoutDirection(qt_layout_direction())
        self._warehouse: Dict = {}
        self._branches = []
        self._can_edit = self._operation_allowed(
            inventory_operation_policy.OP_WAREHOUSE_EDIT if warehouse_id else inventory_operation_policy.OP_WAREHOUSE_CREATE
        )
        self._build_ui()
        self._load_branches()
        if warehouse_id:
            self._load_warehouse(int(warehouse_id))
        else:
            self._set_new_defaults()
        self._apply_permissions()
        self._connect_dirty_tracking()
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.workspace_save)
        QShortcut(QKeySequence('Esc'), self, activated=self._close_parent_tab)

    def workspace_title(self) -> str:
        base = self.document_state.title or self.windowTitle() or translate('warehouse_document_new')
        return base + (' *' if self.is_dirty() else '')

    def _operation_allowed(self, operation: str) -> bool:
        try:
            return inventory_operation_policy.can(operation)
        except Exception:
            return True

    def _require_operation(self, operation: str) -> bool:
        try:
            inventory_operation_policy.require(operation, context='WarehouseDocumentTab')
            return True
        except Exception as exc:
            show_toast(str(exc), 'warning', self)
            return False

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.title_label = QLabel()
        self.title_label.setObjectName('DocumentTitle')
        self.subtitle_label = QLabel(translate('warehouse_document_subtitle'))
        self.subtitle_label.setObjectName('mutedLabel')
        header_text = QVBoxLayout()
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header.addLayout(header_text, 1)
        self.save_btn = QPushButton(translate('save_ctrl_s'))
        self.save_btn.setObjectName('primary')
        self.save_btn.clicked.connect(self.workspace_save)
        self.close_btn = QPushButton(translate('close'))
        self.close_btn.clicked.connect(self._close_parent_tab)
        header.addWidget(self.save_btn)
        header.addWidget(self.close_btn)
        root.addLayout(header)

        panel = QFrame(self)
        panel.setObjectName('DocumentPanel')
        form = QGridLayout(panel)
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText(translate('warehouse_name_placeholder'))
        self.code_edit = QLineEdit(self)
        self.code_edit.setPlaceholderText(translate('warehouse_code_placeholder'))
        self.branch_combo = QComboBox(self)
        self.location_edit = QLineEdit(self)
        self.location_edit.setPlaceholderText(translate('warehouse_location_placeholder'))
        self.active_check = QCheckBox(translate('active'), self)
        self.active_check.setChecked(True)
        self.notes_edit = QTextEdit(self)
        self.notes_edit.setMaximumHeight(120)
        self.notes_edit.setPlaceholderText(translate('warehouse_notes_placeholder'))

        form.addWidget(QLabel(translate('warehouse_name_label')), 0, 0)
        form.addWidget(self.name_edit, 0, 1)
        form.addWidget(QLabel(translate('warehouse_code_label')), 0, 2)
        form.addWidget(self.code_edit, 0, 3)
        form.addWidget(QLabel(translate('branch_label')), 1, 0)
        form.addWidget(self.branch_combo, 1, 1)
        form.addWidget(QLabel(translate('warehouse_location_label')), 1, 2)
        form.addWidget(self.location_edit, 1, 3)
        form.addWidget(QLabel(translate('notes_label')), 2, 0)
        form.addWidget(self.notes_edit, 2, 1, 1, 3)
        form.addWidget(QLabel(translate('status')), 3, 0)
        form.addWidget(self.active_check, 3, 1)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)
        root.addWidget(panel)

        hint = QLabel(translate('warehouse_document_hint'))
        hint.setObjectName('mutedLabel')
        hint.setWordWrap(True)
        root.addWidget(hint)
        root.addStretch(1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.bottom_save_btn = QPushButton(translate('save_ctrl_s'))
        self.bottom_save_btn.setObjectName('primary')
        self.bottom_save_btn.clicked.connect(self.workspace_save)
        bottom.addWidget(self.bottom_save_btn)
        root.addLayout(bottom)

    def _load_branches(self) -> None:
        self.branch_combo.clear()
        try:
            self._branches = branch_service.branches(include_archived=False)
        except Exception:
            self._branches = []
        for branch in self._branches:
            self.branch_combo.addItem(branch.get('name') or str(branch.get('id') or ''), branch.get('id'))

    def _set_branch(self, branch_id) -> None:
        for index in range(self.branch_combo.count()):
            if self.branch_combo.itemData(index) == branch_id:
                self.branch_combo.setCurrentIndex(index)
                return

    def _set_new_defaults(self) -> None:
        self.set_document_title(translate('warehouse_document_new'))
        self.title_label.setText(translate('warehouse_document_new'))
        self._set_branch(branch_service.default_branch_id())
        self.name_edit.setFocus()

    def _load_warehouse(self, warehouse_id: int) -> None:
        wh = warehouse_service.warehouse_by_id(warehouse_id)
        if not wh:
            QMessageBox.warning(self, translate('warehouses'), translate('warehouse_not_found'))
            self._set_new_defaults()
            return
        self._warehouse = dict(wh)
        self.name_edit.setText(wh.get('name') or '')
        self.code_edit.setText(wh.get('code') or '')
        self.location_edit.setText(wh.get('location') or '')
        self.notes_edit.setPlainText(wh.get('notes') or '')
        self.active_check.setChecked(int(wh.get('is_active') or 0) == 1 and not wh.get('deleted_at'))
        self._set_branch(wh.get('branch_id') or branch_service.default_branch_id())
        self.set_document_title(translate('warehouse_document_edit', name=wh.get('name') or ''))
        self.title_label.setText(translate('warehouse_document_edit', name=wh.get('name') or ''))
        self.set_dirty(False)

    def _apply_permissions(self) -> None:
        for widget in (self.name_edit, self.code_edit, self.branch_combo, self.location_edit, self.notes_edit, self.active_check):
            widget.setEnabled(self._can_edit)
        self.save_btn.setEnabled(self._can_edit)
        self.bottom_save_btn.setEnabled(self._can_edit)
        if not self._can_edit:
            self.subtitle_label.setText(translate('warehouse_read_only'))

    def _connect_dirty_tracking(self) -> None:
        self.name_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.code_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.location_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.notes_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.branch_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.active_check.stateChanged.connect(lambda *_: self.set_dirty(True))

    def _payload(self) -> Dict:
        return {
            'name': self.name_edit.text().strip(),
            'code': self.code_edit.text().strip(),
            'branch_id': self.branch_combo.currentData(),
            'location': self.location_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'is_active': 1 if self.active_check.isChecked() else 0,
        }

    def _validate(self) -> bool:
        if not self.name_edit.text().strip():
            show_toast(translate('warehouse_name_required'), 'error', self)
            self.name_edit.setFocus()
            return False
        return True

    def workspace_save(self) -> None:
        operation = inventory_operation_policy.OP_WAREHOUSE_EDIT if self.document_state.document_id else inventory_operation_policy.OP_WAREHOUSE_CREATE
        if not self._can_edit or not self._require_operation(operation):
            return
        if not self._validate():
            return
        payload = self._payload()
        try:
            if self.document_state.document_id:
                warehouse_service.update_warehouse(int(self.document_state.document_id), payload)
                show_toast(translate('warehouse_updated'), 'success', self)
                saved_id = int(self.document_state.document_id)
            else:
                saved_id = int(warehouse_service.add_warehouse(payload))
                self.document_state.document_id = saved_id
                show_toast(translate('warehouse_created'), 'success', self)
            self.set_document_title(translate('warehouse_document_edit', name=payload.get('name') or ''))
            self.title_label.setText(self.document_state.title)
            self.set_dirty(False)
            self.saved.emit(saved_id)
        except Exception as exc:
            QMessageBox.warning(self, translate('warehouses'), str(exc))

    def _close_parent_tab(self) -> None:
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'indexOf') and hasattr(parent, 'removeTab'):
                idx = parent.indexOf(self)
                if idx >= 0 and self.can_close():
                    parent.removeTab(idx)
                return
            parent = parent.parent()
