# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView, QMessageBox,
    QLabel, QListWidget, QListWidgetItem, QDialogButtonBox, QTableView
)
from PyQt5.QtCore import Qt

from views.widgets.modern_ui import apply_modern_dialog
from views.centered_dialog import CenteredDialog
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from utils import show_toast
from printing.printing_service import printing_service
from printing.barcode_multi_print import barcode_profile_candidates, normalize_dialog_rows
from core.services.settings_service import settings_service
from i18n import translate


class BatchPrintDialog(CenteredDialog):
    """Unified profile-aware multi-barcode print dialog.

    Backward compatible with material barcode printing while supporting Phase 339
    profile UIs: apparel variants, restaurant menu items, restaurant tables,
    cafe products and cafe modifiers.  The dialog only feeds the centralized
    Browser-HTML barcode print service; it does not own any print renderer.
    """

    def __init__(
        self,
        parent=None,
        selected_items: Iterable[Dict[str, Any]] | None = None,
        *,
        profile_id: str = "items.default",
        available_items: Iterable[Dict[str, Any]] | None = None,
        available_items_provider: Callable[[], Iterable[Dict[str, Any]]] | None = None,
        title: str | None = None,
    ):
        super().__init__(parent)
        self.profile_id = str(profile_id or "items.default")
        self.setWindowTitle(title or self._profile_title())
        self.resize(820, 560)
        self.selected_items = list(selected_items or [])
        self.available_items = list(available_items or [])
        self.available_items_provider = available_items_provider
        self.print_cfg = settings_service.get_printing_settings()
        self.items_data: List[Dict[str, Any]] = []

        if self.content_widget.layout() is None:
            QVBoxLayout(self.content_widget)

        toolbar = QHBoxLayout()
        info = QLabel(self._profile_help())
        info.setObjectName('muted')
        toolbar.addWidget(info)
        toolbar.addStretch()
        self.content_widget.layout().addLayout(toolbar)

        self.table = SmartTableView(identity=f'batch_print.{self.profile_id}')
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.content_widget.layout().addWidget(self.table)

        self.update_table_model()

        btn_row = QHBoxLayout()
        select_btn = QPushButton(translate('phase233_ui_017'))
        select_btn.clicked.connect(self.select_items)
        remove_btn = QPushButton(translate('phase233_ui_018'))
        remove_btn.clicked.connect(self.remove_selected)
        print_btn = QPushButton(translate('phase233_ui_019'))
        print_btn.clicked.connect(self.do_print)
        cancel_btn = QPushButton(translate('phase233_ui_020'))
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(select_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(print_btn)
        btn_row.addWidget(cancel_btn)
        self.content_widget.layout().addLayout(btn_row)

        self.load_items()
        apply_modern_dialog(self, self.windowTitle())

    def _profile_title(self) -> str:
        return translate(f'barcode.profile.{self.profile_id}.title')

    def _profile_help(self) -> str:
        return translate(f'barcode.profile.{self.profile_id}.help')

    def update_table_model(self):
        headers = ['#', translate('item'), translate('barcode'), translate('phase233_ui_015'), translate('barcode_label_details'), translate('phase235_copies')]
        data = []
        for idx, it in enumerate(self.items_data):
            data.append({
                'id': idx,
                'name': it.get('name') or it.get('item_name') or it.get('product_name') or it.get('table_name') or it.get('modifier_name') or '',
                'barcode': it.get('barcode') or it.get('qr_value') or '',
                'price': it.get('price') or '',
                'details': self._details_text(it),
                'copies': int(it.get('copies') or self.print_cfg.get('barcode_copies', 1) or 1),
            })
        self.model = GenericTableModel(data, headers, data_keys=['id', 'name', 'barcode', 'price', 'details', 'copies'])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def _details_text(self, row: Dict[str, Any]) -> str:
        parts = []
        for key in ('variant_color', 'variant_size', 'variant_code', 'section', 'zone', 'size', 'group'):
            value = str(row.get(key, '') or '').strip()
            if value and value != '—':
                parts.append(value)
        return ' / '.join(parts)

    def load_items(self):
        if self.selected_items:
            for item in self.selected_items:
                self.add_item_to_data(item)
        elif self.available_items:
            # Do not auto-add all candidates.  Offer the selector so the user can
            # choose a subset while still supporting pre-fed sector candidates.
            self.select_items()
        else:
            self.select_items()

    def _candidate_items(self) -> List[Dict[str, Any]]:
        if self.available_items_provider:
            try:
                rows = list(self.available_items_provider() or [])
            except Exception:
                rows = []
        elif self.available_items:
            rows = list(self.available_items)
        else:
            rows = barcode_profile_candidates(self.profile_id)
        return normalize_dialog_rows(rows, self.profile_id)

    def add_item_to_data(self, item, copies=1):
        rows = normalize_dialog_rows([dict(item or {})], self.profile_id)
        if not rows:
            return
        row = rows[0]
        row['copies'] = max(1, int(row.get('copies') or copies or 1))
        unique = (str(row.get('id') or ''), str(row.get('barcode') or row.get('qr_value') or ''), self.profile_id)
        for existing in self.items_data:
            marker = (str(existing.get('id') or ''), str(existing.get('barcode') or existing.get('qr_value') or ''), self.profile_id)
            if marker == unique:
                return
        self.items_data.append(row)
        self.update_table_model()

    def select_items(self):
        items = self._candidate_items()
        if not items:
            show_toast(translate('barcode.no_items_available_for_profile'), 'error', self)
            return
        dialog = CenteredDialog(self)
        dialog.setWindowTitle(self._profile_title())
        dialog.resize(620, 500)
        layout = QVBoxLayout(dialog.content_widget)
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        for index, it in enumerate(items):
            barcode = it.get('barcode') or it.get('qr_value') or ''
            details = self._details_text(it)
            name = it.get('name') or it.get('item_name') or it.get('product_name') or it.get('table_name') or it.get('modifier_name') or ''
            label = ' — '.join(part for part in [name, details, str(barcode)] if part)
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.UserRole, index)
            list_widget.addItem(list_item)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec():
            for list_item in list_widget.selectedItems():
                index = int(list_item.data(Qt.UserRole))
                if 0 <= index < len(items):
                    self.add_item_to_data(items[index])

    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not selected:
            return
        rows = sorted([idx.row() for idx in selected], reverse=True)
        for row in rows:
            if row < len(self.items_data):
                self.items_data.pop(row)
        self.update_table_model()

    def _print_options(self):
        return {'profile_id': self.profile_id}

    def do_print(self):
        if not self.items_data:
            show_toast(translate('phase235_no_items_to_print'), 'error', self)
            return
        items_for_print = []
        for it in self.items_data:
            payload = dict(it)
            payload['copies'] = max(1, int(payload.get('copies') or self.print_cfg.get('barcode_copies', 1) or 1))
            items_for_print.append(payload)
        if printing_service.barcode_profile_labels_print(self.profile_id, items_for_print, self, self._print_options()):
            show_toast(translate('phase235_barcode_print_success'), 'success', self)
            self.accept()
        else:
            show_toast(translate('phase235_barcode_print_failed'), 'error', self)
