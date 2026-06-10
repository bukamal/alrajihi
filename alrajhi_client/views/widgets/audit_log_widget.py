# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox,
                             QDateEdit, QLabel, QHeaderView, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QDate
from database import AuditRepository
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from utils import show_toast

class AuditLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.repo = AuditRepository()
        self.current_page = 0
        self.page_size = 100
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        filter_layout = QHBoxLayout()
        self.user_filter = QComboBox()
        self.user_filter.addItem("الكل", None)
        self.action_filter = QComboBox()
        self.action_filter.addItems(["الكل", "تسجيل دخول", "تسجيل خروج", "إضافة مستخدم", "تعديل مستخدم", "حذف مستخدم", "تغيير كلمة المرور", "إضافة مادة", "تعديل مادة", "حذف مادة", "إضافة فاتورة", "تعديل فاتورة", "حذف فاتورة"])
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(QLabel("المستخدم:"))
        filter_layout.addWidget(self.user_filter)
        filter_layout.addWidget(QLabel("العملية:"))
        filter_layout.addWidget(self.action_filter)
        filter_layout.addWidget(QLabel("من تاريخ:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("إلى تاريخ:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(apply_btn)
        layout.addLayout(filter_layout)

        btn_layout = QHBoxLayout()
        export_btn = QPushButton("📊 تصدير إلى Excel")
        export_btn.clicked.connect(self.export_to_excel)
        delete_old_btn = QPushButton("🗑 حذف السجلات القديمة (أكثر من 90 يوم)")
        delete_old_btn.clicked.connect(self.delete_old_logs)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(delete_old_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
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

    def refresh(self, reset_page=True):
        if reset_page:
            self.current_page = 0
        user_id = self.user_filter.currentData()
        action = self.action_filter.currentText()
        if action == "الكل":
            action = None
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        offset = self.current_page * self.page_size
        logs, self.total_count = self.repo.get_all(
            limit=self.page_size, offset=offset,
            user_id=user_id, action=action, start_date=start, end_date=end
        )
        data = []
        for log in logs:
            data.append({
                'id': log['id'],
                'username': log.get('username', ''),
                'action': log.get('action', ''),
                'entity_type': log.get('entity_type') or log.get('table_name', ''),
                'entity_id': log.get('entity_id') or log.get('record_id', ''),
                'details': log.get('details', ''),
                'source': log.get('source', ''),
                'ip_address': log.get('ip_address', ''),
                'timestamp': (log.get('event_time') or log.get('timestamp', ''))[:19]
            })
        headers = ['username', 'action', 'entity_type', 'entity_id', 'details', 'source', 'ip_address', 'timestamp']
        display_headers = ['المستخدم', 'العملية', 'الكيان', 'رقم السجل', 'التفاصيل', 'المصدر', 'عنوان IP', 'التاريخ والوقت']
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

    def export_to_excel(self):
        self.table.export_to_excel()

    def delete_old_logs(self):
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد من حذف جميع السجلات الأقدم من 90 يوماً؟ لا يمكن التراجع.",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.repo.delete_old_logs(90)
            show_toast("تم حذف السجلات القديمة", "success", self)
            self.refresh()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh(reset_page=False)

    def next_page(self):
        self.current_page += 1
        self.refresh(reset_page=False)


