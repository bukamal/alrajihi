# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QHeaderView, QMessageBox, QDialog, QFormLayout, QComboBox, QLabel)
from PyQt5.QtCore import Qt
from core.services.user_service import user_service
from core.services.user_operation_policy import user_operation_policy
from auth.session import UserSession
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from views.dialogs.change_password_dialog import ChangePasswordDialog
from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from core.services.branch_service import branch_service
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog
from i18n import translate, qt_layout_direction
from views.widgets.inline_document_host import InlineDocumentHostMixin

class UsersWidget(InlineDocumentHostMixin, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.current_page = 0
        self.page_size = 20
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        self.add_btn = QPushButton(translate('add_user_btn'))
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_user)
        top_layout.addWidget(self.add_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.table = SmartTableView(identity="users.list")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_user)
        self._install_inline_document_host(self.table, layout, translate('users_title'))

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton(translate('previous'))
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(translate('next'))
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        apply_modern_widget(self, translate('users_title_icon'), translate('users_subtitle'))
        self.refresh()
        self._apply_operation_state()

    def set_global_filter(self, text: str):
        text = (text or '').strip().lower()
        # Generic visual filter for widgets that expose one or more Qt tables.
        for name, table in self.__dict__.items():
            if not hasattr(table, 'rowCount') or not hasattr(table, 'setRowHidden'):
                continue
            try:
                rows = table.rowCount()
                cols = table.columnCount()
            except Exception:
                continue
            for row in range(rows):
                hay = []
                for col in range(cols):
                    try:
                        item = table.item(row, col) if hasattr(table, 'item') else None
                        if item is not None:
                            hay.append(item.text())
                        elif hasattr(table, 'model') and table.model() is not None:
                            idx = table.model().index(row, col)
                            hay.append(str(table.model().data(idx) or ''))
                    except Exception:
                        pass
                table.setRowHidden(row, bool(text) and text not in ' '.join(hay).lower())


    def refresh(self):
        offset = self.current_page * self.page_size
        try:
            users = user_service.list_users()
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('users_title'))
                return
            raise
        self.total_count = len(users)
        users = users[offset:offset + self.page_size]
        data = []
        for u in users:
            role_keys = {
                'admin': 'role_admin',
                'manager': 'role_manager',
                'accountant': 'role_accountant',
                'cashier': 'role_cashier',
                'viewer': 'role_viewer',
                'user': 'role_user',
            }
            role_text = translate(role_keys.get(str(u.get('role') or 'user').lower(), 'role_user'))
            data.append({
                'id': u.get('id'),
                'username': u.get('username'),
                'full_name': u.get('full_name', ''),
                'role': role_text,
                'branch': u.get('branch_name', ''),
                'created_at': (u.get('created_at', '')[:10] if u.get('created_at') else ''),
                'last_login': (u.get('last_login', '')[:10] if u.get('last_login') else '')
            })
        headers = ['username', 'full_name', 'role', 'branch', 'created_at', 'last_login']
        display_headers = [translate('username'), translate('full_name'), translate('role'), translate('branch'), translate('created_at'), translate('last_login')]
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()
        self._connect_inline_detail_preview()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(translate('page_of', page=self.current_page + 1, total=total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def _main_window(self):
        widget = self
        while widget is not None:
            if hasattr(widget, 'open_user_document'):
                return widget
            widget = widget.parent()
        return None

    def _selected_source_row(self, index=None):
        try:
            if index is not None and hasattr(self.table, 'mapToSource'):
                return self.table.mapToSource(index).row()
        except Exception:
            pass
        try:
            if hasattr(self.table, 'current_source_row'):
                return self.table.current_source_row()
        except Exception:
            pass
        return index.row() if index is not None else -1

    def _apply_operation_state(self):
        try:
            self.add_btn.setEnabled(user_operation_policy.can(user_operation_policy.OP_CREATE))
        except Exception:
            pass

    def _selected_user_id(self, index=None):
        if not hasattr(self, 'model'):
            return None
        row = self._selected_source_row(index)
        if row is None or row < 0:
            return None
        try:
            data = self.model.get_row(row) if hasattr(self.model, 'get_row') else {}
            user_id = data.get('id') if isinstance(data, dict) else None
            if user_id not in (None, ''):
                return user_id
        except Exception:
            pass
        try:
            user_id = self.model.get_id(row)
            return user_id if user_id not in (None, '') else None
        except Exception:
            return None

    def open_user_inline(self, user_id=None):
        if user_id is None:
            return self.add_user()
        try:
            from features.users import UserDocumentTab
            editor = UserDocumentTab(self.inline_editor_host, user_id=user_id)
            return self._show_inline_document(editor, translate('edit_user'))
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None

    def add_user(self):
        # Phase377/378: Add user is inline master-detail, not a workspace sub-tab or modal dialog.
        # Legacy route marker only: main.open_user_document()
        if not user_operation_policy.can(user_operation_policy.OP_CREATE):
            show_toast(translate('permission_denied'), 'warning', self)
            return
        try:
            from features.users import UserDocumentTab
            editor = UserDocumentTab(self.inline_editor_host)
            return self._show_inline_document(editor, translate('add_user_new'))
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None

    def edit_user(self, index=None):
        user_id = self._selected_user_id(index)
        if not user_id:
            show_toast(translate('select_user_first') if translate('select_user_first') != 'select_user_first' else 'اختر مستخدماً أولاً', 'warning', self)
            return None
        try:
            from features.users import UserDocumentTab
            editor = UserDocumentTab(self.inline_editor_host, user_id=user_id)
            return self._show_inline_document(editor, translate('edit_user'))
        except Exception as exc:
            show_toast(str(exc), 'error', self)
            return None

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()


class UserDialog(QDialog):
    def __init__(self, parent=None, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(translate('edit_user') if user_id else translate('add_user_new'))
        self.setLayoutDirection(qt_layout_direction())
        self.resize(400, 350)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        if user_id:
            self.username_edit.setEnabled(False)
        form.addRow(translate('username_label'), self.username_edit)

        self.fullname_edit = QLineEdit()
        form.addRow(translate('full_name_label'), self.fullname_edit)

        self.role_combo = QComboBox()
        self.role_values = ['admin', 'manager', 'accountant', 'cashier', 'viewer']
        self.role_labels = {
            'admin': translate('role_admin'),
            'manager': translate('role_manager'),
            'accountant': translate('role_accountant'),
            'cashier': translate('role_cashier'),
            'viewer': translate('role_viewer'),
        }
        for role in self.role_values:
            self.role_combo.addItem(self.role_labels[role], role)
        form.addRow(translate('role_label'), self.role_combo)

        self.branch_combo = QComboBox()
        try:
            branches = branch_service.branches()
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('branches_title'))
                branches = []
            else:
                raise
        for br in branches:
            self.branch_combo.addItem(br.get('name', f"#{br.get('id')}"), br.get('id'))
        form.addRow(translate('branch_label'), self.branch_combo)

        if not user_id:
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.Password)
            form.addRow(translate('password_label'), self.password_edit)
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.Password)
            form.addRow(translate('confirm_password_label'), self.confirm_edit)
        else:
            change_btn = QPushButton(translate('change_password'))
            change_btn.clicked.connect(self.change_password)
            form.addRow(change_btn)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton(translate('save'))
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton(translate('cancel'))
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        if user_id:
            self.load_user()

    def load_user(self):
        user = user_service.get_user(self.user_id)
        if user:
            self.username_edit.setText(user.get('username', ''))
            self.fullname_edit.setText(user.get('full_name', ''))
            branch_id = user.get('branch_id')
            for i in range(self.branch_combo.count()):
                if str(self.branch_combo.itemData(i)) == str(branch_id):
                    self.branch_combo.setCurrentIndex(i)
                    break
            role = str(user.get('role', 'viewer') or 'viewer').lower()
            if role == 'user':
                role = 'viewer'
            idx = self.role_values.index(role) if role in self.role_values else self.role_values.index('viewer')
            self.role_combo.setCurrentIndex(idx)

    def save(self):
        username = self.username_edit.text().strip()
        if not username:
            QMessageBox.warning(self, translate('error'), translate('username_required'))
            return
        role = self.role_combo.currentData() or 'viewer'
        if not self.user_id:
            password = self.password_edit.text()
            confirm = self.confirm_edit.text()
            if not password:
                QMessageBox.warning(self, translate('error'), translate('password_required'))
                return
            if password != confirm:
                QMessageBox.warning(self, translate('error'), translate('passwords_do_not_match'))
                return
            try:
                user_service.create_user(username, password, self.fullname_edit.text().strip(), role, self.branch_combo.currentData())
                QMessageBox.information(self, translate('success'), translate('user_added'))
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, translate('error'), str(e))
        else:
            try:
                user_service.update_user(self.user_id, self.fullname_edit.text().strip(), role, self.branch_combo.currentData())
                QMessageBox.information(self, translate('success'), translate('user_updated'))
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, translate('error'), str(e))

    def change_password(self):
        dlg = ChangePasswordDialog(self, user_id=self.user_id)
        dlg.exec()



# Phase110 stable offline UI markers:
# notify_offline_read(self, 'المستخدمون')
