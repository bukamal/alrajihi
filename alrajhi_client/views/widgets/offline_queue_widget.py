# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidgetItem, QMessageBox
from PyQt5.QtCore import Qt
import json
from core.services.offline_queue_service import offline_queue_service
from views.widgets.modern_ui import apply_modern_widget
from i18n import translate, qt_layout_direction
from ui.editable_smart_grid import EditableSmartGrid


class OfflineQueueWidget(QWidget):
    """Pending offline write operations created while the client was disconnected."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self._build_ui()
        apply_modern_widget(self, translate('offline_queue_title_icon'), translate('offline_queue_subtitle'))
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel(translate('offline_queue_title'))
        title.setStyleSheet('font-size:20px;font-weight:700;')
        header.addWidget(title)
        header.addStretch()
        self.refresh_btn = QPushButton(translate('refresh'))
        self.retry_btn = QPushButton(translate('retry_now'))
        self.delete_btn = QPushButton(translate('delete_selected'))
        self.clear_sent_btn = QPushButton(translate('clear_sent'))
        header.addWidget(self.refresh_btn)
        header.addWidget(self.retry_btn)
        header.addWidget(self.delete_btn)
        header.addWidget(self.clear_sent_btn)
        layout.addLayout(header)

        self.info_label = QLabel(translate('offline_queue_help'))
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName('ModernInfoBox')
        layout.addWidget(self.info_label)

        self.table = EditableSmartGrid(0, 8, self, identity='offline_queue.list')
        self.table.setHorizontalHeaderLabels(['#', translate('status'), translate('operation'), translate('entity'), translate('endpoint'), translate('attempts'), translate('created_at'), translate('last_error')])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.refresh_btn.clicked.connect(self.refresh)
        self.retry_btn.clicked.connect(self.retry_now)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.clear_sent_btn.clicked.connect(self.clear_sent)

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
        rows = offline_queue_service.recent(300)
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
        self.info_label.setText(translate('pending_requests_count', count=offline_queue_service.count_pending()))

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
            QMessageBox.information(self, translate('offline_queue_title'), translate('select_request_first'))
            return
        if QMessageBox.question(self, translate('delete'), translate('delete_queue_request_confirm')) == QMessageBox.Yes:
            offline_queue_service.delete(req_id)
            self.refresh()

    def clear_sent(self):
        offline_queue_service.clear_sent()
        self.refresh()
