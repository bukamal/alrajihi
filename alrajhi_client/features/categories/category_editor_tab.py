# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtWidgets import QVBoxLayout

from core.services.product_service import product_service
from core.services.category_operation_policy import category_operation_policy
from i18n import qt_layout_direction, translate
from utils import show_toast
from workspace.documents import BaseDocumentTab
from workspace.documents.document_contract import descriptor_for

from .components.category_panels import CategoryHeaderPanel, CategoryPropertiesPanel


class CategoryEditorTab(BaseDocumentTab):
    DOCUMENT_DESCRIPTOR = descriptor_for("category")
    """Document-tab editor for category creation/editing, decomposed into panels."""

    def __init__(self, parent=None, category_id=None) -> None:
        super().__init__('category', document_id=category_id, parent=parent)
        self.category_id = category_id
        self.is_edit = category_id is not None
        self._can_edit = category_operation_policy.can(category_operation_policy.OP_EDIT if self.is_edit else category_operation_policy.OP_CREATE)
        self._build_ui()
        self.reload_parent_categories()
        if self.is_edit:
            self.load_category()
        else:
            self.set_document_title(translate('add_category'))
        self.properties.set_read_only(not self._can_edit)
        self.header.save_btn.setEnabled(self._can_edit)
        if not self._can_edit:
            self.header.set_subtitle(translate('category_read_only'))
        self.properties.changed.connect(lambda: self.set_dirty(True))
        self.set_dirty(False)

    def _build_ui(self) -> None:
        self.setLayoutDirection(qt_layout_direction())
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)
        self.header = CategoryHeaderPanel(self.is_edit, self)
        self.header.saveRequested.connect(self.workspace_save)
        self.properties = CategoryPropertiesPanel(self)
        root.addWidget(self.header)
        root.addWidget(self.properties)
        root.addStretch(1)
        self.setStyleSheet('''
            QFrame#DocumentHeaderCard, QFrame#FormCard { border: 1px solid palette(mid); border-radius: 14px; background: palette(base); }
            QLabel#DocumentTitle { font-size: 18px; font-weight: 900; }
            QLineEdit, QComboBox, QTextEdit { min-height: 34px; padding: 5px 9px; }
            QPushButton#primary { font-weight: 900; padding: 8px 16px; }
        ''')

    def reload_parent_categories(self) -> None:
        self.properties.set_parent_categories(product_service.categories(include_inactive=True, include_deleted=False), self.category_id)

    def load_category(self) -> None:
        category = product_service.category_by_id(int(self.category_id))
        if not category:
            show_toast(translate('category_not_found'), 'error', self)
            return
        self.properties.load_category(category)
        title = f"{translate('categories')}: {category.get('name', self.category_id)}"
        self.header.set_title(title)
        self.set_document_title(title)
        self.set_dirty(False)

    def workspace_save(self) -> None:
        if not self._can_edit:
            show_toast(translate('category_read_only'), 'warning', self)
            return
        payload = self.properties.payload()
        name = payload.get('name', '').strip()
        if not name:
            show_toast(translate('category_name_required'), 'error', self)
            self.properties.focus_name()
            return
        try:
            if self.is_edit:
                product_service.update_category(int(self.category_id), payload)
                saved_id = int(self.category_id)
                show_toast(translate('category_updated'), 'success', self)
            else:
                saved_id = product_service.add_category(payload)
                self.category_id = saved_id
                self.document_state.document_id = saved_id
                self.is_edit = True
                show_toast(translate('category_added'), 'success', self)
            title = f"{translate('categories')}: {name}"
            self.header.set_title(title)
            self.set_document_title(title)
            self.set_dirty(False)
            self.saved.emit(saved_id)
        except Exception as exc:
            show_toast(str(exc), 'error', self)
