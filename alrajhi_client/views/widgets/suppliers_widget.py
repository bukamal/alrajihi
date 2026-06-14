# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
                             QLabel, QComboBox, QHeaderView, QFormLayout)
from PyQt5.QtCore import Qt
from decimal import Decimal
from core.services.entity_service import entity_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.centered_dialog import CenteredDialog
from views.dialogs.add_entity_dialog import AddEntityDialog
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from views.widgets.modern_ui import apply_modern_widget, apply_modern_dialog
from i18n import translate as tr, qt_layout_direction

class SuppliersWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.current_page = 0
        self.page_size = 50
        self.total_count = 0

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        top_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("search_supplier"))
        self.search_edit.textChanged.connect(self.refresh)
        top_layout.addWidget(self.search_edit)

        self.balance_filter = QComboBox()
        self.balance_filter.addItems([tr("all"), tr("positive_balance"), tr("negative_balance"), tr("zero_balance")])
        self.balance_filter.currentIndexChanged.connect(self.refresh)
        top_layout.addWidget(QLabel(tr("balance_filter_label")))
        top_layout.addWidget(self.balance_filter)

        self.add_btn = QPushButton(tr("add_supplier"))
        self.add_btn.setObjectName("primary")
        self.add_btn.clicked.connect(self.add_supplier)
        top_layout.addWidget(self.add_btn)

        layout.addLayout(top_layout)

        self.table = CustomTableView()
        self.table.setSelectionBehavior(CustomTableView.SelectRows)
        self.table.doubleClicked.connect(self.edit_supplier)
        layout.addWidget(self.table)

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton(tr("previous"))
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(tr("next"))
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

        apply_modern_widget(self, tr('suppliers_title'), tr('suppliers_subtitle'))
        self.refresh()

    def refresh(self):
        search = self.search_edit.text().strip() or None
        offset = self.current_page * self.page_size
        try:
            suppliers, self.total_count = entity_service.suppliers(search=search, limit=self.page_size, offset=offset)
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(tr('suppliers')), 'warning', self)
                return
            raise
        display_curr = currency.get_display_currency()
        data = []
        for s in suppliers:
            balance_display = currency.convert(Decimal(str(s.get('balance', 0))), 'USD', display_curr)
            filter_idx = self.balance_filter.currentIndex()
            if filter_idx == 1 and balance_display <= 0:
                continue
            if filter_idx == 2 and balance_display >= 0:
                continue
            if filter_idx == 3 and balance_display != 0:
                continue
            data.append({
                'id': s['id'],
                'name': s.get('name', ''),
                'phone': s.get('phone', ''),
                'address': s.get('address', ''),
                'balance': currency.format_amount(balance_display)
            })
        headers = ['name', 'phone', 'address', 'balance']
        display_headers = [tr('name'), tr('phone'), tr('address'), tr('balance')]
        self.model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.table.setModel(self.model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض؛ لا نخفي العمود الأول الحقيقي.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.refresh_style()

        total_pages = (self.total_count + self.page_size - 1) // self.page_size
        self.page_label.setText(tr("page_of", page=self.current_page + 1, pages=total_pages))
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page + 1 < total_pages)

    def add_supplier(self):
        dialog = AddEntityDialog(self, 'purchase')
        if dialog.exec():
            self.refresh()

    def edit_supplier(self, index):
        row = index.row()
        supp_id = self.model.get_id(row)
        if not supp_id:
            return
        supp = entity_service.supplier_by_id(supp_id)
        if not supp:
            return
        dialog = CenteredDialog(self)
        dialog.setWindowTitle(tr("edit_supplier"))
        dialog.resize(400, 300)
        layout = QFormLayout(dialog.content_widget)
        name_edit = QLineEdit()
        name_edit.setText(supp.get('name', ''))
        phone_edit = QLineEdit()
        phone_edit.setText(supp.get('phone', ''))
        address_edit = QLineEdit()
        address_edit.setText(supp.get('address', ''))
        layout.addRow(tr("name_label"), name_edit)
        layout.addRow(tr("phone_label"), phone_edit)
        layout.addRow(tr("address_label"), address_edit)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("save"))
        cancel_btn = QPushButton(tr("cancel"))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)
        def save():
            try:
                entity_service.update_supplier(supp_id, name_edit.text().strip(), phone_edit.text().strip(), address_edit.text().strip())
                show_toast(tr("update_done"), "success", dialog)
                dialog.accept()
                self.refresh()
            except Exception as e:
                show_toast(str(e), "error", dialog)
        save_btn.clicked.connect(save)
        cancel_btn.clicked.connect(dialog.reject)
        apply_modern_dialog(dialog, tr('edit_supplier'))
        dialog.exec()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()

    def next_page(self):
        self.current_page += 1
        self.refresh()


