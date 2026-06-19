# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Optional

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QShortcut,
)

from i18n import qt_layout_direction, translate
from workspace.documents.base_document_tab import BaseDocumentTab
from core.services.branch_service import branch_service
from core.services.branch_operation_policy import branch_operation_policy
from utils import show_toast


class BranchDocumentTab(BaseDocumentTab):
    """Create/edit branch master data inside the tabbed workspace."""

    def __init__(self, parent=None, branch_id: Optional[int] = None):
        super().__init__('branch', document_id=branch_id, parent=parent)
        self.setLayoutDirection(qt_layout_direction())
        self._branch: Dict = {}
        self._can_edit = self._operation_allowed(
            branch_operation_policy.OP_EDIT if branch_id else branch_operation_policy.OP_CREATE
        )
        self._build_ui()
        if branch_id:
            self._load_branch(int(branch_id))
        else:
            self._set_new_defaults()
        self._apply_permissions()
        self._connect_dirty_tracking()
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.workspace_save)
        QShortcut(QKeySequence('Esc'), self, activated=self._close_parent_tab)

    def workspace_title(self) -> str:
        base = self.document_state.title or self.windowTitle() or translate('branch_document_new')
        return base + (' *' if self.is_dirty() else '')

    def _operation_allowed(self, operation: str) -> bool:
        try:
            return branch_operation_policy.can(operation)
        except Exception:
            return True

    def _require_operation(self, operation: str) -> bool:
        try:
            branch_operation_policy.require(operation, context='BranchDocumentTab')
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
        self.subtitle_label = QLabel(translate('branch_document_subtitle'))
        self.subtitle_label.setObjectName('mutedLabel')
        header_text = QVBoxLayout()
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header.addLayout(header_text, 1)
        # Phase 229: header is informational; save/close live in the bottom action bar.
        root.addLayout(header)

        panel = QFrame(self)
        panel.setObjectName('DocumentPanel')
        form = QGridLayout(panel)
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText(translate('branch_name_placeholder'))
        self.code_edit = QLineEdit(self)
        self.code_edit.setPlaceholderText(translate('branch_code_placeholder'))
        self.address_edit = QLineEdit(self)
        self.address_edit.setPlaceholderText(translate('branch_address_placeholder'))
        self.phone_edit = QLineEdit(self)
        self.phone_edit.setPlaceholderText(translate('branch_phone_placeholder'))
        self.active_check = QCheckBox(translate('active'), self)
        self.active_check.setChecked(True)
        self.notes_edit = QTextEdit(self)
        self.notes_edit.setMaximumHeight(120)
        self.notes_edit.setPlaceholderText(translate('branch_notes_placeholder'))

        form.addWidget(QLabel(translate('branch_name_label')), 0, 0)
        form.addWidget(self.name_edit, 0, 1)
        form.addWidget(QLabel(translate('code_label')), 0, 2)
        form.addWidget(self.code_edit, 0, 3)
        form.addWidget(QLabel(translate('address_label')), 1, 0)
        form.addWidget(self.address_edit, 1, 1)
        form.addWidget(QLabel(translate('phone_label')), 1, 2)
        form.addWidget(self.phone_edit, 1, 3)
        form.addWidget(QLabel(translate('notes_label')), 2, 0)
        form.addWidget(self.notes_edit, 2, 1, 1, 3)
        form.addWidget(QLabel(translate('status')), 3, 0)
        form.addWidget(self.active_check, 3, 1)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)
        root.addWidget(panel)

        hint = QLabel(translate('branch_document_hint'))
        hint.setObjectName('mutedLabel')
        hint.setWordWrap(True)
        root.addWidget(hint)
        root.addStretch(1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.bottom_close_btn = QPushButton(translate('close'))
        self.bottom_close_btn.clicked.connect(self._close_parent_tab)
        self.bottom_save_btn = QPushButton(translate('save_ctrl_s'))
        self.bottom_save_btn.setObjectName('primary')
        self.bottom_save_btn.clicked.connect(self.workspace_save)
        bottom.addWidget(self.bottom_close_btn)
        bottom.addWidget(self.bottom_save_btn)
        self.close_btn = self.bottom_close_btn
        self.save_btn = self.bottom_save_btn
        root.addLayout(bottom)

    def _set_new_defaults(self) -> None:
        self.set_document_title(translate('branch_document_new'))
        self.title_label.setText(translate('branch_document_new'))
        self.name_edit.setFocus()

    def _load_branch(self, branch_id: int) -> None:
        branch = branch_service.branch_by_id(branch_id)
        if not branch:
            QMessageBox.warning(self, translate('branches'), translate('branch_not_found'))
            self._set_new_defaults()
            return
        self._branch = dict(branch)
        self.name_edit.setText(branch.get('name') or '')
        self.code_edit.setText(branch.get('code') or '')
        self.address_edit.setText(branch.get('address') or '')
        self.phone_edit.setText(branch.get('phone') or '')
        self.notes_edit.setPlainText(branch.get('notes') or '')
        self.active_check.setChecked(int(branch.get('is_active') or 0) == 1 and not branch.get('deleted_at'))
        self.set_document_title(translate('branch_document_edit', name=branch.get('name') or ''))
        self.title_label.setText(translate('branch_document_edit', name=branch.get('name') or ''))
        self.set_dirty(False)

    def _apply_permissions(self) -> None:
        for widget in (self.name_edit, self.code_edit, self.address_edit, self.phone_edit, self.notes_edit, self.active_check):
            widget.setEnabled(self._can_edit)
        self.bottom_save_btn.setEnabled(self._can_edit)
        if not self._can_edit:
            self.subtitle_label.setText(translate('branch_read_only'))

    def _connect_dirty_tracking(self) -> None:
        self.name_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.code_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.address_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.phone_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.notes_edit.textChanged.connect(lambda *_: self.set_dirty(True))
        self.active_check.stateChanged.connect(lambda *_: self.set_dirty(True))

    def _payload(self) -> Dict:
        return {
            'name': self.name_edit.text().strip(),
            'code': self.code_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'is_active': 1 if self.active_check.isChecked() else 0,
        }

    def _validate(self) -> bool:
        if not self.name_edit.text().strip():
            show_toast(translate('branch_name_required'), 'error', self)
            self.name_edit.setFocus()
            return False
        return True

    def workspace_save(self) -> None:
        operation = branch_operation_policy.OP_EDIT if self.document_state.document_id else branch_operation_policy.OP_CREATE
        if not self._can_edit or not self._require_operation(operation):
            return
        if not self._validate():
            return
        payload = self._payload()
        try:
            if self.document_state.document_id:
                branch_service.update_branch(int(self.document_state.document_id), payload)
                show_toast(translate('branch_updated'), 'success', self)
            else:
                branch_id = branch_service.add_branch(payload)
                self.document_state.document_id = int(branch_id)
                show_toast(translate('branch_created'), 'success', self)
            self.set_dirty(False)
            self.saved.emit(self.document_state.document_id)
            self._load_branch(int(self.document_state.document_id))
        except Exception as exc:
            QMessageBox.warning(self, translate('error'), str(exc))

    def _close_parent_tab(self) -> None:
        parent = self.parent()
        if parent and hasattr(parent, 'close_current_tab'):
            parent.close_current_tab()
            return
        self.close()
