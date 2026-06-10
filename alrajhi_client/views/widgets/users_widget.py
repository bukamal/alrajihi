# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QHeaderView, QMessageBox, QDialog, QFormLayout, QComboBox, QLabel)
from PyQt5.QtCore import Qt
from database import UserRepository
from auth.session import UserSession
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.dialogs.change_password_dialog import ChangePasswordDialog
from utils import show_toast
from core.services.branch_service import branch_service

class UsersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.current_page = 0
        self.page_size = 20
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ إضافة مستخدم")
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_user)
        top_layout.addWidget(self.add_btn)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_user)
        layout.addWidget(self.table)

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("السابق")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton("التالي")
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        self.refresh()

    def refresh(self):
        offset = self.current_page * self.page_size
        repo = UserRepository()
        users = repo.get_all()
        self.total_count = len(users)
        users = users[offset:offset + self.page_size]
        data = []
        for u in users:
            role_text = "مدير" if u.get('role') == 'admin' else "مستخدم" if u.get('role') == 'user' else "مشاهد"
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
        display_headers = ['اسم المستخدم', 'الاسم الكامل', 'الصلاحية', 'الفرع', 'تاريخ التسجيل', 'آخر دخول']
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(f"الصفحة {self.current_page + 1} من {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def add_user(self):
        dialog = UserDialog(self)
        if dialog.exec():
            self.refresh()

    def edit_user(self, index):
        row = index.row()
        user_id = self.model.get_id(row)
        if user_id:
            dialog = UserDialog(self, user_id=user_id)
            if dialog.exec():
                self.refresh()

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
        self.setWindowTitle("تعديل مستخدم" if user_id else "إضافة مستخدم جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(400, 350)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        if user_id:
            self.username_edit.setEnabled(False)
        form.addRow("اسم المستخدم:", self.username_edit)

        self.fullname_edit = QLineEdit()
        form.addRow("الاسم الكامل:", self.fullname_edit)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["مدير", "مستخدم", "مشاهد"])
        form.addRow("الصلاحية:", self.role_combo)

        self.branch_combo = QComboBox()
        for br in branch_service.branches():
            self.branch_combo.addItem(br.get('name', f"#{br.get('id')}"), br.get('id'))
        form.addRow("الفرع:", self.branch_combo)

        if not user_id:
            self.password_edit = QLineEdit()
            self.password_edit.setEchoMode(QLineEdit.Password)
            form.addRow("كلمة المرور:", self.password_edit)
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.Password)
            form.addRow("تأكيد كلمة المرور:", self.confirm_edit)
        else:
            change_btn = QPushButton("تغيير كلمة المرور")
            change_btn.clicked.connect(self.change_password)
            form.addRow(change_btn)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

        if user_id:
            self.load_user()

    def load_user(self):
        repo = UserRepository()
        user = repo.get_by_id(self.user_id)
        if user:
            self.username_edit.setText(user.get('username', ''))
            self.fullname_edit.setText(user.get('full_name', ''))
            branch_id = user.get('branch_id')
            for i in range(self.branch_combo.count()):
                if str(self.branch_combo.itemData(i)) == str(branch_id):
                    self.branch_combo.setCurrentIndex(i)
                    break
            role_map = {'admin': 0, 'user': 1, 'viewer': 2}
            self.role_combo.setCurrentIndex(role_map.get(user.get('role', 'user'), 1))

    def save(self):
        username = self.username_edit.text().strip()
        if not username:
            QMessageBox.warning(self, "خطأ", "اسم المستخدم مطلوب")
            return
        role_map = {0: 'admin', 1: 'user', 2: 'viewer'}
        role = role_map[self.role_combo.currentIndex()]
        repo = UserRepository()
        if not self.user_id:
            password = self.password_edit.text()
            confirm = self.confirm_edit.text()
            if not password:
                QMessageBox.warning(self, "خطأ", "كلمة المرور مطلوبة")
                return
            if password != confirm:
                QMessageBox.warning(self, "خطأ", "كلمتا المرور غير متطابقتين")
                return
            try:
                repo.create(username, password, self.fullname_edit.text().strip(), role, self.branch_combo.currentData())
                QMessageBox.information(self, "نجاح", "تمت إضافة المستخدم")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))
        else:
            try:
                repo.update(self.user_id, self.fullname_edit.text().strip(), role, self.branch_combo.currentData())
                QMessageBox.information(self, "نجاح", "تم تحديث المستخدم")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def change_password(self):
        dlg = ChangePasswordDialog(self, user_id=self.user_id)
        dlg.exec()


