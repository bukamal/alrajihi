# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QHeaderView, QLabel, QComboBox, QMessageBox
from PyQt5.QtCore import Qt
from i18n import translate
from action_handler import BaseActionHandler
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from views.widgets.components.table_toolbar import TableToolbar
from views.widgets.modern_ui import apply_modern_widget
from core.offline_guard import is_offline_read_error, offline_read_message
from core.services.permission_service import permission_service

class BaseWidget(QWidget, BaseActionHandler):
    entity_name = translate("item")
    search_placeholder = translate("search_placeholder")
    headers = []
    has_delete = True
    has_edit = True
    has_add = True
    has_export = True
    has_print = True
    has_pagination = False
    page_size = 50
    extra_buttons = []
    edit_permission_action = permission_service.ACTION_EDIT_INVOICES

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_page = 0
        self.total_count = 0
        self.model = None
        self.table = None
        self.search_edit = None
        self._init_base_ui()
        self.setup_base_actions()
        self.refresh()

    def _init_base_ui(self):
        self.setProperty('basitInspired', True)
        self.setProperty('basitManagementWorkspace', True)
        self.setProperty('listWorkspaceVisualTemplatePhase', 447)
        self.setProperty('visualRole', 'list_workspace_surface')
        self.setProperty('visualStyleSource', 'unified_list_workspace_template')
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        self.toolbar = TableToolbar(self.entity_name, self.search_placeholder, self)
        self.toolbar.setProperty('basitListToolbar', True)
        self.toolbar.setProperty('listWorkspaceVisualTemplatePhase', 447)
        self.toolbar.setProperty('visualRole', 'list_filter_bar')
        self.toolbar.addRequested.connect(self.add_item)
        self.toolbar.editRequested.connect(self._on_edit_shortcut)
        self.toolbar.deleteRequested.connect(self._on_delete_shortcut)
        self.toolbar.exportRequested.connect(self.export_to_excel)
        self.toolbar.printRequested.connect(self.print_table)
        self.toolbar.refreshRequested.connect(self.refresh)
        self.toolbar.resetColumnsRequested.connect(lambda: self.table.reset_layout() if self.table else None)
        self.toolbar.searchChanged.connect(lambda _text: self._on_toolbar_search_changed())
        self.toolbar.set_add_visible(self.has_add)
        self.toolbar.set_edit_visible(self.has_edit)
        self.toolbar.set_delete_visible(self.has_delete)
        self.toolbar.set_export_visible(self.has_export)
        self.toolbar.set_print_visible(self.has_print)
        layout.addWidget(self.toolbar)

        # Compatibility aliases used by existing widgets and action handlers.
        self.btn_widget = self.toolbar
        self.btn_layout = None
        self.add_btn = self.toolbar.add_btn
        self.edit_btn = self.toolbar.edit_btn
        self.delete_btn = self.toolbar.delete_btn
        self.export_btn = self.toolbar.export_btn
        self.print_btn = self.toolbar.print_btn
        self.refresh_btn = self.toolbar.refresh_btn
        self.search_edit = self.toolbar.search_edit

        # Optional legacy extra buttons still appear beside the toolbar.
        if self.extra_buttons:
            extra_layout = QHBoxLayout()
            extra_layout.setContentsMargins(0, 0, 0, 0)
            for btn_text, callback_name, btn_name in self.extra_buttons:
                btn = QPushButton(btn_text)
                callback = getattr(self, callback_name, None)
                if callback:
                    btn.clicked.connect(callback)
                btn.setEnabled(False)
                setattr(self, btn_name, btn)
                extra_layout.addWidget(btn)
            extra_layout.addStretch()
            layout.addLayout(extra_layout)

        self.table = SmartTableView()
        self.table.setProperty('basitTable', True)
        self.table.setProperty('basitManagementTable', True)
        self.table.setProperty('visualRole', 'list_table')
        self.table.setProperty('listWorkspaceVisualTemplatePhase', 447)
        self.table.set_table_identity(f"{self.__class__.__name__}.main")
        self.toolbar.set_table(self.table)
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        # doubleClicked is connected once by BaseActionHandler.setup_base_actions().
        self.table.clicked.connect(self._on_table_clicked)
        layout.addWidget(self.table)

        if self.has_pagination:
            self.pagination_layout = QHBoxLayout()
            self.prev_btn = QPushButton(translate("previous"))
            self.prev_btn.clicked.connect(self.prev_page)
            self.next_btn = QPushButton(translate("next"))
            self.next_btn.clicked.connect(self.next_page)
            self.page_label = QLabel()
            self.pagination_layout.addWidget(self.prev_btn)
            self.pagination_layout.addWidget(self.page_label)
            self.pagination_layout.addWidget(self.next_btn)
            self.pagination_layout.addStretch()
            layout.addLayout(self.pagination_layout)

        self.status_label = QLabel()
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)
        apply_modern_widget(self, self.entity_name, self.search_placeholder)

    def _on_toolbar_search_changed(self):
        self.current_page = 0
        self.refresh()

    # Phase116: global context-aware search entry point used by MainWindow.
    def set_global_filter(self, text: str):
        text = text or ""
        if self.search_edit is not None and self.search_edit.text() != text:
            self.search_edit.setText(text)
        else:
            self.current_page = 0
            self.refresh()

    # --- دوال يجب تجاوزها ---
    def fetch_data(self, search=None, limit=None, offset=None):
        raise NotImplementedError

    def get_total_count(self, search=None):
        return 0

    def delete_item(self, item_id):
        raise NotImplementedError

    def open_dialog(self, is_edit=False, item_id=None):
        raise NotImplementedError

    def get_item_name_from_row(self, row):
        if self.model and row < len(self.model._data):
            return str(self.model._data[row][1])
        return translate("item")

    def add_item(self):
        self.open_dialog(is_edit=False)

    def edit_item(self, index):
        action = getattr(self, 'edit_permission_action', permission_service.ACTION_EDIT_INVOICES)
        if not permission_service.can(action):
            QMessageBox.warning(self, translate('permissions'), permission_service.denied_message(action))
            return
        row = index.row()
        item_id = self.model.get_id(row) if self.model else None
        if item_id:
            self.open_dialog(is_edit=True, item_id=item_id)

    def refresh(self):
        search = self.search_edit.text().strip().lower() or None
        try:
            if self.has_pagination:
                self.total_count = self.get_total_count(search)
                offset = self.current_page * self.page_size
                items = self.fetch_data(search, limit=self.page_size, offset=offset)
                total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
                if self.current_page >= total_pages:
                    self.current_page = max(0, total_pages - 1)
                if hasattr(self, 'page_label'):
                    self.page_label.setText(translate("page_of", page=self.current_page + 1, pages=total_pages))
                if hasattr(self, 'prev_btn'):
                    self.prev_btn.setEnabled(self.current_page > 0)
                if hasattr(self, 'next_btn'):
                    self.next_btn.setEnabled(self.current_page + 1 < total_pages)
            else:
                items = self.fetch_data(search)
        except Exception as exc:
            if is_offline_read_error(exc):
                if hasattr(self, 'toolbar'):
                    self.toolbar.set_counter(translate('offline_refresh_failed'))
                if hasattr(self, 'status_label'):
                    self.status_label.setText(translate('offline_refresh_failed'))
                try:
                    show_toast(offline_read_message(self.entity_name), 'warning', self)
                except Exception:
                    pass
                return
            raise
        if items is None:
            items = []
        data = self.prepare_table_data(items)
        data_keys = self.get_data_keys()
        display_headers = getattr(self, 'display_headers', None) or self.headers
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=data_keys)
        self.table.setModel(self.model)
        hide_legacy_id_column = bool(data_keys and data_keys[0] == 'id' and len(display_headers) == len(data_keys))
        if self.model.columnCount() > 0:
            self.table.setColumnHidden(0, hide_legacy_id_column)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        total_records = self.total_count if self.has_pagination else len(items)
        visible_count = len(data)
        if self.has_pagination:
            start = 0 if total_records == 0 else self.current_page * self.page_size + 1
            end = min(total_records, self.current_page * self.page_size + visible_count)
            counter_text = translate("showing_records", start=start, end=end, total=total_records)
        else:
            counter_text = translate("showing_records_simple", count=visible_count, total=total_records)
        self.status_label.setText(counter_text)
        if hasattr(self, 'toolbar'):
            self.toolbar.set_counter(counter_text)
        sm = self.table.selectionModel()
        if sm is not None:
            try:
                sm.selectionChanged.disconnect(self._on_selection_changed)
            except:
                pass
            sm.selectionChanged.connect(self._on_selection_changed)
        self._update_action_buttons_state()

    def prepare_table_data(self, items):
        return [[item.get('id'), item.get('name', '')] for item in items]

    def get_data_keys(self):
        return ['id', 'name']

    def export_to_excel(self):
        if not permission_service.can(permission_service.ACTION_EXPORT_REPORTS):
            QMessageBox.warning(self, 'الصلاحيات', permission_service.denied_message(permission_service.ACTION_EXPORT_REPORTS))
            return
        if hasattr(self.table, 'export_to_excel'):
            self.table.export_to_excel()
        else:
            show_toast(translate("feature_not_available"), "error", self)

    def print_table(self):
        if hasattr(self.table, 'print_table'):
            self.table.print_table()
        else:
            show_toast(translate("feature_not_available"), "error", self)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()

    def _on_table_clicked(self, index):
        pass

    def _on_selection_changed(self, selected, deselected):
        self._update_action_buttons_state()

    def _update_action_buttons_state(self):
        sm = self.table.selectionModel() if self.table else None
        has_selection = len(sm.selectedRows()) > 0 if sm else False
        can_edit = permission_service.can(permission_service.ACTION_EDIT_INVOICES)
        can_delete = permission_service.can(permission_service.ACTION_DELETE)
        if self.has_edit and hasattr(self, 'edit_btn'):
            self.edit_btn.setEnabled(has_selection and can_edit)
        if self.has_delete and hasattr(self, 'delete_btn'):
            self.delete_btn.setEnabled(has_selection and can_delete)
        if hasattr(self, 'toolbar'):
            self.toolbar.set_edit_enabled(has_selection and self.has_edit and can_edit)
            self.toolbar.set_delete_enabled(has_selection and self.has_delete and can_delete)
        for _, _, btn_name in self.extra_buttons:
            if hasattr(self, btn_name):
                getattr(self, btn_name).setEnabled(has_selection)



# Phase110 offline guard markers: تعذر التحديث: الخادم غير متصل
