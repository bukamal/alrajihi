# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Optional

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QComboBox,
    QShortcut,
    QVBoxLayout,
)

from i18n import qt_layout_direction, translate
from workspace.documents.base_document_tab import BaseDocumentTab
from core.services.user_service import user_service
from core.services.branch_service import branch_service
from core.services.user_operation_policy import user_operation_policy
from offline_read import is_offline_read_error, notify_offline_read
from utils import show_toast


class UserDocumentTab(BaseDocumentTab):
    """Create/edit ERP users inside the tabbed workspace."""

    ROLE_VALUES = ['admin', 'manager', 'accountant', 'cashier', 'viewer']

    def __init__(self, parent=None, user_id: Optional[int] = None):
        super().__init__('user', document_id=user_id, parent=parent)
        self.setLayoutDirection(qt_layout_direction())
        self._user: Dict = {}
        self._can_edit = self._operation_allowed(user_operation_policy.OP_EDIT if user_id else user_operation_policy.OP_CREATE)
        self._build_ui()
        self._load_branches()
        if user_id:
            self._load_user(int(user_id))
        else:
            self._set_new_defaults()
        self._apply_permissions()
        self._connect_dirty_tracking()
        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.workspace_save)
        QShortcut(QKeySequence('Esc'), self, activated=self._close_parent_tab)

    def workspace_title(self) -> str:
        base = self.document_state.title or self.windowTitle() or translate('user_document_new')
        return base + (' *' if self.is_dirty() else '')

    def _operation_allowed(self, operation: str) -> bool:
        try:
            return user_operation_policy.can(operation)
        except Exception:
            return True

    def _require_operation(self, operation: str) -> bool:
        try:
            user_operation_policy.require(operation, context='UserDocumentTab')
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
        self.subtitle_label = QLabel(translate('user_document_subtitle'))
        self.subtitle_label.setObjectName('mutedLabel')
        header_text = QVBoxLayout()
        header_text.addWidget(self.title_label)
        header_text.addWidget(self.subtitle_label)
        header.addLayout(header_text, 1)
        # Phase 229: header is informational; save/close live in bottom action bar.
        root.addLayout(header)

        panel = QFrame(self)
        panel.setObjectName('DocumentPanel')
        form = QGridLayout(panel)
        form.setContentsMargins(14, 14, 14, 14)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        self.username_edit = QLineEdit(self)
        self.username_edit.setPlaceholderText(translate('username'))
        self.fullname_edit = QLineEdit(self)
        self.fullname_edit.setPlaceholderText(translate('full_name'))
        self.role_combo = QComboBox(self)
        self.branch_combo = QComboBox(self)
        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText(translate('password'))
        self.confirm_edit = QLineEdit(self)
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setPlaceholderText(translate('confirm_password'))

        role_labels = {
            'admin': translate('role_admin'),
            'manager': translate('role_manager'),
            'accountant': translate('role_accountant'),
            'cashier': translate('role_cashier'),
            'viewer': translate('role_viewer'),
        }
        for role in self.ROLE_VALUES:
            self.role_combo.addItem(role_labels.get(role, role), role)

        form.addWidget(QLabel(translate('username_label')), 0, 0)
        form.addWidget(self.username_edit, 0, 1)
        form.addWidget(QLabel(translate('full_name_label')), 0, 2)
        form.addWidget(self.fullname_edit, 0, 3)
        form.addWidget(QLabel(translate('role_label')), 1, 0)
        form.addWidget(self.role_combo, 1, 1)
        form.addWidget(QLabel(translate('branch_label')), 1, 2)
        form.addWidget(self.branch_combo, 1, 3)
        form.addWidget(QLabel(translate('password_label')), 2, 0)
        form.addWidget(self.password_edit, 2, 1)
        form.addWidget(QLabel(translate('confirm_password_label')), 2, 2)
        form.addWidget(self.confirm_edit, 2, 3)
        root.addWidget(panel)
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
        root.addLayout(bottom)
        self.close_btn = self.bottom_close_btn
        self.save_btn = self.bottom_save_btn

    def _load_branches(self):
        self.branch_combo.clear()
        self.branch_combo.addItem(translate('no_branch'), None)
        try:
            branches = branch_service.branches()
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('branches_title'))
                branches = []
            else:
                raise
        for br in branches or []:
            self.branch_combo.addItem(br.get('name', f"#{br.get('id')}"), br.get('id'))

    def _set_new_defaults(self):
        self.set_document_title(translate('user_document_new'))
        self.title_label.setText(translate('user_document_new'))
        self.username_edit.setEnabled(True)
        self.set_dirty(False)

    def _load_user(self, user_id: int):
        self._user = user_service.get_user(user_id) or {}
        self.username_edit.setText(str(self._user.get('username') or ''))
        self.fullname_edit.setText(str(self._user.get('full_name') or ''))
        self.username_edit.setEnabled(False)
        role = str(self._user.get('role') or 'viewer').lower()
        if role == 'user':
            role = 'viewer'
        idx = self.ROLE_VALUES.index(role) if role in self.ROLE_VALUES else self.ROLE_VALUES.index('viewer')
        self.role_combo.setCurrentIndex(idx)
        branch_id = self._user.get('branch_id')
        for i in range(self.branch_combo.count()):
            if str(self.branch_combo.itemData(i)) == str(branch_id):
                self.branch_combo.setCurrentIndex(i)
                break
        title = translate('user_document_edit')
        if self.username_edit.text():
            title = f"{title}: {self.username_edit.text()}"
        self.set_document_title(title)
        self.title_label.setText(title)
        self.password_edit.hide(); self.confirm_edit.hide()
        # Hide labels by keeping the row empty would require layout surgery; keep fields hidden and disabled.
        self.password_edit.setEnabled(False); self.confirm_edit.setEnabled(False)
        self.set_dirty(False)

    def _apply_permissions(self):
        editable = bool(self._can_edit)
        for widget in (self.username_edit, self.fullname_edit, self.role_combo, self.branch_combo, self.password_edit, self.confirm_edit):
            widget.setEnabled(editable and widget.isVisible())
        self.bottom_save_btn.setEnabled(editable)
        if not editable:
            self.subtitle_label.setText(translate('user_read_only'))

    def _connect_dirty_tracking(self):
        for widget in (self.username_edit, self.fullname_edit, self.password_edit, self.confirm_edit):
            widget.textChanged.connect(lambda *_: self.set_dirty(True))
        self.role_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))
        self.branch_combo.currentIndexChanged.connect(lambda *_: self.set_dirty(True))

    def _payload(self):
        return {
            'username': self.username_edit.text().strip(),
            'full_name': self.fullname_edit.text().strip(),
            'role': self.role_combo.currentData() or 'viewer',
            'branch_id': self.branch_combo.currentData(),
            'password': self.password_edit.text(),
            'confirm': self.confirm_edit.text(),
        }

    def _validate(self, data: Dict) -> bool:
        if not data['username']:
            QMessageBox.warning(self, translate('error'), translate('username_required'))
            return False
        if not self.document_state.document_id:
            if not data['password']:
                QMessageBox.warning(self, translate('error'), translate('password_required'))
                return False
            if data['password'] != data['confirm']:
                QMessageBox.warning(self, translate('error'), translate('passwords_do_not_match'))
                return False
        return True

    def workspace_save(self):
        if not self._can_edit:
            QMessageBox.warning(self, translate('error'), translate('user_read_only'))
            return
        operation = user_operation_policy.OP_EDIT if self.document_state.document_id else user_operation_policy.OP_CREATE
        if not self._require_operation(operation):
            return
        data = self._payload()
        if not self._validate(data):
            return
        try:
            if self.document_state.document_id:
                user_service.update_user(self.document_state.document_id, data['full_name'], data['role'], data['branch_id'])
                saved_id = self.document_state.document_id
                show_toast(translate('user_updated'), 'success', self)
            else:
                saved_id = user_service.create_user(data['username'], data['password'], data['full_name'], data['role'], data['branch_id'])
                self.document_state.document_id = int(saved_id) if str(saved_id).isdigit() else saved_id
                show_toast(translate('user_added'), 'success', self)
                self.username_edit.setEnabled(False)
                self.password_edit.hide(); self.confirm_edit.hide()
            self.set_dirty(False)
            self.saved.emit(saved_id)
            self._load_user(int(saved_id)) if str(saved_id).isdigit() else None
        except Exception as exc:
            QMessageBox.critical(self, translate('error'), str(exc))

    def _close_parent_tab(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'close_current_tab'):
                parent.close_current_tab()
                return
            parent = parent.parent()
        self.close()
