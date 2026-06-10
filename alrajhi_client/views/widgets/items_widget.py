# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView
from PyQt5.QtCore import Qt
from decimal import Decimal
from core.services.product_service import product_service
from currency import currency
from views.custom_table_view import CustomTableView
from models.table_models import GenericTableModel
from views.dialogs.item_dialog import ItemDialog
from views.dialogs.batch_print_dialog import BatchPrintDialog
from utils import show_toast
from views.widgets.base_widget import BaseWidget

class ItemsWidget(BaseWidget):
    entity_name = "المادة"
    search_placeholder = "بحث عن مادة (اسم أو باركود)..."
    headers = ['name', 'unit', 'quantity', 'reorder_level', 'stock_status', 'avg_cost', 'total_value', 'barcode']
    display_headers = ['المادة', 'الوحدة', 'الكمية', 'حد إعادة الطلب', 'الحالة', 'متوسط التكلفة', 'قيمة المخزون', 'الباركود']
    has_delete = True
    has_add = True
    has_export = True
    has_print = True
    has_pagination = True
    page_size = 50
    extra_buttons = [
        ("🖨️ طباعة باركود", "print_barcode", "print_barcode_btn"),
        ("📑 طباعة متعددة", "batch_print", "batch_print_btn"),
    ]

    def __init__(self, parent=None):
        self.category_filter = QComboBox()
        self.type_filter = QComboBox()
        super().__init__(parent)
        self.load_categories()
        self.load_filters()
        # Extra buttons are already created by BaseWidget from extra_buttons.
        self.category_filter.currentIndexChanged.connect(self.refresh)
        self.type_filter.currentIndexChanged.connect(self.refresh)

    def _setup_extra_buttons(self):
        for btn_text, callback_name, btn_name in self.extra_buttons:
            btn = QPushButton(btn_text)
            callback = getattr(self, callback_name, None)
            if callback:
                btn.clicked.connect(callback)
            btn.setEnabled(False)
            setattr(self, btn_name, btn)
            self.btn_layout.addWidget(btn)

    def load_categories(self):
        categories = product_service.categories()
        self.category_filter.addItem("جميع التصنيفات", None)
        for c in categories:
            self.category_filter.addItem(c['name'], c['id'])

    def load_filters(self):
        """إضافة فلاتر المواد فوق الجدول مع استخدام بحث الشريط الموحد."""
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(QLabel("التصنيف:"))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel("النوع:"))
        if self.type_filter.count() == 0:
            self.type_filter.addItem("جميع الأنواع", None)
            self.type_filter.addItem("مخزون", "مخزون")
            self.type_filter.addItem("منتج نهائي", "منتج نهائي")
            self.type_filter.addItem("خدمة", "خدمة")
        filter_layout.addWidget(self.type_filter)
        filter_layout.addStretch()
        self.layout().insertLayout(1, filter_layout)

    def fetch_data(self, search=None, limit=None, offset=None):
        return product_service.items_pair(search=search, limit=limit, offset=offset)

    def get_total_count(self, search=None):
        _, total = product_service.items_pair(search=search, limit=1, offset=0)
        return total

    def delete_item(self, item_id):
        product_service.delete_item(item_id)

    def open_dialog(self, is_edit=False, item_id=None):
        dialog = ItemDialog(self, item_id=item_id if is_edit else None)
        if dialog.exec():
            self.refresh()

    def get_item_name_from_row(self, row):
        """إرجاع اسم المادة من الصف المحدد (لرسالة تأكيد الحذف)"""
        if self.model and row < self.model.rowCount():
            row_data = self.model.get_row(row)
            return row_data.get('name', 'المادة')
        return "المادة"


    def _stock_status(self, available_qty, reorder_level):
        if available_qty <= 0:
            return '🔴 نافد', 'out'
        if reorder_level > 0 and available_qty <= reorder_level:
            return '🟠 منخفض', 'low'
        return '🟢 جيد', 'ok'

    def prepare_table_data(self, items):
        data = []
        display_curr = currency.get_display_currency()
        for it in items:
            avg_cost_display = currency.convert(Decimal(str(it.get('average_cost', 0))), 'USD', display_curr)
            available_qty = Decimal(str(it.get('available', it.get('quantity', 0))))
            total_value_usd = available_qty * Decimal(str(it.get('average_cost', 0)))
            total_value_display = currency.convert(total_value_usd, 'USD', display_curr)
            reorder_level = Decimal(str(it.get('reorder_level', 0) or 0))
            status_label, severity = self._stock_status(available_qty, reorder_level)
            data.append({
                'id': it['id'],
                'name': it['name'],
                'unit': it.get('unit', ''),
                'quantity': f"{available_qty:.2f}",
                'reorder_level': f"{reorder_level:.2f}",
                'stock_status': status_label,
                'avg_cost': currency.format_amount(avg_cost_display),
                'total_value': currency.format_amount(total_value_display),
                'barcode': it.get('barcode', ''),
                '_row_status': severity
            })
        return data

    def get_data_keys(self):
        # يجب أن يطابق ترتيب المفاتيح ترتيب عناوين الأعمدة المعروضة.
        # المعرّف id يبقى داخل بيانات الصف ويُستخدم عبر key_fields، لكنه لا يُعرض كعمود.
        return ['name', 'unit', 'quantity', 'reorder_level', 'stock_status', 'avg_cost', 'total_value', 'barcode']

    def print_barcode(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            show_toast("اختر مادة أولاً", "warning", self)
            return
        row = selected[0].row()
        item_id = self.model.get_id(row)
        if not item_id:
            return
        item = product_service.item_by_id(item_id)
        if not item or not item.get('barcode'):
            show_toast("هذه المادة ليس لها باركود", "error", self)
            return
        from printing.thermal_printer import PDFPrinter
        pdf_printer = PDFPrinter(self)
        price_display = currency.format_amount(currency.convert(item.get('selling_price', 0), 'USD', currency.get_display_currency()))
        pdf_printer.print_label(item.get('barcode'), item['name'], price_display, 1, {'label_size': '50x30', 'columns': 1})

    def batch_print(self):
        dialog = BatchPrintDialog(self)
        dialog.exec()

    def _update_action_buttons_state(self):
        super()._update_action_buttons_state()
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        if hasattr(self, 'print_barcode_btn'):
            self.print_barcode_btn.setEnabled(has_selection)
        if hasattr(self, 'batch_print_btn'):
            self.batch_print_btn.setEnabled(True)

    def refresh(self):
        search = self.search_edit.text().strip().lower() or None
        category_id = self.category_filter.currentData()
        item_type = self.type_filter.currentData()
        offset = self.current_page * self.page_size
        items, self.total_count = self.fetch_data(search=search, limit=self.page_size, offset=offset)
        filtered = []
        for it in items:
            if category_id and it.get('category_id') != category_id:
                continue
            if item_type and it.get('item_type') != item_type:
                continue
            filtered.append(it)
        data = self.prepare_table_data(filtered)
        self.model = GenericTableModel(data, self.display_headers, key_fields=['id'], data_keys=self.get_data_keys())
        self.table.setModel(self.model)
        # لا نخفي العمود الأول هنا؛ id ليس ضمن أعمدة العرض أصلاً.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.has_pagination:
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)
            self.page_label.setText(f"الصفحة {self.current_page + 1} من {total_pages}")
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page + 1 < total_pages)
        visible_count = len(data)
        start_row = 0 if self.total_count == 0 else self.current_page * self.page_size + 1
        end_row = min(self.total_count, self.current_page * self.page_size + visible_count)
        counter_text = f"عرض {start_row}-{end_row} من أصل {self.total_count} سجل"
        self.status_label.setText(counter_text)
        if hasattr(self, 'toolbar'):
            self.toolbar.set_counter(counter_text)
        self._update_action_buttons_state()
        # ربط إشارة التحديد بعد تعيين النموذج
        sm = self.table.selectionModel()
        if sm is not None:
            try:
                sm.selectionChanged.disconnect(self._on_selection_changed)
            except:
                pass
            sm.selectionChanged.connect(self._on_selection_changed)


