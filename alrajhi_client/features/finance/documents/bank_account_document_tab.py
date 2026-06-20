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


class BankAccountDocumentTab(BaseDocumentTab):
    DOCUMENT_DESCRIPTOR = descriptor_for("bank_account")
    """Create/edit bank account master data inside the tabbed workspace."""

    def __init__(self, parent=None, bank_account_id: Optional[int] = None):
        super().__init__('bank_account', document_id=bank_account_id, parent=parent)
        self.setLayoutDirection(qt_layout_direction())
        self._account: Dict = {}
        self._branches = []
        self._can_edit = self._operation_allowed(
            finance_operation_policy.OP_BANK_EDIT if bank_account_id else finance_operation_policy.OP_BANK_CREATE
        )
        self._build_ui(); self._load_branches()
        if bank_account_id:
            self._load_bank_account(int(bank_account_id))
        else:
            self._set_new_defaults()
        self._apply_permissions(); self._connect_dirty_tracking()
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.workspace_save)
        QShortcut(QKeySequence('Esc'), self, activated=self._close_parent_tab)

    def workspace_title(self) -> str:
        base = self.document_state.title or self.windowTitle() or translate('bank_account_document_new')
        return base + (' *' if self.is_dirty() else '')

    def _operation_allowed(self, operation: str) -> bool:
        try: return finance_operation_policy.can(operation)
        except Exception: return True

    def _require_operation(self, operation: str) -> bool:
        try:
            finance_operation_policy.require(operation, context='BankAccountDocumentTab')
            return True
        except Exception as exc:
            show_toast(str(exc), 'warning', self); return False

    def _build_ui(self) -> None:
        root = QVBoxLayout(self); root.setContentsMargins(16,16,16,16); root.setSpacing(12)
        header = QHBoxLayout(); self.title_label = QLabel(); self.title_label.setObjectName('DocumentTitle')
        self.subtitle_label = QLabel(translate('bank_account_document_subtitle')); self.subtitle_label.setObjectName('mutedLabel')
        text = QVBoxLayout(); text.addWidget(self.title_label); text.addWidget(self.subtitle_label); header.addLayout(text, 1)
        # Phase 229: header is informational; save/close live in bottom action bar.
        root.addLayout(header)
        panel = QFrame(self); panel.setObjectName('DocumentPanel'); form = QGridLayout(panel); form.setContentsMargins(14,14,14,14); form.setHorizontalSpacing(12); form.setVerticalSpacing(10)
        self.branch_combo = QComboBox(self)
        self.bank_edit = QLineEdit(self); self.bank_edit.setPlaceholderText(translate('bank_name_placeholder'))
        self.account_name = QLineEdit(self); self.account_name.setPlaceholderText(translate('bank_account_name_placeholder'))
        self.account_number = QLineEdit(self); self.account_number.setPlaceholderText(translate('bank_account_number_placeholder'))
        self.iban = QLineEdit(self); self.iban.setPlaceholderText(translate('bank_iban_placeholder'))
        self.notes = QTextEdit(self); self.notes.setMaximumHeight(120); self.notes.setPlaceholderText(translate('bank_account_notes_placeholder'))
        self.active_check = QCheckBox(translate('active'), self); self.active_check.setChecked(True)
        form.addWidget(QLabel(translate('branch_label')), 0, 0); form.addWidget(self.branch_combo, 0, 1)
        form.addWidget(QLabel(translate('bank_label')), 0, 2); form.addWidget(self.bank_edit, 0, 3)
        form.addWidget(QLabel(translate('account_name_label')), 1, 0); form.addWidget(self.account_name, 1, 1)
        form.addWidget(QLabel(translate('account_number_label')), 1, 2); form.addWidget(self.account_number, 1, 3)
        form.addWidget(QLabel(translate('iban_label')), 2, 0); form.addWidget(self.iban, 2, 1)
        form.addWidget(QLabel(translate('notes_label')), 3, 0); form.addWidget(self.notes, 3, 1, 1, 3)
        form.addWidget(QLabel(translate('status')), 4, 0); form.addWidget(self.active_check, 4, 1)
        form.setColumnStretch(1, 1); form.setColumnStretch(3, 1); root.addWidget(panel)
        hint = QLabel(translate('bank_account_document_hint')); hint.setObjectName('mutedLabel'); hint.setWordWrap(True); root.addWidget(hint); root.addStretch(1)
        bottom = QHBoxLayout(); bottom.addStretch(1); self.bottom_close_btn = QPushButton(translate('close')); self.bottom_close_btn.clicked.connect(self._close_parent_tab); self.bottom_save_btn = QPushButton(translate('save_ctrl_s')); self.bottom_save_btn.setObjectName('primary'); self.bottom_save_btn.clicked.connect(self.workspace_save); bottom.addWidget(self.bottom_close_btn); bottom.addWidget(self.bottom_save_btn); root.addLayout(bottom); self.close_btn = self.bottom_close_btn; self.save_btn = self.bottom_save_btn

    def _load_branches(self) -> None:
        self.branch_combo.clear()
        try: self._branches = branch_service.branches(include_archived=False)
        except Exception: self._branches = []
        for branch in self._branches: self.branch_combo.addItem(branch.get('name') or str(branch.get('id') or ''), branch.get('id'))

    def _set_branch(self, branch_id) -> None:
        for i in range(self.branch_combo.count()):
            if self.branch_combo.itemData(i) == branch_id:
                self.branch_combo.setCurrentIndex(i); return

    def _set_new_defaults(self) -> None:
        self.set_document_title(translate('bank_account_document_new')); self.title_label.setText(translate('bank_account_document_new'))
        self._set_branch(branch_service.default_branch_id()); self.bank_edit.setFocus()

    def _load_bank_account(self, bank_account_id: int) -> None:
        data = cashbox_service.bank_account_by_id(bank_account_id)
        if not data:
            QMessageBox.warning(self, translate('bank_accounts'), translate('bank_account_not_found')); self._set_new_defaults(); return
        self._account = dict(data)
        self.bank_edit.setText(data.get('bank_name') or ''); self.account_name.setText(data.get('account_name') or '')
        self.account_number.setText(data.get('account_number') or ''); self.iban.setText(data.get('iban') or '')
        self.notes.setPlainText(data.get('notes') or ''); self.active_check.setChecked(int(data.get('is_active') or 0) == 1 and not data.get('deleted_at'))
        self._set_branch(data.get('branch_id') or branch_service.default_branch_id())
        title = translate('bank_account_document_edit', name=data.get('bank_name') or data.get('account_name') or '')
        self.set_document_title(title); self.title_label.setText(title); self.set_dirty(False)

    def _apply_permissions(self) -> None:
        for widget in (self.branch_combo, self.bank_edit, self.account_name, self.account_number, self.iban, self.notes, self.active_check): widget.setEnabled(self._can_edit)
        self.bottom_save_btn.setEnabled(self._can_edit)
        if not self._can_edit: self.subtitle_label.setText(translate('bank_account_read_only'))

    def _connect_dirty_tracking(self) -> None:
        self.branch_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True)); self.bank_edit.textChanged.connect(lambda *_: self.set_dirty(True)); self.account_name.textChanged.connect(lambda *_: self.set_dirty(True)); self.account_number.textChanged.connect(lambda *_: self.set_dirty(True)); self.iban.textChanged.connect(lambda *_: self.set_dirty(True)); self.notes.textChanged.connect(lambda *_: self.set_dirty(True)); self.active_check.stateChanged.connect(lambda *_: self.set_dirty(True))

    def _payload(self) -> Dict:
        return {'branch_id': self.branch_combo.currentData(), 'bank_name': self.bank_edit.text().strip(), 'account_name': self.account_name.text().strip(), 'account_number': self.account_number.text().strip(), 'iban': self.iban.text().strip(), 'notes': self.notes.toPlainText().strip(), 'is_active': 1 if self.active_check.isChecked() else 0}

    def _validate(self) -> bool:
        if not self.bank_edit.text().strip(): show_toast(translate('bank_name_required'), 'error', self); self.bank_edit.setFocus(); return False
        return True

    def workspace_save(self) -> None:
        op = finance_operation_policy.OP_BANK_EDIT if self.document_state.document_id else finance_operation_policy.OP_BANK_CREATE
        if not self._can_edit or not self._require_operation(op) or not self._validate(): return
        payload = self._payload()
        try:
            if self.document_state.document_id:
                cashbox_service.update_bank_account(int(self.document_state.document_id), payload); saved_id = int(self.document_state.document_id); show_toast(translate('bank_account_updated'), 'success', self)
            else:
                saved_id = int(cashbox_service.add_bank_account(payload)); self.document_state.document_id = saved_id; show_toast(translate('bank_account_created'), 'success', self)
            title = translate('bank_account_document_edit', name=payload.get('bank_name') or payload.get('account_name') or '')
            self.set_document_title(title); self.title_label.setText(title); self.set_dirty(False); self.saved.emit(saved_id)
        except Exception as exc:
            QMessageBox.warning(self, translate('bank_accounts'), str(exc))

    def _close_parent_tab(self) -> None:
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'indexOf') and hasattr(parent, 'removeTab'):
                idx = parent.indexOf(self)
                if idx >= 0 and self.can_close(): parent.removeTab(idx)
                return
            parent = parent.parent()
