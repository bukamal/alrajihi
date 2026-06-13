# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit
from PyQt5.QtCore import Qt, QTimer

from core.services.monitoring_service import monitoring_service


class MonitoringWidget(QWidget):
    """Read-only operations dashboard: API, Offline Queue, Ledger, request log."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        QTimer.singleShot(150, self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel('مراقبة التشغيل')
        title.setStyleSheet('font-size:20px;font-weight:700;')
        header.addWidget(title)
        header.addStretch()
        self.refresh_btn = QPushButton('تحديث')
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.summary = QLabel('')
        self.summary.setWordWrap(True)
        self.summary.setStyleSheet('padding:10px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;')
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(['المؤشر', 'الحالة', 'القيمة', 'ملاحظات'])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.details = QTextEdit(self)
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(150)
        layout.addWidget(self.details)

    def _status_text(self, value):
        if value is True:
            return 'ok'
        if value is False:
            return 'warning'
        return str(value or '')

    def _add_row(self, metric, status, value='', notes=''):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, text in enumerate([metric, status, value, notes]):
            self.table.setItem(row, col, QTableWidgetItem(str(text)))

    def refresh(self):
        try:
            data = monitoring_service.overview()
        except Exception as exc:
            self.summary.setText(f'فشل تحميل مراقبة التشغيل: {exc}')
            return

        status = data.get('status') or 'unknown'
        critical = ', '.join(data.get('critical') or []) or 'لا يوجد'
        warnings = ', '.join(data.get('warnings') or []) or 'لا يوجد'
        self.summary.setText(
            f"الحالة العامة: {status}\n"
            f"مصدر البيانات: {data.get('data_source','')}\n"
            f"تحذيرات: {warnings}\n"
            f"حرج: {critical}"
        )

        self.table.setRowCount(0)
        api = data.get('api') or {}
        queue = data.get('queue') or {}
        ledger = data.get('ledger') or {}
        request_log = data.get('request_log') or []
        self._add_row('API', api.get('status'), api.get('server_url') or api.get('mode'), api.get('error') or api.get('message') or '')
        self._add_row('Offline Queue', queue.get('status'), f"pending={queue.get('pending', 0)}", f"failed_recent={len(queue.get('failed_recent') or [])}")
        self._add_row('Inventory Ledger', ledger.get('status'), 'ready' if ledger.get('ok') else 'not ready', ledger.get('error') or ledger.get('source') or '')
        failed_http = len([r for r in request_log if not r.get('ok')])
        self._add_row('Recent API Requests', 'warning' if failed_http else 'ok', f"errors={failed_http}/{len(request_log)}", '')
        counts = data.get('counts') or {}
        if counts:
            self._add_row('Local Counts', 'info', f"tables={len(counts)}", '')
        self.table.resizeColumnsToContents()

        self.details.setPlainText(json.dumps(data, ensure_ascii=False, indent=2, default=str))
