# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QCheckBox, QDialog, QFormLayout, QMessageBox, QDialogButtonBox, QTextEdit,
    QHeaderView, QTableView
)
from PyQt5.QtCore import Qt

from core.services.branch_service import branch_service
from models.table_models import GenericTableModel
from views.custom_table_view import CustomTableView
from utils import show_toast


class BranchDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.data = data or {}
        self.setWindowTitle('فرع جديد' if not data else 'تعديل فرع')
        self.setLayoutDirection(Qt.RightToLeft)
        self.resize(460, 360)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(self.data.get('name', ''))
        self.code_edit = QLineEdit(self.data.get('code', ''))
        self.address_edit = QLineEdit(self.data.get('address', ''))
        self.phone_edit = QLineEdit(self.data.get('phone', ''))
        self.notes_edit = QTextEdit(self.data.get('notes', ''))
        self.notes_edit.setMaximumHeight(90)
        self.active_check = QCheckBox('نشط')
        self.active_check.setChecked(bool(int(self.data.get('is_active', 1) or 0)))
        form.addRow('اسم الفرع:', self.name_edit)
        form.addRow('الكود:', self.code_edit)
        form.addRow('العنوان:', self.address_edit)
        form.addRow('الهاتف:', self.phone_edit)
        form.addRow('ملاحظات:', self.notes_edit)
        form.addRow('', self.active_check)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText('حفظ')
        buttons.button(QDialogButtonBox.Cancel).setText('إلغاء')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def payload(self):
        return {
            'name': self.name_edit.text().strip(),
            'code': self.code_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'notes': self.notes_edit.toPlainText().strip(),
            'is_active': 1 if self.active_check.isChecked() else 0,
        }


class BranchesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        title = QLabel('🏬 إدارة الفروع')
        title.setObjectName('sectionTitle')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('بحث باسم الفرع أو الكود...')
        self.search_edit.textChanged.connect(self.refresh)
        self.show_archived = QCheckBox('إظهار المؤرشفة')
        self.show_archived.toggled.connect(self.refresh)
        add_btn = QPushButton('➕ فرع جديد')
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_branch)
        edit_btn = QPushButton('✏️ تعديل')
        edit_btn.clicked.connect(self.edit_branch)
        archive_btn = QPushButton('🗑️ أرشفة')
        archive_btn.clicked.connect(self.archive_branch)
        refresh_btn = QPushButton('تحديث')
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(title)
        header.addWidget(self.search_edit, 1)
        header.addWidget(self.show_archived)
        header.addWidget(add_btn)
        header.addWidget(edit_btn)
        header.addWidget(archive_btn)
        header.addWidget(refresh_btn)
        layout.addLayout(header)
        self.table = CustomTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.doubleClicked.connect(lambda _idx: self.edit_branch())
        layout.addWidget(self.table)
        self.status = QLabel()
        self.status.setObjectName('mutedLabel')
        layout.addWidget(self.status)

    def refresh(self):
        branch_service.bootstrap()
        text = self.search_edit.text().strip().lower() if hasattr(self, 'search_edit') else ''
        include_archived = self.show_archived.isChecked() if hasattr(self, 'show_archived') else False
        rows = []
        for branch in branch_service.branches(include_archived=include_archived):
            if text and text not in str(branch.get('name', '')).lower() and text not in str(branch.get('code', '')).lower():
                continue
            archived = bool(branch.get('deleted_at')) or int(branch.get('is_active') or 0) == 0
            rows.append({
                'id': branch.get('id'),
                'name': branch.get('name', ''),
                'code': branch.get('code') or '—',
                'address': branch.get('address') or '—',
                'phone': branch.get('phone') or '—',
                'warehouse_count': int(branch.get('warehouse_count') or 0),
                'is_default': 'نعم' if int(branch.get('is_default') or 0) == 1 else 'لا',
                'status': 'مؤرشف' if archived else 'نشط',
                'notes': branch.get('notes') or '',
            })
        headers = ['الفرع', 'الكود', 'العنوان', 'الهاتف', 'عدد المستودعات', 'رئيسي', 'الحالة', 'ملاحظات']
        keys = ['name', 'code', 'address', 'phone', 'warehouse_count', 'is_default', 'status', 'notes']
        self.model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.status.setText(f'عدد الفروع: {len(rows)}')

    def _selected_id(self):
        if not hasattr(self, 'model'):
            return None
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        row = rows[0].row()
        try:
            return self.model.get_row(row).get('id')
        except Exception:
            return None

    def add_branch(self):
        dlg = BranchDialog(self)
        if dlg.exec_():
            try:
                branch_service.add_branch(dlg.payload())
                show_toast(self, 'تم إنشاء الفرع', 'success')
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, 'خطأ', str(e))

    def edit_branch(self):
        branch_id = self._selected_id()
        if not branch_id:
            QMessageBox.information(self, 'تعديل', 'اختر فرعاً أولاً')
            return
        data = branch_service.branch_by_id(branch_id)
        if not data:
            QMessageBox.warning(self, 'خطأ', 'الفرع غير موجود')
            return
        dlg = BranchDialog(self, data)
        if dlg.exec_():
            try:
                branch_service.update_branch(branch_id, dlg.payload())
                show_toast(self, 'تم تعديل الفرع', 'success')
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, 'خطأ', str(e))

    def archive_branch(self):
        branch_id = self._selected_id()
        if not branch_id:
            QMessageBox.information(self, 'أرشفة', 'اختر فرعاً أولاً')
            return
        if QMessageBox.question(self, 'تأكيد', 'هل تريد أرشفة هذا الفرع؟') != QMessageBox.Yes:
            return
        try:
            branch_service.archive_branch(branch_id)
            show_toast(self, 'تمت أرشفة الفرع', 'success')
            self.refresh()
        except Exception as e:
            QMessageBox.warning(self, 'خطأ', str(e))
