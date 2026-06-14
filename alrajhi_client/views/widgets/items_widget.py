# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView
from PyQt5.QtCore import Qt
from i18n import translate, qt_layout_direction
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
    entity_name = translate("item")
    search_placeholder = translate("items_search_placeholder")
    headers = ['name', 'quantity', 'unit', 'sold_quantity', 'available_quantity', 'available_total', 'unit_cost']

    def _display_headers(self):
        return [
            translate('item_name_header'),
            translate('quantity'),
            translate('default_unit_header'),
            translate('sold_quantity'),
            translate('available_quantity'),
            translate('available_total'),
            translate('unit_cost'),
        ]
    has_delete = True
    has_add = True
    has_export = True
    has_print = True
    has_pagination = True
    page_size = 50
    extra_buttons = []

    def _extra_buttons(self):
        return [
            (translate("print_barcode"), "print_barcode", "print_barcode_btn"),
            (translate("batch_print"), "batch_print", "batch_print_btn"),
        ]

    def __init__(self, parent=None):
        self.entity_name = translate('item')
        self.search_placeholder = translate('items_search_placeholder')
        self.display_headers = self._display_headers()
        self.extra_buttons = self._extra_buttons()
        self.category_filter = QComboBox()
        self.type_filter = QComboBox()
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
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
        self.category_filter.addItem(translate("all_categories"), None)
        for c in categories:
            self.category_filter.addItem(c['name'], c['id'])

    def load_filters(self):
        """إضافة فلاتر المواد فوق الجدول مع استخدام بحث الشريط الموحد."""
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.addWidget(QLabel(translate("category_label")))
        filter_layout.addWidget(self.category_filter)
        filter_layout.addWidget(QLabel(translate("item_type_label")))
        if self.type_filter.count() == 0:
            self.type_filter.addItem(translate("all_types"), None)
            self.type_filter.addItem(translate("stock_item_type"), "مخزون")
            self.type_filter.addItem(translate("finished_product_type"), "منتج نهائي")
            self.type_filter.addItem(translate("service_item_type"), "خدمة")
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
            return row_data.get('name', translate('item'))
        return translate("item")


    def _stock_status(self, available_qty, reorder_level):
        if available_qty <= 0:
            return translate('stock_empty'), 'out'
        if reorder_level > 0 and available_qty <= reorder_level:
            return translate('stock_low'), 'low'
        return translate('stock_ok'), 'ok'

    def prepare_table_data(self, items):
        data = []
        display_curr = currency.get_display_currency()
        item_ids = [it.get('id') for it in items if it.get('id') is not None]
        sold_map = product_service.sold_quantities(item_ids)
        for it in items:
            item_id = it.get('id')
            opening_qty = Decimal(str(it.get('opening_quantity', it.get('quantity', 0)) or 0))
            available_qty = Decimal(str(it.get('available', it.get('quantity', 0)) or 0))
            sold_qty = Decimal(str(sold_map.get(int(item_id), 0))) if item_id is not None else Decimal('0')
            unit_cost_usd = Decimal(str(it.get('average_cost', it.get('purchase_price', 0)) or 0))
            total_value_usd = available_qty * unit_cost_usd
            unit_cost_display = currency.convert(unit_cost_usd, 'USD', display_curr)
            total_value_display = currency.convert(total_value_usd, 'USD', display_curr)
            reorder_level = Decimal(str(it.get('reorder_level', 0) or 0))
            _, severity = self._stock_status(available_qty, reorder_level)
            data.append({
                'id': it['id'],
                'name': it.get('name', ''),
                'quantity': f"{opening_qty:.2f}",
                'unit': it.get('unit') or translate('unit_piece'),
                'sold_quantity': f"{sold_qty:.2f}",
                'available_quantity': f"{available_qty:.2f}",
                'available_total': currency.format_amount(total_value_display),
                'unit_cost': currency.format_amount(unit_cost_display),
                '_row_status': severity
            })
        return data

    def get_data_keys(self):
        # يجب أن يطابق ترتيب المفاتيح ترتيب عناوين الأعمدة المعروضة.
        # المعرّف id يبقى داخل بيانات الصف ويُستخدم عبر key_fields، لكنه لا يُعرض كعمود.
        return ['name', 'quantity', 'unit', 'sold_quantity', 'available_quantity', 'available_total', 'unit_cost']

    def print_barcode(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            show_toast(translate("select_item_first"), "warning", self)
            return
        row = selected[0].row()
        item_id = self.model.get_id(row)
        if not item_id:
            return
        item = product_service.item_by_id(item_id)
        if not item or not item.get('barcode'):
            show_toast(translate("item_has_no_barcode"), "error", self)
            return
        # Single barcode printing now uses the same unified dialog/service path
        # as batch barcode printing, with defaults loaded from Printing Settings.
        dialog = BatchPrintDialog(self, selected_items=[item])
        dialog.exec()

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
        self.display_headers = self._display_headers()
        self.model = GenericTableModel(data, self.display_headers, key_fields=['id'], data_keys=self.get_data_keys())
        self.table.setModel(self.model)
        # لا نخفي العمود الأول هنا؛ id ليس ضمن أعمدة العرض أصلاً.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        if self.has_pagination:
            total_pages = max(1, (self.total_count + self.page_size - 1) // self.page_size)
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)
            self.page_label.setText(translate("page_of", page=self.current_page + 1, pages=total_pages))
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page + 1 < total_pages)
        visible_count = len(data)
        start_row = 0 if self.total_count == 0 else self.current_page * self.page_size + 1
        end_row = min(self.total_count, self.current_page * self.page_size + visible_count)
        counter_text = translate("showing_records", start=start_row, end=end_row, total=self.total_count)
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


