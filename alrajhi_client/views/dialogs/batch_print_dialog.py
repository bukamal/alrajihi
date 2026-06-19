# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QTableWidgetItem,
                             QPushButton, QSpinBox, QHeaderView, QMessageBox, QComboBox, QLabel,
                             QListWidget, QListWidgetItem, QDialogButtonBox, QTableView, QCheckBox)
from PyQt5.QtCore import Qt
from views.widgets.modern_ui import apply_modern_dialog
from views.centered_dialog import CenteredDialog
from ui.smart_table_view import SmartTableView
from models.table_models import GenericTableModel
from core.services.catalog_service import catalog_service
from utils import show_toast
from printing.printing_service import printing_service
from printer_manager import PrinterManager
from core.services.settings_service import settings_service
from i18n import translate

class BatchPrintDialog(CenteredDialog):
    def __init__(self, parent=None, selected_items=None):
        super().__init__(parent)
        self.setWindowTitle(translate('phase233_ui_011'))
        self.resize(750, 550)
        self.selected_items = selected_items or []
        self.printer_manager = PrinterManager()
        self.printer_manager.load_default_printer()
        self.print_cfg = settings_service.get_printing_settings()
        self.items_data = []

        # التأكد من وجود layout في content_widget
        if self.content_widget.layout() is None:
            QVBoxLayout(self.content_widget)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel(translate('phase233_ui_022')))
        self.printer_combo = QComboBox()
        default_printer = self.print_cfg.get('barcode_default_printer', '')
        self.printer_combo.addItem(translate('phase235_system_print_dialog'), '')
        for p in self.printer_manager.printers:
            # Phase 235: no visible PDF/PNG pseudo-printer choices from barcode print buttons.
            if getattr(p.type, 'value', '') in {'pdf', 'image'}:
                continue
            self.printer_combo.addItem(p.name, p.connection_string or p.id)
        idx = self.printer_combo.findData(default_printer)
        if idx >= 0:
            self.printer_combo.setCurrentIndex(idx)
        toolbar.addWidget(self.printer_combo)

        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 10)
        self.copies_spin.setValue(int(self.print_cfg.get('barcode_copies', 1) or 1))
        toolbar.addWidget(QLabel(translate('phase233_ui_023')))
        toolbar.addWidget(self.copies_spin)

        self.label_size_combo = QComboBox()
        self.label_size_combo.addItems(["40x30", "50x30", "60x40", "80mm"])
        self.label_size_combo.setCurrentText(self.print_cfg.get('barcode_label_size', '50x30'))
        toolbar.addWidget(QLabel(translate('phase233_ui_024')))
        toolbar.addWidget(self.label_size_combo)

        self.symbology_combo = QComboBox()
        self.symbology_combo.addItems(["AUTO", "EAN13", "CODE128"])
        self.symbology_combo.setCurrentText(self.print_cfg.get('barcode_symbology', 'AUTO'))
        toolbar.addWidget(QLabel(translate('phase233_ui_025')))
        toolbar.addWidget(self.symbology_combo)
        self.content_widget.layout().addLayout(toolbar)

        options_row = QHBoxLayout()
        self.show_company_check = QCheckBox(translate('phase233_ui_012'))
        self.show_company_check.setChecked(bool(self.print_cfg.get('barcode_show_company', True)))
        self.show_logo_check = QCheckBox(translate('phase233_ui_013'))
        self.show_logo_check.setChecked(bool(self.print_cfg.get('barcode_show_logo', self.print_cfg.get('show_logo', True))))
        self.show_qr_check = QCheckBox("QR")
        self.show_qr_check.setChecked(bool(self.print_cfg.get('barcode_show_qr', True)))
        self.show_name_check = QCheckBox(translate('phase233_ui_014'))
        self.show_name_check.setChecked(bool(self.print_cfg.get('barcode_show_name', True)))
        self.show_price_check = QCheckBox(translate('phase233_ui_015'))
        self.show_price_check.setChecked(bool(self.print_cfg.get('barcode_show_price', True)))
        self.show_text_check = QCheckBox(translate('phase233_ui_016'))
        self.show_text_check.setChecked(bool(self.print_cfg.get('barcode_show_text', True)))
        for chk in (self.show_company_check, self.show_logo_check, self.show_qr_check, self.show_name_check, self.show_price_check, self.show_text_check):
            options_row.addWidget(chk)
        options_row.addStretch()
        self.content_widget.layout().addLayout(options_row)

        self.table = SmartTableView(identity='batch_print.items')
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
        btn_row.addWidget(print_btn)
        btn_row.addWidget(cancel_btn)
        self.content_widget.layout().addLayout(btn_row)

        self.load_items()

    def update_table_model(self):
        data = []
        for idx, it in enumerate(self.items_data):
            data.append([idx, it['name'], it['barcode'], it['price'], it['copies']])
        headers = ['#', translate('item'), translate('barcode'), translate('phase233_ui_015'), translate('phase235_copies')]
        self.model = GenericTableModel(data, headers, data_keys=['id', 'name', 'barcode', 'price', 'copies'])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def load_items(self):
        if self.selected_items:
            for item in self.selected_items:
                self.add_item_to_data(item)
        else:
            self.select_items()

    def add_item_to_data(self, item, copies=1):
        # item يمكن أن يكون كائنًا (من selected_items) أو قاموسًا (من select_items)
        # نتعامل مع الحالتين:
        if hasattr(item, 'id'):
            item_id = item.id
            item_name = item.name
            item_barcode = getattr(item, 'barcode', '')
            selling_price = getattr(item, 'selling_price', 0)
        else:
            item_id = item['id']
            item_name = item['name']
            item_barcode = item.get('barcode', '')
            selling_price = item.get('selling_price', 0)

        # التحقق من عدم التكرار
        for it in self.items_data:
            if it['id'] == item_id:
                return
        from currency import currency
        price_display = currency.format_amount(currency.convert(selling_price, currency.storage_currency(), currency.get_display_currency()))
        self.items_data.append({
            'id': item_id,
            'name': item_name,
            'barcode': item_barcode,
            'price': price_display,
            'copies': copies
        })
        self.update_table_model()

    def select_items(self):
        dialog = CenteredDialog(self)
        dialog.setWindowTitle(translate('phase233_ui_021'))
        dialog.resize(550, 450)
        layout = QVBoxLayout(dialog.content_widget)
        items = catalog_service.items(limit=1000)  # قائمة موحدة من المواد
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.MultiSelection)
        for it in items:
            if it.get('barcode'):
                item_text = f"{it['name']} - {it.get('barcode')}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, it['id'])
                list_widget.addItem(list_item)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        apply_modern_dialog(self, translate('batch_print'))
        if dialog.exec():
            for list_item in list_widget.selectedItems():
                item_id = list_item.data(Qt.UserRole)
                # البحث عن المادة الكاملة في القائمة الأصلية
                it = next((x for x in items if x['id'] == item_id), None)
                if it:
                    self.add_item_to_data(it)

    def remove_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        rows = sorted([idx.row() for idx in selected], reverse=True)
        for row in rows:
            if row < len(self.items_data):
                self.items_data.pop(row)
        self.update_table_model()


    def _print_options(self):
        return {
            'label_size': self.label_size_combo.currentText(),
            'symbology': self.symbology_combo.currentText(),
            'show_company': self.show_company_check.isChecked(),
            'show_logo': self.show_logo_check.isChecked(),
            'show_qr': self.show_qr_check.isChecked(),
            'show_name': self.show_name_check.isChecked(),
            'show_price': self.show_price_check.isChecked(),
            'show_barcode_text': self.show_text_check.isChecked(),
            'columns': int(self.print_cfg.get('barcode_columns', 1 if self.label_size_combo.currentText() == '80mm' else 2) or 2),
        }

    def do_print(self):
        if not self.items_data:
            show_toast(translate('phase235_no_items_to_print'), 'error', self)
            return
        printer_name = self.printer_combo.currentData() or ''
        items_for_print = []
        for it in self.items_data:
            items_for_print.append({
                'barcode': it['barcode'],
                'name': it['name'],
                'price': it['price'],
                'copies': it.get('copies', self.copies_spin.value())
            })
        # Phase 235: single unified barcode print path; options come from project settings and dialog overrides.
        if printing_service.barcode_labels_print(items_for_print, self, self._print_options(), printer_name):
            show_toast(translate('phase235_barcode_print_success'), "success", self)
            self.accept()
        else:
            show_toast(translate('phase235_barcode_print_failed'), "error", self)


