# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidgetItem, QTextEdit
from PyQt5.QtCore import Qt, QTimer

from core.services.monitoring_service import monitoring_service
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate, qt_layout_direction
from ui.editable_smart_grid import EditableSmartGrid


class MonitoringWidget(QWidget):
    """Read-only operations dashboard: API, Offline Queue, Ledger, request log."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._build_ui()
        # Phase117: no duplicated top header card on monitoring page.
        apply_modern_widget(self)
        QTimer.singleShot(150, self.refresh)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        self.refresh_btn = QPushButton(translate('refresh'))
        self.refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_btn)
        layout.addLayout(toolbar)

        self.summary = QLabel('')
        self.summary.setVisible(False)

        self.table = EditableSmartGrid(0, 4, self, identity='monitoring.overview')
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

    def set_global_filter(self, text: str):
        text = (text or '').strip().lower()
        # Generic visual filter for widgets that expose one or more Qt tables.
        for name, table in self.__dict__.items():
            if not hasattr(table, 'rowCount') or not hasattr(table, 'setRowHidden'):
                continue
            try:
                rows = table.rowCount()
                cols = table.columnCount()
            except Exception:
                continue
            for row in range(rows):
                hay = []
                for col in range(cols):
                    try:
                        item = table.item(row, col) if hasattr(table, 'item') else None
                        if item is not None:
                            hay.append(item.text())
                        elif hasattr(table, 'model') and table.model() is not None:
                            idx = table.model().index(row, col)
                            hay.append(str(table.model().data(idx) or ''))
                    except Exception:
                        pass
                table.setRowHidden(row, bool(text) and text not in ' '.join(hay).lower())


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
