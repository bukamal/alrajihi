# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QComboBox, QTextEdit, QCheckBox, QLabel, QMenu
)
from PyQt5.QtCore import Qt

from core.services.product_service import product_service
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from utils import show_toast
from views.widgets.modern_ui import apply_modern_widget


class CategoriesWidget(QWidget):
    """Professional category manager with hierarchy, status, and safe archive."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._categories = []
        self.setObjectName('CategoriesWidget')
        self.setup_ui()
        apply_modern_widget(self, '🏷️ التصنيفات', 'تنظيم المواد ضمن مجموعات واضحة')
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('بحث في التصنيفات...')
        self.search_edit.textChanged.connect(self.refresh)
        self.show_archived = QCheckBox('إظهار المؤرشف')
        self.show_archived.stateChanged.connect(self.refresh)
        add_btn = QPushButton('➕ تصنيف جديد')
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_category)
        toolbar.addWidget(QLabel('التصنيفات'))
        toolbar.addWidget(self.search_edit, 1)
        toolbar.addWidget(self.show_archived)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_category)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.table)

        hint = QLabel('ملاحظة: التصنيف يمكن أن يحتوي تصنيفات فرعية. الأرشفة ممنوعة إذا كان مرتبطاً بمواد أو بتصنيفات فرعية نشطة.')
        hint.setObjectName('mutedLabel')
        layout.addWidget(hint)

    def refresh(self):
        self._categories = product_service.categories(
            search=self.search_edit.text().strip(),
            include_inactive=True,
            include_deleted=self.show_archived.isChecked()
        )
        data = []
        for cat in self._categories:
            item_count = int(cat.get('item_count') or 0)
            child_count = int(cat.get('child_count') or 0)
            archived = bool(cat.get('deleted_at')) or int(cat.get('is_active') or 0) == 0
            data.append({
                'id': cat.get('id'),
                'name': cat.get('name', ''),
                'full_name': cat.get('full_name') or cat.get('name', ''),
                'parent_name': cat.get('parent_name') or '—',
                'description': cat.get('description') or '',
                'item_count': item_count,
                'child_count': child_count,
                'status': 'مؤرشف' if archived else 'نشط',
                '_row_status': 'warning' if archived else '',
            })
        headers = ['المسار', 'الأب', 'عدد المواد', 'فرعية', 'الحالة', 'الوصف']
        keys = ['full_name', 'parent_name', 'item_count', 'child_count', 'status', 'description']
        self.model = GenericTableModel(data, headers, key_fields=['id'], data_keys=keys)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if hasattr(self.table, 'refresh_style'):
            self.table.refresh_style()

    def current_category_id(self):
        idx = self.table.currentIndex()
        if not idx.isValid() or not hasattr(self, 'model'):
            return None
        return self.model.get_id(idx.row())

    def _category_payload_dialog(self, title, category=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(460, 330)
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText('اسم التصنيف')
        parent_combo = QComboBox()
        parent_combo.addItem('بدون أب', None)
        for cat in product_service.categories(include_inactive=True, include_deleted=False):
            if category and int(cat.get('id')) == int(category.get('id')):
                continue
            parent_combo.addItem(cat.get('full_name') or cat.get('name', ''), cat.get('id'))
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText('وصف مختصر اختياري')
        desc_edit.setMaximumHeight(80)
        active_check = QCheckBox('نشط')
        active_check.setChecked(True)

        if category:
            name_edit.setText(category.get('name', ''))
            desc_edit.setPlainText(category.get('description') or '')
            active_check.setChecked(int(category.get('is_active') or 0) == 1 and not category.get('deleted_at'))
            parent_id = category.get('parent_id')
            for i in range(parent_combo.count()):
                if parent_combo.itemData(i) == parent_id:
                    parent_combo.setCurrentIndex(i)
                    break

        layout.addRow('الاسم:', name_edit)
        layout.addRow('التصنيف الأب:', parent_combo)
        layout.addRow('الوصف:', desc_edit)
        layout.addRow('', active_check)

        btns = QHBoxLayout()
        save_btn = QPushButton('حفظ')
        save_btn.setObjectName('primary')
        cancel_btn = QPushButton('إلغاء')
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

        payload = {}

        def save():
            name = name_edit.text().strip()
            if not name:
                show_toast('اسم التصنيف مطلوب', 'error', dialog)
                name_edit.setFocus()
                return
            payload.update({
                'name': name,
                'parent_id': parent_combo.currentData(),
                'description': desc_edit.toPlainText().strip(),
                'is_active': 1 if active_check.isChecked() else 0,
                'color': '#64748B',
                'icon': 'folder',
            })
            dialog.accept()

        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted:
            return payload
        return None

    def add_category(self):
        payload = self._category_payload_dialog('إضافة تصنيف')
        if not payload:
            return
        try:
            product_service.add_category(payload)
            show_toast('تمت إضافة التصنيف', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def edit_category(self, index=None):
        cat_id = self.current_category_id() if index is None else self.model.get_id(index.row())
        if not cat_id:
            show_toast('اختر تصنيفاً أولاً', 'warning', self)
            return
        category = product_service.category_by_id(cat_id)
        if not category:
            show_toast('التصنيف غير موجود', 'error', self)
            return
        payload = self._category_payload_dialog('تعديل تصنيف', category)
        if not payload:
            return
        try:
            product_service.update_category(cat_id, payload)
            show_toast('تم تحديث التصنيف', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def archive_selected(self):
        cat_id = self.current_category_id()
        if not cat_id:
            show_toast('اختر تصنيفاً أولاً', 'warning', self)
            return
        reply = QMessageBox.question(self, 'تأكيد الأرشفة', 'هل تريد أرشفة هذا التصنيف؟', QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            product_service.delete_category(cat_id)
            show_toast('تمت أرشفة التصنيف', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def restore_selected(self):
        cat_id = self.current_category_id()
        if not cat_id:
            show_toast('اختر تصنيفاً أولاً', 'warning', self)
            return
        try:
            product_service.restore_category(cat_id)
            show_toast('تمت استعادة التصنيف', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        edit = menu.addAction('تعديل')
        archive = menu.addAction('أرشفة')
        restore = menu.addAction('استعادة')
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == edit:
            self.edit_category()
        elif action == archive:
            self.archive_selected()
        elif action == restore:
            self.restore_selected()
