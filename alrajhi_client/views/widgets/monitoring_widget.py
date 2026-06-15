# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit
from PyQt5.QtCore import Qt, QTimer

from core.services.monitoring_service import monitoring_service
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate, qt_layout_direction


from alrajhi_client.i18n import translate  # Phase110 explicit package import for localization guard
class MonitoringWidget(QWidget):
    """Read-only operations dashboard: API, Offline Queue, Ledger, request log."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._build_ui()
        apply_modern_widget(self, translate('monitoring_title_icon'), translate('monitoring_subtitle'))
        QTimer.singleShot(150, self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel(translate('monitoring_title'))
        title.setStyleSheet('font-size:20px;font-weight:700;')
        header.addWidget(title)
        header.addStretch()
        self.refresh_btn = QPushButton(translate('refresh'))
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        self.summary = QLabel('')
        self.summary.setWordWrap(True)
        self.summary.setObjectName('ModernSummaryBox')
        layout.addWidget(self.summary)

        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels([translate('metric'), translate('status'), translate('value'), translate('notes')])
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
            self.summary.setText(translate('monitoring_load_failed', error=exc))
            return

        status = data.get('status') or 'unknown'
        critical = ', '.join(data.get('critical') or []) or translate('none')
        warnings = ', '.join(data.get('warnings') or []) or translate('none')
        self.summary.setText(
            translate('monitoring_summary', status=status, data_source=data.get('data_source',''), warnings=warnings, critical=critical)
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
