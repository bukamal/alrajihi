# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
                             QHeaderView, QMessageBox, QMenu, QAction, QLabel)
from PyQt5.QtCore import Qt
from core.services.manufacturing_service import manufacturing_service
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.dialogs.bom_dialog import BOMDialog
from views.dialogs.production_order_dialog import ProductionOrderDialog
from views.dialogs.production_details_dialog import ProductionDetailsDialog
from utils import show_toast

class ManufacturingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = manufacturing_service
        self.setLayoutDirection(Qt.RightToLeft)
        self.bom_page = 0
        self.orders_page = 0
        self.page_size = 30

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        self.tabs = QTabWidget()
        self.bom_tab = QWidget()
        self.orders_tab = QWidget()
        self.setup_bom_tab()
        self.setup_orders_tab()
        self.tabs.addTab(self.bom_tab, "قوائم المواد (BOM)")
        self.tabs.addTab(self.orders_tab, "أوامر الإنتاج")
        layout.addWidget(self.tabs)

        self.refresh_bom()
        self.refresh_orders()

    def setup_bom_tab(self):
        layout = QVBoxLayout(self.bom_tab)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ إضافة قائمة مواد")
        add_btn.clicked.connect(self.add_bom)
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.refresh_bom)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        self.bom_table = CustomTableView()
        self.bom_table.setSelectionBehavior(CustomTableView.SelectRows)
        self.bom_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bom_table.customContextMenuRequested.connect(self.show_bom_context_menu)
        self.bom_table.doubleClicked.connect(self.edit_bom)
        layout.addWidget(self.bom_table)

        # Pagination for BOM
        pagination = QHBoxLayout()
        self.bom_prev = QPushButton("السابق")
        self.bom_prev.clicked.connect(lambda: self.prev_page('bom'))
        self.bom_next = QPushButton("التالي")
        self.bom_next.clicked.connect(lambda: self.next_page('bom'))
        self.bom_page_label = QLabel()
        pagination.addWidget(self.bom_prev)
        pagination.addWidget(self.bom_page_label)
        pagination.addWidget(self.bom_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def setup_orders_tab(self):
        layout = QVBoxLayout(self.orders_tab)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ أمر إنتاج جديد")
        add_btn.clicked.connect(self.add_order)
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.refresh_orders)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(refresh_btn)
        layout.addLayout(btn_layout)

        self.orders_table = CustomTableView()
        self.orders_table.setSelectionBehavior(CustomTableView.SelectRows)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.show_order_context_menu)
        self.orders_table.doubleClicked.connect(self.view_order)
        layout.addWidget(self.orders_table)

        pagination = QHBoxLayout()
        self.orders_prev = QPushButton("السابق")
        self.orders_prev.clicked.connect(lambda: self.prev_page('orders'))
        self.orders_next = QPushButton("التالي")
        self.orders_next.clicked.connect(lambda: self.next_page('orders'))
        self.orders_page_label = QLabel()
        pagination.addWidget(self.orders_prev)
        pagination.addWidget(self.orders_page_label)
        pagination.addWidget(self.orders_next)
        pagination.addStretch()
        layout.addLayout(pagination)

    def refresh_bom(self, reset_page=True):
        if reset_page:
            self.bom_page = 0
        offset = self.bom_page * self.page_size
        boms, total = self.service.boms_pair(limit=self.page_size, offset=offset)
        data = []
        for b in boms:
            data.append({
                'id': b['id'],
                'product': b.get('product_name', ''),
                'quantity': str(b.get('quantity', 1)),
                'created_at': b.get('created_at', '')[:10] if b.get('created_at') else ''
            })
        headers = ['product', 'quantity', 'created_at']
        display_headers = ['المنتج', 'الكمية', 'تاريخ الإنشاء']
        self.bom_model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.bom_table.setModel(self.bom_model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
        self.bom_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bom_table.refresh_style()

        total_pages = (total + self.page_size - 1) // self.page_size
        self.bom_page_label.setText(f"الصفحة {self.bom_page + 1} من {total_pages}")
        self.bom_prev.setEnabled(self.bom_page > 0)
        self.bom_next.setEnabled(self.bom_page + 1 < total_pages)

    def refresh_orders(self, reset_page=True):
        if reset_page:
            self.orders_page = 0
        offset = self.orders_page * self.page_size
        orders, total = self.service.production_orders_pair(limit=self.page_size, offset=offset)
        status_map = {'planned': 'مخطط', 'in_progress': 'قيد التنفيذ', 'completed': 'مكتمل', 'cancelled': 'ملغي'}
        data = []
        for o in orders:
            data.append({
                'id': o['id'],
                'order_number': o.get('order_number', ''),
                'product': o.get('product_name', ''),
                'planned_qty': str(o.get('planned_qty', 0)),
                'produced_qty': str(o.get('produced_qty', 0)),
                'status': status_map.get(o.get('status', 'planned'), 'مخطط'),
                'raw_warehouse': o.get('raw_warehouse_name') or '-',
                'output_warehouse': o.get('output_warehouse_name') or '-',
                'start_date': o.get('start_date', '-')[:10] if o.get('start_date') else '-'
            })
        headers = ['order_number', 'product', 'planned_qty', 'produced_qty', 'status', 'raw_warehouse', 'output_warehouse', 'start_date']
        display_headers = ['رقم الأمر', 'المنتج', 'الكمية المخططة', 'الكمية المنتجة', 'الحالة', 'مستودع الخام', 'مستودع المنتج', 'تاريخ البدء']
        self.orders_model = GenericTableModel(data, display_headers, key_fields=['id'], data_keys=headers)
        self.orders_table.setModel(self.orders_model)
        # id محفوظ داخلياً عبر key_fields ولا يوجد كعمود عرض.
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.orders_table.refresh_style()

        total_pages = (total + self.page_size - 1) // self.page_size
        self.orders_page_label.setText(f"الصفحة {self.orders_page + 1} من {total_pages}")
        self.orders_prev.setEnabled(self.orders_page > 0)
        self.orders_next.setEnabled(self.orders_page + 1 < total_pages)

    def show_bom_context_menu(self, pos):
        index = self.bom_table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        bom_id = self.bom_model.get_id(row)
        if not bom_id:
            return
        menu = QMenu()
        edit_action = QAction("✏️ تعديل", self)
        edit_action.triggered.connect(lambda: self.edit_bom_by_id(bom_id))
        delete_action = QAction("🗑 حذف", self)
        delete_action.triggered.connect(lambda: self.delete_bom_by_id(bom_id))
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.exec(self.bom_table.viewport().mapToGlobal(pos))

    def show_order_context_menu(self, pos):
        index = self.orders_table.indexAt(pos)
        if not index.isValid():
            return
        row = index.row()
        order_id = self.orders_model.get_id(row)
        if not order_id:
            return
        order_status = self.orders_model.get_row(row).get('status', '')
        menu = QMenu()
        view_action = QAction("👁️ عرض التفاصيل", self)
        view_action.triggered.connect(lambda: self.view_order_by_id(order_id))
        menu.addAction(view_action)
        if order_status in ('مخطط', 'ملغي'):
            delete_action = QAction("🗑 حذف الأمر", self)
            delete_action.triggered.connect(lambda: self.delete_order_by_id(order_id))
            menu.addAction(delete_action)
        menu.exec(self.orders_table.viewport().mapToGlobal(pos))

    def add_bom(self):
        dialog = BOMDialog(self)
        if dialog.exec():
            self.refresh_bom()

    def edit_bom(self, index):
        row = index.row()
        bom_id = self.bom_model.get_id(row)
        self.edit_bom_by_id(bom_id)

    def edit_bom_by_id(self, bom_id):
        can_edit, msg = self.service.can_edit_bom(bom_id)
        if not can_edit:
            QMessageBox.warning(self, "تحذير", msg)
            return
        dialog = BOMDialog(self, bom_id=bom_id)
        if dialog.exec():
            self.refresh_bom()

    def delete_bom_by_id(self, bom_id):
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل تريد حذف قائمة المواد هذه؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, msg = self.service.delete_bom(bom_id)
            if success:
                show_toast("تم حذف قائمة المواد", "success", self)
                self.refresh_bom()
            else:
                QMessageBox.critical(self, "خطأ", msg)

    def add_order(self):
        dialog = ProductionOrderDialog(self)
        if dialog.exec():
            self.refresh_orders()

    def view_order(self, index):
        row = index.row()
        order_id = self.orders_model.get_id(row)
        self.view_order_by_id(order_id)

    def view_order_by_id(self, order_id):
        dialog = ProductionDetailsDialog(self, order_id)
        dialog.exec()
        self.refresh_orders()

    def delete_order_by_id(self, order_id):
        reply = QMessageBox.question(self, "تأكيد الحذف", "هل تريد حذف أمر الإنتاج هذا؟", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, msg = self.service.delete_production_order(order_id)
            if success:
                show_toast("تم حذف أمر الإنتاج", "success", self)
                self.refresh_orders()
            else:
                QMessageBox.critical(self, "خطأ", msg)

    def prev_page(self, target):
        if target == 'bom' and self.bom_page > 0:
            self.bom_page -= 1
            self.refresh_bom(reset_page=False)
        elif target == 'orders' and self.orders_page > 0:
            self.orders_page -= 1
            self.refresh_orders(reset_page=False)

    def next_page(self, target):
        if target == 'bom':
            self.bom_page += 1
            self.refresh_bom(reset_page=False)
        elif target == 'orders':
            self.orders_page += 1
            self.refresh_orders(reset_page=False)


