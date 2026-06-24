# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QComboBox, QTextEdit, QCheckBox, QLabel, QMenu
)
from PyQt5.QtCore import Qt

from core.services.product_service import product_service
from core.services.category_operation_policy import category_operation_policy
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate, qt_layout_direction
from views.widgets.inline_document_host import InlineDocumentHostMixin


class CategoriesWidget(InlineDocumentHostMixin, QWidget):
    """Professional category manager with hierarchy, status, and safe archive."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._categories = []
        self.setObjectName('CategoriesWidget')
        self.setup_ui()
        apply_modern_widget(self, translate('categories_title_icon'), translate('categories_subtitle'))
        self._apply_operation_state()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translate('categories_search_placeholder'))
        self.search_edit.textChanged.connect(self.refresh)
        self.show_archived = QCheckBox(translate('show_archived'))
        self.show_archived.stateChanged.connect(self.refresh)
        self.add_btn = QPushButton(translate('new_category_btn'))
        self.add_btn.setObjectName('primary')
        self.add_btn.clicked.connect(self.add_category)
        toolbar.addWidget(QLabel(translate('categories')))
        toolbar.addWidget(self.search_edit, 1)
        toolbar.addWidget(self.show_archived)
        toolbar.addWidget(self.add_btn)
        layout.addLayout(toolbar)

        self.table = SmartTableView(identity="categories.list")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_category)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self._install_inline_document_host(self.table, layout, translate('categories'))

        hint = QLabel(translate('categories_hint'))
        hint.setObjectName('mutedLabel')
        layout.addWidget(hint)


    def _main_window(self):
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, 'open_category_document'):
                return parent
            parent = parent.parent()
        return None

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(self, 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        elif hasattr(self, 'refresh'):
            self.refresh()


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
                'status': translate('archived') if archived else translate('active'),
                '_row_status': 'warning' if archived else '',
            })
        headers = [translate('path'), translate('parent'), translate('items_count'), translate('child_categories'), translate('status'), translate('description')]
        keys = ['full_name', 'parent_name', 'item_count', 'child_count', 'status', 'description']
        self.model = GenericTableModel(data, headers, key_fields=['id'], data_keys=keys)
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if hasattr(self.table, 'refresh_style'):
            self.table.refresh_style()
        self._connect_inline_detail_preview()

    def _source_row_for_index(self, index=None):
        idx = index if index is not None else self.table.currentIndex()
        if not idx.isValid() or not hasattr(self, 'model'):
            return -1
        if hasattr(self.table, 'current_source_row') and index is None:
            return self.table.current_source_row()
        model = self.table.model()
        if hasattr(model, 'mapToSource'):
            try:
                idx = model.mapToSource(idx)
            except Exception:
                pass
        return idx.row()

    def current_category_id(self):
        row = self._source_row_for_index()
        if row < 0 or not hasattr(self, 'model'):
            return None
        return self.model.get_id(row)

    def _apply_operation_state(self):
        can_create = category_operation_policy.can(category_operation_policy.OP_CREATE)
        if hasattr(self, 'add_btn'):
            self.add_btn.setEnabled(can_create)

    def _category_payload_dialog(self, title, category=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLayoutDirection(qt_layout_direction())
        dialog.resize(460, 330)
        layout = QFormLayout(dialog)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText(translate('category_name'))
        parent_combo = QComboBox()
        parent_combo.addItem(translate('no_parent'), None)
        for cat in product_service.categories(include_inactive=True, include_deleted=False):
            if category and int(cat.get('id')) == int(category.get('id')):
                continue
            parent_combo.addItem(cat.get('full_name') or cat.get('name', ''), cat.get('id'))
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText(translate('optional_short_description'))
        desc_edit.setMaximumHeight(80)
        active_check = QCheckBox(translate('active'))
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

        layout.addRow(translate('name_label'), name_edit)
        layout.addRow(translate('parent_category_label'), parent_combo)
        layout.addRow(translate('description_label'), desc_edit)
        layout.addRow('', active_check)

        btns = QHBoxLayout()
        save_btn = QPushButton(translate('save'))
        save_btn.setObjectName('primary')
        cancel_btn = QPushButton(translate('cancel'))
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addRow(btns)

        payload = {}

        def save():
            name = name_edit.text().strip()
            if not name:
                show_toast(translate('category_name_required'), 'error', dialog)
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
        if not category_operation_policy.can(category_operation_policy.OP_CREATE):
            show_toast(translate('category_operation_denied'), 'warning', self)
            return
        # Phase377: Add category is inline master-detail, not a workspace sub-tab.
        # Legacy route marker only: main.open_category_document()
        try:
            from features.categories import CategoryEditorTab
            editor = CategoryEditorTab(self.inline_editor_host)
            return self._show_inline_document(editor, translate('add_category'))
        except Exception as exc:
            show_toast(str(exc), 'warning', self)
            payload = self._category_payload_dialog(translate('add_category'))
            if not payload:
                return
            try:
                product_service.add_category(payload)
                show_toast(translate('category_added'), 'success', self)
                self.refresh()
            except Exception as e:
                show_toast(str(e), 'error', self)

    def edit_category(self, index=None):
        row = self._source_row_for_index(index)
        cat_id = self.current_category_id() if index is None else (self.model.get_id(row) if row >= 0 else None)
        if not cat_id:
            show_toast(translate('select_category_first'), 'warning', self)
            return
        if not category_operation_policy.can(category_operation_policy.OP_EDIT):
            show_toast(translate('category_operation_denied'), 'warning', self)
            return
        try:
            from features.categories import CategoryEditorTab
            editor = CategoryEditorTab(self.inline_editor_host, category_id=cat_id)
            return self._show_inline_document(editor, translate('edit_category'))
        except Exception as exc:
            show_toast(str(exc), 'warning', self)
            category = product_service.category_by_id(cat_id)
            if not category:
                show_toast(translate('category_not_found'), 'error', self)
                return
            payload = self._category_payload_dialog(translate('edit_category'), category)
            if not payload:
                return
            try:
                product_service.update_category(cat_id, payload)
                show_toast(translate('category_updated'), 'success', self)
                self.refresh()
            except Exception as e:
                show_toast(str(e), 'error', self)

    def archive_selected(self):
        cat_id = self.current_category_id()
        if not cat_id:
            show_toast(translate('select_category_first'), 'warning', self)
            return
        if not category_operation_policy.can(category_operation_policy.OP_ARCHIVE):
            show_toast(translate('category_operation_denied'), 'warning', self)
            return
        reply = QMessageBox.question(self, translate('confirm_archive'), translate('archive_category_confirm'), QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            product_service.delete_category(cat_id)
            show_toast(translate('category_archived'), 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def restore_selected(self):
        cat_id = self.current_category_id()
        if not cat_id:
            show_toast(translate('select_category_first'), 'warning', self)
            return
        if not category_operation_policy.can(category_operation_policy.OP_RESTORE):
            show_toast(translate('category_operation_denied'), 'warning', self)
            return
        try:
            product_service.restore_category(cat_id)
            show_toast(translate('category_restored'), 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        edit = menu.addAction(translate('edit'))
        archive = menu.addAction(translate('archive'))
        restore = menu.addAction(translate('restore'))
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == edit:
            self.edit_category()
        elif action == archive:
            self.archive_selected()
        elif action == restore:
            self.restore_selected()
