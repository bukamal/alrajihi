# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QFormLayout, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QDoubleSpinBox, QPushButton, QListWidget,
                             QListWidgetItem, QGroupBox, QMessageBox, QDialog)
from PyQt5.QtCore import Qt
from i18n import translate, qt_layout_direction
from views.centered_dialog import CenteredDialog
from core.services.catalog_service import catalog_service
from core.services.manufacturing_service import manufacturing_service
from currency import currency
from utils import show_toast
from core.offline_guard import is_offline_read_error, offline_read_message
from ui.form_validation import FormValidator, make_error_label
from views.widgets.modern_ui import apply_modern_dialog

class BOMDialog(CenteredDialog):
    def __init__(self, parent=None, bom_id=None):
        super().__init__(parent)
        self.bom_id = bom_id
        self.service = manufacturing_service
        self.is_edit = bom_id is not None
        self.setWindowTitle(translate("add_bom_title") if not self.is_edit else translate("edit_bom_title"))
        self.resize(600, 500)

        # تخطيط رئيسي
        main_layout = QVBoxLayout(self.content_widget)
        form = QFormLayout()
        main_layout.addLayout(form)
        
        self.product_combo = QComboBox()
        try:
            items = catalog_service.items()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_items_offline')), 'warning', self)
                items = []
            else:
                raise
        self.product_map = {}
        for it in items:
            if it.get('item_type') == 'منتج نهائي':
                price_display = currency.format_amount(currency.convert(it.get('selling_price', 0), 'USD', currency.get_display_currency()))
                self.product_combo.addItem(f"{it['name']} ({price_display})", it['id'])
                self.product_map[it['id']] = it
        form.addRow(translate("finished_product"), self.product_combo)
        self.product_error = make_error_label()
        form.addRow("", self.product_error)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.01, 999999)
        self.qty_spin.setValue(1)
        form.addRow(translate("quantity_per_unit"), self.qty_spin)
        self.qty_error = make_error_label()
        form.addRow("", self.qty_error)

        group = QGroupBox(translate("bom_components_group"))
        group_layout = QVBoxLayout(group)
        self.lines_list = QListWidget()
        group_layout.addWidget(self.lines_list)
        btn_add_line = QPushButton(translate("add_component"))
        btn_remove_line = QPushButton(translate("delete_selected_component"))
        group_layout.addWidget(btn_add_line)
        group_layout.addWidget(btn_remove_line)
        main_layout.addWidget(group)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton(translate("save_ctrl_s"))
        save_btn.setObjectName("primary")
        cancel_btn = QPushButton(translate("cancel_esc"))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        self.lines = []

        btn_add_line.clicked.connect(self.add_line)
        btn_remove_line.clicked.connect(self.remove_line)
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)

        if self.is_edit:
            self.load_bom_data()
        self.install_form_shortcuts(self.save)
        apply_modern_dialog(self, translate('bom_recipe'))
        self.watch_dirty_widgets([self.product_combo, self.qty_spin], reset=True)

    def add_line(self):
        # ... (نفس الكود السابق) ...
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDoubleSpinBox, QComboBox
        dialog = QDialog(self)
        dialog.setWindowTitle(translate("add_component_title"))
        dialog.setLayoutDirection(qt_layout_direction())
        dialog.resize(450, 320)
        sub_layout = QFormLayout(dialog)

        item_combo = QComboBox()
        try:
            items = catalog_service.items()
        except Exception as exc:
            if is_offline_read_error(exc):
                show_toast(offline_read_message(translate('manufacturing_items_offline')), 'warning', self)
                items = []
            else:
                raise
        for it in items:
            if it.get('item_type') in ('مخزون', 'منتج نهائي') and it['id'] != self.product_combo.currentData():
                item_combo.addItem(f"{it['name']} ({currency.format_amount(currency.convert(it.get('selling_price', 0), 'USD', currency.get_display_currency()))})", it['id'])
        sub_layout.addRow(translate("material_label"), item_combo)

        qty_edit = QDoubleSpinBox()
        qty_edit.setRange(0.01, 999999)
        qty_edit.setValue(1)
        sub_layout.addRow(translate("quantity") + ":", qty_edit)

        waste_spin = QDoubleSpinBox()
        waste_spin.setRange(0, 100)
        waste_spin.setSuffix("%")
        sub_layout.addRow(translate("waste_percent"), waste_spin)

        unit_combo = QComboBox()
        unit_combo.addItem(translate("base_unit"), None)
        sub_layout.addRow(translate("unit_label"), unit_combo)

        sub_btn_layout = QHBoxLayout()
        sub_save = QPushButton(translate("add"))
        sub_cancel = QPushButton(translate("cancel"))
        sub_btn_layout.addWidget(sub_save)
        sub_btn_layout.addWidget(sub_cancel)
        sub_layout.addRow(sub_btn_layout)

        def update_units():
            item_id = item_combo.currentData()
            unit_combo.clear()
            unit_combo.addItem(translate("base_unit"), None)
            if item_id:
                for u in catalog_service.item_units(item_id):
                    unit_combo.addItem(u['unit_name'], u['id'])
        item_combo.currentIndexChanged.connect(update_units)
        update_units()

        def on_add():
            item_id = item_combo.currentData()
            if not item_id:
                show_toast(translate("select_item"), "error", dialog)
                return
            qty = qty_edit.value()
            waste = waste_spin.value() / 100
            unit_id = unit_combo.currentData()
            item_name = item_combo.currentText().split(' (')[0]
            self.lines.append({
                'item_id': item_id,
                'item_name': item_name,
                'quantity': qty,
                'waste_percent': waste,
                'unit_id': unit_id
            })
            self.lines_list.addItem(translate('component_line', item=item_name, qty=qty, waste=(translate('waste_suffix', waste=waste_spin.value()) if waste > 0 else '')))
            self.mark_dirty()
            dialog.accept()

        sub_save.clicked.connect(on_add)
        sub_cancel.clicked.connect(dialog.reject)
        dialog.exec()

    def remove_line(self):
        row = self.lines_list.currentRow()
        if row >= 0:
            self.lines.pop(row)
            self.lines_list.takeItem(row)
            self.mark_dirty()

    def load_bom_data(self):
        bom = self.service.get_bom(self.bom_id)
        if not bom:
            show_toast(translate("bom_not_found"), "error", self)
            self.reject()
            return
        idx = self.product_combo.findData(bom['product_id'])
        if idx >= 0:
            self.product_combo.setCurrentIndex(idx)
        self.qty_spin.setValue(float(bom['quantity']))
        for line in bom.get('lines', []):
            self.lines.append({
                'item_id': line['item_id'],
                'item_name': line.get('item_name', ''),
                'quantity': float(line['quantity']),
                'waste_percent': float(line.get('waste_percent', 0)),
                'unit_id': line.get('unit_id')
            })
            self.lines_list.addItem(translate('component_line', item=line.get('item_name', ''), qty=float(line['quantity']), waste=(translate('waste_suffix', waste=float(line.get('waste_percent', 0))*100) if float(line.get('waste_percent', 0)) > 0 else '')))

    def save(self):
        validator = FormValidator()
        product_id = self.product_combo.currentData()
        validator.custom(bool(product_id), self.product_combo, self.product_error, translate("select_finished_product"))
        validator.positive(self.qty_spin, self.qty_error, translate("production_quantity"))
        if not validator.is_valid:
            validator.focus_first_invalid()
            return
        if not self.lines:
            show_toast(translate("component_required"), "error", self)
            return
        for l in self.lines:
            if l.get('item_id') == product_id:
                show_toast(translate("bom_self_component_error"), "error", self)
                return
            if float(l.get('quantity', 0)) <= 0:
                show_toast(translate("component_quantity_positive"), "error", self)
                return
        bom_data = {
            'id': self.bom_id or 0,
            'product_id': product_id,
            'quantity': self.qty_spin.value(),
            'lines': []
        }
        for l in self.lines:
            bom_data['lines'].append({
                'item_id': l['item_id'],
                'quantity': l['quantity'],
                'unit_id': l.get('unit_id'),
                'waste_percent': l['waste_percent']
            })
        try:
            self.service.save_bom(bom_data)
            show_toast(translate("bom_saved"), "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)



# Phase110 offline guard markers: مواد التصنيع
