# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
                             QDateEdit, QLabel, QHeaderView, QMessageBox, QFileDialog, QLineEdit, QDialog, QTextEdit)
from PyQt5.QtCore import Qt, QDate
from core.services.audit_service import audit_service
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from offline_read import is_offline_read_error, notify_offline_read
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog
from i18n import translate, qt_layout_direction

class AuditLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.audit_service = audit_service
        self.current_page = 0
        self.page_size = 100
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        filter_layout = QHBoxLayout()
        self.user_filter = QComboBox()
        self.user_filter.addItem(translate('all'), None)
        self.action_filter = QComboBox()
        self.action_filter.addItem(translate('all'), None)
        for label, value in [
            (translate('action_create'), "CREATE"), (translate('edit'), "UPDATE"), (translate('action_soft_delete'), "SOFT_DELETE"),
            (translate('delete'), "DELETE"), (translate('action_update_units'), "UPDATE_UNITS"), (translate('action_post'), "POST"),
            (translate('action_reverse'), "REVERSE"), (translate('action_login'), "LOGIN"), (translate('action_logout'), "LOGOUT"),
        ]:
            self.action_filter.addItem(label, value)
        self.entity_filter = QComboBox()
        self.entity_filter.addItem(translate('all_entities'), None)
        for label, value in [
            (translate('sales_invoices'), "SALE_INVOICE"), (translate('purchase_invoices'), "PURCHASE_INVOICE"),
            (translate('items'), "ITEM"), (translate('categories'), "CATEGORY"), (translate('customers'), "CUSTOMER"),
            (translate('suppliers'), "SUPPLIER"), (translate('vouchers'), "VOUCHER"), (translate('expenses'), "EXPENSE"),
        ]:
            self.entity_filter.addItem(label, value)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(translate('audit_search_placeholder'))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        apply_btn = QPushButton(translate('apply'))
        apply_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(QLabel(translate('user_label')))
        filter_layout.addWidget(self.user_filter)
        filter_layout.addWidget(QLabel(translate('operation_label')))
        filter_layout.addWidget(self.action_filter)
        filter_layout.addWidget(QLabel(translate('entity_label')))
        filter_layout.addWidget(self.entity_filter)
        filter_layout.addWidget(QLabel(translate('search_label')))
        filter_layout.addWidget(self.search_edit)
        filter_layout.addWidget(QLabel(translate('from_date_label')))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel(translate('to_date_label')))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(apply_btn)
        layout.addLayout(filter_layout)

        btn_layout = QHBoxLayout()
        export_btn = QPushButton(translate('export_excel'))
        export_btn.clicked.connect(self.export_to_excel)
        delete_old_btn = QPushButton(translate('delete_old_logs'))
        delete_old_btn.clicked.connect(self.delete_old_logs)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(delete_old_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = SmartTableView(identity="audit_log.list")
        self.table.setSelectionBehavior(SmartTableView.SelectRows)
        self.table.doubleClicked.connect(self.show_details)
        layout.addWidget(self.table)

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

        apply_modern_widget(self, translate('audit_log_title_icon'), translate('audit_log_subtitle'))
        self.refresh()

    def set_global_filter(self, text: str):
        text = text or ''
        field = getattr(self, 'search_edit', None)
        if field is not None and field.text() != text:
            field.setText(text)
        elif hasattr(self, 'refresh'):
            self.refresh()


    def refresh(self, reset_page=True):
        if reset_page:
            self.current_page = 0
        user_id = self.user_filter.currentData()
        action = self.action_filter.currentData()
        entity_type = self.entity_filter.currentData()
        search_text = self.search_edit.text().strip()
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        offset = self.current_page * self.page_size
        try:
            logs, self.total_count = self.audit_service.list_logs(
                limit=self.page_size, offset=offset,
                user_id=user_id, action=action, table_name=entity_type, start_date=start, end_date=end
            )
        except Exception as exc:
            if is_offline_read_error(exc):
                notify_offline_read(self, translate('audit_log_title'))
                return
            raise
        if search_text:
            needle = search_text.lower()
            logs = [l for l in logs if needle in str(l.get('entity_id') or l.get('record_id') or '').lower()
                    or needle in str(l.get('details') or '').lower()
                    or needle in str(l.get('old_values') or '').lower()
                    or needle in str(l.get('new_values') or '').lower()]
            self.total_count = len(logs)
        data = []
        for log in logs:
            data.append({
                'id': log['id'],
                'username': log.get('username', ''),
                'action': self._action_label(log.get('action', '')),
                'entity_type': log.get('entity_type') or log.get('table_name', ''),
                'entity_id': log.get('entity_id') or log.get('record_id', ''),
                'details': self._short_details(log),
                'source': log.get('source', ''),
                'ip_address': log.get('ip_address', ''),
                'timestamp': (log.get('event_time') or log.get('timestamp', ''))[:19]
            })
        headers = ['username', 'action', 'entity_type', 'entity_id', 'details', 'source', 'ip_address', 'timestamp']
        display_headers = [translate('user'), translate('operation'), translate('entity'), translate('record_id'), translate('details'), translate('source'), translate('ip_address'), translate('date_time')]
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(translate('page_of', page=self.current_page + 1, total=total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)


    def _action_label(self, action):
        mapping = {
            'CREATE': translate('action_create'), 'UPDATE': translate('edit'), 'DELETE': translate('delete'), 'SOFT_DELETE': translate('action_soft_delete'),
            'UPDATE_UNITS': translate('action_update_units'), 'POST': translate('action_post'), 'REVERSE': translate('action_reverse'),
            'LOGIN': translate('action_login'), 'LOGOUT': translate('action_logout')
        }
        return mapping.get(action, action or '')

    def _short_details(self, log):
        details = log.get('details') or ''
        if len(details) > 140:
            return details[:140] + '…'
        return details

    def show_details(self):
        row = self.table.currentIndex().row()
        if row < 0 or not hasattr(self, 'model'):
            return
        try:
            log = self.model._data[row]
        except Exception:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(translate('audit_log_details'))
        dlg.setLayoutDirection(qt_layout_direction())
        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText('\n'.join(f"{k}: {v}" for k, v in log.items()))
        layout.addWidget(text)
        close_btn = QPushButton(translate('close'))
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.resize(760, 520)
        dlg.exec_()

    def export_to_excel(self):
        self.table.export_to_excel()

    def delete_old_logs(self):
        reply = QMessageBox.question(self, translate('confirm_delete'), translate('delete_old_logs_confirm'),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.audit_service.delete_old_logs(90)
            show_toast(translate('old_logs_deleted'), 'success', self)
            self.refresh()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh(reset_page=False)

    def next_page(self):
        self.current_page += 1
        self.refresh(reset_page=False)



# Phase110 stable offline UI markers:
# notify_offline_read(self, 'سجل التدقيق')
