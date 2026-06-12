# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
import json


class OfflineQueueWidget(QWidget):
    """Pending offline write operations created while the client was disconnected."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel('الطلبات المعلقة')
        title.setStyleSheet('font-size:20px;font-weight:700;')
        header.addWidget(title)
        header.addStretch()
        self.refresh_btn = QPushButton('تحديث')
        self.retry_btn = QPushButton('إعادة إرسال الآن')
        self.delete_btn = QPushButton('حذف المحدد')
        self.clear_sent_btn = QPushButton('تنظيف المرسلة')
        header.addWidget(self.refresh_btn)
        header.addWidget(self.retry_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.clear_sent_btn)
        layout.addLayout(header)

        self.info_label = QLabel('تُحفظ هنا عمليات الإنشاء/التعديل/الحذف عند انقطاع الاتصال. يتم إرسالها تلقائياً عند رجوع الخادم.')
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet('color:#475569; padding:8px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;')
        layout.addWidget(self.info_label)

        self.table = QTableWidget(0, 8, self)
        self.table.setHorizontalHeaderLabels(['#', 'الحالة', 'العملية', 'الكيان', 'المسار', 'المحاولات', 'وقت الإنشاء', 'آخر خطأ'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.refresh_btn.clicked.connect(self.refresh)
        self.retry_btn.clicked.connect(self.retry_now)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.clear_sent_btn.clicked.connect(self.clear_sent)

    def refresh(self):
        from database.connection import offline_queue
        rows = offline_queue.get_recent_requests(300)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = [
                row.get('id'), row.get('status') or 'pending', row.get('title') or row.get('method'),
                row.get('entity') or '', row.get('endpoint') or '', row.get('attempts') or 0,
                row.get('created_at') or '', row.get('last_error') or ''
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if c == 0:
                    item.setData(Qt.UserRole, int(row.get('id')))
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.info_label.setText(f'عدد الطلبات المعلقة: {offline_queue.count_pending()}')

    def _selected_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        item = self.table.item(indexes[0].row(), 0)
        return item.data(Qt.UserRole) if item else None

    def retry_now(self):
        mw = self.window()
        if hasattr(mw, 'process_offline_queue'):
            mw.process_offline_queue(show_messages=True)
        self.refresh()

    def delete_selected(self):
        req_id = self._selected_id()
        if not req_id:
            QMessageBox.information(self, 'الطلبات المعلقة', 'اختر طلباً أولاً.')
            return
        if QMessageBox.question(self, 'حذف', 'حذف الطلب المحدد من الطابور؟') == QMessageBox.Yes:
            from database.connection import offline_queue
            offline_queue.delete_request(req_id)
            self.refresh()

    def clear_sent(self):
        from database.connection import offline_queue
        offline_queue.clear_sent()
        self.refresh()
