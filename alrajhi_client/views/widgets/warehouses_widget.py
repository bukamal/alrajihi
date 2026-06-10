# -*- coding: utf-8 -*-
from decimal import Decimal

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTableView,
    QTabWidget, QDialog, QFormLayout, QCheckBox, QTextEdit, QMessageBox, QComboBox,
    QHeaderView
)
from PyQt5.QtCore import Qt

from core.services.warehouse_service import warehouse_service
from currency import currency
from models.table_models import GenericTableModel
from views.custom_table_view import CustomTableView
from utils import show_toast


class WarehousesWidget(QWidget):
    """Warehouse-1 UI: warehouse master data and read-only item balances."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setObjectName('WarehousesWidget')
        warehouse_service.bootstrap()
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QLabel('إدارة المستودعات')
        header.setObjectName('pageTitle')
        layout.addWidget(header)

        hint = QLabel('هذه المرحلة تؤسس المستودعات وتعرض الأرصدة حسب المستودع دون تغيير سلوك الفواتير أو التصنيع بعد.')
        hint.setObjectName('mutedLabel')
        layout.addWidget(hint)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._setup_warehouses_tab()
        self._setup_balances_tab()
        self._setup_movements_tab()

    def _setup_warehouses_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.wh_search = QLineEdit()
        self.wh_search.setPlaceholderText('بحث في المستودعات...')
        self.wh_search.textChanged.connect(self.refresh_warehouses)
        self.show_archived = QCheckBox('إظهار المؤرشف')
        self.show_archived.stateChanged.connect(self.refresh_warehouses)
        add_btn = QPushButton('➕ مستودع جديد')
        add_btn.setObjectName('primary')
        add_btn.clicked.connect(self.add_warehouse)
        edit_btn = QPushButton('✏️ تعديل')
        edit_btn.clicked.connect(self.edit_warehouse)
        archive_btn = QPushButton('🗄️ أرشفة')
        archive_btn.clicked.connect(self.archive_warehouse)
        tools.addWidget(QLabel('المستودعات'))
        tools.addWidget(self.wh_search, 1)
        tools.addWidget(self.show_archived)
        tools.addWidget(add_btn)
        tools.addWidget(edit_btn)
        tools.addWidget(archive_btn)
        layout.addLayout(tools)
        self.wh_table = CustomTableView()
        self.wh_table.setSelectionBehavior(QTableView.SelectRows)
        self.wh_table.doubleClicked.connect(lambda _idx: self.edit_warehouse())
        layout.addWidget(self.wh_table)
        self.tabs.addTab(page, 'المستودعات')

    def _setup_balances_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.balance_search = QLineEdit()
        self.balance_search.setPlaceholderText('بحث باسم المادة أو الباركود أو المستودع...')
        self.balance_search.textChanged.connect(self.refresh_balances)
        self.warehouse_filter = QComboBox()
        self.warehouse_filter.currentIndexChanged.connect(self.refresh_balances)
        tools.addWidget(QLabel('أرصدة المواد'))
        tools.addWidget(self.balance_search, 1)
        tools.addWidget(QLabel('المستودع:'))
        tools.addWidget(self.warehouse_filter)
        layout.addLayout(tools)
        self.balance_table = CustomTableView()
        self.balance_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.balance_table)
        self.balance_status = QLabel()
        self.balance_status.setObjectName('mutedLabel')
        layout.addWidget(self.balance_status)
        self.tabs.addTab(page, 'الأرصدة')

    def _setup_movements_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        tools = QHBoxLayout()
        self.mov_warehouse_filter = QComboBox()
        self.mov_warehouse_filter.currentIndexChanged.connect(self.refresh_movements)
        refresh_btn = QPushButton('تحديث')
        refresh_btn.clicked.connect(self.refresh_movements)
        tools.addWidget(QLabel('آخر حركات المستودعات'))
        tools.addStretch()
        tools.addWidget(QLabel('المستودع:'))
        tools.addWidget(self.mov_warehouse_filter)
        tools.addWidget(refresh_btn)
        layout.addLayout(tools)
        self.mov_table = CustomTableView()
        self.mov_table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.mov_table)
        self.tabs.addTab(page, 'الحركات')

    def refresh(self):
        warehouse_service.bootstrap()
        self._reload_warehouse_filters()
        self.refresh_warehouses()
        self.refresh_balances()
        self.refresh_movements()

    def _reload_warehouse_filters(self):
        warehouses = warehouse_service.warehouses(include_archived=False)
        for combo in (self.warehouse_filter, self.mov_warehouse_filter):
            current = combo.currentData() if combo.count() else None
            combo.blockSignals(True)
            combo.clear()
            combo.addItem('كل المستودعات', None)
            for wh in warehouses:
                combo.addItem(wh.get('name', ''), wh.get('id'))
            if current is not None:
                for i in range(combo.count()):
                    if combo.itemData(i) == current:
                        combo.setCurrentIndex(i)
                        break
            combo.blockSignals(False)

    def refresh_warehouses(self):
        rows = []
        text = (self.wh_search.text() if hasattr(self, 'wh_search') else '').strip().lower()
        include_archived = self.show_archived.isChecked() if hasattr(self, 'show_archived') else False
        for wh in warehouse_service.warehouses(include_archived=include_archived):
            if text and text not in str(wh.get('name', '')).lower() and text not in str(wh.get('code', '')).lower():
                continue
            archived = bool(wh.get('deleted_at')) or int(wh.get('is_active') or 0) == 0
            rows.append({
                'id': wh.get('id'),
                'name': wh.get('name', ''),
                'code': wh.get('code') or '—',
                'location': wh.get('location') or '—',
                'item_count': int(wh.get('item_count') or 0),
                'total_qty': f"{Decimal(str(wh.get('total_qty') or 0)):.2f}",
                'is_default': 'نعم' if int(wh.get('is_default') or 0) == 1 else 'لا',
                'status': 'مؤرشف' if archived else 'نشط',
                'notes': wh.get('notes') or '',
            })
        headers = ['المستودع', 'الكود', 'الموقع', 'عدد المواد', 'إجمالي الكميات', 'رئيسي', 'الحالة', 'ملاحظات']
        keys = ['name', 'code', 'location', 'item_count', 'total_qty', 'is_default', 'status', 'notes']
        self.wh_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.wh_table.setModel(self.wh_model)
        self.wh_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.wh_table.horizontalHeader().setStretchLastSection(True)

    def refresh_balances(self):
        search = self.balance_search.text().strip() if hasattr(self, 'balance_search') else None
        wh_id = self.warehouse_filter.currentData() if hasattr(self, 'warehouse_filter') else None
        balances = warehouse_service.balances(search=search, warehouse_id=wh_id)
        rows = []
        total_value = Decimal('0')
        for b in balances:
            qty = Decimal(str(b.get('quantity') or 0))
            avg = Decimal(str(b.get('average_cost') or 0))
            value = qty * avg
            total_value += value
            rows.append({
                'id': b.get('id'),
                'warehouse_name': b.get('warehouse_name', ''),
                'item_name': b.get('item_name', ''),
                'barcode': b.get('barcode') or '—',
                'quantity': f'{qty:.2f}',
                'unit': b.get('unit') or '',
                'average_cost': currency.format_amount(avg),
                'stock_value': currency.format_amount(value),
                'updated_at': b.get('updated_at') or '',
            })
        headers = ['المستودع', 'المادة', 'الباركود', 'الكمية', 'الوحدة', 'متوسط التكلفة', 'قيمة المخزون', 'آخر تحديث']
        keys = ['warehouse_name', 'item_name', 'barcode', 'quantity', 'unit', 'average_cost', 'stock_value', 'updated_at']
        self.balance_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.balance_table.setModel(self.balance_model)
        self.balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.balance_table.horizontalHeader().setStretchLastSection(True)
        self.balance_status.setText(f'عدد السجلات: {len(rows)} | إجمالي القيمة: {currency.format_amount(total_value)}')

    def refresh_movements(self):
        wh_id = self.mov_warehouse_filter.currentData() if hasattr(self, 'mov_warehouse_filter') else None
        rows = []
        for m in warehouse_service.movements(warehouse_id=wh_id, limit=200):
            rows.append({
                'id': m.get('id'),
                'date': m.get('movement_date') or m.get('created_at') or '',
                'warehouse_name': m.get('warehouse_name', ''),
                'item_name': m.get('item_name', ''),
                'type': self._movement_label(m.get('movement_type')),
                'quantity': m.get('quantity') or '0',
                'unit_cost': currency.format_amount(m.get('unit_cost') or 0),
                'reference': m.get('reference_type') or '—',
                'notes': m.get('notes') or '',
            })
        headers = ['التاريخ', 'المستودع', 'المادة', 'النوع', 'الكمية', 'التكلفة', 'المرجع', 'ملاحظات']
        keys = ['date', 'warehouse_name', 'item_name', 'type', 'quantity', 'unit_cost', 'reference', 'notes']
        self.mov_model = GenericTableModel(rows, headers, key_fields=['id'], data_keys=keys)
        self.mov_table.setModel(self.mov_model)
        self.mov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.mov_table.horizontalHeader().setStretchLastSection(True)

    def _movement_label(self, mtype):
        return {
            'migration_opening': 'ترحيل افتتاحي',
            'opening': 'افتتاحي',
            'purchase': 'شراء',
            'sale': 'بيع',
            'adjustment': 'تسوية',
            'production_out': 'إنتاج',
            'production_consume': 'استهلاك إنتاج',
        }.get(mtype or '', mtype or '')

    def current_warehouse_id(self):
        idx = self.wh_table.currentIndex()
        if not idx.isValid() or not hasattr(self, 'wh_model'):
            return None
        return self.wh_model.get_id(idx.row())

    def _warehouse_dialog(self, title, warehouse=None):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLayoutDirection(Qt.RightToLeft)
        dialog.resize(460, 320)
        layout = QFormLayout(dialog)
        name = QLineEdit()
        code = QLineEdit()
        location = QLineEdit()
        notes = QTextEdit()
        notes.setMaximumHeight(90)
        active = QCheckBox('نشط')
        active.setChecked(True)
        if warehouse:
            name.setText(warehouse.get('name', ''))
            code.setText(warehouse.get('code') or '')
            location.setText(warehouse.get('location') or '')
            notes.setPlainText(warehouse.get('notes') or '')
            active.setChecked(int(warehouse.get('is_active') or 0) == 1 and not warehouse.get('deleted_at'))
        layout.addRow('الاسم:', name)
        layout.addRow('الكود:', code)
        layout.addRow('الموقع:', location)
        layout.addRow('ملاحظات:', notes)
        layout.addRow('', active)
        btns = QHBoxLayout()
        save = QPushButton('حفظ')
        save.setObjectName('primary')
        cancel = QPushButton('إلغاء')
        btns.addWidget(save)
        btns.addWidget(cancel)
        layout.addRow(btns)
        payload = {}
        def do_save():
            if not name.text().strip():
                show_toast('اسم المستودع مطلوب', 'error', dialog)
                name.setFocus()
                return
            payload.update({
                'name': name.text().strip(),
                'code': code.text().strip(),
                'location': location.text().strip(),
                'notes': notes.toPlainText().strip(),
                'is_active': 1 if active.isChecked() else 0,
            })
            dialog.accept()
        save.clicked.connect(do_save)
        cancel.clicked.connect(dialog.reject)
        if dialog.exec() == QDialog.Accepted:
            return payload
        return None

    def add_warehouse(self):
        payload = self._warehouse_dialog('إضافة مستودع')
        if not payload:
            return
        try:
            warehouse_service.add_warehouse(payload)
            show_toast('تم إنشاء المستودع', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def edit_warehouse(self):
        wh_id = self.current_warehouse_id()
        if not wh_id:
            show_toast('اختر مستودعاً أولاً', 'warning', self)
            return
        wh = warehouse_service.warehouse_by_id(wh_id)
        if not wh:
            show_toast('المستودع غير موجود', 'error', self)
            return
        payload = self._warehouse_dialog('تعديل مستودع', wh)
        if not payload:
            return
        try:
            warehouse_service.update_warehouse(wh_id, payload)
            show_toast('تم تحديث المستودع', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)

    def archive_warehouse(self):
        wh_id = self.current_warehouse_id()
        if not wh_id:
            show_toast('اختر مستودعاً أولاً', 'warning', self)
            return
        reply = QMessageBox.question(self, 'تأكيد الأرشفة', 'هل تريد أرشفة هذا المستودع؟', QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        try:
            warehouse_service.archive_warehouse(wh_id)
            show_toast('تمت أرشفة المستودع', 'success', self)
            self.refresh()
        except Exception as e:
            show_toast(str(e), 'error', self)
