# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from views.centered_dialog import CenteredDialog
from core.services.entity_service import entity_service
from utils import show_toast
from ui.form_validation import FormValidator, make_error_label
from views.widgets.modern_ui import apply_modern_dialog

class AddEntityDialog(CenteredDialog):
    def __init__(self, parent, inv_type):
        super().__init__(parent)
        self.inv_type = inv_type
        self.entity_name = None
        self.setWindowTitle(f"إضافة {'عميل' if inv_type == 'sale' else 'مورد'} جديد")
        self.resize(400, 300)
        
        # إضافة تخطيط إلى content_widget
        layout = QVBoxLayout(self.content_widget)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("الاسم")
        form.addRow("الاسم:", self.name_edit)
        self.name_error = make_error_label()
        form.addRow("", self.name_error)
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("الهاتف (اختياري)")
        form.addRow("الهاتف:", self.phone_edit)
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("العنوان (اختياري)")
        form.addRow("العنوان:", self.address_edit)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        save_btn.setObjectName("primary")
        cancel_btn = QPushButton("إلغاء")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        self.install_form_shortcuts(self.save)
        apply_modern_dialog(self, 'إضافة عميل/مورد')
        self.watch_dirty_widgets([self.name_edit, self.phone_edit, self.address_edit], reset=True)

    def save(self):
        validator = FormValidator()
        if not validator.required(self.name_edit, self.name_error, "الاسم"):
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
            show_toast("تمت الإضافة", "success", self)
            self.accept()
        except Exception as e:
            show_toast(str(e), "error", self)


