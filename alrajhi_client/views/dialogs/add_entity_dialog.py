# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from i18n import translate as tr, qt_layout_direction
from views.centered_dialog import CenteredDialog
from core.services.entity_service import entity_service
from utils import show_toast
from ui.form_validation import FormValidator, make_error_label
from views.widgets.modern_ui import apply_modern_dialog

class AddEntityDialog(CenteredDialog):
    def __init__(self, parent, inv_type):
        super().__init__(parent)
        self.setLayoutDirection(qt_layout_direction())
        self.inv_type = inv_type
        self.entity_name = None
        self.entity_key = 'customer' if inv_type == 'sale' else 'supplier'
        self.entity_label = tr(self.entity_key)
        self.setWindowTitle(tr('add_customer_title') if inv_type == 'sale' else tr('add_supplier_title'))
        self.resize(400, 300)
        
        # إضافة تخطيط إلى content_widget
        layout = QVBoxLayout(self.content_widget)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr('name'))
        form.addRow(tr('name_label'), self.name_edit)
        self.name_error = make_error_label()
        form.addRow('', self.name_error)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText(tr('phone_optional'))
        form.addRow(tr('phone_label'), self.phone_edit)
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText(tr('address_optional'))
        form.addRow(tr('address_label'), self.address_edit)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr('save'))
        save_btn.setObjectName("primary")
        cancel_btn = QPushButton(tr('cancel'))
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        self.install_form_shortcuts(self.save)
        apply_modern_dialog(self, tr('add_entity_dialog_title'))
        self.watch_dirty_widgets([self.name_edit, self.phone_edit, self.address_edit], reset=True)

    def save(self):
        validator = FormValidator()
        if not validator.required(self.name_edit, self.name_error, tr('name')):
            validator.focus_first_invalid()
            return
        name = self.name_edit.text().strip()
        phone = self.phone_edit.text().strip()
        address = self.address_edit.text().strip()
        try:
            if self.inv_type == 'sale':
                entity_service.add_customer(name, phone, address)
            else:
                entity_service.add_supplier(name, phone, address)
            self.entity_name = name
            show_toast(tr('add_done'), 'success', self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)


