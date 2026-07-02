# -*- coding: utf-8 -*-
"""Professional inline quick-create panel used across document surfaces.

The widget is intentionally inline-first and never opens separate workspace tabs.  It saves through existing services/gateways so local,
client/server, permissions and audit behavior remain consistent.
"""
from __future__ import annotations

from typing import Any, Dict

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from i18n import qt_layout_direction, translate
from utils import show_toast
from ui.visual_state import set_visual_state
from ui.inline_quick_create_registry import definition_for


def _tr(key: str, **kwargs) -> str:
    return translate(key, **kwargs)


def quick_create_can(entity_type: str) -> bool:
    """Return whether the current user/session may create the entity inline."""
    try:
        entity = str(entity_type or "").strip().lower()
        if entity == "category":
            from core.services.category_operation_policy import category_operation_policy
            return bool(category_operation_policy.can(category_operation_policy.OP_CREATE))
        if entity == "customer":
            from core.services.party_operation_policy import party_operation_policy
            return bool(party_operation_policy.can(party_operation_policy.OP_CUSTOMER_CREATE))
        if entity == "supplier":
            from core.services.party_operation_policy import party_operation_policy
            return bool(party_operation_policy.can(party_operation_policy.OP_SUPPLIER_CREATE))
        if entity == "item":
            from core.services.permission_service import permission_service
            return bool(permission_service.can(permission_service.ACTION_EDIT_ITEMS))
        if entity == "unit":
            return True
        if entity == "cashbox":
            from core.services.finance_operation_policy import finance_operation_policy
            return bool(finance_operation_policy.can(finance_operation_policy.OP_CASHBOX_CREATE))
        if entity == "bank_account":
            from core.services.finance_operation_policy import finance_operation_policy
            return bool(finance_operation_policy.can(finance_operation_policy.OP_BANK_CREATE))
        if entity == "warehouse":
            from core.services.inventory_operation_policy import inventory_operation_policy
            return bool(inventory_operation_policy.can(inventory_operation_policy.OP_WAREHOUSE_CREATE))
    except Exception:
        return False
    return False


class InlineQuickCreatePanel(QFrame):
    """Reusable inline create card with save-and-select behavior."""

    created = pyqtSignal(str, dict)
    cancelled = pyqtSignal(str)

    def __init__(self, entity_type: str, parent=None, *, context: Dict[str, Any] | None = None) -> None:
        super().__init__(parent)
        self.entity_type = str(entity_type or "").strip().lower()
        self.definition = definition_for(self.entity_type)
        self.context: Dict[str, Any] = dict(context or {})
        self.inputs: Dict[str, Any] = {}
        self.setObjectName(f"InlineQuickCreatePanel_{self.entity_type}")
        self.setProperty("visualRole", "inline_quick_create_panel")
        self.setProperty("quickCreateEntity", self.entity_type)
        self.setProperty("quickCreateMode", self.definition.mode)
        self.setProperty("phase", "460")
        self.setLayoutDirection(qt_layout_direction())
        self._build_ui()
        self.setVisible(False)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        title = QLabel(_tr(self.definition.title_key))
        title.setObjectName("InlineQuickCreateTitle")
        subtitle = QLabel(_tr(self.definition.subtitle_key))
        subtitle.setObjectName("InlineQuickCreateSubtitle")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        self.error_label = QLabel("")
        self.error_label.setObjectName("InlineQuickCreateError")
        self.error_label.setVisible(False)
        set_visual_state(self.error_label, "danger", weight="strong", size="caption", role="semantic_status")

        form = QFormLayout()
        form.setObjectName("InlineQuickCreateForm")
        form.setLabelAlignment(Qt.AlignRight)
        for field in self.definition.fields:
            widget = self._make_widget(field)
            self.inputs[field.name] = widget
            label = _tr(field.label_key) + (" *" if field.required else "")
            form.addRow(label, widget)
        root.addLayout(form)
        root.addWidget(self.error_label)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.cancel_btn = QPushButton(_tr("cancel"))
        self.cancel_btn.setObjectName("InlineQuickCreateCancelButton")
        self.cancel_btn.setProperty("visualRole", "document_secondary_action")
        self.save_btn = QPushButton(_tr(self.definition.save_label_key))
        self.save_btn.setObjectName("InlineQuickCreateSaveButton")
        self.save_btn.setProperty("visualRole", "document_primary_action")
        self.cancel_btn.clicked.connect(self.cancel)
        self.save_btn.clicked.connect(self.save)
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.save_btn)
        root.addLayout(actions)

    def _make_widget(self, field):
        if field.widget == "combo":
            combo = QComboBox(self)
            combo.setObjectName(f"InlineQuickCreate_{self.entity_type}_{field.name}")
            self._load_combo(field.name, combo)
            return combo
        if field.widget == "text_edit":
            edit = QTextEdit(self)
            edit.setObjectName(f"InlineQuickCreate_{self.entity_type}_{field.name}")
            edit.setFixedHeight(64)
            if field.placeholder_key:
                edit.setPlaceholderText(_tr(field.placeholder_key))
            return edit
        if field.widget == "decimal":
            spin = QDoubleSpinBox(self)
            spin.setObjectName(f"InlineQuickCreate_{self.entity_type}_{field.name}")
            spin.setRange(0, 999999999)
            spin.setDecimals(3 if field.name == "conversion_factor" else 2)
            if field.name == "conversion_factor":
                spin.setValue(1)
            return spin
        edit = QLineEdit(self)
        edit.setObjectName(f"InlineQuickCreate_{self.entity_type}_{field.name}")
        if field.placeholder_key:
            edit.setPlaceholderText(_tr(field.placeholder_key))
        return edit

    def _load_combo(self, field_name: str, combo: QComboBox) -> None:
        if field_name == "parent_id":
            combo.addItem(_tr("no_parent"), None)
            for category in self.context.get("categories", []) or []:
                combo.addItem(category.get("full_name") or category.get("name", ""), category.get("id"))
            return
        if field_name == "category_id":
            combo.addItem(_tr("no_category"), None)
            rows = self.context.get("categories")
            if rows is None:
                try:
                    from core.services.product_service import product_service
                    rows = product_service.categories()
                except Exception:
                    rows = []
            for category in rows or []:
                combo.addItem(category.get("full_name") or category.get("name", ""), category.get("id"))
            return
        if field_name == "branch_id":
            rows = self.context.get("branches")
            default_id = self.context.get("branch_id")
            if rows is None:
                try:
                    from core.services.branch_service import branch_service
                    rows = branch_service.branches(include_archived=False)
                    default_id = default_id or branch_service.current_branch_id() or branch_service.default_branch_id()
                except Exception:
                    rows = []
            for branch in rows or []:
                combo.addItem(branch.get("name") or str(branch.get("id") or ""), branch.get("id"))
            if default_id is not None:
                idx = combo.findData(default_id)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            return

    def set_context(self, **context: Any) -> None:
        self.context.update(context)
        for field in self.definition.fields:
            widget = self.inputs.get(field.name)
            if isinstance(widget, QComboBox):
                current = widget.currentData()
                widget.blockSignals(True)
                widget.clear()
                self._load_combo(field.name, widget)
                if current is not None:
                    idx = widget.findData(current)
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
                widget.blockSignals(False)

    def show_panel(self, focus_first: bool = True) -> None:
        if not quick_create_can(self.entity_type):
            show_toast(_tr("inline_quick_create_permission_denied"), "warning", self)
            return
        self.setVisible(True)
        self.error_label.setVisible(False)
        if focus_first:
            for widget in self.inputs.values():
                if hasattr(widget, "setFocus"):
                    widget.setFocus()
                    if hasattr(widget, "selectAll"):
                        widget.selectAll()
                    break

    def toggle_panel(self) -> None:
        if self.isVisible():
            self.cancel()
        else:
            self.show_panel()

    def cancel(self) -> None:
        self.clear_inputs()
        self.setVisible(False)
        self.cancelled.emit(self.entity_type)

    def clear_inputs(self) -> None:
        for widget in self.inputs.values():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(1 if widget.objectName().endswith("conversion_factor") else 0)
            elif isinstance(widget, QComboBox) and widget.count():
                widget.setCurrentIndex(0)
        self.error_label.clear()
        self.error_label.setVisible(False)

    def payload(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        for field in self.definition.fields:
            widget = self.inputs.get(field.name)
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText().strip()
            elif isinstance(widget, QDoubleSpinBox):
                value = widget.value()
            elif isinstance(widget, QComboBox):
                value = widget.currentData()
            else:
                value = None
            data[field.name] = value
        return data

    def _validate(self, data: Dict[str, Any]) -> bool:
        for field in self.definition.fields:
            if field.required and not str(data.get(field.name) or "").strip():
                self._show_error(_tr("inline_quick_create_required", field=_tr(field.label_key)))
                widget = self.inputs.get(field.name)
                if hasattr(widget, "setFocus"):
                    widget.setFocus()
                return False
        return True

    def _show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        show_toast(message, "error", self)

    def _find_existing_category(self, name: str, parent_id: Any):
        normalized = str(name or "").strip().casefold()
        parent = int(parent_id or 0)
        for category in self.context.get("categories", []) or []:
            if str(category.get("name") or "").strip().casefold() == normalized and int(category.get("parent_id") or 0) == parent:
                return category
        return None

    def _find_existing_party(self, entity: str, name: str, phone: str = ""):
        try:
            from core.services.catalog_service import catalog_service
            rows = catalog_service.customers(limit=500) if entity == "customer" else catalog_service.suppliers(limit=500)
        except Exception:
            rows = []
        normalized = str(name or "").strip().casefold()
        phone_norm = str(phone or "").strip()
        for row in rows or []:
            if str(row.get("name") or "").strip().casefold() == normalized:
                if not phone_norm or str(row.get("phone") or "").strip() == phone_norm:
                    return row
        return None

    def _find_existing_cashbox(self, name: str, branch_id: Any):
        try:
            from core.services.cashbox_service import cashbox_service
            rows = cashbox_service.cashboxes(include_archived=False)
        except Exception:
            rows = []
        normalized = str(name or "").strip().casefold()
        branch_norm = str(branch_id or "").strip()
        for row in rows or []:
            if str(row.get("name") or "").strip().casefold() == normalized:
                if not branch_norm or str(row.get("branch_id") or "").strip() == branch_norm:
                    return row
        return None

    def _find_existing_bank_account(self, bank_name: str, account_number: str = "", branch_id: Any = None):
        try:
            from core.services.cashbox_service import cashbox_service
            rows = cashbox_service.bank_accounts(include_archived=False)
        except Exception:
            rows = []
        bank_norm = str(bank_name or "").strip().casefold()
        number_norm = str(account_number or "").strip()
        branch_norm = str(branch_id or "").strip()
        for row in rows or []:
            if str(row.get("bank_name") or "").strip().casefold() == bank_norm:
                number_matches = not number_norm or str(row.get("account_number") or "").strip() == number_norm
                branch_matches = not branch_norm or str(row.get("branch_id") or "").strip() == branch_norm
                if number_matches and branch_matches:
                    return row
        return None

    def _find_existing_warehouse(self, name: str, code: str = "", branch_id: Any = None):
        try:
            from core.services.warehouse_service import warehouse_service
            rows = warehouse_service.warehouses(include_archived=False)
        except Exception:
            rows = []
        name_norm = str(name or "").strip().casefold()
        code_norm = str(code or "").strip().casefold()
        branch_norm = str(branch_id or "").strip()
        for row in rows or []:
            same_name = str(row.get("name") or "").strip().casefold() == name_norm
            same_code = bool(code_norm) and str(row.get("code") or "").strip().casefold() == code_norm
            same_branch = not branch_norm or str(row.get("branch_id") or "").strip() == branch_norm
            if same_branch and (same_name or same_code):
                return row
        return None

    def _save_category(self, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._find_existing_category(data.get("name"), data.get("parent_id"))
        if existing:
            return {"id": existing.get("id"), "name": existing.get("name"), "existing": True}
        from core.services.product_service import product_service
        new_id = product_service.add_category({
            "name": str(data.get("name") or "").strip(),
            "parent_id": data.get("parent_id"),
            "description": str(data.get("description") or "").strip(),
            "color": "#64748B",
            "icon": "folder",
            "is_active": 1,
        })
        return {"id": new_id, "name": data.get("name"), "existing": False}

    def _save_party(self, entity: str, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._find_existing_party(entity, data.get("name"), data.get("phone"))
        if existing:
            return {"id": existing.get("id"), "name": existing.get("name"), "existing": True}
        from core.services.entity_service import entity_service
        name = str(data.get("name") or "").strip()
        phone = str(data.get("phone") or "").strip()
        address = str(data.get("address") or "").strip()
        new_id = entity_service.add_customer(name, phone, address) if entity == "customer" else entity_service.add_supplier(name, phone, address)
        return {"id": new_id, "name": name, "existing": False}

    def _save_unit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Unit quick-create is contextual for material forms.  The host persists
        # units with the material through ProductService.replace_units().
        name = str(data.get("unit_name") or "").strip()
        return {
            "id": name,
            "unit_name": name,
            "conversion_factor": float(data.get("conversion_factor") or 1),
            "barcode": str(data.get("barcode") or "").strip(),
            "existing": False,
        }

    def _save_cashbox(self, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._find_existing_cashbox(data.get("name"), data.get("branch_id"))
        if existing:
            return {"id": existing.get("id"), "name": existing.get("name"), "existing": True}
        from core.services.branch_service import branch_service
        from core.services.cashbox_service import cashbox_service
        branch_id = data.get("branch_id") or branch_service.current_branch_id() or branch_service.default_branch_id()
        payload = {
            "branch_id": branch_id,
            "name": str(data.get("name") or "").strip(),
            "notes": str(data.get("notes") or "").strip(),
            "is_active": 1,
        }
        new_id = cashbox_service.add_cashbox(payload)
        return {"id": new_id, "name": payload["name"], "branch_id": branch_id, "existing": False}

    def _save_bank_account(self, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._find_existing_bank_account(data.get("bank_name"), data.get("account_number"), data.get("branch_id"))
        if existing:
            name = existing.get("bank_name") or existing.get("account_name") or str(existing.get("id"))
            return {"id": existing.get("id"), "name": name, "existing": True}
        from core.services.branch_service import branch_service
        from core.services.cashbox_service import cashbox_service
        branch_id = data.get("branch_id") or branch_service.current_branch_id() or branch_service.default_branch_id()
        payload = {
            "branch_id": branch_id,
            "bank_name": str(data.get("bank_name") or "").strip(),
            "account_name": str(data.get("account_name") or "").strip(),
            "account_number": str(data.get("account_number") or "").strip(),
            "iban": "",
            "notes": str(data.get("notes") or "").strip(),
            "is_active": 1,
        }
        new_id = cashbox_service.add_bank_account(payload)
        label = payload["bank_name"] or payload["account_name"]
        return {"id": new_id, "name": label, "branch_id": branch_id, "existing": False}

    def _save_warehouse(self, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self._find_existing_warehouse(data.get("name"), data.get("code"), data.get("branch_id"))
        if existing:
            return {"id": existing.get("id"), "name": existing.get("name"), "code": existing.get("code"), "existing": True}
        from core.services.branch_service import branch_service
        from core.services.warehouse_service import warehouse_service
        branch_id = data.get("branch_id") or branch_service.current_branch_id() or branch_service.default_branch_id()
        payload = {
            "name": str(data.get("name") or "").strip(),
            "code": str(data.get("code") or "").strip(),
            "branch_id": branch_id,
            "location": str(data.get("location") or "").strip(),
            "notes": str(data.get("notes") or "").strip(),
            "is_active": 1,
        }
        new_id = warehouse_service.add_warehouse(payload)
        return {"id": new_id, "name": payload["name"], "code": payload.get("code"), "branch_id": branch_id, "existing": False}

    def _save_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from core.item_types import STOCK
        from core.services.product_service import product_service
        item_type = self.context.get("item_type") or STOCK
        payload = {
            "name": str(data.get("name") or "").strip(),
            "barcode": str(data.get("barcode") or "").strip() or None,
            "category_id": data.get("category_id"),
            "unit": str(data.get("unit") or _tr("unit_piece")).strip(),
            "selling_price": float(data.get("selling_price") or 0),
            "purchase_price": float(data.get("purchase_price") or 0),
            "quantity": 0,
            "reorder_level": 0,
            "item_type": item_type,
            "units": [],
        }
        new_id = product_service.add_item(payload)
        return {
            "id": new_id,
            "name": payload["name"],
            "barcode": payload.get("barcode"),
            "category_id": payload.get("category_id"),
            "unit": payload.get("unit"),
            "existing": False,
        }

    def save(self) -> None:
        if not quick_create_can(self.entity_type):
            self._show_error(_tr("inline_quick_create_permission_denied"))
            return
        data = self.payload()
        if not self._validate(data):
            return
        try:
            if self.entity_type == "category":
                result = self._save_category(data)
            elif self.entity_type in ("customer", "supplier"):
                result = self._save_party(self.entity_type, data)
            elif self.entity_type == "unit":
                result = self._save_unit(data)
            elif self.entity_type == "cashbox":
                result = self._save_cashbox(data)
            elif self.entity_type == "bank_account":
                result = self._save_bank_account(data)
            elif self.entity_type == "warehouse":
                result = self._save_warehouse(data)
            elif self.entity_type == "item":
                result = self._save_item(data)
            else:
                raise ValueError(f"Unsupported inline quick create entity: {self.entity_type}")
            result["entity_type"] = self.entity_type
            self.created.emit(self.entity_type, result)
            show_toast(_tr("inline_quick_create_existing_selected") if result.get("existing") else _tr("inline_quick_create_saved_selected"), "info" if result.get("existing") else "success", self)
            self.clear_inputs()
            self.setVisible(False)
        except Exception as exc:
            self._show_error(_tr("inline_quick_create_failed", error=str(exc)))
