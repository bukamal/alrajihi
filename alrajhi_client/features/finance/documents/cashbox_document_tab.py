# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Optional

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QShortcut,
)

from i18n import qt_layout_direction, translate
from workspace.documents.base_document_tab import BaseDocumentTab
from workspace.documents.document_contract import descriptor_for
from core.services.branch_service import branch_service
from core.services.cashbox_service import cashbox_service
from core.services.finance_operation_policy import finance_operation_policy
from utils import show_toast


class CashboxDocumentTab(BaseDocumentTab):
    DOCUMENT_DESCRIPTOR = descriptor_for("cashbox")
    """Create/edit cashbox master data inside the tabbed workspace."""

    def __init__(self, parent=None, cashbox_id: Optional[int] = None):
        super().__init__('cashbox', document_id=cashbox_id, parent=parent)
        self.setLayoutDirection(qt_layout_direction())
        self._cashbox: Dict = {}
        self._branches = []
        self._can_edit = self._operation_allowed(
            finance_operation_policy.OP_CASHBOX_EDIT if cashbox_id else finance_operation_policy.OP_CASHBOX_CREATE
        )
        self._build_ui()
        self._load_branches()
        if cashbox_id:
            self._load_cashbox(int(cashbox_id))
        else:
            self._set_new_defaults()
        self._apply_permissions()
        self._connect_dirty_tracking()
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.workspace_save)
        QShortcut(QKeySequence('Esc'), self, activated=self._close_parent_tab)

    def workspace_title(self) -> str:
        base = self.document_state.title or self.windowTitle() or translate('cashbox_document_new')
        return base + (' *' if self.is_dirty() else '')

    def _operation_allowed(self, operation: str) -> bool:
        try:
            return finance_operation_policy.can(operation)
        except Exception:
            return True

    def _require_operation(self, operation: str) -> bool:
        try:
            finance_operation_policy.require(operation, context='CashboxDocumentTab')
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
        self.subtitle_label = QLabel(translate('cashbox_document_subtitle'))
        self.subtitle_label.setObjectName('mutedLabel')
        text = QVBoxLayout(); text.addWidget(self.title_label); text.addWidget(self.subtitle_label)
        header.addLayout(text, 1)
        # Phase 229: header is informational; save/close live in bottom action bar.
        root.addLayout(header)
        panel = QFrame(self); panel.setObjectName('DocumentPanel')
        form = QGridLayout(panel); form.setContentsMargins(14,14,14,14); form.setHorizontalSpacing(12); form.setVerticalSpacing(10)
        self.branch_combo = QComboBox(self)
        self.name_edit = QLineEdit(self); self.name_edit.setPlaceholderText(translate('cashbox_name_placeholder'))
        self.code_edit = QLineEdit(self); self.code_edit.setPlaceholderText(translate('cashbox_code_placeholder'))
        self.notes_edit = QTextEdit(self); self.notes_edit.setMaximumHeight(120); self.notes_edit.setPlaceholderText(translate('cashbox_notes_placeholder'))
        self.active_check = QCheckBox(translate('active'), self); self.active_check.setChecked(True)
        form.addWidget(QLabel(translate('branch_label')), 0, 0); form.addWidget(self.branch_combo, 0, 1)
        form.addWidget(QLabel(translate('cashbox_name_label')), 0, 2); form.addWidget(self.name_edit, 0, 3)
        form.addWidget(QLabel(translate('code_label')), 1, 0); form.addWidget(self.code_edit, 1, 1)
        form.addWidget(QLabel(translate('notes_label')), 2, 0); form.addWidget(self.notes_edit, 2, 1, 1, 3)
        form.addWidget(QLabel(translate('status')), 3, 0); form.addWidget(self.active_check, 3, 1)
        form.setColumnStretch(1, 1); form.setColumnStretch(3, 1)
        root.addWidget(panel)
        hint = QLabel(translate('cashbox_document_hint')); hint.setObjectName('mutedLabel'); hint.setWordWrap(True); root.addWidget(hint); root.addStretch(1)
        bottom = QHBoxLayout(); bottom.addStretch(1)
        self.bottom_close_btn = QPushButton(translate('close')); self.bottom_close_btn.clicked.connect(self._close_parent_tab)
        self.bottom_save_btn = QPushButton(translate('save_ctrl_s')); self.bottom_save_btn.setObjectName('primary'); self.bottom_save_btn.clicked.connect(self.workspace_save)
        bottom.addWidget(self.bottom_close_btn); bottom.addWidget(self.bottom_save_btn); root.addLayout(bottom)
        self.close_btn = self.bottom_close_btn; self.save_btn = self.bottom_save_btn

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
                self.branch_combo.setCurrentIndex(index); return

    def _set_new_defaults(self) -> None:
        self.set_document_title(translate('cashbox_document_new'))
        self.title_label.setText(translate('cashbox_document_new'))
        self._set_branch(branch_service.default_branch_id())
        self.name_edit.setFocus()

    def _load_cashbox(self, cashbox_id: int) -> None:
        data = cashbox_service.cashbox_by_id(cashbox_id)
        if not data:
            QMessageBox.warning(self, translate('cashboxes'), translate('cashbox_not_found'))
            self._set_new_defaults(); return
        self._cashbox = dict(data)
        self.name_edit.setText(data.get('name') or '')
        self.code_edit.setText(data.get('code') or '')
        self.notes_edit.setPlainText(data.get('notes') or '')
        self.active_check.setChecked(int(data.get('is_active') or 0) == 1 and not data.get('deleted_at'))
        self._set_branch(data.get('branch_id') or branch_service.default_branch_id())
        title = translate('cashbox_document_edit', name=data.get('name') or '')
        self.set_document_title(title); self.title_label.setText(title); self.set_dirty(False)

    def _apply_permissions(self) -> None:
        for widget in (self.branch_combo, self.name_edit, self.code_edit, self.notes_edit, self.active_check):
            widget.setEnabled(self._can_edit)
        self.bottom_save_btn.setEnabled(self._can_edit)
        if not self._can_edit:
            self.subtitle_label.setText(translate('cashbox_read_only'))

    def _connect_dirty_tracking(self) -> None:
        self.branch_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.name_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.code_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.notes_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.active_check.stateChanged.connect(lambda *_: self.set_dirty(True))

    def _payload(self) -> Dict:
        return {'branch_id': self.branch_combo.currentData(), 'name': self.name_edit.text().strip(), 'code': self.code_edit.text().strip(), 'notes': self.notes_edit.toPlainText().strip(), 'is_active': 1 if self.active_check.isChecked() else 0}

    def _validate(self) -> bool:
        if not self.name_edit.text().strip():
            show_toast(translate('cashbox_name_required'), 'error', self); self.name_edit.setFocus(); return False
        return True

    def workspace_save(self) -> None:
        op = finance_operation_policy.OP_CASHBOX_EDIT if self.document_state.document_id else finance_operation_policy.OP_CASHBOX_CREATE
        if not self._can_edit or not self._require_operation(op) or not self._validate():
            return
        payload = self._payload()
        try:
            if self.document_state.document_id:
                cashbox_service.update_cashbox(int(self.document_state.document_id), payload)
                saved_id = int(self.document_state.document_id); show_toast(translate('cashbox_updated'), 'success', self)
            else:
                saved_id = int(cashbox_service.add_cashbox(payload)); self.document_state.document_id = saved_id; show_toast(translate('cashbox_created'), 'success', self)
            title = translate('cashbox_document_edit', name=payload.get('name') or '')
            self.set_document_title(title); self.title_label.setText(title); self.set_dirty(False); self.saved.emit(saved_id)
        except Exception as exc:
            QMessageBox.warning(self, translate('cashboxes'), str(exc))

    def _close_parent_tab(self) -> None:
        # Phase351: cashbox document close uses the shared workspace lifecycle.
        self.request_workspace_close()
